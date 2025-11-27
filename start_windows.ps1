#requires -Version 5.1
param(
    [int]$ApiPort = 8006,
    [int]$ElasticPort = 9200,
    [string]$ElasticImage = "docker.elastic.co/elasticsearch/elasticsearch:8.13.4"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok { param($Message) Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$logsDir = Join-Path $projectRoot "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function Resolve-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command py -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        throw "python/py 不在 PATH 中，请安装 Python 3.10+ 或将其加入 PATH"
    }
    return $python.Path
}

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name 未安装或不在 PATH 中"
    }
    return $command.Path
}

function Test-PortInUse {
    param([int]$Port)
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        return $null -ne $conn
    } catch {
        return $false
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$Retries = 60,
        [int]$DelaySeconds = 2
    )

    Write-Info "等待 $ServiceName 启动..."
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Ok "$ServiceName 已就绪"
                return $true
            }
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    Write-Err "$ServiceName 在预期时间内未响应"
    return $false
}

function Ensure-Venv {
    $activateScript = Join-Path $projectRoot "contract_env/Scripts/Activate.ps1"
    if (Test-Path $activateScript) {
        . $activateScript
        Write-Info "已激活虚拟环境 contract_env"
    }
}

function Ensure-Elasticsearch {
    param(
        [string]$Image,
        [int]$Port
    )

    try {
        Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Ok "Elasticsearch 已在运行 (http://localhost:$Port)"
        return
    } catch {}

    Require-Command "docker" | Out-Null
    Write-Info "启动 Elasticsearch (容器名: es)..."

    $exists = docker ps -a --format "{{.Names}}" | Select-String -Quiet "^es$"
    if ($exists) {
        $running = docker ps --format "{{.Names}}" | Select-String -Quiet "^es$"
        if (-not $running) {
            docker start es | Out-Null
        }
    } else {
        docker run -d --name es `
            -p "$Port`:9200" `
            -e "discovery.type=single-node" `
            -e "xpack.security.enabled=false" `
            -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" `
            $Image | Out-Null
    }

    if (-not (Wait-HttpOk -Url "http://localhost:$Port" -ServiceName "Elasticsearch" -Retries 60 -DelaySeconds 3)) {
        throw "Elasticsearch 启动失败，请检查 Docker 日志"
    }
}

function Install-BackendDeps {
    param([string]$PythonPath)

    $requirements = Join-Path $backendDir "requirements.txt"
    if (-not (Test-Path $requirements)) {
        Write-Warn "未找到 backend/requirements.txt，跳过后端依赖安装"
        return
    }

    Write-Info "安装后端依赖..."
    Push-Location $backendDir
    Ensure-Venv
    & $PythonPath -m pip install -r $requirements 2>&1 | Tee-Object -FilePath (Join-Path $logsDir "backend.log")
    if ($LASTEXITCODE -ne 0) {
        throw "后端依赖安装失败，查看 logs/backend.log"
    }
    Pop-Location
    Write-Ok "后端依赖安装完成"
}

function Build-Frontend {
    param([string]$NpmPath)

    $frontendLog = Join-Path $logsDir "frontend.log"
    Push-Location $frontendDir

    if (-not (Test-Path "node_modules")) {
        Write-Info "安装前端依赖..."
        & $NpmPath install 2>&1 | Tee-Object -FilePath $frontendLog
        if ($LASTEXITCODE -ne 0) {
            throw "前端依赖安装失败，查看 logs/frontend.log"
        }
    } else {
        Write-Info "前端依赖已存在，跳过 npm install"
    }

    Write-Info "构建前端静态资源..."
    & $NpmPath run build 2>&1 | Tee-Object -FilePath $frontendLog -Append
    if ($LASTEXITCODE -ne 0) {
        throw "前端构建失败，查看 logs/frontend.log"
    }

    Pop-Location
    Write-Ok "前端构建完成"
}

function Create-Index {
    param([string]$PythonPath)

    Write-Info "检查并创建 Elasticsearch 索引..."
    try {
        Invoke-WebRequest -Uri "http://localhost:$ElasticPort/contracts_unified" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Ok "索引 contracts_unified 已存在"
        return
    } catch {}

    Push-Location $backendDir
    Ensure-Venv
    & $PythonPath create_unified_index.py
    if ($LASTEXITCODE -ne 0) {
        throw "索引创建失败，请检查 logs/backend.log"
    }
    Pop-Location
    Write-Ok "索引创建完成"
}

function Start-Backend {
    param(
        [string]$PythonPath,
        [int]$Port
    )

    if (Test-PortInUse -Port $Port) {
        throw "端口 $Port 已被占用，请先停止占用该端口的进程"
    }

    Write-Info "启动后端服务..."
    $backendLog = Join-Path $logsDir "backend.log"
    Push-Location $backendDir
    Ensure-Venv

    $process = Start-Process -FilePath $PythonPath `
        -ArgumentList "contractApi.py" `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $backendLog `
        -RedirectStandardError $backendLog `
        -PassThru

    Set-Content -Path (Join-Path $logsDir "backend.pid") -Value $process.Id
    Pop-Location

    if (-not (Wait-HttpOk -Url "http://localhost:$Port/docs" -ServiceName "后端 API" -Retries 90 -DelaySeconds 2)) {
        throw "后端未按预期启动，请查看 logs/backend.log"
    }

    Write-Ok "后端服务已启动 (PID: $($process.Id))"
}

Write-Host ""
Write-Info "========== 合同智能检索项目启动 (Windows) =========="

try {
    $pythonPath = Resolve-Python
    $npmPath = Require-Command "npm"

    Ensure-Elasticsearch -Image $ElasticImage -Port $ElasticPort
    Install-BackendDeps -PythonPath $pythonPath
    Build-Frontend -NpmPath $npmPath
    Create-Index -PythonPath $pythonPath
    Start-Backend -PythonPath $pythonPath -Port $ApiPort

    Write-Host ""
    Write-Ok "服务启动完成"
    Write-Host "Elasticsearch: http://localhost:$ElasticPort"
    Write-Host "后端 API: http://localhost:$ApiPort"
    Write-Host "API 文档: http://localhost:$ApiPort/docs"
    Write-Host "日志: $logsDir"
    Write-Host "停止服务: 使用 Task Manager 或根据 logs/backend.pid 结束对应进程 (可另写 stop_windows.ps1)"
} catch {
    Write-Err $_
    exit 1
}
