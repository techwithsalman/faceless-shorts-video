param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)
$fh = Join-Path $HOME ".faceless-shorts"
$py = Join-Path $fh "venv\Scripts\python.exe"
if (Test-Path $py) {
    & $py @ScriptArgs
} else {
    & python @ScriptArgs
}
