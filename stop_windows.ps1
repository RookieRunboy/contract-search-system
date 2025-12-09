#requires -Version 5.1
param(
    [switch]$StopElasticsearch,
    [int]$ElasticPort = 9200
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info { param($Message) Write-Host "[INFO]  $Message" -ForegroundColor Cyan }
function Write-Ok   { param($Message) Write-Host "[OK]    $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN]  $Message" -ForegroundColor Yellow }
function Write-Err  { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$logsDir     = Join-Path $projectRoot "logs"
$pidFile     = Join-Path $logsDir "backend.pid"

function Require-Command {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name is not installed or not in PATH"
    }
    return $command.Path
}

function Stop-Backend {
    if (-not (Test-Path $pidFile)) {
        Write-Warn "PID file not found ($pidFile); backend may not be running"
        return
    }

    try {
        $pidText = Get-Content $pidFile -ErrorAction Stop | Select-Object -First 1
    } catch {
        Write-Warn "Failed to read ${pidFile}: $_"
        return
    }

    $backendPid = 0
    if (-not [int]::TryParse($pidText, [ref]$backendPid)) {
        Write-Warn "Invalid PID content: '$pidText'"
        return
    }

    try {
        $proc = Get-Process -Id $backendPid -ErrorAction Stop
    } catch {
        Write-Warn "PID $backendPid does not exist; removing stale pid file"
        Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
        return
    }

    Write-Info "Stopping backend process (PID: $backendPid)..."
    try {
        Stop-Process -Id $backendPid -ErrorAction Stop
        Write-Ok "Backend process stopped"
    } catch {
        Write-Err "Failed to stop backend process: $_"
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
        Write-Warn "Docker not installed; skipping Elasticsearch stop"
        return
    }

    $running  = docker ps --format "{{.Names}}" | Select-String -Quiet "^es$"
    $existing = docker ps -a --format "{{.Names}}" | Select-String -Quiet "^es$"

    if ($running) {
        Write-Info "Stopping Elasticsearch container es (port $Port)..."
        docker stop es | Out-Null
        Write-Ok "Elasticsearch container stopped"
    } elseif ($existing) {
        Write-Warn "Container es exists but is not running; no action taken"
    } else {
        Write-Warn "No container named 'es' found; skipping"
    }
}

Write-Host ""
Write-Info "========== Stop Contract Smart Search (Windows) =========="

try {
    Stop-Backend
    Stop-Elasticsearch -Port $ElasticPort
    Write-Host ""
    Write-Ok "Stop flow completed"
    Write-Host "Logs directory: $logsDir"
} catch {
    Write-Err $_
    exit 1
}
