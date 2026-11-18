<#
.SYNOPSIS
    Automated Environment Bootstrapper for AI Long Video Clipper
    Sets up portable Python, FFmpeg, and Faster-Whisper on clean Windows 10/11 x64 PCs.
#>

param(
    [switch]$ForceReinstall = $false,
    [string]$InstallDir = "$env:LOCALAPPDATA\AI-Long-Video-Clipper\runtime"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "   AI LONG VIDEO CLIPPER — CLEAN PC AUTOMATED SETUP BOOTSTRAPPER     " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host ""

# 1. System Check
$osArch = [System.Environment]::Is64BitOperatingSystem
if (-not $osArch) {
    Write-Error "AI Long Video Clipper requires 64-bit Windows (x64)."
    exit 1
}

Write-Host "[1/5] Checking Hardware & Architecture..." -ForegroundColor Cyan
Write-Host "      Architecture: 64-bit Windows" -ForegroundColor Gray
$gpuInfo = Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name
Write-Host "      Detected Display Devices: $($gpuInfo -join ', ')" -ForegroundColor Gray

# 2. Check / Setup Python
Write-Host "[2/5] Checking Python Runtime..." -ForegroundColor Cyan
$pythonExe = $null

# Check existing venv
$targetVenv = "$HOME\.faceless-shorts\venv"
$venvPython = "$targetVenv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "      Found existing dedicated venv at $venvPython" -ForegroundColor Green
    $pythonExe = $venvPython
} else {
    # Check system python
    $sysPython = (Get-Command python -ErrorAction SilentlyContinue)
    if ($sysPython) {
        $pyVer = & python --version 2>&1
        Write-Host "      Found System Python: $pyVer" -ForegroundColor Green
        Write-Host "      Creating dedicated virtual environment at $targetVenv..." -ForegroundColor Yellow
        New-Item -ItemType Directory -Path "$HOME\.faceless-shorts" -Force | Out-Null
        & python -m venv $targetVenv
        $pythonExe = $venvPython
    } else {
        Write-Host "      Python not found. Attempting automatic installation via winget..." -ForegroundColor Yellow
        $winget = (Get-Command winget -ErrorAction SilentlyContinue)
        if ($winget) {
            Write-Host "      Installing Python 3.11 silently via winget..." -ForegroundColor Cyan
            try {
                & winget install -e --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
            } catch {
                Write-Warning "winget install encountered an issue: $_"
            }
        }
        
        # Check standard installation locations
        $stdPaths = @(
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:ProgramFiles\Python311\python.exe"
        )
        $installedPython = $null
        foreach ($sp in $stdPaths) {
            if (Test-Path $sp) {
                $installedPython = $sp
                break
            }
        }
        
        if (-not $installedPython) {
            Write-Host "      Downloading official Python 3.11.9 installer from python.org..." -ForegroundColor Cyan
            $installerPath = "$env:TEMP\python-3.11.9-amd64.exe"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $installerPath -UseBasicParsing
            Write-Host "      Running silent Python 3.11 installation..." -ForegroundColor Cyan
            Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" -Wait
            Start-Sleep -Seconds 3
            if (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe") {
                $installedPython = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
            }
        }
        
        if ($installedPython) {
            Write-Host "      Creating dedicated virtual environment at $targetVenv..." -ForegroundColor Yellow
            New-Item -ItemType Directory -Path "$HOME\.faceless-shorts" -Force | Out-Null
            & $installedPython -m venv $targetVenv
            $pythonExe = $venvPython
        } else {
            Write-Error "Failed to install Python 3.11 automatically. Please download from https://www.python.org/downloads/ and check 'Add to PATH'."
            exit 1
        }
    }
}

# 3. Install Dependencies
Write-Host "[3/5] Installing Required AI Packages (Torch, Faster-Whisper)..." -ForegroundColor Cyan
& $pythonExe -m pip install --upgrade pip --quiet
Write-Host "      Installing faster-whisper, torch, soundfile, requests..." -ForegroundColor Yellow

# Detect NVIDIA GPU for CUDA PyTorch vs CPU
$hasNvidia = ($gpuInfo -match "NVIDIA")
if ($hasNvidia) {
    Write-Host "      NVIDIA GPU detected! Installing CUDA-accelerated PyTorch..." -ForegroundColor Green
    & $pythonExe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
} else {
    Write-Host "      Non-NVIDIA or integrated graphics detected. Installing CPU PyTorch..." -ForegroundColor Yellow
    & $pythonExe -m pip install torch torchvision torchaudio --quiet
}

& $pythonExe -m pip install faster-whisper soundfile requests --quiet
Write-Host "      Python dependencies successfully installed." -ForegroundColor Green

# 4. Check / Setup FFmpeg
Write-Host "[4/5] Checking FFmpeg & FFprobe..." -ForegroundColor Cyan
$ffmpegCmd = (Get-Command ffmpeg -ErrorAction SilentlyContinue)
if ($ffmpegCmd) {
    $ffVer = (& ffmpeg -version)[0]
    Write-Host "      FFmpeg is available: $ffVer" -ForegroundColor Green
} else {
    Write-Host "      FFmpeg not found in PATH. Checking winget..." -ForegroundColor Yellow
    $winget = (Get-Command winget -ErrorAction SilentlyContinue)
    if ($winget) {
        Write-Host "      Installing Gyan FFmpeg Essentials via winget..." -ForegroundColor Cyan
        try {
            & winget install -e --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        } catch {
            Write-Warning "winget install failed: $_"
        }
    }
    
    $ffmpegCmd = (Get-Command ffmpeg -ErrorAction SilentlyContinue)
    if (-not $ffmpegCmd) {
        # Check if WinGet packages contain ffmpeg
        $wingetPkgs = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
        if (Test-Path $wingetPkgs) {
            $ffBins = Get-ChildItem -Path $wingetPkgs -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue
            if ($ffBins) {
                $ffBinDir = Split-Path $ffBins[0].FullName
                $env:Path = "$ffBinDir;$env:Path"
                $ffmpegCmd = $ffBins[0].FullName
            }
        }
    }

    if (-not $ffmpegCmd) {
        Write-Host "      Downloading portable FFmpeg essentials from gyan.dev..." -ForegroundColor Cyan
        $ffZip = "$env:TEMP\ffmpeg-release-essentials.zip"
        $ffExtract = "$HOME\.faceless-shorts\ffmpeg"
        New-Item -ItemType Directory -Path $ffExtract -Force | Out-Null
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $ffZip -UseBasicParsing
        Write-Host "      Extracting FFmpeg to $ffExtract..." -ForegroundColor Cyan
        Expand-Archive -Path $ffZip -DestinationPath $ffExtract -Force
        $foundExe = Get-ChildItem -Path $ffExtract -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue
        if ($foundExe) {
            $binFolder = Split-Path $foundExe[0].FullName
            $env:Path = "$binFolder;$env:Path"
            [System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";$binFolder", "User")
            $ffmpegCmd = $foundExe[0].FullName
            Write-Host "      FFmpeg installed to $binFolder." -ForegroundColor Green
        }
    }

    if ($ffmpegCmd) {
        Write-Host "      FFmpeg configured successfully." -ForegroundColor Green
    } else {
        Write-Warning "FFmpeg not detected. Please install FFmpeg from https://ffmpeg.org or winget."
    }
}

# 5. Pre-cache Faster-Whisper Model
Write-Host "[5/5] Pre-caching Faster-Whisper Model (small.en)..." -ForegroundColor Cyan
$cacheDir = "$HOME\.faceless-shorts\cache"
New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null

$downloadScript = @"
from faster_whisper import download_model
import os
cache_dir = r'$cacheDir'
print('Downloading Faster-Whisper small.en to:', cache_dir)
download_model('small.en', output_dir=cache_dir)
print('Model pre-cached successfully!')
"@

& $pythonExe -c $downloadScript

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "   SETUP COMPLETE! AI Long Video Clipper is ready for launch.        " -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
