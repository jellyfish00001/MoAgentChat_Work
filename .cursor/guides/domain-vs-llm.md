# Domain vs LLM

此檔是**技術邊界**（什麼用程式算、什麼交給 LLM）。業務流程示意（非正式）在 `docs/flow-templates/`；coding／Agent 規範在 `.cursor/rules` 與 skills。

| 放 domain（程式） | 放 LLM 節點 |
|-------------------|-------------|
| Excel 載入／欄位檢查 | Reason 敘事、改善建議文案 |
| 工單去重清單 | DSCA／主料語意配對（後期） |
| 261/101/531、跨月、BOM 存在性 | 綜合研判短報告 |
| 金額加總、情形分流骨架 | structured output 填空 |

原則：**數字用程式算，語意與文字交給 LLM**。禁止把完整規則表塞進 system prompt。
