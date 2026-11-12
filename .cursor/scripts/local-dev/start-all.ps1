#Requires -Version 7
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
Start-Process pwsh -ArgumentList @('-NoLogo', '-File', (Join-Path $here 'start-backend.ps1'))
Start-Sleep -Seconds 2
Start-Process pwsh -ArgumentList @('-NoLogo', '-File', (Join-Path $here 'start-frontend.ps1'))
Write-Host 'Started backend and frontend in separate windows.'
Write-Host 'Backend: http://localhost:2024  Frontend: http://localhost:3000'
Write-Host 'Local graphs use langgraph.dev.json; deployment uses langgraph.json.'
Write-Host 'Switch Graph ID in frontend/.env.local (NEXT_PUBLIC_ASSISTANT_ID).'
