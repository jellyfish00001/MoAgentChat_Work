# Flow: load common env → dotnet run Scheduler.Job on :5056 (Hangfire /hangfire)
# Login default admin / admin (override HANGFIRE_PASSWORD)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_scheduler-common.ps1")
if (-not $env:HANGFIRE_PASSWORD) { $env:HANGFIRE_PASSWORD = "admin" }
Set-Location (Join-Path $SchedulerRoot "AiPrepare.Scheduler.Job")
Write-Host "Scheduler.Job → http://127.0.0.1:5056/hangfire  db=$env:SCHEDULE_DB_PATH"
dotnet run --no-launch-profile
