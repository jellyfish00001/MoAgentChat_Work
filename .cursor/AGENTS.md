# mo_agentchat Agent 工作流

> 規範源自 `ai_prepare/.cursor`（歷史同源），已依 **mo_agentchat** 調整；同步上游時先比對差異。

Python **LangGraph** 後端（`server/`）+ **agent-chat-ui** 前端（`frontend/`）。  
契約：`server/langgraph.json`（正式）／`server/langgraph.dev.json`（本機）；鍵集合見 [scripts/checks](scripts/checks/)。

| 先開 | 用途 |
|------|------|
| **[MAP.md](MAP.md)** | 一頁地圖＋SSOT 一覽（任務路由以 MAP §1 為主） |
| **本檔** | 偏好、手眼、邊界、MAP 未列之技能／待決 |

---

## 偏好（原 USER）

- 回覆語言：**繁體中文**
- commit／push：**預設**僅在使用者明確要求時執行；若**已確認的計畫**明文授權「每階段 commit+push」，依該計畫執行（仍勿改 git config／勿 force-push main）
- commit 訊息：conventional 前綴 + **繁中**說明；**禁止** `Co-authored-by: Cursor …`
- 進版控的 `docs/` **不要**連結／依賴 `.cursor/` 路徑
- 機密：只在本機 `.env`；永不寫進 md／規則／commit
- 偏好可運行的最小變更；多階段須模組化、過門後再下一階（`aipark-phase-delivery`）
- **文件分層**：技術／Agent → `.cursor/`；專案說明／營運 → `README`／`docs/`
- **程式註解**：繁中、每方法必有（見 `aipark-docs-comments`）
- **待決分軌**：業務 → `docs/flow-templates/OPEN-QUESTIONS.md`；Agent／架構 → `.cursor/temp/open-decisions.md`

---

## 手眼（優先）

| 能力 | 方式 | 指南 |
|------|------|------|
| LLM 可通 | Skill `azure-apim-llm` 或 `python -m flows.llm.azure_apim` | [guides/azure-apim-llm.md](guides/azure-apim-llm.md) |
| Graph 可跑 | `start-backend.ps1` + Skill `run-graph-smoke` | [guides/local-start.md](guides/local-start.md) |
| Tracing／Chat／Studio 概念 | MCP `langsmith` + localhost:3000 | [guides/local-ui-langsmith.md](guides/local-ui-langsmith.md) |
| Studio + baseUrl | Skill `studio-baseurl` | [guides/playwright-langsmith.md](guides/playwright-langsmith.md) |
| 規範機器閘道 | `scripts/checks/run-all.ps1` | [MAP.md](MAP.md) §0 |

**禁止假裝**已呼叫 LLM、已跑 graph、或已在 LangSmith 看到 trace → `rules/aipark-hands-eyes.mdc`。  
UI 必截圖並 **Read 圖片**；多階段 → `aipark-phase-delivery` + [guides/phase-delivery.md](guides/phase-delivery.md)。

產物：`.cursor/temp/verify-log.md`；截圖：`.cursor/temp/ui-shots/`。

---

## 任務開始：MAP 未列時再讀

路由主表見 [MAP.md](MAP.md) §1。補充：

| 任務類型 | 先讀 |
|----------|------|
| 多階段計畫／每階 push／截圖驗收 | [guides/phase-delivery.md](guides/phase-delivery.md) + `aipark-phase-delivery` |
| 依賴方向／SOLID／Clean | Skill `clean-architecture`（出處見 [MAP.md](MAP.md) §6） |
| 結構／耦合報告 | Skill `architecture-review` |
| 重複／氣味／YAGNI | Skill `kent-beck-style` |
| 架構評分／組織原則 | Skill `review-software-architect` |
| 文件／註解放置 | `rules/aipark-docs-comments.mdc`＋本檔「偏好」 |
| 本次 Agent／架構待決 | `.cursor/temp/open-decisions.md` |

---

## 邊界（防技術債）

- **domain/**：純規則，無 LLM import，可 pytest
- **graphs/**：薄節點；組裝在 `graph.py`
- **llm/**：唯一 factory（`azure_apim.py`；含 `use_responses_api=False`）
- **tools/**：LangChain tool（IO／`interrupt`）；規則在 `domain/`；設定走 `flows.config.Settings`
- **正式契約**：勿改 `langgraph.json`／Dockerfile／CI，除非明確「晉升正式」
- 前端 vendor 少改；本機用 `frontend/.env.local` 切 Graph ID
- 細節見 `rules/aipark-*.mdc`；技術棧摘要見 [guides/stack.md](guides/stack.md)
