# 客戶 Prompt 待決問題

實作三流程對齊時，遇到原文模糊／矛盾／與可觀測 Graph 衝突處記於此。  
欄位：ID／流程／前因／後果／來源／建議作法／狀態。

狀態：`open` 待回覆｜`answered` 已決策｜`optimized` 已依冗餘優化（無需客戶回覆）。

**給用戶填回覆（僅 open 題，純文字可貼 Jira）：** [OPEN-QUESTIONS-請回覆.txt](OPEN-QUESTIONS-請回覆.txt)

**如何對回客戶原文**：每題「來源」含（1）範本檔錨點＝客戶 README **原樣附錄**（`## Source Prompt（客戶原文）` 區塊）；（2）**可 Ctrl+F 的原文摘錄**。在對應 `01`／`02`／`03` 範本下半部搜尋摘錄關鍵字即可定位客戶原本在說什麼。產品決策（非客戶句）會另外標明。

---

## RM-01 情形二「替代關係」判定

| 欄位 | 內容 |
|------|------|
| 流程 | `rework_mo_detective` |
| 前因 | 客戶要把「A 料重工成 B 料」標成情形二，條件寫「261 與 101 **料號不同且屬替代關係**」。我們能判斷「不同料號＋只有 261/101」，但 Prompt **沒說**替代要用 Bom List 的 Alt Item、物料名称，還是另給對照表——所以「替代」目前無法驗證。 |
| 後果 | 繼續用暫行規則：凡異料就當情形二 → 可能把無關兩料誤當替代、Reason／報告寫錯；若改太嚴（一定要 Alt）→ 真實替代案可能掉進情形三，六大檢查負擔變重。 |
| 來源 | [01-範本](01-範本-rework_mo_detective.md) → Source Prompt → `#### 🔍【情形二：A 料 Rework 成 B 料】` → **准入条件** 第 2 條（約 L223–227）。 |
| 原文摘錄 | `2. 261 发料物料（A料）与 101 入库物料（B料）**编码不同**（且属于替代关系）。` |
| 建議作法 | **A（推薦暫行）**：僅 261/101 各一主料且料號不同＋僅有 261+101 → 判情形二，notes 標「替代關係未驗證」。**B**：用表 B 同 Item／Alt Priority 驗證。**C**：等客戶給替代對照表。 |
| 狀態 | open（實作採 A） |

---

## RM-02 情形三條號跳號（1 後接 3）

| 欄位 | 內容 |
|------|------|
| 流程 | `rework_mo_detective` |
| 前因 | 情形三「定義確定」原文只列 **1. A Rework B**，下一段直接 **3. A Rework A**，中間沒有「2.」——像貼文時漏了一條（例如半品／多階定義），不是單純排版空行。 |
| 後果 | 我們只實作現有兩條；若客戶心裡其實有第 2 種定義，那些工單會被現有規則誤分到 1 或 3，Reason 與報告模板都會偏。 |
| 來源 | [01-範本](01-範本-rework_mo_detective.md) → Source Prompt → `#### 🔍【情形三：成半品 & 机台维修 MO】` → **定义确定**（約 L237–247）。搜尋：`定义确定` 或 `A Rework B`。 |
| 原文摘錄 | `* **定义确定**：` → 先 `1.在同一张工单内…判定为「A Rework B」`（三條 ✅），接著直接 `3.在同一张工单内…判定为「A Rework A」`（無「2.」）。 |
| 建議作法 | **推薦**：實作僅依現有 1／3 兩條；問題檔保留等客戶補 2。 |
| 狀態 | open |

---

## RM-03 大發料 Missrate：\*A=0 與 ZPP329 是否共用

| 欄位 | 內容 |
|------|------|
| 流程 | rework + rd_risk |
| 前因 | **同一類大發料庫位（\*A/\*B）**，兩份客戶 Prompt 說法不同：rework 寫 \*A 的 Missrate **固定當 0**；rd_risk 寫必須先查 **ZPP329**，沒資料時**不准假設 0%**。兩套若各做各的，同料同工單結論會打架。 |
| 後果 | 會計／內控對同一筆「超發」可能一個流程說 OK、另一個說異常調帳；對帳與看板數字無法互相比對。 |
| 來源（rework） | [01-範本](01-範本-rework_mo_detective.md) → Source Prompt → 六大检查 **3. 大发料 Missrate**（約 L282–284）＋輸出模板【3】備註（約 L413–414）。搜尋：`库位为*A的Missrate为0` 或 `Missrate 固定按 0`。 |
| 原文摘錄（rework） | `（库位为*A的Missrate为0，最大发料量=标准用量+标准用量*Missrate）`；備註：`Storage Location 以 *A 结尾的大发料：Missrate 固定按 0 判断` |
| 來源（rd_risk） | [02-範本](02-範本-rd_risk_dashboard.md) → Source Prompt → `2.异常调账` → **【注意事項】Miss Rate 處理順序**（約 L169–172）。搜尋：`不得自行假設為 0%`。 |
| 原文摘錄（rd_risk） | `1).優先使用「ZPP329-Missrate 設定」表中該料號的實際 Miss Rate`／`2).若無資料 → 標記為「⚠️ 缺少 Miss Rate，無法完整判斷」`／`3).不得自行假設為 0%，除非輸入資料明確指定` |
| 建議作法 | **推薦**：rework 情形三大發料：\*A 用 0；\*B 若有 ZPP329 用表，無則 notes「缺 Missrate」不判超標金額。rd_risk 嚴格跟 ZPP329 規則。 |
| 狀態 | open（實作採推薦） |

---

## RM-04 Reason 是否允許 LLM 覆寫

| 欄位 | 內容 |
|------|------|
| 流程 | `rework_mo_detective` |
| 前因 | 客戶目標是把固定字串（如 `05.Rework MO-时间差`）寫回 QV 的 Reason 欄；產品化又決定「規則用程式、LLM 只寫人話」。若仍讓 LLM 改 Reason，等於兩套真相。 |
| 後果 | Reason 與 RPA／Cover／匯總報表對不起來；同一工單每次跑 LLM 可能換字，無法回歸測試。 |
| 來源（客戶） | [01-範本](01-範本-rework_mo_detective.md) → Source Prompt → `# 目标`（約 L116–117）。搜尋：`自动更新目标表`。 |
| 原文摘錄 | `…自动更新目标表 QV_Report-material.xlsx 中的 Reason 栏位…`；後續多處指定固定字串如 `05.Rework MO-时间差`／`未跨月，待确认`（情形一／二「判定与 Reason 标记」）。 |
| 來源（產品） | 非客戶句：domain＝規則寫死 Reason；LLM 只 narrate（見範本上半／domain-vs-llm）。 |
| 建議作法 | **已定**：程式寫死 Reason；LLM 只產出 narrative／improvement，**禁止**改 reason 碼。 |
| 狀態 | answered |

---

## RD-01 「其他異常」如何自動命名

| 欄位 | 內容 |
|------|------|
| 流程 | `rd_risk_dashboard` |
| 前因 | 六類異常的第 6 類要求：**禁止**畫面上寫「其他異常」，要自動取具體名（如「XX 異常」），但 Prompt／demo.html **都沒給**命名規則或關鍵字表——只有「不要叫其他」的禁令。 |
| 後果 | 無法穩定產出第六類 KPI／明細；若 AI 亂取名，同現象每次名稱不同，看板無法彙總。 |
| 來源 | [02-範本](02-範本-rd_risk_dashboard.md) → Source Prompt → Knowledge／異常定義 **`6.其他異常`**（約 L216–217）。搜尋：`不得直接顯示「其他異常」`。 |
| 原文摘錄 | `【定義】：除以上五種異常外的情況，自動歸納為具體異常類型（如「XX 異常」），不得直接顯示「其他異常」。` |
| 建議作法 | **推薦暫行**：第六類先空清單；若偵測到無法歸類列，標記 `待命名異常` 並進 OPEN 等規則。不發明業務名。 |
| 狀態 | open（實作採推薦） |

---

## RD-02 主料語意相似度門檻

| 欄位 | 內容 |
|------|------|
| 流程 | `rd_risk_dashboard` |
| 前因 | 「物料挪用」要先排除**主料**（261 領入與 101 入庫在描述上像同一產品），剩下不在 BOM 的才算挪用。Prompt 只列「產品系列／機種／功能」等質性條件，**沒有**分數或字串重疊門檻。 |
| 後果 | 門檻太鬆 → 真挪用被當主料漏抓；太嚴 → 正常主料被算進挪用金額，KPI 與行動清單會嚇到主管。 |
| 來源 | [02-範本](02-範本-rd_risk_dashboard.md) → Source Prompt → `3.物料挪用` → **工單主料説明／主料辨識**（約 L174–189）。搜尋：`主料辨識將增加以下條件`。 |
| 原文摘錄 | `1. 261 領入料與 101 入庫料的 Material Description 共享關鍵產品／功能特徵，例如：產品系列；機種／平台名稱；…`／`2. 即使料號前綴不同，只要功能與產品特徵相同或高度相似，仍判定為領入主料`／`4.工單物料明細，只存在1個261，1個101，那這兩筆都是主料號` |
| 建議作法 | **A（推薦暫行）**：規則優先——單筆 261+單筆 101 全當主料；料號＝BOM Header 排除；描述用 token 重疊≥2 或相同前綴 3+ 字元當主料。語意 LLM **後期**再加。 |
| 狀態 | open（實作採 A） |

---

## RD-03 System Status／未結案欄位是否在樣本

| 欄位 | 內容 |
|------|------|
| 流程 | `rd_risk_dashboard` |
| 前因 | 超期 KPI 要依狀態拆成「已結案但超期／尚未結案且超期／未達期限」；當初不確定示範用的 COOIS 有沒有 `System Status` 欄。 |
| 後果 | 沒欄就只能用 Close date 空白近似，和客戶報表口徑可能差一截。 |
| 來源（客戶） | [02-範本](02-範本-rd_risk_dashboard.md) → Source Prompt → `4.超期KPI Days` → **【注意事項】** 第 4 點（約 L200–204）。搜尋：`依 System Status 區分`。 |
| 原文摘錄 | `4).報告中需依 System Status 區分：已結案但超期\尚未結案且超期\尚未達 KPI 期限` |
| 來源（樣本） | `server/testdata/rd_risk/` → `COOIS-Header.xlsx` 欄位核對（非 Prompt 句）。 |
| 建議作法 | 載入時探測欄位；有則用，無則用 Close date 是否空白近似，notes 標「System Status 缺失」。 |
| 狀態 | answered（樣本已證實） |
| 參考檔結論 | `COOIS-Header.xlsx` **已有** `System Status`（例：`CLSD CNF DLV…`）。實作應優先讀此欄；僅當欄缺失才退回 Close date。 |

---

## QV-01 Reason↔Cover 語義匹配規則表

| 欄位 | 內容 |
|------|------|
| 流程 | `qv_dms_pipeline` |
| 前因 | Cover 回填要把材料分析 Pivot 的 Reason **對到** Cover 的 Reason Code 再寫 PCL500；Prompt 寫「語義匹配」，卻幾乎沒附對照表（只有幾條繁中替換）。後來發現 `原因分类demo`／WCD 其實就是那 12 類標準名。 |
| 後果 | 沒對照時：金額寫錯行、或 Pivot 總額對不上 Cover 驗證失敗一直重跑；有 12 類清單後主路徑可做，但若還有「別名→標準名」表未給，少數 Reason 仍會進 `unmatched`。 |
| 來源（客戶） | [03-範本](03-範本-qv_dms_pipeline.md) → Source Prompt → `# 分析步驟` → **一、1、「材料分析.xlsx」** 之 **2)**（約 L176）。搜尋：`一一语义匹配`。 |
| 原文摘錄 | `2).根据[Pivot.xlsx ]中的[Reason]列与[Cover.xls]中的[Reason Code]列进行一一语义匹配，匹配成功则将[Pivot.xlsx ]中[QV in Material(LC)]列金额写入对应行的D列单元格（列名为"PCL500"）` |
| 來源（參考檔） | `server/testdata/qv_dms/原因分类demo.xlsx`、`QV DMS-WCD.xlsb`（見 REF-01）。 |
| 建議作法 | **推薦（已被參考檔強化）**：以 `原因分类demo.xlsx`／WCD Cover 的 **12 類原因分类** 為 Cover 前段對照標準；Pivot Reason 經 Prompt 替換／去編號後與「原因分类」**字串相等**（可加 NFKC）匹配寫入 PCL500。匹配不到列入 `unmatched_reasons`。 |
| 狀態 | answered（參考檔可解主路徑；仍請確認是否還有「語義別名」表） |
| 參考檔結論 | `原因分类demo` 的 12 類與現行 `Cover.xlsx` 前 12 列 Reason Code **完全一致**。 |

---

## QV-02 缺當期材料分析.xlsx 時是否硬停

| 欄位 | 內容 |
|------|------|
| 流程 | `qv_dms_pipeline` |
| 前因 | 步驟 1.1（Pivot→PCL500）一定要**當期** `材料分析.xlsx`；客戶示範包／testdata 常常只有 `材料分析-previous.xlsx`。WCD.xlsb 裡雖有材料分析 sheet，但不是獨立 xlsx 契約檔。 |
| 後果 | 整條 pipeline 硬停 → 报工／會計也測不到；只跳過 1.1 → Cover 前段 PCL500 空著，但後面步驟與產出仍可驗證。 |
| 來源（客戶） | [03-範本](03-範本-qv_dms_pipeline.md) → Source Prompt → 開頭「我会提供 6 个文件」＋步驟 **一、1、「材料分析.xlsx」整理与回填**（約 L146–162）。搜尋：`材料分析.xlsx` 與 `我会提供 6 个文件`。 |
| 原文摘錄 | `-我会提供 6 个文件：生產工單.xlsx、材料分析.xlsx、…及 Cover.xlsx。`；步驟標題：`1、「材料分析.xlsx」整理与回填`（把當期材料分析當必備輸入）。 |
| 來源（產品／testdata） | 本機常缺當期檔 → 暫行「1.1 硬停該步、其餘可跑」（非客戶句）。 |
| 建議作法 | **已定暫行**：一.1 硬停該步（messages 標明），一.2～一.5 仍可跑；總驗證標「材料分析未回填」。 |
| 狀態 | answered |

---

## QV-03 Email／Teams 是否實發

| 欄位 | 內容 |
|------|------|
| 流程 | `qv_dms_pipeline` |
| 前因 | Prompt 步驟要求跑完 Cover 後發 Email／Teams；本機開發與 CI **不該**真的打到公司信箱／頻道。 |
| 後果 | 若實發：測試一次就打擾真實收件者；若不做任何產物：又像漏了「通知」步驟。折衷是只產草稿檔證明節點有跑。 |
| 來源 | [03-範本](03-範本-qv_dms_pipeline.md) → Source Prompt → **`7、寄送邮件与teams通知`**（約 L243–246）。搜尋：`寄送邮件与teams通知`。 |
| 原文摘錄 | `将填充完成的[cover.xlsx]表发送Email给D23040558@wistron.com，并且发送 Microsoft Teams 通知给D23040558@wistron.com`；`邮件主旨为「QV DMS分析表-YYYYMM」…` |
| 建議作法 | **已定**：只寫 `outputs/` 草稿 txt／markdown，不呼叫 SMTP／Teams API。 |
| 狀態 | answered |

---

## REF-01 Prompt 未提及檔——預期用途？（已做內容交叉檢驗）

| 欄位 | 內容 |
|------|------|
| 流程 | 跨流程（尤其 `qv_dms`、`rd_risk`） |
| 前因 | 客戶 Agent 包的 `ref data` 除了 Prompt 列的輸入表，還塞了未點名的 demo／樣張／說明（原因分类、WCD.xlsb、Dismantle.docx、demo.html）。這些常是「沒寫進 Prompt 的答案」；先前怕誤當契約輸入曾沒放進 repo，現已放入 testdata 但程式多半還沒讀。 |
| 後果 | 不採用 → Cover 匹配、拆解 Key Parts、看板版型容易偏離客戶示範；亂採用 → 可能把 30MB 樣張當線上唯一輸入、或把說明文件當資料表。需要你確認每檔是執行／golden／純人工。 |
| 來源 | **非單一 Prompt 句**——客戶原始包裡有、但 Source Prompt **未點名**的檔；現存於 `server/testdata/`（2026-10-27 開啟檢查）。對照：各流程 Prompt「输入／数据来源」只列契約表，未列下表四檔。 |
| 建議作法 | 預設採下表「建議」欄（B／C）；若不同意請改標。 |
| 狀態 | open（等你確認建議標註；內容面已可驅動實作） |

### REF 交叉檢驗 → 能回答哪些 OPEN 問題？

| 參考檔 | 內容摘要 | 對 OPEN 問題 | 建議標註 |
|--------|----------|--------------|----------|
| `原因分类demo.xlsx`（sheet `DMS分析`） | 12 列：`Bom change`…`报工差异`（與 Cover 前 12 個 Reason Code **同名**） | **可解 QV-01 主路徑**：不是模糊「語義」，而是**固定原因分类清單** | **B** 執行時可當對照表／或直接信 Cover 前 12 列 |
| `QV DMS-WCD.xlsb` | 完整樣張：Cover／DMS分析／**材料分析**／生產工單／會計調整／庫存／MOH／65011201；Cover 含序號 1–13（含「未分析」）與中英 Reason | **補強 QV-01**（樣張列名）；**補強 QV-02**：內含當期風格 `材料分析` sheet，可匯出成缺的 `材料分析.xlsx` 做測試 | **C** golden＋可抽 sheet 補 testdata；不必當線上唯一輸入 |
| `Dismantle.docx` | 有頭 ZMPD／無頭 ZMPE；FA Key Parts＝MB,LCD,KB,SSD,BTY,電源,攝像頭…；PCBA＝CPU,SSD(on_board),DIMM,VGA,顯存…；應拆未拆檢查說明 | **補強拆解異常規則**（非 RD-01 命名）；不解答主料語意門檻 RD-02 | **B** 寫進 domain 拆解規則知識 |
| `demo.html` | 完整深色看板：6 KPI、研判、圖表、行動表、分頁明細；含「倒置未發現／挪用範例」等文案與 Miss Rate 口徑註腳 | **視覺／結構 golden**（OPT-01 模板應對齊此檔）；**不**給「其他異常」自動命名演算法 → RD-01 仍 open | **C**（或 B＝CSS／區塊結構必須對齊） |

### 仍無法由參考檔回答者

| ID | 原因 |
|----|------|
| RM-01／02／03 | 未點名檔皆非 rework 規則補充 |
| RD-01 | demo 只有已命名範例，無「如何發明 XX 異常」規則 |
| RD-02 | 無相似度門檻或描述對照表 |
| QV-03 | 與通知通道無關 |

### REF-01 請確認（可只回「同意建議」）

| 檔案 | 建議 | 請確認／修改 |
|------|------|----------------|
| `原因分类demo.xlsx` | **B** | |
| `QV DMS-WCD.xlsb` | **C**（並可匯出 `材料分析`→testdata） | |
| `Dismantle.docx` | **B** | |
| `demo.html` | **C**（版型對齊） | |

（rework 五表皆已在 Prompt／testdata 且有讀取。）

---

## OPT-01 客戶冗餘已優化（無需回覆）

| ID | 說明 |
|----|------|
| OPT-01 | rd_risk／qv「只輸出 HTML、不要過程」→ 改為可觀測節點 + 模板 HTML（產品化決策）。 |
| OPT-02 | qv Cover 儀表板重複貼兩次的 Python → 單一 `render_html` 產生器。 |
| OPT-03 | rework 活潑語氣 → 僅 `narrate`；規則節點用中性摘要。 |
| 狀態 | optimized |
