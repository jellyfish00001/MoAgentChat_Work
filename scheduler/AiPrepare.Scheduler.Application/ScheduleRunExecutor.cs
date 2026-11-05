using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace AiPrepare.Scheduler.Application;

/// <summary>唯一執行管線：認領 → LangGraph thread+run → 完成；Job 與 run-now 共用。</summary>
public sealed class ScheduleRunExecutor : IScheduleRunExecutor
{
    private readonly IScheduleRepository _repo;
    private readonly ILangGraphClient _lg;
    private readonly IOptions<CompanySchedulesOptions> _companyOpts;
    private readonly ILogger<ScheduleRunExecutor> _log;

    /// <summary>注入仓储、LangGraph、公司掃描開關與結構化日誌。</summary>
    public ScheduleRunExecutor(
        IScheduleRepository repo,
        ILangGraphClient lg,
        IOptions<CompanySchedulesOptions> companyOpts,
        ILogger<ScheduleRunExecutor> log)
    {
        _repo = repo;
        _lg = lg;
        _companyOpts = companyOpts;
        _log = log;
    }

    /// <summary>掃描到期排程並逐筆 Execute；公司列受 CompanySchedules:Enabled 控制。</summary>
    public async Task<int> ProcessDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default)
    {
        var includeCompany = _companyOpts.Value.Enabled;
        var due = await _repo.ListDueAsync(untilUtc, includeCompany, ct);
        var n = 0;
        foreach (var s in due)
        {
            await ExecuteAsync(s.Id, ct);
            n++;
        }
        return n;
    }

    /// <summary>執行單一排程一次（新 thread）；不受公司掃描開關影響。</summary>
    public async Task<ScheduleRun> ExecuteAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var schedule = await _repo.GetAsync(scheduleId, ct)
            ?? throw new InvalidOperationException($"Schedule {scheduleId} not found");

        // 1. 認領：先推 NextRunAt，避免並發 due-scanner 重複撿同一列
        schedule.NextRunAt = NextRunCalculator.ComputeNext(
            schedule.Kind, DateTimeOffset.UtcNow, schedule.TimeOfDay, schedule.Weekday, schedule.IntervalHours);
        schedule.UpdatedAt = DateTimeOffset.UtcNow;
        await _repo.UpdateAsync(schedule, ct);

        // 2. 建立 Running 紀錄
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
            // 3. 呼叫 LangGraph（metadata.source=schedule）
            var result = await _lg.CreateThreadAndRunAsync(
                new LangGraphRunRequest(
                    schedule.ApiUrl,
                    schedule.AssistantId,
                    schedule.Prompt,
                    schedule.Id,
                    schedule.Title,
                    schedule.UserId),
                ct);

            // 4. 寫回成功／失敗狀態
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
            // 5. 例外仍要落庫，避免永遠卡在 Running
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
