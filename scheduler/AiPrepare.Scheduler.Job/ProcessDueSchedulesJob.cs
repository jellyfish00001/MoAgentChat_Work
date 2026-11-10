using AiPrepare.Scheduler.Application.Abstractions;

namespace AiPrepare.Scheduler.Job;

/// <summary>薄 Hangfire 入口：每分鐘處理到期排程一次。</summary>
public sealed class ProcessDueSchedulesJob
{
    private readonly IScheduleRunExecutor _executor;

    /// <summary>注入共用執行管線。</summary>
    public ProcessDueSchedulesJob(IScheduleRunExecutor executor) => _executor = executor;

    /// <summary>Hangfire 呼叫點；勿在此寫業務邏輯。</summary>
    public Task RunAsync() => _executor.ProcessDueAsync(DateTimeOffset.UtcNow);
}
