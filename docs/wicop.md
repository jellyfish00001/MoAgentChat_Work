# WiCOP 申請紀錄 — Armstrong K8s Namespace

> 申請日期：2026/10/14（New Account Combo）
> 申請狀態：[WiCOP Apply Status](https://wicop.wistron.com/wicop/applicationForms/applyStatus)　｜　教學：[Cloud Guide Book 1.1 Setting-up-accounts](https://cloud-guidebook.wistron.com/developer/01_Kickoff-a-project/1.1_Setting-up-accounts/)
> 回到 [README](../README.md)

> [!TIP]
> 如果要**重填**，以下就是第一次送出的完整內容，可以照著填，再依「待確認事項」調整。

## 摘要

| 項目 | 值 |
|---|---|
| **ApplyNo** | **20261014C0005** |
| 目前關卡 | COG PIC Audit（2026/10/14） |
| Purpose | for finance ai agent |
| IBU | `ARMWHQFinAgentP`（Service Name：`ARMWHQFinAgent`） |
| IBG | `MLL000` |
| Project | `FinAgent` |
| **Namespace** | **`finagent`** |
| Cluster | `whq-arm-prd-01`（PRD） |
| EA ID | PBI for Finance / 455 |

命名規則：`[Provider][Site][Alias][ENV]`，Armstrong 的代碼是 `ARM`，ENV 用一個字母（P），所以 PRD 的 IBU 就是 `ARM` + `WHQ` + `FinAgent` + `P`。

---

## 1. IBU（Infra Billing Unit）

申請一個新的 IBU。

| 欄位 | 值 |
|---|---|
| Service Provider | K8S |
| Application Name（EA ID） | PBI for Finance / 455 / CHINGYI CHUEH |
| Service（System）Alias Name | FinAgent |
| Cloud Type | Regional Cloud-Armstrong |
| Cloud Site | WHQ |
| User ITSM workgroup for Financial | `CCOE-ARMWHQFinAgent` |

### 環境

| 環境 | Cloud Cluster ID | IBU | 2026 Budget（TWD） |
|---|---|---|---|
| DEV | — | — | — |
| QAS | — | — | — |
| PRD | `whq-arm-prd-01` | `ARMWHQFinAgentP` | 0 |

### Owner 與計費

| 欄位 | 值 |
|---|---|
| Owner（PMCS PAJ Review1） | JAY YU |
| PAJ Owner（PMCS PAJ Review2） | CHINGYI CHUEH |
| Cost Center | MLLF00 |
| Project Code | — |
| Charge Model | PAJ Owner with Cost Center（BG） |
| Charge Type | By Percentage：CHINGYI CHUEH／MLLF00 100% |
| Forward Monthly Billing to PAJ Owner | NO |

## 2. IBG（Infra Billing Group）

| 欄位 | 值 |
|---|---|
| IBG／Division Name | MLL000 |
| Owner（部門主管） | ALLEN HSIEH |
| PAJ Owner | CHINGYI CHUEH |
| Cost Center | MLLF00 |

## 3. Project

| 欄位 | 值 |
|---|---|
| Project Name | FinAgent |
| Namespace | `finagent` |
| PO／Tech Leader | JAY YU |
| AI-related（需要 GPU／CPU 資源） | No（LLM 走 Columbus，不在 namespace 內跑模型） |

### Resource Quota

| 環境 | Cluster | CPU（Core） | Memory（GB） | Storage |
|---|---|---|---|---|
| PRD | `whq-arm-prd-01` | 1 | 1 | N/A／0 GB |

## 4. Team

成員都是 CHINGYI CHUEH（Manager）、JAY YU、KEN JK YANG 三人。

| Team | 名稱 | 用途 |
|---|---|---|
| GitLab Team（Developers） | `GITLAB-FINAGENT` | GitLab 開發者權限 |
| PRD Change Approvers | `CCOE-FINAGENT` | PRD 變更核准 |
| Code Owners | `CODE-FINAGENT` | Code owner |
| JSM Team | `OPS-FINAGENT` | 維運（啟用 JSM 個人授權會計費） |

---

## 待確認事項

> [!WARNING]
> 以下是送出前（或核准後要追蹤）建議確認的地方：

1. ~~只申請了 PRD~~ → 後來加開 QAS，目前是 PRD＋QAS；DEV 之後有需要再補申請。
2. **Resource Quota 偏小**：1 core／1 GB 要跑 LangGraph Agent Server、Redis，之後還有前端，記憶體很可能不夠。建議至少 **2 core／4 GB** 起跳。
3. **Storage 是 0**：Redis 如果要開 persistence，需要 PVC。PostgreSQL 走 WCP，不佔這裡的空間。
4. **Project Code 和 Cost Center 跟 ASP 不一致**：ASP 填的是 `IB202512.506`／`ML0000`，WiCOP 這邊是空白／`MLLF00`。確認是否需要一致。
5. **Budget 0、Major User Location 空白**：確認這兩欄是不是必填。
6. 核准後記得拿 **Onboarding Pack**（[查看方式](https://cloud-guidebook.wistron.com/developer/11_FAQ/WiCOP%20related/#3-how-to-check-the-onboarding-pack-of-your-project)）。
