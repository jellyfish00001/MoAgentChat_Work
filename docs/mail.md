# 寄信功能

讓 agent 幫使用者寄信。信件一定要使用者在畫面上確認後才會寄出，不會在使用者不知情時寄信。

## 寄信流程

```text
使用者提出寄信需求
  → LLM 整理收件人、副本、主旨、內文，呼叫 send_mail
  → 檢查收件人
  → 畫面出現確認卡，等使用者 Approve／Edit／Reject
  → 再檢查一次收件人（使用者可能在確認卡改過）
  → 送到 Logic App 寄出
  → 回報結果
```

- **Approve**：照原內容寄出。
- **Edit**：可修改收件人、副本、主旨、內文後寄出。
- **Reject**：取消，不寄信。

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
3. 對 agent 說「寄一封測試信給 <你的 email>」，在確認卡按 Approve。
4. `logic_app` 模式到信箱確認有收到。

單元測試（不連 LLM／Logic App）：

```powershell
cd server
.\.venv\Scripts\python.exe -m pytest tests/domain/test_mail.py -q
```
