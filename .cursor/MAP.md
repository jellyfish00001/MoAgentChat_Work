# mo_agentchat `.cursor` 地圖

工作區根：`D:\mo_agentchat`（規範源自 `ai_prepare/.cursor` 歷史同步）。**先讀本檔 → 再 `@` 目標檔**，避免全庫掃碼。

**規範分層**：MAP＝索引＋SSOT；[AGENTS.md](AGENTS.md)＝偏好／手眼／邊界；alwaysApply＝短 FAIL；glob rule＝改該區禁則；guide＝長步驟；skill＝程序；`scripts/checks`＝可機器判定權威。

本機：`server/langgraph.dev.json`；正式：`server/langgraph.json`。`graphs` 鍵集合以兩檔＋[scripts/checks](scripts/checks/) 為準。

---

## 0. SSOT 一覽

| 主題 | 唯一寫滿／權威 |
|------|----------------|
| 本機啟動指令 | [guides/local-start.md](guides/local-start.md) |
| local-dev 腳本清單 | [scripts/local-dev/README.md](scripts/local-dev/README.md) |
| temp／verify-log | `.cursor/temp/…`（政策見 `aipark-phase-delivery`） |
| commit／push／偏好 | [AGENTS.md](AGENTS.md)「偏好」；secrets＋phase 互指 |
| 跨層命名詳表 | [guides/naming-conventions.md](guides/naming-conventions.md)（速查：`aipark-naming`） |
| 多階段過門 | `aipark-phase-delivery`＋[guides/phase-delivery.md](guides/phase-delivery.md) |
| Scheduler 禁則／口令 | `aipark-scheduler-layering`＋[guides/scheduler-coding.md](guides/scheduler-coding.md) |
| LangSmith 專案名 | `server/.env` → `LANGCHAIN_PROJECT` |
| Graph 鍵／路徑用詞／斷鏈 | [scripts/checks/run-all.ps1](scripts/checks/run-all.ps1) |
| 規則出處／skills 分層 | 本檔 §6 |

---

## 1. 一分鐘：該開哪裡

```text
需要「本機起後端／前端」 ──► guides/local-start.md（腳本：scripts/local-dev/）
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
需要「跨層命名」──► guides/naming-conventions.md + rules/aipark-naming.mdc
需要「規範機器閘道」──► scripts/checks/run-all.ps1
需要「偏好／手眼／邊界」──► AGENTS.md
```

---

## 2. 目錄一覽

| 路徑 | 用途 |
|------|------|
| **本檔 MAP.md** | 一頁地圖＋SSOT＋出處摘要 |
| [AGENTS.md](AGENTS.md) | 偏好、手眼、邊界、技能補充 |
| [mcp.json](mcp.json) | MCP（無機密） |
| [rules/](rules/) | `.mdc` 強制規則 |
| [guides/](guides/) | 長步驟／詳表／研究 |
| [skills/](skills/) | 運維薄 skill＋開源改編審查（§6） |
| [scripts/local-dev/](scripts/local-dev/) | 本機啟動 |
| [scripts/checks/](scripts/checks/) | 可機器判定規範閘道 |
| [temp/](temp/) | 本機驗證產物（路徑一律 `.cursor/temp/…`） |

---

## 3. Repo 空間地圖

| 要找… | 路徑 |
|--------|------|
| 正式 demo agent | `server/graph.py` + `server/langgraph.json` |
| 本機多 graph 設定 | `server/langgraph.dev.json` |
| 業務 graphs／domain | `server/flows/` |
| Agent tools（寄信 `send_mail`） | `server/flows/tools/` |
| 測試 Excel 範本 | `server/testdata/` |
| 流程圖範本（非正式） | `docs/flow-templates/` |
| Agent Chat UI | `frontend/`（`aipark-frontend-ui`／`aipark-agent-chat`） |
| CI／Harbor | `pipeline/`、`.gitlab-ci.yml` |

---

## 4. MCP

| id | 用途 |
|----|------|
| `langsmith` | 查 projects／runs；需 `LANGSMITH_API_KEY` |
| `context7` | 官方庫文件；需 `CONTEXT7_API_KEY` |
| `jira` | Jira Cloud；需環境變數，勿寫進 repo |
| `scheduler-pg` | 排程 QAS Postgres（唯讀）；需 `SCHEDULE_DB_URL` |
| `cursor-ide-browser` | 驗 Chat UI／網頁 |

機密一律本機環境／`server/.env`。部署用 Vault／Secret 注入 `SCHEDULE_DB`。

---

## 5. 啟動速查

完整指令：**[guides/local-start.md](guides/local-start.md)**。

- API：`http://localhost:2024` · Chat：`http://localhost:3000`
- 排程腳本／Hangfire：見 [scripts/local-dev/README.md](scripts/local-dev/README.md)

---

## 6. 出處與 Skills（原 SOURCES，摘要）

改編靈感（非自創教條）：LangGraph 官方結構；`awesome-cursor-rules-mdc`（playwright／next／ts）；agent-chat-ui；langsmith／context7 MCP；ERS.Job → `ers-job-layering`＋`aipark-scheduler-layering`。

開源改編 skills（MIT 等，各資料夾含 LICENSE）：`clean-architecture`、`kent-beck-style`、`architecture-review`、`review-software-architect`（僅加本專案路徑對照）。

| 層 | 位置 | 內容 |
|----|------|------|
| 個人（跨專案） | `%USERPROFILE%\.cursor\skills\` | 如 `playwright-cdp-session` |
| 專案運維 | `.cursor/skills/` | `azure-apim-llm`、`run-graph-smoke`、`studio-baseurl`、`scaffold-graph` |
| 專案審查 | `.cursor/skills/` | 上列四個開源改編 skill |

機器閘道：`.cursor/scripts/checks/run-all.ps1`。命名依據摘要見 [guides/naming-conventions.md](guides/naming-conventions.md)。
