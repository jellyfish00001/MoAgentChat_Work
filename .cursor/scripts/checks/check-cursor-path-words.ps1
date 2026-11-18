#Requires -Version 7
# 權威：規範正文禁止裸寫 temp/verify-log、temp/ui-shots（須 .cursor/temp/…）
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$cursor = Join-Path $root '.cursor'
$targets = @(
    (Join-Path $cursor 'MAP.md')
    (Join-Path $cursor 'AGENTS.md')
)
$targets += Get-ChildItem -LiteralPath (Join-Path $cursor 'rules') -Filter '*.mdc' -File | ForEach-Object FullName
$targets += Get-ChildItem -LiteralPath (Join-Path $cursor 'guides') -Filter '*.md' -File | ForEach-Object FullName

# 允許 .cursor/temp/...；禁止未加前綴的 temp/verify-log 或 temp/ui-shots
$badPattern = '(?<!\.cursor/)temp/(verify-log|ui-shots|pw-langsmith-profile|open-decisions)'
$failures = [System.Collections.Generic.List[string]]::new()

foreach ($path in $targets) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $lines = Get-Content -LiteralPath $path -Encoding utf8
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match $badPattern) {
            $rel = $path.Substring($root.Path.Length).TrimStart('\', '/')
            $failures.Add("${rel}:$($i + 1): $line")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host 'FAIL: bare temp/ path words (use .cursor/temp/...):'
    $failures | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host 'OK: no bare temp/verify-log|ui-shots|… in norms'
exit 0
