# 跨層命名規範（Naming／後端／DB／env）

本專案**依層套用不同慣例**，不要整條鏈路硬套同一種寫法。  
排程庫細節與欄位對照表另見 [`docs/schedule-db.md`](../../docs/schedule-db.md)；本檔是 Agent／開發常駐規範。

強制摘要：[`rules/aipark-naming.mdc`](../rules/aipark-naming.mdc)（`alwaysApply`）。

---

## 一覽表

| 層級 | 慣例 | 例子 | 依據／本專案落點 |
|------|------|------|------------------|
| **PostgreSQL 表／欄** | 小寫 `snake_case`；表名複數 | `schedules`、`user_id`、`next_run_at` | PG 文件示例；未加引號折小寫；EF `UseSnakeCaseNamingConvention`；欄位必有 `COMMENT` |
| **C# Domain／DTO／公開成員** | `PascalCase` | `UserId`、`NextRunAt`、`ScheduleDto` | .NET 命名；`scheduler/` |
| **Scheduler HTTP JSON ↔ React** | `camelCase` | `userId`、`nextRunAt` | ASP.NET 預設 JSON；`frontend/src/lib/schedule-api.ts` |
| **Python 模組／函式／變數** | `snake_case` | `send_mail`、`user_id`、`create_schedule` | PEP 8；`server/flows/` |
| **Python 類別／Pydantic model** | `PascalCase` | `Settings`、`MailFields` | PEP 8／Pydantic |
| **LangGraph state／tool／上游 JSON** | `snake_case`（與上游一致） | `messages`、`user_id`、`graph_id` | LangGraph／SDK；`LangGraphHttpClient` 用 `SnakeCaseLower` |
| **React／TS 變數、props、物件欄** | `camelCase` | `userId`、`assistantId` | TS／React 主流；`aipark-typescript`／`aipark-next-chat` |
| **React／TS 元件／型別名** | `PascalCase` | `ScheduleSidebar`、`ScheduleDto` | React／TS |
| **React DOM／SVG 屬性** | DOM `camelCase` | `clipPath`（不是 `clip-path`） | `aipark-next-chat` |
| **環境變數／Secret／CI 鍵** | `SCREAMING_SNAKE` | `SCHEDULE_DB`、`LANGSMITH_API_KEY` | 12-factor／ops |
| **檔案／目錄（Python）** | `snake_case` | `schedule.py`、`rework_mo/` | PEP 8 |
| **檔案／目錄（React 元件）** | `PascalCase` 元件檔或既有 vendor 慣例 | `ScheduleForm.tsx`；vendor 小 diff 優先 | `aipark-agent-chat` |

---

## 資料流對照（排程為例）

```text
React TS camelCase     ←JSON camelCase→     C# DTO PascalCase
                                                  ↓ map
                                            Domain PascalCase
                                                  ↓ EF SnakeCaseNamingConvention
                                            PG snake_case + COMMENT

Python tool／domain    ← 對 Scheduler 仍走 JSON camelCase（HTTP 契約）
LangGraph metadata     → snake_case（user_id 等，對齊上游）
```

---

## 各棧既有 rule（命名以外）

| 範圍 | Rule／Guide | 已涵蓋 | 本檔補上 |
|------|-------------|--------|----------|
| Python／LangChain | `aipark-python-langchain.mdc` | 型別、Pydantic、禁 deprecated Chain、settings | 模組／函式 `snake_case`、類別 PascalCase |
| LangGraph | `aipark-langgraph.mdc` | graph 結構、`messages` | state／對外鍵 snake_case |
| TypeScript | `aipark-typescript.mdc` | strict、`unknown`、勿洩密 | 變數／payload camelCase；型別名 PascalCase |
| Next／React | `aipark-next-chat.mdc`、`aipark-frontend-ui.mdc` | App Router、theme tokens | 元件 PascalCase；DOM camelCase |
| Scheduler 分層 | `aipark-scheduler-layering.mdc`、`guides/scheduler-coding.md` | 薄 Job、DI、Migrations | PG snake_case＋COMMENT；JSON camelCase |
| 註解／文件分層 | `aipark-docs-comments.mdc` | 繁中方法註解、文件放哪 | DB COMMENT 與分層命名連動 |

**結論**：先前**沒有**統一的跨層命名矩陣；語言／UI／分層 rule 各自存在。本檔＋`aipark-naming.mdc` 補上這塊，並與上表對齊。

---

## 禁止／易踩坑

- PG 用 camelCase／PascalCase（需雙引號、易踩大小寫）。
- 把 Scheduler API JSON 改成 snake_case，卻不改前端（契約斷裂）。
- 在 `frontend` 用 `NEXT_PUBLIC_*` 塞密鑰；env 鍵仍用 `SCREAMING_SNAKE`，值不進 Git。
- Python `os.getenv` 散落；設定鍵名仍為 `SCREAMING_SNAKE`，讀取經 `Settings`。
- 為「統一風格」把 C# 公開屬性改成 snake_case（違反 .NET）。

---

## 變更檢查（改 API／DB／前端時）

1. 新 DB 欄：實體 PascalCase → migration 產出 snake_case → `HasComment` 繁中用途。  
2. 新 API 欄：DTO PascalCase → JSON camelCase → 前端型別同步 camelCase。  
3. 新 LangGraph／tool 欄：優先 snake_case，與既有 state／上游一致。  
4. 同步更新 `docs/schedule-db.md` Schema 快照（若動排程表）。
