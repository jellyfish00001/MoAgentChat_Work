# mo_agentchat `.cursor` 地圖

工作區根：`D:\mo_agentchat`（規範源自 `D:\ai_prepare\.cursor`）。**先讀本檔 → 再 `@` 目標檔**，避免全庫掃碼。

本機多流程測試用 `server/langgraph.dev.json`；正式部署使用 `server/langgraph.json`。目前兩者皆包含 `agent` 和三條業務 Graph，以各設定檔的實際內容為準。

---

## 1. 一分鐘：該開哪裡

```text
需要「本機起後端／前端」 ──► scripts/local-dev/ + 根 AGENTS.md
需要「LLM 連線」         ──► guides/azure-apim-llm.md + server/flows/llm/
需要「改 Graph」         ──► guides/graph-scaffold.md + server/flows/graphs/
需要「業務規則（無 LLM）」──► guides/domain-vs-llm.md + server/flows/domain/
需要「寄信／HITL tool」  ──► guides/mail-tool.md + server/flows/tools/ + docs/mail.md
需要「Chat／LangSmith」  ──► guides/local-ui-langsmith.md + MCP langsmith
需要「流程圖範本」       ──► docs/flow-templates/（非正式 runbook；OPEN-QUESTIONS）
需要「範本 Excel」       ──► server/testdata/{rework_mo,rd_risk,qv_dms}/
需要「正式 CI／部署」    ──► 根 README.md + pipeline/ + docs/gitlab_flow.md
需要「Scheduler／Job 分層」──► guides/scheduler-coding.md + guides/ers-job-layering.md
需要「排程流程圖」──► docs/schedule-api.md／schedule-deploy.md／schedule-db.md
```

---

## 2. 目錄一覽

| 路徑 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | Agent 工作流 |
| **本檔 MAP.md** | 一頁地圖 |
| [USER.md](USER.md) | 個人偏好 |
| [SOURCES.md](SOURCES.md) | rules／參考出處 |
| [mcp.json](mcp.json) | MCP（無機密） |
| [rules/](rules/) | `.mdc` 強制規則（含 `aipark-docs-comments`：文件／註解分層） |
| [guides/](guides/) | 短文細節 |
| [skills/](skills/) | 專案薄 skill（運維）＋開源改編架構審查（見 [SOURCES.md](SOURCES.md)） |
| [scripts/local-dev/](scripts/local-dev/) | 本機啟動（多 graph） |
| [temp/](temp/) | 本機驗證產物（gitignore）；保留文字驗收結論與有效待辦；測試圖片檢視後刪除，profile 不清除 |
| [guides/phase-delivery.md](guides/phase-delivery.md) | 多階段門檻（測→截圖 Read→git） |
| [guides/scheduler-coding.md](guides/scheduler-coding.md) | Scheduler／Job 分層與維運查看 |
| [guides/ers-job-layering.md](guides/ers-job-layering.md) | ERS.Job 中間層／注入／設定／enum 研究 → 本專案規範 |
| [rules/aipark-scheduler-layering.mdc](rules/aipark-scheduler-layering.mdc) | Scheduler 改碼時強制：集中目錄、薄 Job、禁雙管線 |

---

## 3. Repo 空間地圖

| 要找… | 路徑 |
|--------|------|
| 正式 demo agent | `server/graph.py` + `server/langgraph.json` |
| 本機多 graph 設定 | `server/langgraph.dev.json` |
| 業務 graphs／domain | `server/flows/` |
| Agent tools（寄信 `send_mail`） | `server/flows/tools/`（規則 `flows/domain/mail.py`） |
| 測試 Excel 範本 | `server/testdata/` |
| 流程圖範本（非正式） | `docs/flow-templates/` |
| Agent Chat UI | `frontend/`（程式；theme／vendor 約定見 `rules/aipark-frontend-ui`／`aipark-agent-chat`。`AGENTS.md`／`CLAUDE.md` 為 next 自動產物，已 gitignore） |
| CI／Harbor | `pipeline/`、`.gitlab-ci.yml` |

---

## 4. MCP

| id | 用途 |
|----|------|
| `langsmith` | 查 projects／runs（手眼驗 tracing）；需 `LANGSMITH_API_KEY` |
| `context7` | 官方庫文件；需 `CONTEXT7_API_KEY` |
| `jira` | Jira Cloud 查詢／開單（`mcp-atlassian` → `swpc`）；需 `JIRA_URL`／`JIRA_USERNAME`／`JIRA_API_TOKEN`（Windows User 環境變數，勿寫進 repo） |
| `cursor-ide-browser` | 驗 Chat UI／網頁 |

機密一律本機環境／`server/.env`，見 `server/.env.example`。Jira token **不要**寫進 `mcp.json` 或 commit。

---

## 5. 啟動速查（本機多流程）

可複製完整說明：**[guides/local-start.md](guides/local-start.md)**

```powershell
# 後端（於 server/；使用 langgraph.dev.json，不覆寫正式 langgraph.json）
pwsh -NoProfile -File .cursor/scripts/local-dev/start-backend.ps1

# 前端（於 frontend/）
pwsh -NoProfile -File .cursor/scripts/local-dev/start-frontend.ps1
```

- API：`http://localhost:2024`
- Chat：`http://localhost:3000`
- Graph ID：`agent`（正式回歸）／`rework_mo_detective`／`rd_risk_dashboard`／`qv_dms_pipeline`
- 排程（實作後）：Schedule.Api／Job 腳本見 [scripts/local-dev/README.md](scripts/local-dev/README.md)；Hangfire 看 `/hangfire`
