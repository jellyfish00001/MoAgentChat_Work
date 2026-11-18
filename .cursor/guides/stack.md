# Stack

| 層 | 技術 |
|----|------|
| 後端 | Python 3.11+、LangGraph、langgraph-cli（`langgraph dev` → `:2024`） |
| LLM | Azure AD Client Credentials → APIM → `AzureChatOpenAI` |
| 觀測 | LangSmith tracing（`LANGCHAIN_*` / `LANGSMITH_*`） |
| 前端 | [agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui)（Next.js，`:3000`） |
| 依賴 | `server/requirements.txt` 與 `requirements-dev.txt`（backend）；`pnpm-lock.yaml`（frontend） |

契約：Graph state 含 `messages`（`add_messages`），才能接 chat UI。
