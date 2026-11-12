#Requires -Version 7
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
$frontend = Join-Path $root 'frontend'
Set-Location -LiteralPath $frontend
$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if (-not (Test-Path -LiteralPath (Join-Path $frontend 'node_modules'))) {
    if ($pnpm) {
        & pnpm @('install')
    } else {
        & npx @('--yes', 'pnpm@9', 'install')
    }
}
if ($pnpm) {
    & pnpm @('dev')
} else {
    & npx @('--yes', 'pnpm@9', 'dev')
}
