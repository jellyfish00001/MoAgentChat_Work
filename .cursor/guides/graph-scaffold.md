# 新 Graph 建檔順序

1. 在 `server/flows/graphs/<name>/` 建立：
   - `state.py` — TypedDict + `messages`
   - `nodes.py` — 薄節點
   - `prompts.py` — 僅 LLM 文案
   - `graph.py` — 組裝並 `export graph`
2. 業務數字／分流放 `server/flows/domain/`（無 LLM）
3. 結構化輸出放 `server/flows/schemas/`
4. 註冊 `server/langgraph.dev.json` 的 `graphs` 鍵（本機多流程）
5. 加 `server/tests/domain/` 單測（規則優先）
6. `langgraph dev --config langgraph.dev.json` 驗證
7. **晉升正式**時才改 `server/langgraph.json`（及 Dockerfile／CI）；平時勿動

可用 Skill `scaffold-graph` 產生骨架；不要一次生三條業務圖。
