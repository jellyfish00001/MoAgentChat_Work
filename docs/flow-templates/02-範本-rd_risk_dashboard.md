# 【範本／本機】Rework&Dismantle 風險看板（`rd_risk_dashboard`）

> 非正式環境紀錄。對應程式：`server/flows/graphs/rd_risk_dashboard/`；測試資料：`server/testdata/rd_risk/`。

| 項目 | 內容 |
|------|------|
| Graph ID | `rd_risk_dashboard` |
| 程式 | `server/flows/graphs/rd_risk_dashboard/` |

預覽：`Ctrl+Shift+V`。

## A. 目前可跑的 LangGraph（MVP）

```mermaid
flowchart LR
  S([開始]) --> L[load_data]
  L --> A[scan]
  A --> N[narrate]
  N --> P[persist]
  P --> E([結束])
  COOIS[(COOIS-Header)] -.-> L
  Mat[(工單物料領用)] -.-> L
  A -.-> Todo[其餘五類異常 TODO]
```

## B. 完整規格目標（六類異常 → 看板）

```mermaid
flowchart TD
  S([開始]) --> Load[載入四表]
  Load --> Cls[分類 Rework / Dismantle]
  Cls --> Eng[異常規則引擎]
  Eng --> R1[流程倒置]
  Eng --> R2[異常調帳]
  Eng --> R3[物料挪用]
  Eng --> R4[超期 KPI]
  Eng --> R5[拆解異常]
  Eng --> R6[其他具名]
  R1 --> KPI[彙總 KPI]
  R2 --> KPI
  R3 --> KPI
  R4 --> KPI
  R5 --> KPI
  R6 --> KPI
  KPI --> LLM[LLM 研判與行動清單]
  LLM --> Board[管理看板]
  Board --> EndNode([結束])
```
