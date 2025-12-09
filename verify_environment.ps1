#!/usr/bin/env powershell
#requires -Version 5.1

<#
.SYNOPSIS
    Verify environment and dependencies for Contract Search System on Windows Server
.DESCRIPTION
    Checks all required dependencies including Python, Node.js, Docker, and project structure
.EXAMPLE
    .\verify_environment.ps1
#>

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok { param($Message) Write-Host "[OK]   $Message" -ForegroundColor Green }
function Write-Warn { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Heading { param($Message) Write-Host "\n========== $Message ==========" -ForegroundColor Magenta }

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

Write-Heading "Contract Search System Environment Verification"
Write-Host "Project Root: $projectRoot\n"

# Check Windows PowerShell version
Write-Heading "1. Basic Environment Check"
$psVersion = $PSVersionTable.PSVersion
if ($psVersion.Major -lt 5) {
    Write-Err "PowerShell version too low, need 5.1 or higher"
    Write-Err "Current version: $($psVersion.Major).$($psVersion.Minor)"
} else {
    Write-Ok "PowerShell version: $($psVersion.Major).$($psVersion.Minor)"
}

# Check Python environment
function Check-Python {
    Write-Heading "2. Python Environment Check"
    
    $python = $null
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command py -ErrorAction SilentlyContinue
    }
    
    if (-not $python) {
        Write-Err "Python not found, please install Python 3.10 or higher"
        Write-Info "Recommended: Python 3.10+ (https://www.python.org/downloads/)"
        return $false
    }
    
    try {
        $versionOutput = & $python.Path --version 2>&1
        $versionMatch = [regex]::Match($versionOutput, 'Python (\d+)\.(\d+)\.(\d+)')
        
        if ($versionMatch.Success) {
            $major = [int]$versionMatch.Groups[1].Value
            $minor = [int]$versionMatch.Groups[2].Value
            $patch = [int]$versionMatch.Groups[3].Value
            
            Write-Info "Python Path: $($python.Path)"
            Write-Info "Python Version: $major.$minor.$patch"
            
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
                Write-Err "Python version too low, need 3.10 or higher"
                return $false
            } else {
                Write-Ok "Python version meets requirements (3.10+)"
                return $true
            }
        } else {
            Write-Err "Cannot parse Python version info"
            return $false
        }
    } catch {
        Write-Err "Error checking Python version: $_"
        return $false
    }
}

# Check Node.js environment
function Check-Nodejs {
    Write-Heading "3. Node.js Environment Check"
    
    try {
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $npm) {
            Write-Err "Node.js/npm not found, please install Node.js 16 or higher"
            Write-Info "Recommended: Node.js 16+ (https://nodejs.org/en/download/)"
            return $false
        }
        
        $versionOutput = & $npm.Path --version 2>&1
        Write-Info "npm Path: $($npm.Path)"
        Write-Info "npm Version: $versionOutput"
        
        $node = Get-Command node -ErrorAction SilentlyContinue
        if ($node) {
            $nodeVersion = & $node.Path --version 2>&1
            Write-Info "Node.js Version: $nodeVersion"
        }
        
        Write-Ok "Node.js/npm installed"
        return $true
    } catch {
        Write-Err "Error checking Node.js environment: $_"
        return $false
    }
}

# Check Docker environment
function Check-Docker {
    Write-Heading "4. Docker Environment Check"
    
    try {
        $docker = Get-Command docker -ErrorAction SilentlyContinue
        if (-not $docker) {
            Write-Warn "Docker not found, please install Docker Desktop for Windows"
            Write-Info "Recommended: Docker Desktop (https://www.docker.com/products/docker-desktop/)"
            Write-Info "Note: Docker is required for running Elasticsearch"
            return $false
        }
        
        Write-Info "Docker Path: $($docker.Path)"
        
        # Check if Docker is running
        try {
            & $docker.Path info | Out-Null
            Write-Ok "Docker installed and running"
            return $true
        } catch {
            Write-Warn "Docker installed but not running, please start Docker Desktop"
            return $false
        }
    } catch {
        Write-Err "Error checking Docker environment: $_"
        return $false
    }
}

# Check project file structure
function Check-ProjectStructure {
    Write-Heading "5. Project File Structure Check"
    
    $requiredFiles = @(
        @{Path = "$backendDir\requirements.txt"; Name = "Backend requirements file"},
        @{Path = "$frontendDir\package.json"; Name = "Frontend package file"},
        @{Path = "$projectRoot\start_windows.ps1"; Name = "Windows start script"},
        @{Path = "$projectRoot\stop_windows.ps1"; Name = "Windows stop script"}
    )
    
    $allFilesExist = $true
    foreach ($file in $requiredFiles) {
        if (Test-Path $file.Path) {
            Write-Ok "Found $($file.Name): $($file.Path)"
        } else {
            Write-Err "Missing $($file.Name): $($file.Path)"
            $allFilesExist = $false
        }
    }
    
    return $allFilesExist
}

# Check environment variables
function Check-EnvironmentVariables {
    Write-Heading "6. Environment Variables Configuration Check"
    
    $envExamplePath = "$backendDir\.env.example"
    $envPath = "$backendDir\.env"
    
    if (Test-Path $envExamplePath) {
        Write-Ok "Found environment variable example: $envExamplePath"
        
        if (Test-Path $envPath) {
            Write-Ok "Found environment variable config: $envPath"
            
            # Check required environment variables
            $envContent = Get-Content $envPath
            $requiredVars = @("CONTRACT_API_KEY", "QWEN_API_KEY")
            $missingVars = @()
            
            foreach ($var in $requiredVars) {
                if (-not ($envContent -match "^$var=.*")) {
                    $missingVars += $var
                }
            }
            
            if ($missingVars.Count -gt 0) {
                Write-Warn "Missing required environment variables: $($missingVars -join ', ')"
                Write-Info "Please configure these API keys in .env file"
            } else {
                Write-Ok "All required environment variables configured"
            }
        } else {
            Write-Warn "Missing environment variable config: $envPath"
            Write-Info "Please create .env file based on $envExamplePath and configure API keys"
        }
    } else {
        Write-Err "Missing environment variable example: $envExamplePath"
    }
}

# Show startup guide in Chinese
function Show-StartupGuide {
    Write-Heading "7. Project Startup Guide"
    
    Write-Host @"

====================================
合同智能检索系统 - Windows启动指南
====================================

1. 前提条件
   - Windows Server 2012 R2或更高版本
   - PowerShell 5.1或更高版本
   - Python 3.10或更高版本
   - Node.js 16或更高版本
   - Docker Desktop for Windows（用于运行Elasticsearch）

2. 环境变量配置
   在backend目录下创建.env文件，配置以下API密钥：
   - CONTRACT_API_KEY：DeepSeek API密钥
   - QWEN_API_KEY：阿里云通义千问API密钥

3. 启动步骤
   以管理员身份运行PowerShell，执行以下命令：
   ```
   cd "$projectRoot"
   .\start_windows.ps1
   ```

   启动脚本会自动执行以下操作：
   - 检查并启动Elasticsearch（通过Docker）
   - 安装Python虚拟环境（如果不存在）
   - 安装后端依赖
   - 安装前端依赖
   - 构建前端静态资源
   - 创建Elasticsearch索引
   - 启动后端服务

4. 服务访问地址
   - Elasticsearch: http://localhost:9200
   - 后端API: http://localhost:8006
   - API文档: http://localhost:8006/docs

5. 停止服务
   以管理员身份运行PowerShell，执行以下命令：
   ```
   cd "$projectRoot"
   .\stop_windows.ps1
   ```

   可选参数：
   - -StopElasticsearch：同时停止Elasticsearch容器
   - -ElasticPort：指定Elasticsearch端口（默认9200）

6. 自定义配置
   启动脚本支持以下参数：
   - -ApiPort：指定后端服务端口（默认8006）
   - -ElasticPort：指定Elasticsearch端口（默认9200）
   - -ElasticImage：指定Elasticsearch镜像（默认docker.elastic.co/elasticsearch/elasticsearch:8.13.4）

====================================

"@
}

# Execute all checks
$pythonOk = Check-Python
$nodejsOk = Check-Nodejs
$dockerOk = Check-Docker
$projectOk = Check-ProjectStructure
Check-EnvironmentVariables

Write-Heading "8. Environment Check Results Summary"

$allChecks = @(
    @{Name = "Python 3.10+"; Status = $pythonOk},
    @{Name = "Node.js 16+"; Status = $nodejsOk},
    @{Name = "Docker (for Elasticsearch)"; Status = $dockerOk},
    @{Name = "Project file structure"; Status = $projectOk}
)

$passed = 0
$failed = 0

foreach ($check in $allChecks) {
    if ($check.Status) {
        Write-Ok "✓ $($check.Name)"
        $passed++
    } else {
        Write-Err "✗ $($check.Name)"
        $failed++
    }
}

Write-Host "\n[INFO] Check completed: $passed passed, $failed failed"

if ($failed -eq 0) {
    Write-Host "\n🎉 All environment checks passed! You can start the project."
} else {
    Write-Host "\n⚠️  Some environment checks failed, please install missing dependencies according to the prompts."
}

# Show detailed startup guide in Chinese
Show-StartupGuide

Write-Host "\n[INFO] Script execution completed. Happy using!"
