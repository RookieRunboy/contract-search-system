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
    # Use explicit Python path that we know works
    $pythonPath = "C:\Users\lenovo\AppData\Local\Programs\Python\Python312\python.exe"
    if (-not (Test-Path $pythonPath)) {
        throw "Python executable not found at expected path: $pythonPath"
    }
    return $pythonPath
}

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name is not installed or not in PATH"
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

    Write-Info "Waiting for $ServiceName to start..."
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Ok "$ServiceName is ready"
                return $true
            }
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    Write-Err "$ServiceName did not respond within expected time"
    return $false
}

function Ensure-Venv {
    $activateScript = Join-Path $projectRoot "contract_env/Scripts/Activate.ps1"
    if (Test-Path $activateScript) {
        . $activateScript
        Write-Info "Activated virtual environment contract_env"
    }
}

function Ensure-Elasticsearch {
    param(
        [string]$Image,
        [int]$Port
    )

    try {
        Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Ok "Elasticsearch is already running (http://localhost:$Port)"
        return
    } catch {}

    Require-Command "docker" | Out-Null
    Write-Info "Starting Elasticsearch (container name: es)..."

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
        throw "Elasticsearch failed to start. Please check Docker logs"
    }
}

function Install-BackendDeps {
    param([string]$PythonPath)

    $requirements = Join-Path $backendDir "requirements.txt"
    if (-not (Test-Path $requirements)) {
        Write-Warn "backend/requirements.txt not found, skipping backend dependency installation"
        return
    }

    Write-Info "Installing backend dependencies..."
    Write-Info "Backend directory: $backendDir"
    Write-Info "Requirements file: $requirements"
    Write-Info "Python path: $PythonPath"
    Write-Info "Python version: $(& $PythonPath --version)"
    Write-Info "Pip version: $(& $PythonPath -m pip --version)"

    # Ensure logs directory exists
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
        Write-Info "Created logs directory: $logsDir"
    }

    $logFile = Join-Path $logsDir "backend.log"
    Write-Info "Log file: $logFile"

    try {
        Write-Info "Installing dependencies from requirements.txt..."
        $result = & $PythonPath -m pip install -r $requirements 2>&1
        $result | Out-File -FilePath $logFile -Append
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to install backend dependencies. Check $logFile"
            exit 1
        }
        Write-Ok "Backend dependencies installed successfully"
    } catch {
        Write-Err "Exception during dependency installation: $_"
        $_ | Out-File -FilePath $logFile -Append
        exit 1
    }
}

function Build-Frontend {
    param([string]$NpmPath)

    $frontendLog = Join-Path $logsDir "frontend.log"
    Push-Location $frontendDir

    # npm/vite prints chunk-size warnings to stderr; with ErrorActionPreference=Stop they can be treated as terminating.
    # Relax to Continue during the build and restore afterward.
    try {
        $ErrorActionPreference = "Continue"

        if (-not (Test-Path "node_modules")) {
            Write-Info "Installing frontend dependencies..."
            & $NpmPath install 2>&1 | Tee-Object -FilePath $frontendLog
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install frontend dependencies. Check logs/frontend.log"
            }
        } else {
            Write-Info "Frontend dependencies already exist, skipping npm install"
        }

        Write-Info "Building frontend static assets..."
        & $NpmPath run build 2>&1 | Tee-Object -FilePath $frontendLog -Append
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to build frontend. Check logs/frontend.log"
        }

        Write-Ok "Frontend built successfully"
    } finally {
        $ErrorActionPreference = "Stop"
        Pop-Location
    }
}

function Create-Index {
    param([string]$PythonPath)

    Write-Info "Checking and creating Elasticsearch index..."
    try {
        Invoke-WebRequest -Uri "http://localhost:$ElasticPort/contracts_unified" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Ok "Index contracts_unified already exists"
        return
    } catch {}

    Push-Location $backendDir
    Ensure-Venv
    & $PythonPath create_unified_index.py
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create index. Please check logs/backend.log"
    }
    Pop-Location
    Write-Ok "Index created successfully"
}

function Start-Backend {
    param(
        [string]$PythonPath,
        [int]$Port
    )

    if (Test-PortInUse -Port $Port) {
        throw "Port $Port is already in use. Please stop the process occupying this port first"
    }

    Write-Info "Starting backend service..."
    $backendStdOut = Join-Path $logsDir "backend.log"
    $backendStdErr = Join-Path $logsDir "backend.err.log"
    Push-Location $backendDir
    Ensure-Venv

    # 加载环境变量
    $envFile = Join-Path $backendDir ".env"
    if (Test-Path $envFile) {
        Write-Info "Loading environment variables from $envFile"
        Get-Content $envFile | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith("#")) {
                $key, $value = $line.Split('=', 2)
                if ($key -and $value) {
                    Set-Content -Path "env:\$key" -Value $value
                    Write-Info "Set environment variable: $key"
                }
            }
        }
    } else {
        Write-Warn "Environment file $envFile not found, proceeding without it"
    }

    $process = Start-Process -FilePath $PythonPath `
        -ArgumentList "contractApi.py" `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $backendStdOut `
        -RedirectStandardError $backendStdErr `
        -PassThru

    Set-Content -Path (Join-Path $logsDir "backend.pid") -Value $process.Id
    Pop-Location

    if (-not (Wait-HttpOk -Url "http://localhost:$Port/docs" -ServiceName "Backend API" -Retries 90 -DelaySeconds 2)) {
        throw "Backend did not start as expected. Please check logs/backend.log"
    }

    Write-Ok "Backend service started (PID: $($process.Id))"
}

Write-Host ""
Write-Info "========== Contract Smart Search Project Startup (Windows) =========="

try {
    $pythonPath = Resolve-Python
    $npmPath = Require-Command "npm"

    Ensure-Elasticsearch -Image $ElasticImage -Port $ElasticPort
    Install-BackendDeps -PythonPath $pythonPath
    Build-Frontend -NpmPath $npmPath
    Create-Index -PythonPath $pythonPath
    Start-Backend -PythonPath $pythonPath -Port $ApiPort

    Write-Host ""
    Write-Ok "Service startup completed"
    Write-Host "Elasticsearch: http://localhost:$ElasticPort"
    Write-Host "Backend API: http://localhost:$ApiPort"
    Write-Host "API Documentation: http://localhost:$ApiPort/docs"
    Write-Host "Logs: $logsDir"
    Write-Host "Stop service: Use Task Manager or kill process based on logs/backend.pid (or use stop_windows.ps1)"
} catch {
    Write-Err $_
    exit 1
}
