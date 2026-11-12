# PENDING：複製為 `rules/aipark-phase-delivery.mdc`（需 Agent mode）

Frontmatter:

```yaml
---
description: Multi-phase delivery gates — test, screenshot Read, git per phase; no fake-done
alwaysApply: true
---
```

正文與計畫「執行憲法」+「phase-delivery」一致，重點：

1. 一階段做完才算完；未過門不進下一階  
2. 計畫授權時每階段 commit+push  
3. UI 截圖必須 Read 圖片驗收  
4. 禁止假完成、禁止重複管線／巨石檔  
5. temp 保留 verify-log、ui-shots、pw-langsmith-profile  
6. 全部階段後總驗收  

（實作時把完整正文寫入 `.mdc`，本檔可刪或留作來源。）

同樣待寫：擴充 `rules/aipark-hands-eyes.mdc` 加入 UI 截圖 + Read 條。
