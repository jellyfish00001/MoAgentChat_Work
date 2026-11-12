# 規則與參考出處

取用日期：2026-03-26（2026-10-22 補 Playwright／Next／TS／個人 skills；**2026-10-29** 補架構審查開源 skills）。以下為**改編靈感或上游原文＋本專案路徑對照**，非自創審查教條。

| 來源 | Stars／性質 | 本專案用法 |
|------|-------------|------------|
| [LangGraph Application structure](https://docs.langchain.com/oss/python/langgraph/application-structure) | 官方 | `server/`、`langgraph.json` |
| [sanjeed5/awesome-cursor-rules-mdc](https://github.com/sanjeed5/awesome-cursor-rules-mdc) | ~3k★ | `langchain`／`langgraph` → 精煉 rules；**2026-10-22** 再改編 `playwright.mdc`→`flows-playwright.mdc`、`next-js.mdc`→`flows-next-chat.mdc`、`typescript.mdc`→`flows-typescript.mdc`（本地對照 clone：`refs/awesome-cursor-rules-mdc/`，gitignore） |
| [survivorforge/cursor-rules](https://github.com/survivorforge/cursor-rules) `rules/langchain-ai` | 社群 | Pydantic structured output、禁 deprecated Chain、retry |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | ~40k★ | Python LLM／測試靈感（其 `optimize-dry-solid-…` 檔內容幾乎為空 stub，**未採用**） |
| [langchain-ai/agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) | 官方前端 | `frontend/` |
| [langchain-ai/langsmith-mcp-server](https://github.com/langchain-ai/langsmith-mcp-server) | 官方 MCP | `mcp.json` → `uvx langsmith-mcp-server` |
| [Upstash Context7 MCP](https://github.com/upstash/context7) | 官方文件 MCP | `mcp.json` → `@upstash/context7-mcp`（需 `CONTEXT7_API_KEY`） |
| Cursor 內建 | IDE | 瀏覽器用 `cursor-ide-browser`（不必自架 Playwright MCP） |
| ERS2.0 `web/.cursor`（本機） | 內部參考 | **只借** MAP／手眼／commit 邊界；不抄業務棧 |
| ERS2.0 `web/api/src/ERS.Job`（+ Domain／Application／Contracts） | 內部參考 | 分層／`IJobBase`／`hangfire:jobs` 啟停／薄 Job→Domain；避閉包綁死 Recurring、厚 Job、Consts 神檔 → `.cursor/guides/ers-job-layering.md` + `rules/aipark-scheduler-layering.mdc` |

## 架構／模組化審查（2026-10-29）

| 來源 | License | 本專案檔案 | 微調方式 |
|------|---------|------------|----------|
| [nathankim0/clean-architecture-skills](https://github.com/nathankim0/clean-architecture-skills) → `clean-architecture` | MIT | `.cursor/skills/clean-architecture/`（`SKILL.md` + `LICENSE` + `SKILL.upstream.md`） | 保留上游正文；僅加「本專案對照」映射到既有 `domain/`／`graphs/`／`llm/`／`schemas/`／`config/` |
| 同上 → `kent-beck-style` | MIT | `.cursor/skills/kent-beck-style/` | 同上；用於重複／氣味／YAGNI／小步重構 |
| [tansuasici/claude-code-kit](https://github.com/tansuasici/claude-code-kit) → `architecture-review` | MIT | `.cursor/skills/architecture-review/` | 保留上游 Process／SOLID／輸出格式；加本專案路徑對照；去掉 Claude-only `allowed-tools` |
| [simiancraft/simiancraft-skills](https://github.com/simiancraft/simiancraft-skills) → `review-software-architect` | MIT | `.cursor/skills/review-software-architect/` | 保留上游 lenses／評分；加本專案路徑對照 |

參考閱讀（**未整檔納入**，避免百科＋斷鏈 references）：

- [DeerHide/agent_skills `software-architecture`](https://github.com/DeerHide/agent_skills/blob/main/skills/software-architecture/SKILL.md) — SOLID／DRY／KISS／YAGNI／Clean Architecture 總覽
- [Uncle Bob — The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) — 依賴向內原則原文
- [Cursor — Agent best practices](https://cursor.com/blog/agent-best-practices) — Rules 靜態 vs Skills 動態
- [Cursor — Rules docs](https://cursor.com/docs/rules) — 專案規範放 `.cursor/rules`
- Skill `kent-beck-style` Comments-as-smell — 註解寫 why、勿敘述 what → 精煉為 `rules/aipark-docs-comments.mdc`

既有、與本專案棧綁定的邊界（非本次開源搬運）：`rules/aipark-domain-rules.mdc`、`aipark-langgraph.mdc`、`aipark-python-langchain.mdc`、`aipark-docs-comments.mdc`、`guides/domain-vs-llm.md`、`guides/graph-scaffold.md`。

## Skills 分層

| 層 | 位置 | 內容 |
|------|------|------|
| 個人（跨專案） | `%USERPROFILE%\.cursor\skills\` | `playwright-cdp-session`、`markdown-mermaid-preview` 等 |
| 專案（薄／運維） | `.cursor/skills/` | `azure-apim-llm`、`run-graph-smoke`、`studio-baseurl`、`scaffold-graph` |
| 專案（開源改編） | `.cursor/skills/` | `clean-architecture`、`kent-beck-style`、`architecture-review`、`review-software-architect` |

本專案原創指南（非開源搬運）：`guides/domain-vs-llm.md`、`guides/azure-apim-llm.md`、`guides/playwright-langsmith.md`、`rules/aipark-domain-rules.mdc`。
