# `.cursor/scripts/checks` — 規範機器閘道

權威＝腳本 exit code。Rule／MAP 只指標，不重複長描述。

| 腳本 | 判定 |
|------|------|
| `check-langgraph-keys.ps1` | `server/langgraph.json` 與 `langgraph.dev.json` 的 `graphs` 鍵集合相等 |
| `check-cursor-path-words.ps1` | 規範正文禁止裸寫 `temp/verify-log` 等（須 `.cursor/temp/…`） |
| `check-rule-links.ps1` | MAP／AGENTS／rules／guides 相對 Markdown 連結可解析 |
| `check-no-ai-prepare-stale.ps1` | 禁止未標「源自／歷史／lineage」的 `ai_prepare/.cursor` 現行路徑 |

```powershell
pwsh -NoProfile -File .cursor/scripts/checks/run-all.ps1
```

**腳本通過 ≠ 多階段 PASS**（手眼／UI Read／假完成仍為判斷型門檻）。
