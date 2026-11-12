# local-dev（mo_agentchat）

| 腳本 | 用途 |
|------|------|
| `start-backend.ps1` | `server/.venv` + `pip install`（如需）+ `langgraph dev`（`langgraph.dev.json`） |
| `start-frontend.ps1` | `pnpm install`（如需）+ `pnpm dev` |
| `start-all.ps1` | 各開一個視窗 |
| `_scheduler-common.ps1` | 排程腳本共用（路徑／環境） |
| `start-scheduler-api.ps1` | Schedule.Api `:5055` |
| `start-scheduler-job.ps1` | Scheduler.Job `:5056`（Hangfire `/hangfire`） |

需 PowerShell 7（`pwsh`）。

## 正式 vs 本機

| | 設定檔 | Graph |
|--|--------|-------|
| 正式／CI | `server/langgraph.json` | 目前為 `agent` + 三條業務 |
| 本機腳本 | `server/langgraph.dev.json` | `agent` + 三條業務 |

前端本機請建 `frontend/.env.local`（已 gitignore），例如：

```env
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=rework_mo_detective
```

回歸正式 demo：把 `NEXT_PUBLIC_ASSISTANT_ID` 改回 `agent`。
