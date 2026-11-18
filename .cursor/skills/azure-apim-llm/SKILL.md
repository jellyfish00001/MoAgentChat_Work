---
name: azure-apim-llm
description: Smoke-test Azure AAD + APIM LLM via flows.llm.azure_apim; classify token/APIM/model failures.
---

# azure-apim-llm

## Steps

1. 確認工作目錄可 import：`cd server`（`flows` 在 `server/flows`）。
2. `server/.env` 含正式契約的 8 個必填變數（見 `server/.env.example`）；勿印出 secrets。
3. 啟動 venv 後執行：

```powershell
cd D:\mo_agentchat\server
.\.venv\Scripts\python.exe -m flows.llm.azure_apim "只回覆 OK"
```

4. 成功：stdout 含模型回覆。失敗：依錯誤分類（token／APIM／model／network／import），寫入 `.cursor/temp/verify-log.md`。
5. 工廠必須 `use_responses_api=False`（對齊 `server/graph.py` 公司 AI Gateway）。
