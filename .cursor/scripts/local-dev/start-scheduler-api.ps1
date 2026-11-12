# Flow: load common env → dotnet run Schedule.Api on http://127.0.0.1:5055
# Prerequisites: .NET SDK; DB path SCHEDULE_DB_PATH (default D:\ai_prepare_data\schedules.sqlite)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_scheduler-common.ps1")
Set-Location (Join-Path $SchedulerRoot "AiPrepare.Scheduler.Api")
Write-Host "Schedule.Api → http://127.0.0.1:5055  db=$env:SCHEDULE_DB_PATH"
dotnet run --no-launch-profile
