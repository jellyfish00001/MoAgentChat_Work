# 寄信功能

讓 agent 幫使用者寄信。一般對話必須在畫面確認；受控內網測試可明確啟用排程自動寄信，正式模式仍須先完成公司登入與服務授權。

## 免登入內網測試模式

- 不新增登入頁或共用密碼，沿用 `useLocalUser` 的 `local-demo-user`（localStorage 可指定測試 ID）。這只是模擬使用者，不是身分驗證，測試人員之間沒有可信的資料隔離。
- Agent 設定 `APP_ENV=local|test|qas`、`TEST_SCHEDULE_AUTO_MAIL=true`、`MAIL_TEST_MODE=true`，且 `MAIL_TEST_RECIPIENTS` 非空並只能包含 `wits.johnnyho@wistron.com`／`JohnnyHo@wits.com`，才可測試自動寄信；錯誤設定啟動即失敗。自動寄信測試開關預設 false。
- 排程已保存 `autoSendMail=true` 且本次 run 來源為 schedule、configurable 開關為布林 true 時免確認；關閉的排程與一般對話仍停在確認卡。已等待確認的信件不會因啟用測試模式被自動送出。
- **這些旗標不是可信授權，能直接存取 API 的人也能偽造**。僅限公司內網、VPN 或既有 ingress allowlist 限制的少數測試人員，Agent／Scheduler 不得直接公開。應用程式本身沒有測試人員白名單或登入保護，部署者必須在入口限制存取。
- 既有 `autoSendMail=true` 的排程在此模式下會恢復自動寄信；啟動 Job 前先檢查既有到期排程。不使用真實薪資／敏感資料，也不增加未核准的實發信箱。正式部署停用測試模式，後續驗證待辦仍須完成。

## 寄信流程

```text
使用者提出寄信需求
  → LLM 整理收件人、副本、主旨、內文，呼叫 send_mail
  → 檢查收件人
  → 畫面出現寄信確認卡，等使用者確認寄送或取消
  → 再檢查一次收件人（使用者可能在確認卡改過）
  → 送到 Logic App 寄出
  → 回報結果
```

- **確認寄送**：依畫面內容寄出；可先修改收件人、副本、主旨與內文。
- **取消寄送**：取消，不寄信，不需要填寫拒絕原因。
- 確認卡只顯示信件欄位與操作，不顯示 Studio、執行狀態、工具 ID 等開發資訊；收件人清單以分號隔開，不顯示 JSON 陣列。

## 排程與動態收件人

- 對話寄信可從人員查詢結果整理多人收件名單，但每封信仍須顯示確認卡，使用者確認後才寄出。
- 排程「信件自動發送」開關預設關閉。僅管理者啟用上述受限測試模式時生效，其他環境只保存偏好並等待人工確認。收件人仍由執行內容或查詢結果帶入，不新增固定信箱欄位。
- 關閉時，排程執行到 `send_mail` 會等待原對話的寄信確認卡。排程紀錄為 `WaitingForConfirmation`，可從側欄點排程名稱開啟原對話，確認或取消；不會誤記成已成功寄送。
- 已移除自訂請求簽章、專用 HTTP middleware 與防重播 SQLite；不再需要額外共用簽章金鑰或 nonce 磁碟。舊的 `schedule_mail_authorized=true` 不生效；受限測試模式另外由 Agent 環境設定明確啟用。
- Scheduler 遇到自動寄信偏好時會記錄由 Agent 測試政策決定是否確認的警告。尚未完成的工具恢復時會走新流程；已完成的寄送無法撤回。郵件服務結果不確定時，不可盲目重試。
- 每封仍檢查 To/Cc 的網域與合計 20 人限制。多人同封彼此看得到收件名單；個人薪資等不同內容須逐封呼叫，不能群寄。此開關不是完整的薪資人員權限驗證或批次寄送管理。
- 既有排程結果通知仍維持 Draft，只寫紀錄，沒有開啟實際寄送。

## 收件人規則

- 收件人至少 1 位。
- 收件人加副本最多 20 位。
- 每個地址都要是有效的 email，網域必須在 `MAIL_ALLOWED_DOMAINS` 清單內（不分大小寫）。
- `MAIL_TEST_MODE` **預設 true**，To/Cc 還必須逐一精確符合 `MAIL_TEST_RECIPIENTS`；同公司其他人也不允許。清單空白時全部拒絕。確認卡修改後與最終 Logic App 出口都會再次檢查；只要一位不允許，整封不寄。
- 收件人可以用 list，或用逗號、分號隔開的字串，前後空白會自動去掉。
- 不符合規則就不寄出，直接回報原因。

## 寄出的內容

送到 Logic App 的欄位：

| Logic App 欄位 | 內容 |
|---|---|
| `DataFactoryName` | 主旨 |
| `EmailTo` | 收件人和副本，用 `;` 隔開 |
| `ErrorMessage` | 內文（純文字） |
| `PipelineName` | 固定 `AI Agent` |

收到的信：

- 寄件者是 Logic App 設定的信箱。
- 主旨後面會加上「-AI Agent Execute Status」。
- 目前沒有獨立的副本欄位，副本會和收件人一起放在收件者。

## 回報結果

| status | 意思 |
|---|---|
| `sent` | Logic App 已收到請求（2xx）。不代表已送達，請到信箱確認 |
| `dry_run` | 不寄出，只記錄收件人數，不記錄信箱／主旨／內文 |
| `cancelled` | 使用者取消 |
| `rejected` | 收件人不符合規則 |
| `failed` | Logic App 回錯誤或連不上 |

## 設定

| 環境變數 | 說明 |
|---|---|
| `MAIL_BACKEND` | 空白＝不開寄信；`dry_run`＝只寫 log；`logic_app`＝真的寄出 |
| `MAIL_ALLOWED_DOMAINS` | 允許的收件網域，逗號隔開，例如 `wistron.com,wits.com` |
| `MAIL_LOGIC_APP_URL` | Logic App 的 HTTP 觸發網址（`logic_app` 必填） |
| `MAIL_TEST_MODE` | 預設 true；只有管理者明確設定 false 才能解除精確測試信箱限制，LLM 不得變更 |
| `MAIL_TEST_RECIPIENTS` | 允許測試的完整信箱，逗號／分號隔開、不分大小寫；預設空白全部拒絕 |
| `APP_ENV` | 測試排程自動寄信只接受 local、test、qas；這是部署宣告，不是登入驗證 |
| `TEST_SCHEDULE_AUTO_MAIL` | 預設 false；true 時啟用受限內網測試自動寄信，強制測試信箱限制 |

- 沒設定 `MAIL_BACKEND` 就不開寄信，其他功能不受影響。
- 有設定但缺少必填變數時，server 啟動就會報錯。
- `MAIL_LOGIC_APP_URL` 含簽章，等同密碼：本機只放 `server/.env`，部署放 Vault，不能進 Git。
- Scheduler 的執行及狀態查詢只使用管理者設定的 `LANGGRAPH_API_URL`（未設定為本機 `127.0.0.1:2024`），不再信任排程傳入的 `apiUrl`，也不跟隨 HTTP 重新導向，避免把特權請求送到使用者指定主機。
- **尚未涵蓋**：使用者登入、排程所有權、公開 CRUD／run-now 及 Agent thread／確認回覆的存取控制。人工確認不等於確認者已驗證身分；未完成前僅限受控測試，不可公開部署或處理真實薪資資料。Prompt、同公司網域及自動寄信開關都不是個資存取權限，也不能保證消除提示詞注入。

### 公司登入接入後必補的驗證（待辦）

參考 ERS 的 API 驗證、Job → Domain Service 分層與測試信箱控管；本專案的 Scheduler → Agent 是跨 HTTP 服務，不能直接把 ERS 的進程內信任套到公開 Agent API。

- [ ] 使用公司 Entra／IAM 標準驗證套件，驗證 Token 簽章、Issuer、Audience、效期；不能只解碼 JWT 或信任客戶端宣稱的 appid。依公司政策驗證租戶、角色／scope；缺少或錯誤 Token 回 401，權限不足回 403。
- [ ] 使用者 ID 取已驗證 claims；替換 localStorage userId、body userId 與對話 metadata 作為授權依據的用法。排程新增、讀取、修改、刪除、執行與紀錄查詢皆檢查所有權／角色。
- [ ] 同步保護 frontend proxy、Scheduler 公開與 internal API、Agent thread／state／history／resume 等入口。確認卡只有有權限的使用者可核准；不能只驗證前端，保留繞過 API 的測試。
- [ ] Scheduler 使用獨立的公司服務身分（如 client credentials 或平台 workload identity），Agent 驗證呼叫者及限定 scope／角色。一般已登入使用者仍不能開啟「可信排程執行」權限；服務憑證不放前端或 LLM 參數。
- [ ] 免確認授權由後端根據已驗證 Scheduler 身分、資料庫排程開關、擁有者、schedule/run/thread/assistant 關聯產生；一般聊天不能沿用。舊偏好須由有權限者重新確認才啟用，不因接好登入就自動恢復所有既有 true。
- [ ] 保留 To/Cc、Edit 後、最終出口的測試信箱限制，正式解除由管理者控管；查詢人員資料與信件內容必須符合擁有者的資料權限。薪資等內容需逐人隔離，不能靠網域白名單。
- [ ] 加入持久化寄送紀錄與重送／冪等策略（可參考 ERS MailLog，但已受理不等於已送達），記錄排程、執行、核准者、實際收件人及結果；權限、保留期限與敏感內容最小化另行定義。
- [ ] 驗收：未登入、錯誤 audience／issuer／簽章、過期、跨使用者排程／thread、偽造旗標、一般使用者冒充服務、重複觸發、Edit 繞過都被阻擋；合法排程自動寄信與人工確認兩條流程通過後，才啟用正式環境免確認分支。上述受限內網測試例外不代表正式授權完成。

### 部署前最小檢查

1. 重新建置 Agent、Scheduler Api 與 Job 映像，同步部署程式及 `langgraph.json`；不再使用已移除的 HTTP middleware。
2. Api／Job 的 `LANGGRAPH_API_URL` 指向叢集內 Agent Service（容器預設埠 8000），不可沿用本機埠 2024。
3. 不再設定舊的簽章金鑰、nonce DB 環境變數或其專用掛載；Scheduler 本身的排程 DB 仍須持久化，並未移除。Agent 對話持久化與副本限制依原部署架構處理，不因這次簡化而自動支援多實例。
4. 保留 `MAIL_TEST_MODE=true`，精確清單只放 `wits.johnnyho@wistron.com,JohnnyHo@wits.com`；Logic App URL 另由 Secret 注入。沒有設定清單時寄信會被拒絕，這不是部署失敗。
5. 確認 Agent、Api 健康檢查；檢查既有排程後再啟動 Job。測試模式驗收自動寄信開啟／關閉兩條流程；部署實信驗收只可寄給上述兩個信箱，單元測試不等於部署環境實信驗收。

## 程式位置

| 檔案 | 內容 |
|---|---|
| `server/flows/domain/mail.py` | 收件人整理與檢查（純規則） |
| `server/flows/tools/mail_senders.py` | 寄信方式：`dry_run`、`logic_app` |
| `server/flows/tools/mail.py` | `send_mail` 工具與確認流程 |
| `server/graph.py` | 把 `send_mail` 接進 agent，避免恢復確認時重複寄出 |

## 本機測試

1. `server/.env` 設定 `MAIL_BACKEND`、`MAIL_ALLOWED_DOMAINS`、`MAIL_TEST_MODE=true`、`MAIL_TEST_RECIPIENTS=wits.johnnyho@wistron.com,JohnnyHo@wits.com`（真的寄信再加 `MAIL_LOGIC_APP_URL`）。測試不得寄給其他人。
2. 啟動 server 和 frontend。
3. 對 agent 說「寄一封測試信給 <你的 email>」，在確認卡按「確認寄送」。
4. `logic_app` 模式到信箱確認有收到。

單元測試（不連 LLM／Logic App）：

```powershell
cd server
.\.venv\Scripts\python.exe -m pytest tests\domain\test_mail.py tests\test_mail_security.py -q
```

以上安全測試只使用 sender／網路 mock 與記憶體 graph，不連 LLM、不建立真排程、不寄真信。涵蓋預設模式偽造旗標仍須確認、測試模式自動／人工流程、錯誤環境設定、Edit／Cc／最終出口限制與日誌最小化；C# 測試另驗證只呼叫管理者設定的主機及傳遞當次開關。
