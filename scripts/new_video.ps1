param(
    [string]$Style,
    [string]$Name,
    [string]$Dir,
    [switch]$List
)

$skillDir = Split-Path -Parent $PSScriptRoot
$stylesDir = Join-Path $skillDir "styles"

if ($List) {
    Get-ChildItem -Directory -Path $stylesDir | ForEach-Object { $_.Name }
    exit 0
}

if (-not $Style -or -not $Name) {
    $availableStyles = (Get-ChildItem -Directory -Path $stylesDir | ForEach-Object { $_.Name }) -join ' '
    Write-Error "Usage: .\scripts\new_video.ps1 -Style <style> -Name <short-name> [-Dir <parent>] (styles: $availableStyles)"
    exit 1
}

$parent = if ($Dir) { $Dir } else { Join-Path $HOME "faceless-shorts" }
$src = Join-Path $stylesDir "$Style\example"

if (-not (Test-Path $src)) {
    Write-Error "No style '$Style' found at $src"
    exit 1
}

$dst = Join-Path $parent $Name
if (Test-Path $dst) {
    Write-Error "$dst already exists: pick another name"
    exit 1
}

New-Item -ItemType Directory -Force -Path $parent | Out-Null
Copy-Item -Path $src -Destination $dst -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $dst "renders") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dst "review") | Out-Null

$narrationWav = Join-Path $dst "data\narration.wav"
$mixWav = Join-Path $dst "data\mix.wav"
if (Test-Path $narrationWav) { Remove-Item $narrationWav }
if (Test-Path $mixWav) { Remove-Item $mixWav }

Write-Host $dst
Write-Host "style: $Style. Read styles\$Style\STYLE.md, then rewrite script.json + src/shots.js"
