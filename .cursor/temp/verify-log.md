# W.AgentChat UI 驗收紀錄

## 清理索引（2026-11-12）

本節優先於下方歷史路徑；舊驗收結果不是目前版本的驗收證明。
本次實際盤點為 52 張 PNG（先前口頭估計 53 張不正確），以 6 張編號總覽檢視全部圖片，
另開原圖確認 Classic 主題、舊側欄、dry-run 錯誤遮罩、小視窗遮擋及修正後彈窗等案例。
這是歷史資料清理，不是重新執行 UI 或排程測試，也不宣稱每張原圖均逐字閱讀。

- 使用者確認測試過程圖片不需保留，因此全部刪除，不留歷史圖或代表圖。
- 下方提及的截圖均為歷史索引，原檔已清除；文字結論不代表新週月排程／自動寄信已驗收。
- `schedule-phase-gates.md` 與 `architecture-review.md` 已刪除：前者重複 `guides/phase-delivery.md`，後者為過時架構快照；未完成事項已摘要至 `open-decisions.md`。
- 保留歷史 JSON/API 證據、瀏覽器 profile 及仍被啟動腳本引用的 Playwright 工具。本次不讀取或清除登入 cookies。

Date: 2026-10-29  
URL: http://localhost:3000  
Shots: `.cursor/temp/ui-shots/`

## 主題（現行）

- 僅 **Light**（預設）／**Dark**；`wistron-classic` 已移除，舊值遷移為 Light。
- `:root` / `data-theme="wistron-light"` = frosted paper；`wistron-dark` = deep navy。

## 截圖索引（歷史；Classic 檔名為舊版）

| 檔案 | 區塊 | 結論 |
|------|------|------|
| 01-classic-hero-settings.png | 舊 Classic + Theme 三色選單 | 已過時（Classic 已刪） |
| 02-dark-hero-settings.png | Dark 主題 | 符合色票 |
| 03-light-hero-settings.png | Light 主題 | 符合色票（現為預設） |
| 04-classic-history-sheet.png | 歷史 Sheet | 舊版；邏輯仍用 panel token |
| 05-classic-chat-loading.png | 對話中／loading | 舊版；後端未起時 toast 屬預期 |
| 06-classic-rounded-shark-letters.png | 鯊魚字母 + 圓角 | 形狀／字母邏輯仍有效 |
| 07-dark-rounded-settings.png | Dark + 圓角 + 選單 | 符合；選單應僅剩兩色塊 |

## 看圖／取樣核對

### ASCII
- **鯊魚身體**：小寫 `wistron` 字母。
- **背景**：純 `--ascii-bg` + 淡格線；魚群 `-` 近滿透明度，鯊略透。

### UI
- Theme：兩色圓形 swatch（Light／Dark）；預設 Light。
- GitHub 已移除；標題 **W.AgentChat**。

### 已知／待改善
1. 本機未起 LangGraph 時連線 toast／Dev overlay — 與美術無關。
2. Agent inbox／tool 表需 interrupt 流程才易完整截圖。

## Build
- `pnpm run build`（frontend）：先前已通過；本次僅刪 Classic token／選單。

## 本機服務（2026-10-29）
- Frontend `:3000` 已在跑。
- Backend：`langgraph.dev.json` 曾帶 UTF-8 BOM → 已改無 BOM；`langgraph dev` Ready，`GET /ok` → `{"ok":true}`。
- Chat：http://localhost:3000 ；API：http://127.0.0.1:2024

---

## 規範／架構 pass 回歸（2026-10-29 午後）

Skills：`run-graph-smoke`（後 API + 前 Chat）。Ports：API `2024`，UI `3000`。

| 檢查 | 結果 |
|------|------|
| `GET /ok` | `{"ok":true}` → `ui-shots/backend-ok.json` |
| `POST /assistants/search` | 含 `agent`／`rework_mo_detective`／`rd_risk_dashboard`／`qv_dms_pipeline` → `assistants-search.json` |
| API `runs/wait` rework | thread OK；7 messages；persist 寫出 outputs → `rework-smoke-summary.json` |
| Chat UI 載入 | W.AgentChat Light → `frontend-chat-loaded.png` |
| Chat UI rework 送訊 | `assistantId=rework_mo_detective`；list_orders 見 3 工單＋narrate → `frontend-graph-smoke.png` |
| 後端證據頁截圖 | `backend-ok-or-assistants.png` |

已知雜訊（非本 pass 引入）：Next.js hydration overlay（`thread/history`）；不影響本次煙測回覆。

報告：`.cursor/temp/architecture-review.md`；待決：`.cursor/temp/open-decisions.md`（未改 OPEN-QUESTIONS）。

## Schedule UI P3–P5（2026-11-04，前端模組；未跑瀏覽器 smoke）

- Parser self-test：`pnpm dlx tsx src/lib/scheduleDraftParser.test.ts` → OK
- 依賴：Schedule API `http://127.0.0.1:5055`、LangGraph `NEXT_PUBLIC_API_URL`、`.env.local` 已加 `NEXT_PUBLIC_SCHEDULE_API_URL`
- 手動：側欄排程 CRUD／run-now；composer 送「每天早上9點提醒我…」→ 確認卡；排程 thread 徽章＋標題


## Schedule Phase P0 — 2026-11-04
### 實作範圍
- .cursor phase-delivery / hands-eyes / guides / MAP / AGENTS / USER / temp gates
- scheduler 分層骨架 + sln；Domain.Tests 2 passed；build OK
### 自動化／API／Hangfire 證據
- dotnet test Domain.Tests 2 passed
- dotnet build AiPrepare.Scheduler.sln 成功
### UI 截圖
- （P0 無 UI）
### Git
- （待本輪 push）
### 結論
- PASS

## Schedule Phase P1 — 2026-11-04
### 實作範圍
- Domain/Application/Infrastructure/Api；共用 IScheduleRunExecutor；SQLite；CORS/JobKey；runs API
- 修正 SQLite DateTimeOffset ORDER BY
### 自動化／API 證據
- temp/ui-shots/schedule/p1-health.json
- temp/ui-shots/schedule/p1-create.json
- temp/ui-shots/schedule/p1-list.json
- temp/ui-shots/schedule/p1-patch.json
### 結論
- PASS（HTTP CRUD）

## Schedule Phase P3–P5 — 2026-11-05
### 實作範圍
- 前端模組：schedule-api／parser／側欄／徽章／頂欄／意圖確認卡（繁中方法註解）
- 驗收預覽：`?scheduleConfirmPreview=true`（不寫庫）
### UI 截圖（Agent 已 Read）
- [x] p3-sidebar-overview.png／p3-schedule-sidebar.png — 側欄列表+表單，semantic tokens
- [x] p4-schedule-badge-header.png — 歷史「排程」徽章＋頂欄 schedule 標題
- [x] p5-intent-confirm-card.png — 確認卡「建立排程？」可見
### 否決項
- 無明顯溢出；確認卡對比足夠
### 結論
- PASS

## Schedule Phase P6 — 2026-11-05
### 實作範圍
- `.cursor` 規則：繁中每方法註解；commit 繁中說明；Hangfire 維運口令寫入 scheduler-coding
- repo：`scheduler/README.md` 極短啟動
### 結論
- PASS（總驗收：Api health、Hangfire Succeeded、LangGraph thread、Chat 側欄／確認卡）

## GPT 排程側欄 UI — 2026-11-05
### 實作範圍
- GraphSwitcher：移除「全員·Demo／財務隱藏說明／目前：…」
- ScheduleSidebar：GPT 式橫幅（展開／＋）、列名開上次對話、刪除｜立即執行｜編輯、暫不執行弱色後排
- ScheduleDialog＋ui/dialog：新增／編輯＋「暫不執行」→ enabled=false（Create 後 PATCH）
### UI 截圖（Agent 已 Read）
- [x] p-ui-banner-collapsed.png — Demo 下方僅「排程 7」橫幅＋＋，列表收合
- [x] p-ui-banner-expanded.png — 列名＋刪除／播放／編輯圖示
- [x] p-ui-create-dialog.png — 新增彈窗含暫不執行 Switch
### 否決項
- 無溢出／半成品；Dialog 對比足夠；無硬編碼破壞 tokens
### 結論
- PASS

## 側欄 W.AgentChat／聊天摺疊 — 2026-11-05
### 實作範圍
- Thread History → W.AgentChat；移除 Separator
- 新增可摺疊「聊天」橫幅包住對話列表
- 排程／聊天 hover：展開聊天／摺疊聊天
### UI 截圖（Agent 已 Read）
- [x] sidebar/01-schedule-expanded.png — 排程展開 hover「摺疊聊天」
- [x] sidebar/02-chat-expanded.png — 聊天展開 hover「摺疊聊天」
- [x] sidebar/03-schedule-collapsed.png — 排程收合
- [x] sidebar/04-chat-collapsed.png — 聊天收合 hover「展開聊天」
- [x] sidebar/05-sidebar-overview.png — 無分隔線、標題 W.AgentChat
### 自動化 tip 文案
- 排程展開／聊天展開 → 摺疊聊天；收合 → 展開聊天
### 否決項
- 無分隔線；無 Thread History；tooltip 對比足夠
### 結論
- PASS

## 對話 … 選單與 tooltip 上方 — 2026-11-05
### 實作範圍
- 聊天列右側「…」：重新命名（metadata.thread_title）／刪除對話
- 排程／聊天展開箭頭 tooltip 改 side=top（箭頭上方）
### UI 截圖（Agent 已 Read）
- [x] sidebar/06-tooltip-top.png — tipAbove=true，文案「摺疊聊天」
- [x] sidebar/07-thread-menu.png — 「重新命名」「刪除對話」
- [x] sidebar/08-rename-dialog.png — 重新命名彈窗
### 結論
- PASS

## 排程預設收合＋選單右上 — 2026-11-05
- 排程預設收合並 localStorage 記住
- …選單 fixed 錨在按鈕右上方（above+rightAligned）
- 截圖 sidebar/09-menu-topright.png
### 結論
- PASS

## 排程 Dialog 響應式 — 2026-11-05
- 改 max-h／vw 寬度；表單可捲；Select portal
- large／mid／short／narrow 量測 fits+欄位不溢出；listbox portal OK
- 截圖 11–15
### 結論
- PASS

## 聊天捲軸 auto＋Dialog 視窗比例 — 2026-11-05
- 聊天列表 overflow-y-scroll→auto；隱藏 webkit scrollbar-button
- Dialog max-h/w = calc(100dvh/vw - 1.5rem)；表單可捲、按鈕固定
- 驗證：needsScroll=false；520×560／480×420 fits+createVisible
### 結論
- PASS

## Scheduler 通知介面（Draft 不實發）— 2026-11-05
- 新增 `INotificationSender` + `DraftNotificationSender`；`Notification:Mode=Draft`
- Schedules：`NotifyEnabled`／`EmailTo`／`EmailCc`；Runs：`NotifyOutcome`
- Migration `AddScheduleNotificationFields`；`dotnet build` scheduler sln OK
- 文件：`schedule-api`／`deploy`／`db` 流程圖更新；`schedule-db.md` 末尾 Schema 快照
- 未跑實機寄信；Http 實發尚未實作（刻意）
### 結論
- PASS（介面＋Draft；未驗證 run-now 端到端，需重啟 Api／Job 套用 Migrate）

## schedule-db 執行期流程圖改上→下 — 2026-11-05
- 拆成三張 TD 單欄圖；避免橫向匯流＋useMaxWidth 壓縮看不清
- Playwright 560px 寬預覽截圖：`.cursor/temp/ui-shots/schedule/runtime-flow-td.png`
- Read 圖片：字可讀、圖 1／3 明顯直向；未整頁裁切
### 結論
- PASS

## 2026-11-12 FAA-25 寄信合併（mo_agentchat）

- 來源：ai_prepare `origin/FAA-25/mail-logic-app`（a6c5416、29df2bd），依 flows 分層改寫
- pytest：`server/tests` 全部 29 passed（新增 test_mail 8、test_mail_tool 6）
- ruff check／format --check：PASS
- 真 LLM dry_run 冒煙（.cursor/temp/mail_smoke.py）：tools 含 send_mail → __interrupt__ 為 HITL 格式（to=wits.johnnyho@wistron.com，cc=JohnnyHo@wits.com）→ approve → ToolMessage status=dry_run，AI 回覆告知測試模式未寄出
- 未真寄：本機無 MAIL_LOGIC_APP_URL（logic_app 未驗）
- 2026-11-12 Chat UI 驗收（localhost:3000，graph agent）：送寄信需求 → 出現 send_mail 確認卡（To/Cc/Subject/Body 可編輯、Approve/Reject）→ Approve → Tool Result status=dry_run，AI 回覆「測試模式，沒有真的寄出」；backend log 有 [mail dry_run] 完整信件。截圖：ui-shots/mail/faa25-dry-run-result.png。頁面 1 Issue 為 schedule-api 未啟動（與寄信無關）

### FAA-25 寄信確認補充

- 發現同一回合多個工具依序中斷時，已核准的寄信可能在恢復後重複執行；已以 LangGraph `task` 保存各工具結果，並測試寄信後接天氣、兩封信分別核准或拒絕。
- 使用僅綁定 loopback 的假 Logic App 驗證 POST 欄位、中文內容、核准／拒絕、修改後網域檢查及 HTTP 503 錯誤；未寄出真信。
- 實際 LLM 與本機 LangGraph HTTP API 的 `dry_run` 測試通過，均確認只有一次寄信工具結果；測試 API 已關閉。
- `server/tests`：38 passed；Ruff check／format --check：PASS。
- 已修正 `.cursor` 中與目前 `langgraph.json`、本機路徑及寄信狀態不符的說明；前言格式與 Graph 設定驗證通過。
- 實際寄信仍未執行：尚無 `MAIL_LOGIC_APP_URL`；Logic App 受理請求不代表信件已送達。

- 2026-11-12 11:05：依使用者要求移除暫時驗證檔（server/tests/tools/*、.cursor/temp/mail_smoke.py），僅保留規範要求的 tests/domain/test_mail.py；pytest 23 passed、ruff 通過、graph 載入含 send_mail。
