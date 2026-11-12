#Requires -Version 7
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$script = Join-Path $PSScriptRoot 'start-playwright-langsmith.mjs'
Write-Host 'Starting Playwright Chrome (CDP :9333, persistent LangSmith profile)...'
Write-Host 'Opens Columbus formal org + local Studio; leave this terminal running.'
Set-Location -LiteralPath $root
& node @($script, '--formal', '--studio')
