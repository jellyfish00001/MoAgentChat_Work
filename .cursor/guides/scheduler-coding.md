# Scheduler／Job 可維護性（對齊 ERS，避其坑）

給 Agent 與人類：`scheduler/`（.NET Api + Job）與相關前端模組。細節部署見排程計畫；本檔是**常駐編碼規範**。

ERS.Job 結構研究（中間層／介面／注入／設定／enum、可學與應避）：**[ers-job-layering.md](ers-job-layering.md)**。  
強制規則（globs）：`rules/aipark-scheduler-layering.mdc`。  
對外流程圖：[`docs/schedule-api.md`](../../docs/schedule-api.md)、[`schedule-deploy.md`](../../docs/schedule-deploy.md)、[`schedule-db.md`](../../docs/schedule-db.md)。

## 分層（依賴不可逆）

```text
AiPrepare.Scheduler.Job          → Application
AiPrepare.Scheduler.Api          → Application
Application                      → Domain
Infrastructure 實作 Application 介面，可依賴 Domain
```

- **Domain**：實體、`ScheduleKind`、`ScheduleScope`、`NextRunCalculator`（無 IO）；enum **一概念一檔**，不堆神檔、不散落 Program。
- **Application**：用例（CRUD／Due／Claim／Complete／RunNow）；**唯一** `IScheduleRunExecutor`；介面只在 `Abstractions/`，DTO 只在 `Dtos/`，Options 與 Service 同層。
- **Infrastructure**：SQLite（之後可換 PostgreSQL／Npgsql）、`LangGraphHttpClient`、`DraftNotificationSender`、EF Migrations；**唯一** `AddSchedulerCore`。
- **Api／Job**：極薄宿主；禁止在此寫業務規則或第二套執行管線。
- **多筆任務**：DB 多列（含 `Scope=Company`），不是多條 Hangfire RecurringJob 類。
- **通知**：`INotificationSender`；本機 `Notification:Mode=Draft` **不實發**。To／Cc 在 `Schedules`；結果摘要在 `ScheduleRuns.NotifyOutcome`。禁止讓 LLM 決定是否寄信。

## Schema 演進（EF Migrations）

部署後加欄／改索引**必須**走 Migration，不可再依賴 `EnsureCreated`。

```powershell
cd scheduler
dotnet ef migrations add <Name> `
  --project AiPrepare.Scheduler.Infrastructure `
  --startup-project AiPrepare.Scheduler.Api `
  --output-dir Persistence/Migrations
```

- Api／Job 啟動呼叫 `Database.MigrateAsync()`。
- 本機若舊 DB 由 `EnsureCreated` 建立、無 `__EFMigrationsHistory`：備份後刪 `SCHEDULE_DB_PATH`（預設 `D:\ai_prepare_data\schedules.sqlite`）再啟動重建。
- 公司掃描：`CompanySchedules:Enabled`（env `COMPANY_SCHEDULES_ENABLED`）；`false` 時 due-scanner 跳過 `Scope=Company`（`run-now` 仍可）。
- 公司 CRUD：`POST /api/internal/schedules/company`、`POST .../company/list`（`X-Job-Key`）；一般 `POST /api/schedules/list` 永不回傳公司列。業務 API 統一 POST。
- 後續換 PostgreSQL：另產 Npgsql Migrations，勿直接重用 SQLite migration 檔。

## 薄 Job（學 ERS `Fubon_PaymentInfoJob`）

```csharp
public async Task Run() => await _executor.ProcessDueAsync(ct);
```

不要學 Uber 類「Job 內 SFTP／DB／HTTP 全塞」。

## Hangfire／維運查看

| 管道 | 用途 |
|------|------|
| `/hangfire` Dashboard | Recurring、Succeeded／Failed（本機 launch 可開） |
| `schedule_runs` API／DB | 業務 claim／complete、`thread_id` |
| `ILogger` | 結構化；禁止 `Console.WriteLine` 當主 log |
| Chat 徽章（有 UI 後） | 使用者可見的排程對話 |

### 本機怎麼看 Job（口令）

1. `pwsh .cursor/scripts/local-dev/start-scheduler-job.ps1` → 開 `http://127.0.0.1:5056/hangfire`（admin／`HANGFIRE_PASSWORD`）。
2. **定期工作** 應見 `ProcessDueSchedulesJob` Enabled。
3. 調整一筆 `NextRunAt <= now`（或 UI／API run-now）→ 等 ≤1 分鐘或 Dashboard「立即執行」。
4. **完成的工作** 出現 `ProcessDueSchedulesJob.RunAsync` Succeeded。
5. `POST http://127.0.0.1:5055/api/schedules/{id}/runs/list` 應有 `status=Succeeded` 與 `threadId`；再 `GET :2024/threads/{id}`。

- 使用者排程存在 **DB**；Hangfire 只養 **一條** due-scanner（每分鐘），不要每 user 一條 RecurringJob。
- 註冊 recurring 時 **不要** `AddOrUpdate(() => capturedScoped.Run())`；依型別讓 Activator 每次 resolve。
- 密碼／JobKey 用 env／User Secrets，不進 git。
- MemoryStorage 僅本機 POC；正式換持久 storage。

## 註解（對齊 `aipark-docs-comments`；繁中）

- **每個方法**都要有繁中註解（C# `/// <summary>` 或 `//`；TS `/** */`）。
- 複雜方法內部加**區段**繁中註解（claim、LangGraph、SQLite 限制等 why）。
- 類／檔一句責任；長文只在 `.cursor/guides/`，不進業務 cs／tsx 灌水。
- Commit 訊息：conventional + **繁中**說明。

## 前端

- `components/schedule/*`、`lib/schedule-api.ts`、parser 純函式可測。
- 禁止把排程全部塞進 `thread/index.tsx`。
- UI token：`aipark-frontend-ui`。

## 反糊弄檢查

- 有無第二套 run 管線？Controller／Job 是否過厚？單檔是否過大應再拆？
- 常數（graph_id、header）是否集中？測試是否測行為？
