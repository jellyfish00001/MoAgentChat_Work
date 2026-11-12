# Playwright 固定 Port 測 LangSmith／Studio

## 為什麼你會看到 Failed to initialize Studio

常見原因：

1. 點了 Tracing 專案 **ai_prepare**（那不是 Agent Server）
2. Studio URL **沒有** `baseUrl=http://127.0.0.1:2024`
3. 本機後端 `:2024` 沒開
4. 用別的瀏覽器分頁、登入狀態／連線設定不一致

正確 Studio 連結：

`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## 固定 Port + 保持登入

| 項目 | 值 |
|------|-----|
| CDP Port | **9333** |
| Profile | `.cursor/temp/pw-langsmith-profile/`（持久 cookies） |
| 啟動 | `pwsh .cursor/scripts/local-dev/start-playwright-langsmith.ps1` |
| 檢查 | `node .cursor/scripts/local-dev/pw-check-studio.mjs` |
| 正式環境 | `https://columbus-langsmith.wistron.com/o/f679e495-9a73-469f-a922-f4c3b165ff3a` |

1. 確認後端：`http://127.0.0.1:2025/ok`（或 `:2024`，視啟動埠）
2. 執行啟動腳本 → 會開 **headed Chrome**，預設帶 **正式 Columbus** +（可選）本機 Studio
3. 若未登入：在該視窗登入（登入狀態會留在 profile）
4. 不要關這個 Chrome／不要關啟動終端
5. Agent 可用 CDP `http://127.0.0.1:9333` 接上同一視窗一起測

旗標：`--formal`（正式 org）、`--studio`（本機 Studio `baseUrl`）。

看 token／逐步思考：正式環境用 Columbus org；雲端則 https://smith.langchain.com → Project **ai_prepare** → Runs  
（這與 Studio 的 `baseUrl` 連線是兩件事。）
