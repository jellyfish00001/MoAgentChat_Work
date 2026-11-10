# Scheduler（本機）

- Api：`http://127.0.0.1:5055` — `pwsh .cursor/scripts/local-dev/start-scheduler-api.ps1`
- Job：`http://127.0.0.1:5056/hangfire`（admin／環境變數 `HANGFIRE_PASSWORD`，預設 admin）— `pwsh .cursor/scripts/local-dev/start-scheduler-job.ps1`
- DB：`D:\ai_prepare_data\schedules.sqlite`（`SCHEDULE_DB_PATH`）
- 執行依賴本機 LangGraph `:2024`（`assistantId=agent`）

維運：Dashboard Succeeded／Failed、`POST /api/schedules/{id}/runs/list`、結構化日誌。業務 API 統一 POST。細節見 Agent guide（`.cursor`，不進版控）。
