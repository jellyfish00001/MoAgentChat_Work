# mo_agentchat Agent 工作流

> 規範源自 `ai_prepare/.cursor`（同一套 Agent 規範），已依 mo_agentchat 調整；同步上游時先比對差異。

Python **LangGraph** 後端（`server/`）+ **agent-chat-ui** 前端（`frontend/`）。  
正式環境使用 `server/langgraph.json`，目前包含 `agent` 和三條業務 Graph；本機腳本使用 `server/langgraph.dev.json`。

| 先開 | 用途 |
|------|------|
| **[MAP.md](MAP.md)** | 一頁地圖 |
| **本檔** | 任務→先讀哪裡、手眼 |
| [USER.md](USER.md) | 語言、commit、手眼偏好 |

---

## 手眼（優先）

| 能力 | 方式 | 指南 |
|------|------|------|
| LLM 可通 | Skill `azure-apim-llm` 或 `python -m flows.llm.azure_apim` | [guides/azure-apim-llm.md](guides/azure-apim-llm.md) |
| Graph 可跑 | `start-backend.ps1` + Skill `run-graph-smoke` | [guides/stack.md](guides/stack.md) |
| Tracing／Chat／Studio 概念 | MCP `langsmith` + localhost:3000 | [guides/local-ui-langsmith.md](guides/local-ui-langsmith.md) |
| Studio + baseUrl | Skill `studio-baseurl` | [guides/playwright-langsmith.md](guides/playwright-langsmith.md) |

**禁止假裝**已呼叫 LLM、已跑 graph、或已在 LangSmith 看到 trace → `rules/aipark-hands-eyes.mdc`。  
UI 必截圖並 **Read 圖片**；多階段計畫門檻 → `rules/aipark-phase-delivery.mdc` + [guides/phase-delivery.md](guides/phase-delivery.md)。

產物：`temp/verify-log.md`（無密碼）；截圖：`temp/ui-shots/`（子目錄依功能）。

---

## 任務開始：先讀哪裡

| 任務類型 | 先讀 |
|----------|------|
| 迷路／總覽 | [MAP.md](MAP.md) |
| 多階段計畫／每階 push／截圖驗收 | [guides/phase-delivery.md](guides/phase-delivery.md) + `aipark-phase-delivery` |
| Scheduler／Job 編碼 | [guides/scheduler-coding.md](guides/scheduler-coding.md) |
| 新 Graph | [guides/graph-scaffold.md](guides/graph-scaffold.md) + Skill `scaffold-graph` |
| 業務規則 | [guides/domain-vs-llm.md](guides/domain-vs-llm.md) + `server/flows/domain/` |
| 寄信／Agent tool（HITL） | [guides/mail-tool.md](guides/mail-tool.md) + `server/flows/tools/` |
| Azure／APIM | [guides/azure-apim-llm.md](guides/azure-apim-llm.md) |
| Chat／LangSmith | [guides/local-ui-langsmith.md](guides/local-ui-langsmith.md) |
| 正式部署 | 根 `README.md`、`docs/gitlab_flow.md` |
| 依賴方向／SOLID／Clean | Skill `clean-architecture`（[來源](SOURCES.md)） |
| 結構／耦合報告 | Skill `architecture-review`（[來源](SOURCES.md)） |
| 重複／氣味／YAGNI | Skill `kent-beck-style`（[來源](SOURCES.md)） |
| 架構評分／組織原則 | Skill `review-software-architect`（[來源](SOURCES.md)） |
| 文件／註解放置 | `rules/aipark-docs-comments.mdc`（always）＋ [USER.md](USER.md) |
| 本次 Agent／架構待決 | `temp/open-decisions.md`（勿寫入 `docs/flow-templates/OPEN-QUESTIONS.md`） |

---

## 邊界（防技術債）

- **domain/**：純規則，無 LLM import，可 pytest
- **graphs/**：薄節點；組裝在 `graph.py`
- **llm/**：唯一 factory（`azure_apim.py`；含 `use_responses_api=False`）
- **tools/**：agent 用的 LangChain tool（IO／`interrupt` 串接）；規則抽到 `domain/`，設定走 `flows.config.Settings`；選用功能（如寄信）沒設環境變數就不載入
- **正式契約**：勿改 `langgraph.json`／Dockerfile／CI 行為，除非明確「晉升正式」任務
- 前端 vendor 少改；本機用 `frontend/.env.local` 切 Graph ID
- **文件**：技術規範 → `.cursor/`；專案說明 → `README`／`docs/`；程式註解繁中、每方法必有（`aipark-docs-comments`）；commit 訊息用繁中說明

細節見 `rules/aipark-*.mdc`。
