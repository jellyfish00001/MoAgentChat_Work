# Shared paths/env for Schedule.Api (:5055) and Scheduler.Job (:5056).
# Dot-source from start-scheduler-*.ps1 — do not run alone.

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$SchedulerRoot = Join-Path $RepoRoot "scheduler"
if (-not $env:SCHEDULE_DB_PATH) {
    $env:SCHEDULE_DB_PATH = "D:\ai_prepare_data\schedules.sqlite"
}
if (-not $env:SCHEDULE_JOB_KEY) {
    $env:SCHEDULE_JOB_KEY = "dev-job-key"
}
New-Item -ItemType Directory -Force -Path (Split-Path $env:SCHEDULE_DB_PATH) | Out-Null
