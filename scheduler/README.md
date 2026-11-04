# Scheduler (local)

- Api: `http://127.0.0.1:5055` — `pwsh .cursor/scripts/local-dev/start-scheduler-api.ps1`
- Job: `http://127.0.0.1:5056/hangfire` — `pwsh .cursor/scripts/local-dev/start-scheduler-job.ps1` (admin/admin)
- DB: `D:\ai_prepare_data\schedules.sqlite` (`SCHEDULE_DB_PATH`)
- Needs LangGraph at `:2024` for run-now / due execution (`assistantId=agent`)
