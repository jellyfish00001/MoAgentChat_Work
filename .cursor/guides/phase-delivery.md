# 多階段計畫交付（常駐）

規則來源：`rules/aipark-phase-delivery.mdc`（alwaysApply）。本檔是操作細節。

## 何時套用

使用者確認的多步驟計畫、明確「分階段／每階段 push／要截圖驗收」的任務。以後無需再強調。

## 過門模板（追加到 `temp/verify-log.md`）

```markdown
## Phase N — YYYY-MM-DD
### 實作範圍
- …
### 自動化／API 證據
- temp/ui-shots/…（json/txt）
### UI 截圖（Agent 已 Read）
- [ ] pN-….png — 觀察結論：…
### 美觀／品質否決
- （無／列出）
### Git
- commit: …
- push: …
### 結論
- PASS / FAIL
```

## 腳本

- Chat／排程 UI：可用 Playwright；重複流程放 `.cursor/scripts/local-dev/pw-*.mjs`。
- LangSmith Studio：既有 `start-playwright-langsmith.ps1`（profile 勿刪）。
- 排程 Api／Job 啟動腳本（實作後）：`scripts/local-dev/start-scheduler-api.ps1`、`start-scheduler-job.ps1`（見 local-dev README）。

## 最終總驗收

全部階段 push 後：功能清單勾選 + 截圖索引 + verify-log 結案段；缺一不宣稱計畫完成。
