#requires -Version 5.1
param(
    [switch]$StopElasticsearch,
    [int]$ElasticPort = 9200
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok { param($Message) Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$logsDir = Join-Path $projectRoot "logs"
$pidFile = Join-Path $logsDir "backend.pid"

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name 未安装或不在 PATH 中"
    }
    return $command.Path
}

function Stop-Backend {
    if (-not (Test-Path $pidFile)) {
        Write-Warn "未找到 $pidFile，可能尚未启动或已手动停止"
        return
    }

    try {
        $pidText = Get-Content $pidFile -ErrorAction Stop | Select-Object -First 1
    } catch {
        Write-Warn "读取 $pidFile 失败：$_"
        return
    }

    $pid = 0
    if (-not [int]::TryParse($pidText, [ref]$pid)) {
        Write-Warn "PID 内容无效：'$pidText'"
        return
    }

    try {
        $proc = Get-Process -Id $pid -ErrorAction Stop
    } catch {
        Write-Warn "PID $pid 对应的进程不存在，移除无效的 PID 文件"
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
        return
    }

    Write-Info "停止后端进程 (PID: $pid)..."
    try {
        Stop-Process -Id $pid -ErrorAction Stop
        Write-Ok "后端进程已停止"
    } catch {
        Write-Err "停止后端进程失败：$_"
        return
    } finally {
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
    }
}

function Stop-Elasticsearch {
    param([int]$Port)

    if (-not $StopElasticsearch) {
        return
    }

    try {
        Require-Command "docker" | Out-Null
    } catch {
        Write-Warn "未安装 Docker，跳过停止 Elasticsearch 容器"
        return
    }

    $running = docker ps --format "{{.Names}}" | Select-String -Quiet "^es$"
    $existing = docker ps -a --format "{{.Names}}" | Select-String -Quiet "^es$"

    if ($running) {
        Write-Info "停止 Elasticsearch 容器 es (端口 $Port)..."
        docker stop es | Out-Null
        Write-Ok "Elasticsearch 容器已停止"
    } elseif ($existing) {
        Write-Warn "容器 es 存在但未运行，未执行停止操作"
    } else {
        Write-Warn "未找到名为 es 的容器，跳过"
    }
}

Write-Host ""
Write-Info "========== 停止合同智能检索项目 (Windows) =========="

try {
    Stop-Backend
    Stop-Elasticsearch -Port $ElasticPort
    Write-Host ""
    Write-Ok "停止流程完成"
    Write-Host "日志目录: $logsDir"
} catch {
    Write-Err $_
    exit 1
}
