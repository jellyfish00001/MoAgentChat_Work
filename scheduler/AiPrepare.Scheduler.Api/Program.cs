using AiPrepare.Scheduler.Application;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Application.Dtos;
using AiPrepare.Scheduler.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

var sqlitePath = builder.Configuration["SCHEDULE_DB_PATH"]
    ?? Environment.GetEnvironmentVariable("SCHEDULE_DB_PATH")
    ?? @"D:\ai_prepare_data\schedules.sqlite";
var jobKey = builder.Configuration["JOB_KEY"]
    ?? Environment.GetEnvironmentVariable("SCHEDULE_JOB_KEY")
    ?? "dev-job-key";

builder.Services.AddSchedulerCore(sqlitePath);
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.WithOrigins("http://localhost:3000").AllowAnyHeader().AllowAnyMethod()));

var app = builder.Build();
await app.Services.EnsureDbAsync();

app.UseCors();
app.MapGet("/health", () => Results.Ok(new { ok = true, db = sqlitePath }));

app.MapGet("/api/schedules", async (string userId, ScheduleService svc, CancellationToken ct) =>
    Results.Ok(await svc.ListAsync(userId, ct)));

app.MapPost("/api/schedules", async (CreateScheduleRequest body, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.CreateAsync(body, ct);
    return Results.Created($"/api/schedules/{dto.Id}", dto);
});

app.MapGet("/api/schedules/{id:guid}", async (Guid id, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.GetAsync(id, ct);
    return dto is null ? Results.NotFound() : Results.Ok(dto);
});

app.MapPatch("/api/schedules/{id:guid}", async (Guid id, PatchScheduleRequest body, ScheduleService svc, CancellationToken ct) =>
{
    var dto = await svc.PatchAsync(id, body, ct);
    return dto is null ? Results.NotFound() : Results.Ok(dto);
});

app.MapDelete("/api/schedules/{id:guid}", async (Guid id, ScheduleService svc, CancellationToken ct) =>
{
    await svc.DeleteAsync(id, ct);
    return Results.NoContent();
});

app.MapGet("/api/schedules/{id:guid}/runs", async (Guid id, ScheduleService svc, CancellationToken ct) =>
    Results.Ok(await svc.ListRunsAsync(id, ct)));

app.MapPost("/api/schedules/{id:guid}/run-now", async (Guid id, IScheduleRunExecutor exec, CancellationToken ct) =>
{
    var run = await exec.ExecuteAsync(id, ct);
    return Results.Ok(new ScheduleRunDto(
        run.Id, run.ScheduleId, run.Status, run.ThreadId, run.Error, run.StartedAt, run.FinishedAt));
});

app.MapGet("/api/internal/schedules/due", async (HttpRequest req, ScheduleService svc, CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    var until = DateTimeOffset.UtcNow.AddMinutes(1);
    var due = await svc.ListDueEntitiesAsync(until, ct);
    return Results.Ok(due.Select(s => new { s.Id, s.Title, s.NextRunAt }));
});

app.MapPost("/api/internal/schedules/process-due", async (HttpRequest req, IScheduleRunExecutor exec, CancellationToken ct) =>
{
    if (!CheckJobKey(req, jobKey)) return Results.Unauthorized();
    var n = await exec.ProcessDueAsync(DateTimeOffset.UtcNow.AddMinutes(1), ct);
    return Results.Ok(new { processed = n });
});

app.Run("http://127.0.0.1:5055");

static bool CheckJobKey(HttpRequest req, string expected)
    => req.Headers.TryGetValue("X-Job-Key", out var v) && v == expected;
