# AI Long Video Clipper - PowerShell Launcher
param(
    [switch]$Cli,
    [string[]]$InputVideos,
    [string[]]$Durations = @("30:3", "45:3", "60:2"),
    [string]$Format = "both",
    [switch]$NoSubtitles,
    [int]$Port = 8765
)

$VenvPython = "C:\Users\HP\.faceless-shorts\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Error "[ERROR] Python virtual environment not found at $VenvPython"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Cli -or $InputVideos) {
    if (-not $InputVideos) {
        Write-Host "Usage: .\run_clipper.ps1 -Cli -InputVideos 'path1.mp4','path2.mp4' -Format both" -ForegroundColor Yellow
        exit 1
    }
    $cliArgs = @("$ScriptDir\scripts\clipper.py", "--input") + $InputVideos + @("--durations") + $Durations + @("--format", $Format)
    if ($NoSubtitles) { $cliArgs += "--no-subtitles" }
    & $VenvPython @cliArgs
} else {
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host " BEYOND HISTORY — AI LONG VIDEO CLIPPER MODULE" -ForegroundColor Yellow
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "Starting Web UI on http://localhost:$Port ..." -ForegroundColor Green
    Start-Process "http://localhost:$Port"
    & $VenvPython "$ScriptDir\scripts\clipper_server.py" $Port
}
