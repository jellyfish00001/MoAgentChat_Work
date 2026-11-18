---
name: studio-baseurl
description: Open LangSmith Studio against local LangGraph via baseUrl; distinguish Tracing project vs Agent Server.
---

# studio-baseurl

## Correct URL

```text
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

後端必須先 `ok`：`http://127.0.0.1:2024/ok`。

## Do / Don't

- **Do**：Connect agent server / `baseUrl` 指向本機 LangGraph。
- **Don't**：點 Tracing 專案名（如 `ai_prepare`）期望進 Studio → 會 *Studio not available*。
- Token／逐步 LLM：同一帳號開 Project **ai_prepare** → **Runs**（與 Studio 是兩條路）。
- 需要保持登入：用個人 skill `playwright-cdp-session`（CDP `:9333`）。

## Verify

1. Studio 頁可見 graph 節點（如 `list_orders`…）且無 Failed to initialize。
2. Chat UI：`http://localhost:3000/?apiUrl=http://localhost:2024&assistantId=<graph_id>`。
3. 記一筆到 `.cursor/temp/verify-log.md`（無 secrets）。
