#Requires -Version 7
# 本機多流程：langgraph.dev.json（不覆寫正式 langgraph.json）
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$server = Join-Path $root 'server'
$envFile = Join-Path $server '.env'
$devConfig = Join-Path $server 'langgraph.dev.json'

if (-not (Test-Path -LiteralPath $devConfig)) {
    throw "Missing $devConfig"
}

if (Test-Path -LiteralPath $envFile) {
    Get-Content -LiteralPath $envFile | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $pair = $_.Split('=', 2)
        if ($pair.Length -eq 2) {
            Set-Item -Path "Env:$($pair[0].Trim())" -Value $pair[1].Trim()
        }
    }
}

Set-Item -Path Env:PYTHONUTF8 -Value '1'
Set-Item -Path Env:PYTHONIOENCODING -Value 'utf-8'
Set-Location -LiteralPath $server

if (-not (Test-Path -LiteralPath (Join-Path $server '.venv'))) {
    python -m venv .venv
}
$py = Join-Path $server '.venv\Scripts\python.exe'
$langgraph = Join-Path $server '.venv\Scripts\langgraph.exe'
if (-not (Test-Path -LiteralPath $langgraph)) {
    & $py @('-m', 'pip', 'install', '-r', 'requirements.txt')
}

Write-Host "Starting langgraph dev with $devConfig (formal langgraph.json untouched)"
Write-Host "If port 2024 is busy (e.g. old AI_Park), stop that process or pass --port"
& $langgraph @('dev', '--no-browser', '--config', $devConfig)
