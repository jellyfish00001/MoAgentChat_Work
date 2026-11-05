using AiPrepare.Scheduler.Application;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Infrastructure.LangGraph;
using AiPrepare.Scheduler.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace AiPrepare.Scheduler.Infrastructure;

/// <summary>Api／Job 共用的 DI 組裝（SQLite + Application + LangGraph）。</summary>
public static class DependencyInjection
{
    /// <summary>註冊核心服務；資料庫檔放專案外路徑；綁定公司掃描開關。</summary>
    public static IServiceCollection AddSchedulerCore(
        this IServiceCollection services,
        string sqlitePath,
        IConfiguration? configuration = null)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(sqlitePath)!);
        var cs = $"Data Source={sqlitePath}";
        services.AddDbContext<SchedulerDbContext>(o => o.UseSqlite(cs));

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

        services.AddScoped<IScheduleRepository, EfScheduleRepository>();
        services.AddScoped<ScheduleService>();
        services.AddScoped<IScheduleRunExecutor, ScheduleRunExecutor>();
        services.AddHttpClient("langgraph");
        services.AddScoped<ILangGraphClient, LangGraphHttpClient>();
        return services;
    }

    /// <summary>套用 EF Migrations（取代 EnsureCreated，以支援部署後加欄）。</summary>
    public static async Task EnsureDbAsync(this IServiceProvider sp, CancellationToken ct = default)
    {
        using var scope = sp.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<SchedulerDbContext>();
        await db.Database.MigrateAsync(ct);
    }
}
