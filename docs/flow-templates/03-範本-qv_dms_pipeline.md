# 【範本／本機】QV DMS 整理及分析（`qv_dms_pipeline`）

> 非正式環境紀錄。對應程式：`server/flows/graphs/qv_dms_pipeline/`；測試資料：`server/testdata/qv_dms/`。

| 項目 | 內容 |
|------|------|
| Graph ID | `qv_dms_pipeline` |
| 程式 | `server/flows/graphs/qv_dms_pipeline/` |

預覽：`Ctrl+Shift+V`。

## A. 目前可跑的 LangGraph（MVP）

```mermaid
flowchart LR
  S([開始]) --> I[inventory]
  I --> P[plan]
  P --> N[narrate]
  N --> W[persist]
  W --> E([結束])
  Files[(Cover / 工單 / 會計…)] -.-> I
  Missing[缺當期材料分析?] -.-> I
```

## B. 完整規格：Cover 回填 → 分析 → 交付

```mermaid
flowchart TD
  S([開始]) --> C0[最新 Cover.xlsx]
  C0 --> C1[材料分析 Pivot → PCL500]
  C1 --> C2[生產工單报工差异]
  C2 --> C3[會計調整關鍵字]
  C3 --> C4[65011201 Reserve]
  C4 --> C5[庫存調整 Reason]
  C5 --> Fmt[格式 + Email / Teams]
  Fmt --> Viz[樞紐儀表板]
  Viz --> Cur[當期 Material Analysis]
  Cur --> Prev[上期分析]
  Prev --> Cmp[兩期對比]
  Cmp --> Out[簡報與交互頁]
  Out --> EndNode([結束])
```
