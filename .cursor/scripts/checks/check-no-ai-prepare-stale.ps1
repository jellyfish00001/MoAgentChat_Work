#Requires -Version 7
# 權威：禁止把 ai_prepare/.cursor 寫成現行工作路徑（允許「源自／歷史／lineage／同源」敘事）
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$cursor = Join-Path $root '.cursor'
$targets = @(
    (Join-Path $cursor 'MAP.md')
    (Join-Path $cursor 'AGENTS.md')
)
$targets += Get-ChildItem -LiteralPath (Join-Path $cursor 'rules') -Filter '*.mdc' -File | ForEach-Object FullName
$targets += Get-ChildItem -LiteralPath (Join-Path $cursor 'guides') -Filter '*.md' -File | ForEach-Object FullName
$skillsRoot = Join-Path $cursor 'skills'
if (Test-Path -LiteralPath $skillsRoot) {
    $targets += Get-ChildItem -LiteralPath $skillsRoot -Recurse -Filter 'SKILL.md' -File | ForEach-Object FullName
}

$failures = [System.Collections.Generic.List[string]]::new()
foreach ($path in $targets) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $lines = Get-Content -LiteralPath $path -Encoding utf8
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -notmatch 'ai_prepare/\.cursor|ai_prepare\\\.cursor|D:\\ai_prepare') { continue }
        if ($line -match '源自|歷史|lineage|同源|同步上游|Fetched for') { continue }
        $rel = $path.Substring($root.Path.Length).TrimStart('\', '/')
        $failures.Add("${rel}:$($i + 1): $line")
    }
}

if ($failures.Count -gt 0) {
    Write-Host 'FAIL: stale ai_prepare path treated as current (add 源自/歷史/lineage or reword):'
    $failures | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host 'OK: no unexplained ai_prepare/.cursor as current path'
exit 0
