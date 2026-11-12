# 本機前後端啟動（複製到 Cursor 終端）

需 **PowerShell 7**（`pwsh`）。工作目錄：`D:\mo_agentchat`（repo 根）。

| 服務 | URL |
|------|-----|
| 前端 Chat | http://localhost:3000 |
| 後端 LangGraph | http://localhost:2024 （`/ok` 應回 `{"ok":true}`） |

前端請確認 `frontend/.env.local`：

```env
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

（業務圖可改 `rework_mo_detective` / `rd_risk_dashboard` / `qv_dms_pipeline`。）

---

## 方式 A：兩個 Cursor 終端（建議）

**終端 1 — 後端**

```powershell
pwsh -NoProfile -File .cursor/scripts/local-dev/start-backend.ps1
```

**終端 2 — 前端**

```powershell
pwsh -NoProfile -File .cursor/scripts/local-dev/start-frontend.ps1
```

---

## 方式 B：一次開兩個系統視窗

```powershell
pwsh -NoProfile -File .cursor/scripts/local-dev/start-all.ps1
```

---

## 手動（不用腳本）

**後端**

```powershell
cd server
.\.venv\Scripts\Activate.ps1
langgraph dev --no-browser --config langgraph.dev.json
```

**前端**

```powershell
cd frontend
pnpm install
pnpm dev
```

---

## 檢查

```powershell
Invoke-WebRequest http://127.0.0.1:2024/ok -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing
```

埠被佔用：後端可改 `--port 2025`（並把 `.env.local` 的 API URL 對齊）；前端若跳到 3001，先關掉佔 3000 的舊 `next dev`。

詳見：`.cursor/scripts/local-dev/README.md`、`.cursor/MAP.md` §5。
