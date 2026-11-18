# Scheduler（本機）

- Api：`http://127.0.0.1:5055` — `pwsh .cursor/scripts/local-dev/start-scheduler-api.ps1`
- Job：`http://127.0.0.1:5056/hangfire`（admin／環境變數 `HANGFIRE_PASSWORD`，預設 admin）— `pwsh .cursor/scripts/local-dev/start-scheduler-job.ps1`
- DB：**QAS PostgreSQL**（schema `scheduler`）。連線優先序：環境變數 `SCHEDULE_DB` → `ConnectionStrings:Scheduler`（本機可放 `appsettings.Development.json`，已 gitignore）
- 範本鍵名：見 [`.env.example`](.env.example)；部署由 Vault／K8s Secret 注入同名 `SCHEDULE_DB`
- Cursor MCP：`scheduler-pg` 需環境變數 `SCHEDULE_DB_URL`（URI）
- 執行依賴本機 LangGraph `:2024`（`assistantId=agent`）

維運：Dashboard Succeeded／Failed、`POST /api/schedules/{id}/runs/list`、結構化日誌。業務 API 統一 POST。細節見 Agent guide（`.cursor`，不進版控）。
