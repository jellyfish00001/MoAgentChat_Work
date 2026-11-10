using AiPrepare.Scheduler.Application;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Application.Dtos;
using AiPrepare.Scheduler.Infrastructure;
using Microsoft.Extensions.Options;

// 極薄 API 宿主：只做 CORS／JobKey／轉呼叫 Application。
// 業務 API 統一 POST（查詢亦同）；僅 /health 保留 GET 供探針。
var builder = WebApplication.CreateBuilder(args);

var sqlitePath = builder.Configuration["SCHEDULE_DB_PATH"]
    ?? Environment.GetEnvironmentVariable("SCHEDULE_DB_PATH")
    ?? @"D:\ai_prepare_data\schedules.sqlite";
var jobKey = builder.Configuration["JOB_KEY"]
    ?? Environment.GetEnvironmentVariable("SCHEDULE_JOB_KEY")
    ?? "dev-job-key";

builder.Services.AddSchedulerCore(sqlitePath, builder.Configuration);
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.WithOrigins("http://localhost:3000").AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();
await app.Services.EnsureDbAsync();

app.UseCors();

/// <summary>健康檢查（含 DB 路徑，不含機密）；探針用 GET。</summary>
app.MapGet("/health", () => Results.Ok(new { ok = true, db = sqlitePath }));

/// <summary>列出使用者個人排程（不含公司 Scope；body.userId）。</summary>
app.MapPost("/api/schedules/list", async (ListSchedulesRequest body, ScheduleService svc, CancellationToken ct) =>
    Results.Ok(await svc.ListAsync(body.UserId, ct)));

/// <summary>建立個人排程（強制 Scope=User）。</summary>
app.MapPost("/api/schedules", async (CreateScheduleRequest body, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.CreateAsync(body, ct);
    return Results.Created($"/api/schedules/{dto.Id}", dto);
});

/// <summary>取得單一排程。</summary>
app.MapPost("/api/schedules/{id:guid}/get", async (Guid id, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.GetAsync(id, ct);
    return dto is null ? Results.NotFound() : Results.Ok(dto);
});

/// <summary>部分更新（啟停／標題等）。</summary>
app.MapPost("/api/schedules/{id:guid}/patch", async (Guid id, PatchScheduleRequest body, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.PatchAsync(id, body, ct);
    return dto is null ? Results.NotFound() : Results.Ok(dto);
});

/// <summary>刪除排程。</summary>
app.MapPost("/api/schedules/{id:guid}/delete", async (Guid id, ScheduleService svc, CancellationToken ct) =>
{
    await svc.DeleteAsync(id, ct);
    return Results.NoContent();
});

/// <summary>列出執行紀錄（維運／側欄）。</summary>
app.MapPost("/api/schedules/{id:guid}/runs/list", async (Guid id, ScheduleService svc, CancellationToken ct) =>
    Results.Ok(await svc.ListRunsAsync(id, ct)));

/// <summary>立刻執行一次（與 Job 共用 IScheduleRunExecutor；含公司列）。</summary>
app.MapPost("/api/schedules/{id:guid}/run-now", async (Guid id, IScheduleRunExecutor exec, CancellationToken ct) =>
{
    var run = await exec.ExecuteAsync(id, ct);
    return Results.Ok(new ScheduleRunDto(
        run.Id, run.ScheduleId, run.Status, run.ThreadId, run.Error, run.NotifyOutcome,
        run.StartedAt, run.FinishedAt));
});

/// <summary>內部：列出公司排程（需 X-Job-Key）。</summary>
app.MapPost("/api/internal/schedules/company/list", async (HttpRequest req, ScheduleService svc, CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    return Results.Ok(await svc.ListCompanyAsync(ct));
});

/// <summary>內部：建立公司排程（需 X-Job-Key；Scope=Company）。</summary>
app.MapPost("/api/internal/schedules/company", async (HttpRequest req, CreateScheduleRequest body, ScheduleService svc, CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    var dto = await svc.CreateCompanyAsync(body, ct);
    return Results.Created($"/api/schedules/{dto.Id}", dto);
});

/// <summary>內部：列出即將到期（需 X-Job-Key；尊重公司掃描開關）。</summary>
app.MapPost("/api/internal/schedules/due", async (
    HttpRequest req,
    ScheduleService svc,
    IOptions<CompanySchedulesOptions> companyOpts,
    CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    var until = DateTimeOffset.UtcNow.AddMinutes(1);
    var due = await svc.ListDueEntitiesAsync(until, companyOpts.Value.Enabled, ct);
    return Results.Ok(due.Select(s => new { s.Id, s.Title, s.Scope, s.NextRunAt }));
});

/// <summary>內部：觸發 due 掃描（需 X-Job-Key；除錯用）。</summary>
app.MapPost("/api/internal/schedules/process-due", async (HttpRequest req, IScheduleRunExecutor exec, CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    var n = await exec.ProcessDueAsync(DateTimeOffset.UtcNow.AddMinutes(1), ct);
    return Results.Ok(new { processed = n });
});

// k8s 由 ASPNETCORE_URLS 指定（容器內要聽 0.0.0.0）；本機預設只聽 loopback
app.Run(app.Configuration["urls"] ?? "http://127.0.0.1:5055");

/// <summary>比對 X-Job-Key；本機可用固定開發值。</summary>
static bool CheckJobKey(HttpRequest req, string expected)
    => req.Headers.TryGetValue("X-Job-Key", out var v) && v == expected;
