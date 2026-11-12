# USER 偏好

- 回覆語言：**繁體中文**
- commit／push：**預設**僅在使用者明確要求時執行；若**已確認的計畫**明文授權「每階段 commit+push」，依該計畫執行（仍勿改 git config／勿 force-push main）
- commit 訊息：conventional 前綴 + **繁中**說明（例：`feat(frontend): 模組化排程側欄`）
- 手眼：宣稱可對話／可 trace／可 UI 必須真跑；UI 必截圖並 Read 圖片；失敗如實寫原因
- 機密：只在本機 `.env`；永不寫進 md／規則／commit
- 偏好可運行的最小變更；避免為了「完整」堆空殼目錄；多階段計畫須模組化、過門後再下一階（`aipark-phase-delivery`）
- **文件分層**：技術／Agent 規範 → `.cursor/`；專案說明／營運 → `README`／`docs/`
- **程式註解**：繁中；**每個方法**必有註解；複雜方法內部加區段註解（見 `rules/aipark-docs-comments.mdc`）
- **待決分軌**：業務拍板 → `docs/flow-templates/OPEN-QUESTIONS.md`；本次 Agent／架構待決 → `.cursor/temp/open-decisions.md`
