# 寄信功能

讓 agent 幫使用者寄信。信件一定要使用者在畫面上確認後才會寄出，不會在使用者不知情時寄信。

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
- 排程新增「信件自動發送」開關，預設關閉（既有排程也關閉）。開啟並儲存即授權後續執行使用 `send_mail` 自動寄信；收件人仍由執行內容或查詢結果帶入，不新增固定信箱欄位。
- 關閉時，排程執行到 `send_mail` 會等待原對話的寄信確認卡。排程紀錄為 `WaitingForConfirmation`，可從側欄點排程名稱開啟原對話，確認或取消；不會誤記成已成功寄送。
- 自動授權僅在排程啟動時注入該次 run 的 configurable，不依賴 LLM 參數或 thread metadata。後續一般聊天仍須人工確認；修改開關對下一次排程執行生效，不會自動寄出既有待確認信件。
- 自動寄送仍檢查每封 To/Cc 的網域與合計 20 人限制。多人同封彼此看得到收件名單；個人薪資等不同內容須逐封呼叫，不能群寄。此開關不是完整的薪資人員權限驗證或批次寄送管理。
- 既有排程結果通知仍維持 Draft，只寫紀錄，沒有開啟實際寄送。

## 收件人規則

- 收件人至少 1 位。
- 收件人加副本最多 20 位。
- 每個地址都要是有效的 email，網域必須在 `MAIL_ALLOWED_DOMAINS` 清單內（不分大小寫）。
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
| `dry_run` | 測試模式，只寫在 log，沒有真的寄出 |
| `cancelled` | 使用者取消 |
| `rejected` | 收件人不符合規則 |
| `failed` | Logic App 回錯誤或連不上 |

## 設定

| 環境變數 | 說明 |
|---|---|
| `MAIL_BACKEND` | 空白＝不開寄信；`dry_run`＝只寫 log；`logic_app`＝真的寄出 |
| `MAIL_ALLOWED_DOMAINS` | 允許的收件網域，逗號隔開，例如 `wistron.com,wits.com` |
| `MAIL_LOGIC_APP_URL` | Logic App 的 HTTP 觸發網址（`logic_app` 必填） |

- 沒設定 `MAIL_BACKEND` 就不開寄信，其他功能不受影響。
- 有設定但缺少必填變數時，server 啟動就會報錯。
- `MAIL_LOGIC_APP_URL` 含簽章，等同密碼：本機只放 `server/.env`，部署放 Vault，不能進 Git。

## 程式位置

| 檔案 | 內容 |
|---|---|
| `server/flows/domain/mail.py` | 收件人整理與檢查（純規則） |
| `server/flows/tools/mail_senders.py` | 寄信方式：`dry_run`、`logic_app` |
| `server/flows/tools/mail.py` | `send_mail` 工具與確認流程 |
| `server/graph.py` | 把 `send_mail` 接進 agent，避免恢復確認時重複寄出 |

## 本機測試

1. `server/.env` 設定 `MAIL_BACKEND`、`MAIL_ALLOWED_DOMAINS`（真的寄信再加 `MAIL_LOGIC_APP_URL`）。
2. 啟動 server 和 frontend。
3. 對 agent 說「寄一封測試信給 <你的 email>」，在確認卡按「確認寄送」。
4. `logic_app` 模式到信箱確認有收到。

單元測試（不連 LLM／Logic App）：

```powershell
cd server
.\.venv\Scripts\python.exe -m pytest tests/domain/test_mail.py -q
```
