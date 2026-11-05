using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace AiPrepare.Scheduler.Application;

/// <summary>唯一執行管線：認領 → LangGraph →（可選）通知 → 完成；Job 與 run-now 共用。</summary>
public sealed class ScheduleRunExecutor : IScheduleRunExecutor
{
    private readonly IScheduleRepository _repo;
    private readonly ILangGraphClient _lg;
    private readonly INotificationSender _notify;
    private readonly IOptions<CompanySchedulesOptions> _companyOpts;
    private readonly IOptions<NotificationOptions> _notifyOpts;
    private readonly ILogger<ScheduleRunExecutor> _log;

    /// <summary>注入仓储、LangGraph、通知、公司掃描開關與結構化日誌。</summary>
    public ScheduleRunExecutor(
        IScheduleRepository repo,
        ILangGraphClient lg,
        INotificationSender notify,
        IOptions<CompanySchedulesOptions> companyOpts,
        IOptions<NotificationOptions> notifyOpts,
        ILogger<ScheduleRunExecutor> log)
    {
        _repo = repo;
        _lg = lg;
        _notify = notify;
        _companyOpts = companyOpts;
        _notifyOpts = notifyOpts;
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

            // 4. 寫回 LangGraph 成功／失敗狀態
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

            // 5. 確定性通知（非 LLM 判斷）；Draft 模式不實發
            run.NotifyOutcome = await TryNotifyAsync(schedule, run, ct);

            schedule.LastRunAt = run.FinishedAt;
            schedule.UpdatedAt = DateTimeOffset.UtcNow;
            await _repo.UpdateRunAsync(run, ct);
            await _repo.UpdateAsync(schedule, ct);

            _log.LogInformation(
                "Schedule {ScheduleId} run {RunId} {Status} thread={ThreadId} notify={Notify}",
                schedule.Id, run.Id, run.Status, run.ThreadId, run.NotifyOutcome);
            return run;
        }
        catch (Exception ex)
        {
            // 例外仍要落庫，避免永遠卡在 Running；失敗也可走通知
            run.Status = ScheduleRunStatus.Failed;
            run.Error = ex.Message;
            run.FinishedAt = DateTimeOffset.UtcNow;
            try
            {
                run.NotifyOutcome = await TryNotifyAsync(schedule, run, ct);
            }
            catch (Exception notifyEx)
            {
                run.NotifyOutcome = $"Failed:{notifyEx.Message}";
                _log.LogWarning(notifyEx, "Schedule {ScheduleId} notify after exception failed", scheduleId);
            }

            schedule.UpdatedAt = DateTimeOffset.UtcNow;
            await _repo.UpdateRunAsync(run, ct);
            await _repo.UpdateAsync(schedule, ct);
            _log.LogError(ex, "Schedule {ScheduleId} run failed", scheduleId);
            return run;
        }
    }

    /// <summary>依排程通知欄位組裝訊息並呼叫 INotificationSender；未啟用或無 To 則 Skipped。</summary>
    async Task<string> TryNotifyAsync(Schedule schedule, ScheduleRun run, CancellationToken ct)
    {
        if (!schedule.NotifyEnabled)
            return "Skipped:NotifyDisabled";

        var to = SplitAddresses(schedule.EmailTo);
        if (to.Count == 0)
            return "Skipped:NoEmailTo";

        // 本機預設 Draft；即使設定成 Http，若未實作 Http sender 也不應偷偷外送
        var mode = _notifyOpts.Value.Mode ?? "Draft";
        if (!string.Equals(mode, "Draft", StringComparison.OrdinalIgnoreCase))
        {
            _log.LogWarning(
                "Notification Mode={Mode} 尚未啟用實發；強制改走 Draft（schedule={ScheduleId})",
                mode, schedule.Id);
        }

        var succeeded = run.Status == ScheduleRunStatus.Succeeded;
        var statusLabel = succeeded ? "Succeeded" : "Failed";
        var subject = $"{schedule.Title}-{statusLabel} Execute Status";
        var body = succeeded
            ? $"Schedule run succeeded. threadId={run.ThreadId}"
            : (run.Error ?? "Schedule run failed.");

        var message = new NotificationMessage(
            schedule.Id,
            run.Id,
            schedule.Title,
            schedule.Title,
            to,
            SplitAddresses(schedule.EmailCc),
            subject,
            body,
            succeeded,
            succeeded ? null : run.Error);

        var result = await _notify.SendAsync(message, ct);
        return result.Ok
            ? result.Summary
            : $"Failed:{result.Error ?? result.Summary}";
    }

    /// <summary>將逗號／分號分隔的信箱字串拆成清單。</summary>
    static IReadOnlyList<string> SplitAddresses(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            return Array.Empty<string>();
        return raw
            .Split([',', ';'], StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .Where(s => s.Length > 0)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
    }
}
