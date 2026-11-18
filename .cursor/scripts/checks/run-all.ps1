#Requires -Version 7
# 規範機器閘道入口：graph 鍵／路徑用詞／斷鏈／舊路徑敘事
$ErrorActionPreference = 'Stop'
$dir = $PSScriptRoot
$checks = @(
    'check-langgraph-keys.ps1'
    'check-cursor-path-words.ps1'
    'check-rule-links.ps1'
    'check-no-ai-prepare-stale.ps1'
)

$failed = 0
foreach ($name in $checks) {
    $script = Join-Path $dir $name
    Write-Host "=== $name ==="
    & pwsh.exe @('-NoLogo', '-NoProfile', '-NonInteractive', '-File', $script)
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "EXIT $code"
        $failed = 1
    }
}

if ($failed -ne 0) {
    Write-Host 'CHECKS_FAILED'
    exit 1
}
Write-Host 'CHECKS_OK'
exit 0
