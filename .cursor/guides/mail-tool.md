# 寄信工具（send_mail）／HITL tool 規範

功能說明：`docs/mail.md`。本檔只放技術約定。

## 分層

| 檔 | 責任 |
|----|------|
| `server/flows/domain/mail.py` | 收件人整理、網域／人數檢查、確認畫面回傳值還原（純規則，無 LangChain） |
| `server/flows/tools/mail_senders.py` | 寄信方式 `dry_run`／`logic_app`（IO、錯誤轉 `MailError`） |
| `server/flows/tools/mail.py` | `send_mail` tool、`interrupt` 確認流程、`load_mail_tools` 啟動檢查 |
| `server/graph.py` | 只接 `*load_mail_tools()` 與 `MAIL_PROMPT` |

新增寄信方式：在 `SENDERS`／`REQUIRED_SETTINGS` 各加一筆，設定欄位加到 `flows.config.Settings`；不要在 tool 內 `os.getenv`。

## 必守

- Demo 的 `create_schedule` 在 `flows/tools/schedule.py`，純參數規則在 `flows/domain/schedule.py`。必須確認後才使用 Job Key 呼叫 `/api/internal/schedules/personal`，沿用個人 CRUD 管線；userId 取對話 metadata，不給 LLM 指定。Demo 送出訊息不經 regex 攔截，完成工具回合後側欄刷新。排程來源不能再建立排程，自動寄信預設關閉。

- 一般對話及預設模式寄信一定 `interrupt`；Edit 後再檢查收件人。免登入內網測試可明確設定 `APP_ENV=local|test|qas`、`TEST_SCHEDULE_AUTO_MAIL=true`，僅允許 `MAIL_TEST_MODE=true` 且精確清單只包含兩個核准信箱。排程 source 與當次 configurable 開關為 true 才免確認。旗標可偽造，不是安全授權；入口必須由 VPN／ingress allowlist 限少數人，不可公開或用於真實敏感資料。
- 已移除自訂 HMAC、nonce SQLite、專用 HTTP middleware；後續使用公司 Entra／IAM 標準，不能只解碼 JWT。正式環境須完成登入、排程／thread 所有權及獨立 Scheduler 服務身分驗證，再恢復免確認；受限內網測試例外如上。不要因有一般登入就信任自動寄信旗標；正式啟用時舊偏好需有權限者重新確認。
- `MAIL_TEST_MODE` 預設 true、精確信箱白名單預設空（全部拒絕）。本專案實發測試只准 `wits.johnnyho@wistron.com`／`JohnnyHo@wits.com`；To/Cc、Edit 後及最終 sender 都要檢查，任何一人不允許就整封不寄。不能讓 LLM 解除此限制。`dry_run` 日誌只記錄人數，禁止記錄信箱、主旨、內文。HTTP 錯誤不得回傳含金鑰的 URL／response body。
- 排程 `AutoSendMail` 預設 false；畫面明確說明只有受限內網測試模式可免確認。不新增登入頁或共用密碼，沿用 local-demo-user；正式 IAM 與權限待辦保留。不自動送出既有待確認信件，啟動 Job 前檢查既有到期排程。
- 排程 `runs/wait` 的 2xx 不等於完成；查 thread 的 interrupted 狀態，紀錄 `WaitingForConfirmation=4`，保留 threadId 與空 finishedAt，不發結果通知。原對話確認／取消後，查詢排程紀錄同步完成狀態。既有確定性結果通知仍維持 Draft。
- 不為寄信新增排程前端的固定收件人欄位。收件人可能來自人員查詢且包含多人；後續開放自動寄送須先確認查詢範圍、收件人規則、內容及頻率，每次執行仍檢查實際名單，超出授權不得寄送。
- 一個 LLM 回合可能呼叫多個工具；`graph.py` 以 LangGraph `task` 執行每個工具，避免後續確認中斷恢復時重複執行已完成的寄信。真實交付仍需以郵件服務紀錄確認。
- interrupt 用 agent-chat-ui HITL 格式（`action_requests`／`review_configs`，resume `{"decisions":[{"type":...}]}`），前端 `agent-inbox` 才會顯示確認卡。
- `send_mail` 的確認卡使用繁中信件欄位與「確認寄送／取消寄送」，不呈現 Studio、State、thread ID、Mark as Resolved 或重複的工具參數表。收件人陣列顯示為分號分隔文字；修改後仍走後端型別還原與收件人複查。取消直接送出明確的 reject 決定，不透過選取狀態推測。
- `MAIL_BACKEND` 空白＝不載入 tool（現有部署零影響）；啟用後若 `MAIL_ALLOWED_DOMAINS` 缺失或空白，啟動時報錯。解析後無有效網域時拒絕收件人。
- `MAIL_LOGIC_APP_URL` 含 sig 等於密碼：只放 `server/.env`／Vault，不可寫進 md、log、commit。
- Logic App 的 2xx 和工具的 `sent` 僅代表請求已受理，不代表信件已送達；需查看 Logic App 執行紀錄及收件匣。現用 Logic App 沒有副本欄位，Cc 會併入 `EmailTo`。
- tool docstring 給 LLM 看，維持英文；其他方法註解繁中。

## 正式登入接入待辦

- Token 使用公司標準套件驗證簽章、Issuer、Audience、效期與角色／scope；不可只解碼 JWT 或信任客戶端 appid。
- 使用者歸屬改取已驗證 claims；排程 CRUD、run-now、紀錄查詢及 Agent thread／state／history／resume 都檢查擁有者與核准權限，包含前端 proxy 和直接呼叫 API。
- Scheduler 用獨立服務身分；免確認須核對資料庫開關與 schedule/run/thread/assistant 關聯，一般聊天不得沿用。舊的開啟偏好要重新授權。
- 正式部署關閉 `TEST_SCHEDULE_AUTO_MAIL`，以資料權限保護動態人員查詢與內容，補寄送紀錄／冪等及重送政策。完整驗收項目維護於 `docs/mail.md`，不可只加登入頁就視為完成。
- Scheduler 僅呼叫管理者設定的 `LANGGRAPH_API_URL`（容器埠 8000），不可使用使用者傳入 apiUrl；HTTP client 不跟隨重新導向。

## 驗證（手眼）

```powershell
cd server
.\.venv\Scripts\python.exe -m pytest tests\domain tests\test_schedule_tool.py tests\test_mail_security.py -q
```

受限排程測試須另設 `APP_ENV=local`（QAS 用 qas）及 `TEST_SCHEDULE_AUTO_MAIL=true`。
設定不符允許環境、未啟用測試收件人限制或清單包含其他人時，啟動必須失敗。
測試模式開關關閉時，偽造 source／configurable 仍要人工確認；開啟時旗標不具可信身分保證，必須限制內網入口。
回歸測試使用 mock，不連 LLM、不建立真排程、不寄真信；另驗證 C# Scheduler 與前端型別／格式。
排程觸發後實際收信及等待確認兩條部署 E2E 尚須驗收，不可把單元測試當作實信證明。

本機實測：`server/.env` 設 `MAIL_BACKEND`（`dry_run` 或 `logic_app`）、`MAIL_ALLOWED_DOMAINS=wistron.com,wits.com`、`MAIL_TEST_MODE=true` 及僅包含上述兩個信箱的 `MAIL_TEST_RECIPIENTS`，
啟動 server／frontend → Chat UI 要求寄信 → 確認卡「確認寄送」 → ToolMessage `status=dry_run` 或 `sent`。
測試收件人：`wits.johnnyho@wistron.com`、`JohnnyHo@wits.com`。

真實寄送前，由環境負責人以安全方式將 `MAIL_LOGIC_APP_URL` 設定到 `server/.env` 或 Vault，
並設定 `MAIL_BACKEND=logic_app` 及允許的收件網域。獲得使用者確認後才寄送；HTTP 2xx
只證明 Logic App 接受請求，還需確認執行紀錄與收件匣，不能將 `dry_run` 當成實際寄送。

已實測（2026-11-12）：本機 `logic_app` 經 Chat UI Approve → `status=sent` → Outlook 收到。
寄件者為 Logic App 設定的信箱，主旨會被加上後綴「-AI Agent Execute Status」
（來自 `PipelineName`），cc 會併入收件人。
