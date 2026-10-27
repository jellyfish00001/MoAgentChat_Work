# 本機／pytest 測試資料

僅供本機開發與 `server/tests/domain` 使用。  
**進 git**，經 `server/.dockerignore` **不進正式 Docker image**。

正式環境請用 env 覆寫資料目錄（見 `server/.env.example`）。

## 契約檔（Source Prompt 有要求／執行會讀）

| 目錄 | Graph ID | 檔案 |
|------|----------|------|
| `rework_mo/` | `rework_mo_detective` | `QV_Report-Material.xlsx`, `Bom List.xlsx`, `工单物料领用.xlsx`, `物料名称.xlsx`, `维修261Bom List.xlsx` |
| `rd_risk/` | `rd_risk_dashboard` | `COOIS-Header.xlsx`, `工单物料领用.xlsx`, `Bom List.xlsx`, `ZPP329-Missrate設定.csv` |
| `qv_dms/` | `qv_dms_pipeline` | `Cover.xlsx`, `生產工單.xlsx`, `會計調整.xlsx`, `65011201.xlsx`, `庫存調整單.xlsx`, `材料分析-previous.xlsx`；（當期 `材料分析.xlsx` 原始包常缺，見 OPEN-QUESTIONS QV-02） |

## 參考檔（Prompt 未點名；已放入待確認用途）

見 [docs/flow-templates/OPEN-QUESTIONS.md](../../docs/flow-templates/OPEN-QUESTIONS.md) **REF-01**。

| 目錄 | 檔案 | 說明 |
|------|------|------|
| `rd_risk/` | `demo.html`, `Dismantle.docx` | 看板樣式／拆解說明參考；程式尚未讀 |
| `qv_dms/` | `原因分类demo.xlsx`, `QV DMS-WCD.xlsb` | 可能含未寫進 Prompt 的分類或樣張；程式尚未讀 |

路徑覆寫：`FLOWS_TESTDATA_ROOT`、`REWORK_MO_DATA`／`RD_RISK_DATA`／`QV_DMS_DATA`。
