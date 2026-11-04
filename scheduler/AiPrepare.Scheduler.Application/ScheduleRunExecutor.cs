using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.Extensions.Logging;

namespace AiPrepare.Scheduler.Application;

/// <summary>Claim → LangGraph thread+run → complete; used by Job and run-now.</summary>
public sealed class ScheduleRunExecutor : IScheduleRunExecutor
{
    private readonly IScheduleRepository _repo;
    private readonly ILangGraphClient _lg;
    private readonly ILogger<ScheduleRunExecutor> _log;

    public ScheduleRunExecutor(
        IScheduleRepository repo,
        ILangGraphClient lg,
        ILogger<ScheduleRunExecutor> log)
    {
        _repo = repo;
        _lg = lg;
        _log = log;
    }

    public async Task<int> ProcessDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default)
    {
        var due = await _repo.ListDueAsync(untilUtc, ct);
        var n = 0;
        foreach (var s in due)
        {
            await ExecuteAsync(s.Id, ct);
            n++;
        }
        return n;
    }

    public async Task<ScheduleRun> ExecuteAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var schedule = await _repo.GetAsync(scheduleId, ct)
            ?? throw new InvalidOperationException($"Schedule {scheduleId} not found");

        // Claim: push next_run before LangGraph so concurrent due-scanners skip this row.
        schedule.NextRunAt = NextRunCalculator.ComputeNext(
            schedule.Kind, DateTimeOffset.UtcNow, schedule.TimeOfDay, schedule.Weekday, schedule.IntervalHours);
        schedule.UpdatedAt = DateTimeOffset.UtcNow;
        await _repo.UpdateAsync(schedule, ct);

        var run = new ScheduleRun
        {
            Id = Guid.NewGuid(),
            ScheduleId = schedule.Id,
            Status = ScheduleRunStatus.Running,
            StartedAt = DateTimeOffset.UtcNow,
        };
        await _repo.AddRunAsync(run, ct);

        try
        {
            var result = await _lg.CreateThreadAndRunAsync(
                new LangGraphRunRequest(
                    schedule.ApiUrl,
                    schedule.AssistantId,
                    schedule.Prompt,
                    schedule.Id,
                    schedule.Title,
                    schedule.UserId),
                ct);

            run.FinishedAt = DateTimeOffset.UtcNow;
            if (result.Ok)
            {
                run.Status = ScheduleRunStatus.Succeeded;
                run.ThreadId = result.ThreadId;
            }
            else
            {
                run.Status = ScheduleRunStatus.Failed;
                run.Error = result.Error;
            }

            schedule.LastRunAt = run.FinishedAt;
            schedule.UpdatedAt = DateTimeOffset.UtcNow;
            await _repo.UpdateRunAsync(run, ct);
            await _repo.UpdateAsync(schedule, ct);

            _log.LogInformation(
                "Schedule {ScheduleId} run {RunId} {Status} thread={ThreadId}",
                schedule.Id, run.Id, run.Status, run.ThreadId);
            return run;
        }
        catch (Exception ex)
        {
            run.Status = ScheduleRunStatus.Failed;
            run.Error = ex.Message;
            run.FinishedAt = DateTimeOffset.UtcNow;
            schedule.UpdatedAt = DateTimeOffset.UtcNow;
            await _repo.UpdateRunAsync(run, ct);
            await _repo.UpdateAsync(schedule, ct);
            _log.LogError(ex, "Schedule {ScheduleId} run failed", scheduleId);
            return run;
        }
    }
}
