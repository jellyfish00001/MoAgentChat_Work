using AiPrepare.Scheduler.Application.Abstractions;

namespace AiPrepare.Scheduler.Job;

/// <summary>Thin Hangfire entry: process all due schedules once per minute.</summary>
public sealed class ProcessDueSchedulesJob
{
    private readonly IScheduleRunExecutor _executor;

    public ProcessDueSchedulesJob(IScheduleRunExecutor executor) => _executor = executor;

    public Task RunAsync() => _executor.ProcessDueAsync(DateTimeOffset.UtcNow);
}
