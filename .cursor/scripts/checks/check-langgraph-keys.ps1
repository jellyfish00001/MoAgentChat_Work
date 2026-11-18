#Requires -Version 7
# 權威：server/langgraph.json 與 langgraph.dev.json 的 graphs 鍵集合必須相等
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$formal = Join-Path $root 'server\langgraph.json'
$dev = Join-Path $root 'server\langgraph.dev.json'

function Get-GraphKeys([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing file: $path"
    }
    $json = Get-Content -LiteralPath $path -Raw -Encoding utf8 | ConvertFrom-Json
    if (-not $json.graphs) {
        throw "No graphs object in $path"
    }
    @($json.graphs.PSObject.Properties.Name) | Sort-Object
}

$formalKeys = Get-GraphKeys $formal
$devKeys = Get-GraphKeys $dev
$onlyFormal = Compare-Object $formalKeys $devKeys | Where-Object SideIndicator -eq '<=' | ForEach-Object InputObject
$onlyDev = Compare-Object $formalKeys $devKeys | Where-Object SideIndicator -eq '=>' | ForEach-Object InputObject

if ($onlyFormal -or $onlyDev) {
    Write-Host "FAIL: langgraph graphs keys differ"
    if ($onlyFormal) { Write-Host ("  only in langgraph.json: " + ($onlyFormal -join ', ')) }
    if ($onlyDev) { Write-Host ("  only in langgraph.dev.json: " + ($onlyDev -join ', ')) }
    exit 1
}

Write-Host ("OK: graphs keys match (" + ($formalKeys -join ', ') + ")")
exit 0
