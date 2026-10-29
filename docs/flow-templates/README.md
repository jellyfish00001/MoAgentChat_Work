# 本機流程圖範本（非正式紀錄）

> **邊界**：非正式示意／**非**正式 runbook／**非** coding 規範。  
> Agent／技術約定 → [`.cursor/`](../../.cursor/MAP.md)；程式註解政策 → `.cursor/rules/aipark-docs-comments.mdc`。  
> 業務待決（給 user）→ [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)；Agent／架構審查待決 → `.cursor/temp/open-decisions.md`（勿混寫進 OPEN-QUESTIONS）。

與 Cursor Plan 相同：Markdown + Mermaid。**這是本機／測試用示意圖**，不是正式環境 runbook。

預覽：開 `.md` → `Ctrl+Shift+V`（建議擴充 `bierner.markdown-mermaid`）。  
每個 `01`／`02`／`03`：**上半**＝現行 Graph；**下半「原始客戶需求」**＝客戶 README 原樣附錄。附錄 ≠ 已 100% 實作。

- **業務待決問題（請回覆）：** [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)  
- **產出形態：** 規則／金額／Excel／HTML＝程式；LLM＝文案節點。

## 三流程總覽

| # | Graph ID | 業務本質 | LLM | 範本 |
|---|----------|----------|-----|------|
| 1 | `rework_mo_detective` | 情形＋六大檢查＋行級 Reason | `narrate` 短報告（不改 Reason） | [01](01-範本-rework_mo_detective.md) |
| 2 | `rd_risk_dashboard` | 六類異常＋KPI＋HTML 模板 | `narrate` 研判／行動 | [02](02-範本-rd_risk_dashboard.md) |
| 3 | `qv_dms_pipeline` | Cover 回填鏈＋期別分析 | `narrate` 改善方向 | [03](03-範本-qv_dms_pipeline.md) |

原則（見 [`.cursor/guides/domain-vs-llm.md`](../../.cursor/guides/domain-vs-llm.md)）：**數字與規則用程式；語意與對外文案才給 LLM。**

## 程式對照

| 層 | 路徑 |
|----|------|
| Graph 節點 | `server/flows/graphs/<id>/` |
| 純規則（無 LLM） | `server/flows/domain/<主題>/` |
| LLM 結構化輸出 | `server/flows/schemas/` |
| 測試 Excel | `server/testdata/<主題>/` |
| 產出 | `server/outputs/` |
| 本機註冊 | `server/langgraph.dev.json`（正式 image 僅 `agent`） |
