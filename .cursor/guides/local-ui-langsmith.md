# 本機 Chat UI × LangGraph × LangSmith（精簡）

正式專案文件不放操作瑣事；本檔僅給 Agent／本機開發用。

## 分清三件事

| 東西 | 在哪 | 看什麼 |
|------|------|--------|
| Graph 程式／註冊 | `server/flows/graphs/`；本機用 `langgraph.dev.json`，部署用 `langgraph.json` | 節點、State、Graph ID |
| 流程示意（範本） | `docs/flow-templates/` | Mermaid；非正式 runbook |
| 執行軌跡／token | LangSmith 網站（本機 trace 上傳） | 節點、LLM span、延遲 |

沒有「本機 LangSmith 桌面版」。`:2024`＝API JSON；`:3000`＝聊天畫面。

## 啟動

指令 SSOT：[local-start.md](local-start.md)。摘要：

- API：`http://localhost:2024`；Chat：`http://localhost:3000`
- Graph ID：`agent`｜`rework_mo_detective`｜`rd_risk_dashboard`｜`qv_dms_pipeline`（須為兩份 `langgraph*.json` 鍵名）
- 連本機時前端 **LangSmith API Key 留空**（`NEXT_PUBLIC_AUTH_SCHEME` 空）。**看過程＝後端 tracing 上傳**。

正確資料流：

```text
瀏覽器 Chat UI (:3000) ──HTTP──► 本機 LangGraph (:2024/:2025)
                                      │
                                      └── trace 上傳 ──► LangSmith 網站（看節點／token）
```

（可選）Studio：見 [playwright-langsmith.md](playwright-langsmith.md)；`baseUrl` 對齊實際後端埠。

Smoke（Rework MO）：「提取並輸出待分析工单清单」

## LangSmith／Studio

- Tracing 專案名 **以 `server/.env` 的 `LANGCHAIN_PROJECT` 為準**（勿在文件寫死別名）；需 `LANGCHAIN_TRACING_V2=true` + API key。
- 正式瀏覽可走 Columbus LangSmith；雲端備援 `https://smith.langchain.com` → Project → Run。
- Studio（連本機）：終端印的 `...?baseUrl=http://127.0.0.1:2024`；不要從 Tracing 專案名稱進 Studio。
- 保持登入（可選）：`pwsh .cursor/scripts/local-dev/start-playwright-langsmith.ps1`

## 我想看 X → 去哪

| 想… | 去哪 |
|-----|------|
| 範本流程圖 | `docs/flow-templates/` |
| 改節點／規則 | `server/flows/graphs/`、`domain/` |
| 本機 Graph 註冊 | `server/langgraph.dev.json` |
| token／每步 LLM | LangSmith → 專案＝`LANGCHAIN_PROJECT` |
| 聊天 | `http://localhost:3000` |
| domain pytest | `cd server && python -m pytest tests/domain` |
| 規範機器閘道 | `.cursor/scripts/checks/run-all.ps1` |

Dockerfile 會複製 `server/testdata/`。資料路徑可用 `FLOWS_TESTDATA_ROOT` 等覆寫（見 `server/.env.example`）。Graph 鍵集合以兩份 json＋checks 腳本為準。
