using AiPrepare.Scheduler.Application;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Infrastructure.LangGraph;
using AiPrepare.Scheduler.Infrastructure.Persistence;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace AiPrepare.Scheduler.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddSchedulerCore(this IServiceCollection services, string sqlitePath)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(sqlitePath)!);
        var cs = $"Data Source={sqlitePath}";
        services.AddDbContext<SchedulerDbContext>(o => o.UseSqlite(cs));
        services.AddScoped<IScheduleRepository, EfScheduleRepository>();
        services.AddScoped<ScheduleService>();
        services.AddScoped<IScheduleRunExecutor, ScheduleRunExecutor>();
        services.AddHttpClient("langgraph");
        services.AddScoped<ILangGraphClient, LangGraphHttpClient>();
        return services;
    }

    public static async Task EnsureDbAsync(this IServiceProvider sp, CancellationToken ct = default)
    {
        using var scope = sp.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<SchedulerDbContext>();
        await db.Database.EnsureCreatedAsync(ct);
    }
}
