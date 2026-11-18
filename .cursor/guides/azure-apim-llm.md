# Azure AAD + APIM LLM

## 環境變數（`server/.env`）

| 變數 | 用途 |
|------|------|
| `AZ_TENANT_ID` | Azure AD tenant |
| `AZ_CLIENT_ID` | App registration |
| `AZ_CLIENT_SECRET` | Secret |
| `AZ_SCOPE` | 通常 `https://cognitiveservices.azure.com/.default` |
| `AZ_LLM_ENDPOINT` | APIM gateway |
| `AZ_LLM_VERSION` | API version |
| `LLM_MODEL_NAME` | 部署／模型名 |
| `OCP_APIM_SUBSCRIPTION_KEY` | APIM 訂閱 key |

## 呼叫

```powershell
cd server
python -m flows.llm.azure_apim "只回覆 OK"
```

或 Skill `azure-apim-llm`。

實作唯一入口：`server/flows/llm/azure_apim.py`。
