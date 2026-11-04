using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Abstractions;

/// <summary>Single execution pipeline shared by Job due-scan and API run-now.</summary>
public interface IScheduleRunExecutor
{
    Task<ScheduleRun> ExecuteAsync(Guid scheduleId, CancellationToken ct = default);
    Task<int> ProcessDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default);
}
