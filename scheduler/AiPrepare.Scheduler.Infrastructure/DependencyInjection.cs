using AiPrepare.Scheduler.Application;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Infrastructure.LangGraph;
using AiPrepare.Scheduler.Infrastructure.Notifications;
using AiPrepare.Scheduler.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace AiPrepare.Scheduler.Infrastructure;

/// <summary>Api／Job 共用的 DI 組裝（PostgreSQL／Npgsql + Application + LangGraph + 通知）。</summary>
public static class DependencyInjection
{
    /// <summary>註冊核心服務；連線由 DbConnectionResolver 解析；綁定公司掃描與通知開關。</summary>
    public static IServiceCollection AddSchedulerCore(
        this IServiceCollection services,
        IConfiguration? configuration = null)
    {
        var cs = DbConnectionResolver.Resolve(configuration);
        services.AddDbContext<SchedulerDbContext>(o => o.UseNpgsql(cs, npg =>
            npg.MigrationsHistoryTable("__EFMigrationsHistory", "scheduler")));

        // CompanySchedules:Enabled；環境變數 COMPANY_SCHEDULES_ENABLED 可覆寫
        var opts = services.AddOptions<CompanySchedulesOptions>();
        if (configuration is not null)
            opts.Bind(configuration.GetSection(CompanySchedulesOptions.SectionName));
        opts.Configure(o =>
        {
            var env = Environment.GetEnvironmentVariable("COMPANY_SCHEDULES_ENABLED");
            if (env is null) return;
            if (bool.TryParse(env, out var b))
                o.Enabled = b;
            else if (env is "1" or "0")
                o.Enabled = env == "1";
        });

        // Notification:Mode 預設 Draft；環境變數 NOTIFICATION_MODE 可覆寫（本機勿設 Http）
        var notifyOpts = services.AddOptions<NotificationOptions>();
        if (configuration is not null)
            notifyOpts.Bind(configuration.GetSection(NotificationOptions.SectionName));
        notifyOpts.Configure(o =>
        {
            var env = Environment.GetEnvironmentVariable("NOTIFICATION_MODE");
            if (!string.IsNullOrWhiteSpace(env))
                o.Mode = env.Trim();
            // InvokeUrl 只從設定／Secret 來，禁止用環境變數以外的硬編碼
            var url = Environment.GetEnvironmentVariable("NOTIFICATION_INVOKE_URL");
            if (!string.IsNullOrWhiteSpace(url))
                o.InvokeUrl = url.Trim();
        });

        services.AddScoped<IScheduleRepository, EfScheduleRepository>();
        services.AddScoped<ScheduleService>();
        services.AddScoped<IScheduleRunExecutor, ScheduleRunExecutor>();
        services.AddHttpClient("langgraph")
            .ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler { AllowAutoRedirect = false });
        services.AddScoped<ILangGraphClient, LangGraphHttpClient>();
        // 本階段一律 Draft，不註冊實發 Http client，避免誤寄
        services.AddScoped<INotificationSender, DraftNotificationSender>();
        return services;
    }

    /// <summary>建立 scheduler schema（若不存在）後套用 EF Migrations。</summary>
    public static async Task EnsureDbAsync(this IServiceProvider sp, CancellationToken ct = default)
    {
        using var scope = sp.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<SchedulerDbContext>();
        // History 表在 scheduler schema；空庫須先有 schema 才能 CreateIfNotExists
        await db.Database.ExecuteSqlRawAsync("CREATE SCHEMA IF NOT EXISTS scheduler;", ct);
        await db.Database.MigrateAsync(ct);
    }
}
