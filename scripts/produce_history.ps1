param(
    [string]$Name,
    [string]$Topic,
    [string]$Project,
    [string]$Character,
    [string]$Model = "sd-turbo",
    [string]$Voice = "bm_george",
    [float]$Speed = 1.02,
    [int]$Steps = 2,
    [switch]$SkipImages,
    [switch]$SkipAudio,
    [switch]$SkipRender
)

$py = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
if (-not (Test-Path $py)) {
    $py = "$HOME\.faceless-shorts\venv\Scripts\python.exe"
}
if (-not (Test-Path $py)) {
    $py = "python"
}

$script = Join-Path $PSScriptRoot "produce_history.py"

$argsList = @()
if ($Project) { $argsList += @("--project", $Project) }
if ($Name) { $argsList += @("--name", $Name) }
if ($Topic) { $argsList += @("--topic", $Topic) }
if ($Character) { $argsList += @("--character", $Character) }
if ($Model) { $argsList += @("--model", $Model) }
if ($Voice) { $argsList += @("--voice", $Voice) }
if ($Speed) { $argsList += @("--speed", $Speed.ToString()) }
if ($Steps) { $argsList += @("--steps", $Steps.ToString()) }
if ($SkipImages) { $argsList += "--skip-images" }
if ($SkipAudio) { $argsList += "--skip-audio" }
if ($SkipRender) { $argsList += "--skip-render" }

& $py $script @argsList
