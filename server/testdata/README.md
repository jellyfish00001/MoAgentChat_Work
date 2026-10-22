# 本機／pytest 測試資料

僅供本機開發與 `server/tests/domain` 使用。  
**進 git**，經 `server/.dockerignore` **不進正式 Docker image**。

正式環境請用 env 覆寫資料目錄（見 `server/.env.example`）。

| 目錄 | 對應 Graph ID | 契約檔 |
|------|---------------|--------|
| `rework_mo/` | `rework_mo_detective` | `QV_Report-Material.xlsx`, `Bom List.xlsx`, `工单物料领用.xlsx` |
| `rd_risk/` | `rd_risk_dashboard` | `COOIS-Header.xlsx`, `工单物料领用.xlsx` |
| `qv_dms/` | `qv_dms_pipeline` | Cover／生產工單／會計調整／65011201／庫存調整單／材料分析-previous |

路徑覆寫：

- `FLOWS_TESTDATA_ROOT`（根目錄）
- `REWORK_MO_DATA` / `RD_RISK_DATA` / `QV_DMS_DATA`（各流程目錄）
