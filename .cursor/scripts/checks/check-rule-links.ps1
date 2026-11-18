#Requires -Version 7
# 權威：MAP／AGENTS／rules／guides 內相對 Markdown 連結指向的檔案須存在
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$cursor = Join-Path $root '.cursor'
$files = @(
    (Join-Path $cursor 'MAP.md')
    (Join-Path $cursor 'AGENTS.md')
    (Join-Path $root 'AGENTS.md')
)
$files += Get-ChildItem -LiteralPath (Join-Path $cursor 'rules') -Filter '*.mdc' -File | ForEach-Object FullName
$files += Get-ChildItem -LiteralPath (Join-Path $cursor 'guides') -Filter '*.md' -File | ForEach-Object FullName

$linkRe = [regex]'\]\(([^)]+)\)'
$failures = [System.Collections.Generic.List[string]]::new()

foreach ($path in $files) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    $dir = Split-Path -Parent $path
    $text = Get-Content -LiteralPath $path -Raw -Encoding utf8
    foreach ($m in $linkRe.Matches($text)) {
        $raw = $m.Groups[1].Value.Trim()
        if ($raw -match '^(https?://|mailto:|#)') { continue }
        # 去掉 title："path" 或 path "title"
        $target = ($raw -split '\s+', 2)[0].Trim('"''')
        if ([string]::IsNullOrWhiteSpace($target)) { continue }
        # 錨點
        $target = ($target -split '#', 2)[0]
        if ([string]::IsNullOrWhiteSpace($target)) { continue }
        # 以 / 開頭視為 repo 根相對（少見）；否則相對檔案目錄
        if ($target.StartsWith('/')) {
            $resolved = Join-Path $root ($target.TrimStart('/').Replace('/', [IO.Path]::DirectorySeparatorChar))
        } else {
            $resolved = [IO.Path]::GetFullPath((Join-Path $dir ($target.Replace('/', [IO.Path]::DirectorySeparatorChar))))
        }
        if (-not (Test-Path -LiteralPath $resolved)) {
            $relFile = $path.Substring($root.Path.Length).TrimStart('\', '/')
            $failures.Add("${relFile} -> ${target}")
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Host 'FAIL: broken relative markdown links:'
    $failures | Select-Object -Unique | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host 'OK: relative markdown links resolve'
exit 0
