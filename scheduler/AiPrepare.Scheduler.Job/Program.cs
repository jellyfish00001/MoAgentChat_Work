using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Infrastructure;
using AiPrepare.Scheduler.Job;
using Hangfire;
using Hangfire.Dashboard.BasicAuthorization;
using Hangfire.MemoryStorage;

var builder = WebApplication.CreateBuilder(args);

var sqlitePath = builder.Configuration["SCHEDULE_DB_PATH"]
    ?? Environment.GetEnvironmentVariable("SCHEDULE_DB_PATH")
    ?? @"D:\ai_prepare_data\schedules.sqlite";
var hangfireUser = builder.Configuration["hangfire:login"] ?? "admin";
var hangfirePass = builder.Configuration["hangfire:password"]
    ?? Environment.GetEnvironmentVariable("HANGFIRE_PASSWORD")
    ?? "admin";

builder.Services.AddSchedulerCore(sqlitePath);
builder.Services.AddHangfire(c => c
    .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
    .UseSimpleAssemblyNameTypeSerializer()
    .UseRecommendedSerializerSettings()
    .UseMemoryStorage());
builder.Services.AddHangfireServer();
builder.Services.AddScoped<ProcessDueSchedulesJob>();

var app = builder.Build();
await app.Services.EnsureDbAsync();

app.UseHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization =
    [
        new BasicAuthAuthorizationFilter(new BasicAuthAuthorizationFilterOptions
        {
            RequireSsl = false,
            SslRedirect = false,
            LoginCaseSensitive = false,
            Users =
            [
                new BasicAuthAuthorizationUser
                {
                    Login = hangfireUser,
                    PasswordClear = hangfirePass,
                },
            ],
        }),
    ],
});

// Register by type so Hangfire Activator resolves a fresh scope each run (avoid capturing scoped instance).
RecurringJob.AddOrUpdate<ProcessDueSchedulesJob>(
    "ProcessDueSchedulesJob",
    j => j.RunAsync(),
    Cron.Minutely,
    new RecurringJobOptions { TimeZone = TimeZoneInfo.Local });

app.MapGet("/health", () => Results.Ok(new { ok = true, hangfire = "/hangfire" }));
app.Run("http://127.0.0.1:5056");
