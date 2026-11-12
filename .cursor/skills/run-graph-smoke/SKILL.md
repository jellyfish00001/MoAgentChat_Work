---
name: run-graph-smoke
description: Health-check langgraph dev, smoke one of the three graphs, optionally verify LangSmith runs.
---

# run-graph-smoke

## Steps

1. 確認 `server/` 已建 `.venv` 並 `pip install -r requirements.txt`；`server/.env` 有 Azure／可選 tracing（勿列印 secrets）。
2. 啟動或確認：`pwsh .cursor/scripts/local-dev/start-backend.ps1` → `http://127.0.0.1:2024/ok`。
3. `POST http://127.0.0.1:2024/assistants/search` body `{}` 應看到 `agent` 與三條業務 assistant。
4. 擇一 Graph ID 呼叫（Chat UI 或 SDK）：

| Graph ID | 建議訊息 |
|----------|----------|
| `agent` | 回歸：簡單算術或天氣 tool |
| `rework_mo_detective` | 提取並輸出待分析工单清单 |
| `rd_risk_dashboard` | 產出風險看板摘要 |
| `qv_dms_pipeline` | 盤點本月輸入並說明可否開跑 |

5. 確認回覆非空；必要時查 `server/outputs/`。
6. 若 `.env` 已開 tracing：用 MCP `langsmith` 或網站 Project（`LANGCHAIN_PROJECT`）看最新 Run。
7. 記一筆 `.cursor/temp/verify-log.md`。失敗時回報真實錯誤，勿捏造成功。
