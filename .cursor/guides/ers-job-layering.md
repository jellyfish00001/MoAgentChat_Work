# ERS.Job 分層研究 → ai_prepare Scheduler 規範

研究來源：本機 `D:\ERS2.0\web\api\src\ERS.Job`（及同解的 Domain／Application／EFCore／Contracts）。  
目的：學其**中間層與統一介面**，避開其**零散與坑**；本檔是 Agent／人類常駐對照，細節運維仍見 [scheduler-coding.md](scheduler-coding.md)。

---

## 1. ERS 整體怎麼疊（Job 不是業務家）

```text
ERS.Job（Hangfire 宿主）
  ├─ DependsOn → Application / Application.Contracts / Domain / EntityFrameworkCore
  ├─ Jobs/* 實作 IJobBase（理想：只呼叫 DomainService）
  └─ Util：JobRegister、HangfireJobActivator、IJobBase

ERS.HttpApi → Application（IXxxService）
ERS.Application → Domain + AutoMapper Profiles
ERS.Application.Contracts → DTO + IXxxService 介面（對 API／前端的統一契約）
ERS.Domain → IDomainServices + DomainServices + IRepositories 介面 + Entities + ERSConsts
ERS.EntityFrameworkCore → Repository 實作 + DbContext
```

**中間層（對我們最有用的）**

| 層 | ERS 放什麼 | 誰依賴誰 |
|----|------------|----------|
| Contracts | `DTO/*`、`IXxxService` | HttpApi／App 共用契約；**無實作** |
| Application | `XxxService`、AutoMapper Profile | 用例編排；可呼叫 Domain |
| Domain | `IDomainServices`、`DomainServices`、`IRepositories`、實體、常數／enum | 業務規則；**不依賴** EF／Hangfire |
| Infrastructure／EF | Repository、DbContext | 實作 Domain 介面 |
| Job／HttpApi | 極薄入口 | 只 resolve 服務並觸發 |

Job 與 HttpApi **共用同一套 Domain／Application**，不是各寫一管線。

---

## 2. Job 統一介面與設定檔驅動

### 介面（單一合約）

`ERS.Job/Util/IJobBase.cs`：

```csharp
public interface IJobBase
{
    Task Run();
}
```

所有排程類實作同一介面 → 註冊與啟停可統一處理。

### 設定模型

`Model/JobInfo.cs` ↔ `appsettings.json` → `hangfire:jobs[]`：

| 欄位 | 用途 |
|------|------|
| `JobName` | Dashboard／識別 |
| `IsEnable` | **設定檔關閉＝不註冊**（不必改程式） |
| `JobClass` | 必須等於 C# **型別名**（`GetType().Name`） |
| `Cron` | Quartz 風格 cron |

### 注入與註冊流程

1. `ERSJobModule.ConfigureServices`：`Configure<List<JobInfo>>(hangfire:jobs)` + 逐一 `AddScoped<IJobBase, XxxJob>()`
2. `OnApplicationInitialization`：掛 Dashboard、`HangfireJobActivator`（每次 Job 開 **新 Scope**）
3. `JobRegister.RegisterJobsFromConfig()`：`IsEnable` 為真 → 依 `JobClass` 從 `IEnumerable<IJobBase>` 找實例 → `RecurringJob.AddOrUpdate`

**薄 Job 範本（應學）**：`Fubon_PaymentInfoJob` — ctor 只注入 `IFubonPaymentDataDomainService`，`Run()` 一行轉呼叫。  
**厚 Job（應避）**：`Uber_DownloadTransactionByDaillyJob` — Job 內直接 SFTP／MinIO／Repository／組字串。

### Hangfire 作用域

`HangfireJobActivator` + `IServiceScopeFactory`：每次執行新建 scope，避免 Scoped 服務變 Singleton 幽靈。  
**但** `JobRegister` 用 `() => service.Run()` **閉包綁死啟動時的實例** — 這是 ERS 已知坑；ai_prepare 必須用 `RecurringJob.AddOrUpdate<T>(j => j.RunAsync())` 讓 Activator 每次 resolve。

---

## 3. 映射（AutoMapper）放哪裡

- `ERSApplicationModule`：`AbpAutoMapperOptions.AddMaps<ERSApplicationModule>()`
- 規則集中：`ERSApplicationAutoMapperProfile`（Entity ↔ DTO）
- Domain 也可 `AddMaps`（較少）
- **Job 專案本身幾乎不做 mapping**；需要 DTO 轉換時應在 Application／Domain

ai_prepare 現況無 AutoMapper：手寫 `ToDtoAsync` 可接受；若 DTO 變多，再在 Application 加 **一個** Profile／對應器，禁止在 Job／Api Program 散落映射。

---

## 4. Enum／常數怎麼放（學集中、避神檔）

ERS 幾乎所有 enum 堆在 `ERS.Domain/ERSConsts.cs`（上千行）：

- 優點：不會滿專案亂長 enum 檔
- 缺點：單一巨型檔難 diff、難擁有權

**ai_prepare 規範（折衷，避免零散也避免神檔）**：

```text
Domain/
  ScheduleKind.cs      ← 與概念同名、一概念一檔（或少數相關 enum 同檔）
  ScheduleScope.cs
  ScheduleRunStatus.cs （可與 ScheduleRun 同檔若極短）
  禁止：Program.cs／Job 內臨時 enum
  禁止：再建第二套平行常數類複製同一組值
```

業務字面常數（graph id、header 名）→ Application 或 Infrastructure **一個** `SchedulerConstants`／Options，不要複製字串。

---

## 5. 注入慣例對照

| ERS（ABP） | ai_prepare Scheduler |
|------------|----------------------|
| Module `DependsOn` 鏈 | `AddSchedulerCore` 單一組裝點（Api／Job 共用） |
| 約定註冊 `IDomainService` | 明確 `AddScoped`／`AddDbContext` |
| `IOptions` / `appsettings` | `CompanySchedulesOptions`、`SCHEDULE_DB_PATH`、JobKey |
| `IEnumerable<IJobBase>` 多實作 | 目前 **一條** due-scanner；公司多任務＝**DB 多列**，不是多條 Hangfire Job |
| Autofac `RegisterAssemblyTypes`（Jobs） | **不採用**；與手動 `AddScoped` 雙軌易漏註冊（ERS 已有雙軌跡象） |

---

## 6. 設定檔分層（避免散落）

ERS Job：

- `hangfire:login`／`password`／`jobs[]` — 排程宿主
- `Email`／外部系統連線 — 基礎設施
- 執行期參數亦可進 DB `AppConfig`（Uber Job 讀 key）

ai_prepare：

| 設定 | 位置 | 用途 |
|------|------|------|
| `CompanySchedules:Enabled` | Api／Job `appsettings` + env `COMPANY_SCHEDULES_ENABLED` | 是否掃公司列 |
| `SCHEDULE_DB_PATH` | env／config | SQLite 路徑 |
| `JOB_KEY`／`SCHEDULE_JOB_KEY` | env | internal API |
| `hangfire:login`／password | Job appsettings／env | Dashboard |
| 排程「內容」（Prompt／週期） | **DB `Schedules`** | 多筆公司／個人任務；**不要**為每筆再建 Hangfire Recurring |

停公司服務＝關 `CompanySchedules:Enabled`（同進程），對齊 ERS 的 `IsEnable` 精神，但粒度是 **Scope 掃描**，不是刪掉整支 Job 類。

---

## 7. 對 ai_prepare 的「目錄不要零散」清單

允許的集中點（超出就先問要不要新資料夾）：

```text
scheduler/
  *.Domain/           實體、enum、純計算（NextRunCalculator）
  *.Application/
      Abstractions/   介面（IScheduleRepository、IScheduleRunExecutor、ILangGraphClient）
      Dtos/           請求／回應 DTO（唯一）
      *Service.cs、*Executor.cs、*Options.cs
  *.Infrastructure/
      Persistence/    DbContext、Repository、Migrations
      LangGraph/      HTTP 適配
      DependencyInjection.cs   ← 唯一組裝
  *.Api/              Program 映射端點 only
  *.Job/              薄 Hangfire 入口 + appsettings
```

禁止：

- 在 Job 內複製第二套「執行管線」
- 在 Api 寫業務規則或直接操作 DbContext
- enum／DTO 各層各寫一份
- 為每個公司任務新增一個 `XxxJob.cs`（應新增 `Schedules` 列 + Scope=Company）

---

## 8. 新增一個「可排程能力」時的檢查表

1. 業務邏輯進 Application／Domain（或 LangGraph），**不是**新 Hangfire 類（除非全新外部整合且無法用 due-scanner）
2. 需要對外契約 → Application `Dtos` + Api 薄端點；公司用 → `/api/internal/...` + Job-Key
3. 需要開關 → Options／appsettings（或該列 `Enabled`），文件寫進本 guide／scheduler-coding
4. 需要 enum → Domain 一概念一檔
5. 需要持久化欄位 → EF Migration（禁止 EnsureCreated 加欄）
6. Job 宿主若必須新類 → 實作單一入口方法、注入 Executor／Service、註冊時 **依型別** AddOrUpdate

---

## 9. 來源摘要（給 SOURCES）

- `ERS.Job/ERSJobModule.cs`、`Util/IJobBase.cs`、`Util/JobRegister.cs`、`Util/HangfireJobActivator.cs`、`Model/JobInfo.cs`
- 薄：`Jobs/DataSyncJobs/Fubon_PaymentInfoJob.cs`；厚反例：`Uber_DownloadTransactionByDaillyJob.cs`
- 中間層：`ERS.Application.Contracts/DTO`、`ERS.Domain/IDomainServices`、`ERSApplicationAutoMapperProfile.cs`、`ERSConsts.cs`
