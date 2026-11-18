# ==============================================================================
# Beyond History / Faceless Shorts Engine - Office PC Setup & Hardware Validator
# 100% Free, Local, Offline. Zero Paid APIs.
# ==============================================================================

param(
    [string]$CacheDir = "",
    [switch]$ForceCpu,
    [switch]$SkipPipInstall
)

$ErrorActionPreference = "Stop"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Beyond History Shorts Engine - Office PC Setup and Validator" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

# 1. Hardware Detection
Write-Host "`n[1/5] Detecting Office PC Hardware..." -ForegroundColor Yellow
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$cpu = (Get-CimInstance Win32_Processor).Name
$totalRamGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$gpus = Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name

Write-Host "  Operating System: $os"
Write-Host "  CPU Architecture: $cpu"
Write-Host "  Installed RAM:    $totalRamGB GB"
Write-Host "  GPU Device(s):    $($gpus -join ', ')"

$hasNvidia = $false
foreach ($g in $gpus) {
    if ($g -match "NVIDIA|GeForce|RTX|Quadro|Tesla") {
        $hasNvidia = $true
    }
}

if ($hasNvidia -and -not $ForceCpu) {
    Write-Host "  NVIDIA GPU detected! Configuring CUDA acceleration (cu121)." -ForegroundColor Green
} else {
    Write-Host "  Standard CPU profile selected. Will use AVX2/FMA3 attention slicing." -ForegroundColor Yellow
}

# 2. Check Core Tools (Python, Node.js, FFmpeg)
Write-Host "`n[2/5] Auditing Core System Tools..." -ForegroundColor Yellow

# Refresh PATH from User and Machine environment
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")

# Python 3.10+
$pyWorking = $false
$pyCmd = $null
$pyCandidate = Get-Command python -ErrorAction SilentlyContinue
if ($pyCandidate) {
    try {
        $testVer = & $pyCandidate.Source --version 2>&1
        if ($LASTEXITCODE -eq 0 -and $testVer -match "Python 3\.(1[0-9]|[2-9][0-9])") {
            $pyCmd = $pyCandidate
            $pyWorking = $true
        }
    } catch {}
}

if (-not $pyWorking) {
    $fallbackPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($p in $fallbackPaths) {
        if (Test-Path $p) {
            $pyCmd = [PSCustomObject]@{ Source = $p }
            $pyWorking = $true
            break
        }
    }
}

if (-not $pyWorking) {
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { $pyWorking = $true }
}

if (-not $pyWorking) {
    Write-Host "  Python 3.11+ is not found in PATH." -ForegroundColor Red
    Write-Host "  Installing Python 3.11 via WinGet..." -ForegroundColor Yellow
    winget install Python.Python.3.11 --scope user --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=0" --accept-source-agreements --accept-package-agreements
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pyCmd) {
        $pyFallback = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        if (Test-Path $pyFallback) {
            $pyCmd = [PSCustomObject]@{ Source = $pyFallback }
        } else {
            Write-Error "Please restart your terminal after installing Python 3.11."
            exit 1
        }
    }
}
$pyVer = & $pyCmd.Source --version 2>&1
Write-Host "  Python:  Found ($($pyCmd.Source) - $pyVer)" -ForegroundColor Green

# Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "  Node.js is not found in PATH." -ForegroundColor Red
    Write-Host "  Installing Node.js LTS via WinGet..." -ForegroundColor Yellow
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Write-Error "Please restart your terminal after installing Node.js."
        exit 1
    }
}
$nodeVer = & $nodeCmd.Source --version 2>&1
Write-Host "  Node.js: Found ($($nodeCmd.Source) - $nodeVer)" -ForegroundColor Green

# FFmpeg
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCmd) {
    $wingetFfmpegCandidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin"
    )
    foreach ($cand in $wingetFfmpegCandidates) {
        if (Test-Path $cand) {
            $env:Path = "$cand;" + $env:Path
            $ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
            if ($ffmpegCmd) { break }
        }
    }
}
if (-not $ffmpegCmd) {
    Write-Host "  FFmpeg is missing. Installing Gyan.FFmpeg.Essentials via WinGet..." -ForegroundColor Yellow
    winget install Gyan.FFmpeg.Essentials --accept-source-agreements --accept-package-agreements
    $wingetFfmpeg = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin"
    $env:Path = "$wingetFfmpeg;" + $env:Path
    $ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
}
Write-Host "  FFmpeg:  Found ($($ffmpegCmd.Source))" -ForegroundColor Green

# 3. Model Cache Directory Determination
Write-Host "`n[3/5] Determining Optimal AI Model Cache Location..." -ForegroundColor Yellow
if ([string]::IsNullOrWhiteSpace($CacheDir)) {
    if (Test-Path "D:\") {
        $CacheDir = "D:\faceless-shorts-ai\cache"
    } else {
        $CacheDir = "$HOME\.faceless-shorts\cache"
    }
}

if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
}
$cacheDrive = (Get-Item $CacheDir).PSDrive.Name
$driveFreeGB = [math]::Round((Get-PSDrive $cacheDrive).Free / 1GB, 1)
Write-Host "  Target Cache: $CacheDir" -ForegroundColor Green
Write-Host "  Drive $($cacheDrive): Free Space: $driveFreeGB GB"

$env:HF_HOME = $CacheDir
$env:TORCH_HOME = "$CacheDir\torch"
$env:TRANSFORMERS_CACHE = $CacheDir

# 4. Virtual Environment & Python Dependencies
Write-Host "`n[4/5] Preparing Local Python Virtual Environment..." -ForegroundColor Yellow
$venvDir = "$HOME\.faceless-shorts\venv"
$venvPy = "$venvDir\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "  Creating virtual environment at $venvDir..."
    & $pyCmd.Source -m venv $venvDir
}

if (-not $SkipPipInstall) {
    Write-Host "  Upgrading pip..."
    & $venvPy -m pip install --upgrade pip --quiet

    if ($hasNvidia -and -not $ForceCpu) {
        Write-Host "  Installing CUDA-enabled PyTorch (cu121)..." -ForegroundColor Green
        & $venvPy -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --quiet
    } else {
        Write-Host "  Installing CPU-optimized PyTorch..." -ForegroundColor Yellow
        & $venvPy -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --quiet
    }

    Write-Host "  Installing requirements from requirements.txt..."
    $reqFile = Join-Path $PSScriptRoot "requirements.txt"
    if (Test-Path $reqFile) {
        & $venvPy -m pip install -r $reqFile --quiet
    } else {
        & $venvPy -m pip install diffusers transformers accelerate safetensors faster-whisper kokoro-onnx soundfile scipy numpy Pillow --quiet
    }
}

# 5. Kokoro-82M Offline Voice Models
Write-Host "`n[5/5] Checking Kokoro-82M Voice Models..." -ForegroundColor Yellow
$kokoroDir = "$HOME\.faceless-shorts\kokoro"
$onnxModel = "$kokoroDir\kokoro-v1.0.onnx"
$voicesBin = "$kokoroDir\voices-v1.0.bin"

if (-not (Test-Path $onnxModel) -or -not (Test-Path $voicesBin)) {
    Write-Host "  Fetching Kokoro-82M ONNX weights (free open-weight, ~340 MB)..." -ForegroundColor Yellow
    & $venvPy "$PSScriptRoot\scripts\voice.py" --download
} else {
    Write-Host "  Kokoro-82M voice models present ($kokoroDir)" -ForegroundColor Green
}

Write-Host "`n===========================================================" -ForegroundColor Green
Write-Host "  SUCCESS! Office PC is fully configured and ready." -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
Write-Host "  To produce a Beyond History documentary:" -ForegroundColor Cyan
Write-Host "    $venvPy scripts/produce_history.py --project [project-path]`n" -ForegroundColor Cyan
