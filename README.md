# AI_Prepare — 財務 AI Agent 導入準備

「財務 agent 家園」從資源申請到 CI/CD 上線的規劃與進度。

最後更新：2026/10/19

參考資料：《權限申請與 Helm 部屬流程（手把手教學）》2026/09/08、《Release Management SOP 2024》、[tech_study.md](docs/tech_study.md)（Multi-Repo vs Monorepo）、[gitlab_flow.md](docs/gitlab_flow.md)（分支與部署）、[wicop.md](docs/wicop.md)（WiCOP 申請紀錄）、[Columbus 3.3.0 技術資源申請_API](https://wistron.sharepoint.com/sites/PoweredbyColumbus/SitePages/3.3.0_%E6%8A%80%E8%A1%93%E8%B3%87%E6%BA%90%E7%94%B3%E8%AB%8B_API.aspx)、[API COE 簡報](https://wistron.sharepoint.com/:p:/t/WistronAPIProject-APICOE/IQDsiVXKAeGoQYaiEa-GLBIHAcITwWVIjq2xxrNSctxgJsw?e=qEkWjV)

## 結論

- **進度**：ASP 專案、AAD App Registration、AIF-GitLab group 已建立；WiCOP 已送出（Namespace `finagent`）；Columbus 模型 token 已核准、DSP 申請中；LangSmith 沿用現有資源。
- **程式碼**：放在 `aif-gitlab.wistron.com/ai-platform/projects/finaiagent/finagent/`，source code 和 helm 分兩個 repo。
- **上線流程**：GitLab CI（測試、掃描、build image）→ 更新 Helm Repo → Argo CD 部署到 Armstrong。只有 QAS、PRD 兩個環境。
- **架構**：後端是 LangGraph Agent Server（PostgreSQL＋Redis），部署在 Armstrong。前端是 Agent Chat UI，見[第 5 節](#5-前端agent-chat-ui)。
- **下一步**：申請 PostgreSQL、建 `finagent` subgroup 並 fork 範本；Namespace 下來後申請 Helm Repo 串接和 SRE 申請單。

> [!IMPORTANT]
> LangSmith／LangGraph Studio 是 RD 看 trace、debug 用的後台，**不能給財務同仁使用**。使用者用的前端要另外開發。

![整體架構](docs/architecture.svg)

## 1. 專案基本資訊

GitLab group、LangSmith、Helm repo 等資源都掛在 [ASP（AI Service Portal）](https://asportal.wistron.com/project-management/project-list/project-detail?ucId=274&pjGroup=175)的專案／用例底下，**名稱必須一致**。

| 項目 | 欄位 | 值 |
|---|---|---|
| ASP 專案 | 專案名稱／資源群 | [財務agent家園](https://asportal.wistron.com/project-management/project-list/project-detail?ucId=274&pjGroup=175)／`finaiagent` |
| ASP 用例 | 用例名稱／資源名稱 | FIN-AI-AGENT／`finagent` |
| | Owner | CHINGYI CHUEH |
| | Project Code／Charge Dept | IB202512.506（IT-IT-BI Operation Sustain Support, 2026 TSS）／ML0000 |
| WiCOP | Namespace／IBU | `finagent`／`ARMWHQFinAgentP`（[申請紀錄](docs/wicop.md)） |
| AAD | App Registration | [`FIN_AI_Agent`](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/5d17156a-8009-416c-9219-f932d7c982ab/isMSAApp~/false)（App ID `5d17156a-8009-416c-9219-f932d7c982ab`） |
| APM | 應用程式 | [Finance Management Report](https://apm.wistron.com/main/ApplicationDetail?type=view&id=7&name=Finance%20Management%20Report) |
| Harbor | Image 專案 | [`k8sprdwhqfin-ai-agent`](https://harbor.wistron.com/harbor/projects/456/repositories)（例：[`fin_ai_agent/hello-server-qas`](https://harbor.wistron.com/harbor/projects/456/repositories/fin_ai_agent%2Fhello-server-qas/artifacts-tab)） |
| 使用者入口 | 財務入口網站 | [fin.wistron.com](https://fin.wistron.com/#/login)，之後放「AI 家園」連結 |

ASP 和 APIM 不同：ASP 管專案和資源；APIM（Azure API Management）是 Luna／LLM 的 API 閘道，對應 `.env` 的 `OCP_APIM_SUBSCRIPTION_KEY`。

## 2. GitLab 規劃

```
aif-gitlab.wistron.com/ai-platform/projects/
└── finaiagent/            ← ASP 資源群，已建立
    ├── agent-template     ← ASP 自動產生
    └── finagent/          ← ASP 資源名稱，需自建 subgroup
        ├── <source repo>  ← Agent 程式碼（fork columbus agent 範本）
        ├── <helm repo>    ← K8s 部署設定（fork columbus helm 範本）
        └── <frontend repo>← 前端（Agent Chat UI）
```

- 採 Multi-Repo（source code 和 helm 分開），是 Release Management SOP 的標準結構，比較見 [tech_study.md](docs/tech_study.md)。
- 範本在 `aif-gitlab.wistron.com/columbus1/pro-code/` 的 `agent` 和 `helm`，用 fork 帶進 `finagent/`。
- GitLab 權限和 group 申請由 TL 處理。

## 3. 資源申請與進度

依《手把手教學》分三個 Phase。負責人皆為 TL（#10、#12 含 Dev）。

### Phase 1：權限與資源（可並行）

| # | 項目 | 申請管道 | 狀態 |
|---|---|---|---|
| 1 | AAD 帳號與服務 | ITSR（Azure AD－應用程式管理），再到 Washoku 綁定 pod 認證 | App Registration 完成（[ITSR2026100802018259](https://itsr.wistron.com/homepage/myForm/detail/ITSR2026100802018259)）；Washoku 待辦 |
| 2 | AI Use Case | ASP 新建專案（需 Project Code 或 Charge Dept） | 完成 2026/10/12（[ASP 專案頁面](https://asportal.wistron.com/project-management/project-list/project-detail?ucId=274&pjGroup=175)） |
| 3 | AIF-GitLab 權限與 Group | ITSR：AIF-Gitlab 權限申請＋ASP 專案群 Group 申請 | [group](https://aif-gitlab.wistron.com/ai-platform/projects/finaiagent) 完成；WITS 同事權限完成（[ITSR2026101202110096](https://itsr.wistron.com/homepage/myForm/detail/ITSR2026101202110096)），Wistron 同事可自行申請 |
| 4 | Armstrong Namespace | [WiCOP](https://wicop.wistron.com/wicop/applicationForms/applyStatus) New Account Combo（[教學](https://cloud-guidebook.wistron.com/developer/01_Kickoff-a-project/1.1_Setting-up-accounts/)） | 審核中（ApplyNo `20261014C0005`），開 PRD 和 QAS |

### Phase 2：專案與服務（可並行）

| # | 項目 | 申請管道 | 狀態 |
|---|---|---|---|
| 5 | PostgreSQL | WCP | 待辦。Agent Server 存 thread／checkpoint 用；Redis 隨 helm chart 部署 |
| 6 | Columbus AI Gateway 使用權 | DSP | 申請中（[PCA1584](https://dsportal.wistron.com/data-service/my-lists/my-applications/consume-list/detail?serialFormId=PCA1584)） |
| 7 | Columbus 模型 token | ITSR | 完成（[ITSR2026101502170669](https://itsr.wistron.com/homepage/myForm/detail/ITSR2026101502170669)） |
| 8 | LangSmith | ASP → 資源管理 → AgentOps → Pro-Code → 資源申請 | 沿用現有 |
| 9 | 建立專案 repo | 在 `finaiagent/finagent/` 建 subgroup 並 fork 範本 | 可開始 |

### Phase 3：開發與部署（依序）

| # | 項目 | 說明 | 狀態 |
|---|---|---|---|
| 10 | 本機開發 | LangGraph Studio | 進行中 |
| 11 | Vault | Secret 改存 Vault | 待辦 |
| 12 | 可觀測性 | LangSmith tracing | 進行中 |
| 13 | Helm Repo 與 Armstrong 串接 | ITSR，提供 Namespace 和 Helm repo 路徑（須與 ASP 命名一致） | 等 #4、#9 |
| 14 | CI/CD Pipeline 與部署 | 見第 4 節 | 待辦 |

### Release Management 上線前準備

需向 SRE 提供專案資訊，並在 pipeline 加入安全掃描（GitSecOps／DSOMM）：

| 項目 | 內容 |
|---|---|
| DevSecOps-Argo 申請單 | Project Name、AAD TL／RD Group、Subscription、Namespace、Helm repo 路徑與分支對應 |
| GitLab Group Access Token | 建立 `RMTOKEN`，repo CI/CD Variables 設定 `RMTOKEN`、`DOCKER_USERNAME` |
| SonarQube | `SONAR_PROJECTKEY`、`SONAR_TOKEN`、`SONAR_HOST_URL`，根目錄加 `sonar-project.properties` |
| 簽章金鑰 | `COSIGN_KEY`／`COSIGN_PUB` |

SOP 範例用 devpack 平台（`gitlab.devpack.cc`、`sonarqube.devpack.cc`），換到 AIF-GitLab 後的位址要再向 SRE 確認。

## 4. 整體架構

參考 AIF CI/CD Pipeline（手把手教學第 17 頁）：

| 階段 | 內容 |
|---|---|
| CI | push 後：Test → LangGraph Build → Docker Build → 推到 registry。PRD 上線前加跑 SonarQube、SCA、Cosign、Container Scan |
| CD Prep | 取得 image digest → 用 `envsubst` 更新 Helm repo 的 `values.yaml` → commit & push |
| CD | Argo CD 偵測 Helm repo 變更，Sync 到 Armstrong（QAS／PRD） |
| Runtime | Washoku 處理 AAD 認證；Agent Pod 搭配 Redis、連 PostgreSQL、從 Vault 取 secrets |
| Columbus | 透過 APIM 呼叫 Luna LLM；trace 送 LangSmith |

分支與部署：

| 觸發 | 環境 | CI 動作 |
|---|---|---|
| MR 到 `qas` | — | lint（ruff） |
| merge 進 `qas` | QAS | lint → build image 推到 Harbor |
| merge 進 `prd`（主分支） | PRD | 不重新 build，把 QAS 測過的 image 推廣到 PRD |
| 在 `prd` 打 tag（例如 `v1.0.0`） | PRD | PRD image 加上版本號 tag |

版本：Harbor tag `<台灣時間>-<commit>`（例如 `202610191430-a1b2c3d`）是 build 編號，QAS 和 PRD 相同；`v1.0.0` 這類版本號以 git tag 為準。服務的 `/version` 會回傳 build 編號和部署時設定的版本號。

細節見 [docs/gitlab_flow.md](docs/gitlab_flow.md)。

排程流程：[docs/schedule-api.md](docs/schedule-api.md)（API／DB）、[docs/schedule-deploy.md](docs/schedule-deploy.md)（部署預估）、[docs/schedule-db.md](docs/schedule-db.md)（DB 更新與資料）。

## 5. 前端：Agent Chat UI

前端採用 **Agent Chat UI**（LangChain 官方開源，Next.js／TypeScript），使用者從 [fin.wistron.com](https://fin.wistron.com/#/login) 的「AI 家園」連結進入。

選擇原因：與 LangGraph Server 同一套，原生支援 streaming、tool call 顯示、human-in-the-loop，串接成本最低。

要處理的事：

- AAD SSO 需自行串接（MSAL 或 NextAuth）
- 團隊需有人維護 Node.js／TypeScript
- 需要自己的 repo、helm 和 pipeline（`finaiagent/finagent/<frontend repo>`）

評估過的其他方案：Chainlit（純 Python，但客製化有限）、Streamlit／Gradio（只適合 demo）、自建 React（成本最高）、Teams bot（限制多）。

## 6. 下一步

1. 追蹤 WiCOP 核准（#4），取得 Onboarding Pack；確認 [wicop.md 待確認事項](docs/wicop.md#待確認事項)
2. WCP 申請 PostgreSQL（#5）
3. 建 `finagent` subgroup，fork agent 和 helm 範本（#9）
4. Namespace 下來後，ITSR 申請 Helm Repo 與 K8s 串接（#13）
5. 送 DevSecOps-Argo 申請單，準備 RMTOKEN、SonarQube、Cosign 變數
6. `.env` 的 secrets 搬到 Vault 和 GitLab CI/CD Variables
7. 建立前端 repo，部署 Agent Chat UI 並串接 AAD SSO（第 5 節）
