# 【範本／本機】Rework MO 小偵探（`rework_mo_detective`）

> 非正式環境紀錄。對應程式：`server/flows/graphs/rework_mo_detective/`；測試資料：`server/testdata/rework_mo/`。

| 項目 | 內容 |
|------|------|
| Graph ID | `rework_mo_detective` |
| 程式 | `server/flows/graphs/rework_mo_detective/` |

預覽：`Ctrl+Shift+V`（建議 `Markdown Preview Mermaid Support`）。

## A. 目前可跑的 LangGraph

```mermaid
flowchart LR
  S([開始]) --> N1[list_orders]
  N1 --> N2[analyze]
  N2 --> N3[narrate]
  N3 --> N4[persist]
  N4 --> E([結束])
  Excel[(QV / BOM / 領退料)] -.-> N1
  LLM[(Azure APIM)] -.-> N3
  N4 -.-> Out[(outputs JSON)]
```

## B. 單張工單分析邏輯

```mermaid
flowchart TD
  A([取一張 Order]) --> B[讀 QV 明細與領退料]
  B --> C{物料數 / 531?}
  C -->|單料| C1[情形一 A→A]
  C -->|雙料| C2[情形二 替代料]
  C -->|多料或 531| C3[情形三 骨架]
  C1 --> D[跨月 / BOM 檢查]
  C2 --> D
  C3 --> D
  D --> E[suggested_reason 草稿]
  E --> F[LLM 潤飾 Reason]
  F --> G([寫回結果])
```
