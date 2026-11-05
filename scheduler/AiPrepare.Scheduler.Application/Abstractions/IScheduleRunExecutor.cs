using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Abstractions;

/// <summary>唯一執行管線合約（Job 與 run-now 共用）。</summary>
public interface IScheduleRunExecutor
{
    /// <summary>處理所有到期排程；回傳筆數。</summary>
    Task<int> ProcessDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default);

    /// <summary>執行單一排程一次。</summary>
    Task<ScheduleRun> ExecuteAsync(Guid scheduleId, CancellationToken ct = default);
}
