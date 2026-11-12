using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Application.Dtos;
using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application;

/// <summary>排程 CRUD／到期列表；本身不呼叫 LangGraph。</summary>
public sealed class ScheduleService
{
    /// <summary>公司排程固定 UserId（僅 metadata／歸屬，非可見擁有者）。</summary>
    public const string CompanyUserId = "company";

    private readonly IScheduleRepository _repo;
    private readonly ILangGraphClient _lg;

    /// <summary>注入排程仓储。</summary>
    public ScheduleService(IScheduleRepository repo, ILangGraphClient lg)
    {
        _repo = repo;
        _lg = lg;
    }

    /// <summary>建立個人排程（強制 Scope=User）並計算首次 NextRunAt。</summary>
    public async Task<ScheduleDto> CreateAsync(CreateScheduleRequest req, CancellationToken ct = default)
    {
        var schedule = BuildSchedule(req, ScheduleScope.User, req.UserId);
        await _repo.AddAsync(schedule, ct);
        return await ToDtoAsync(schedule, ct);
    }

    /// <summary>建立公司排程（Scope=Company；UserId 預設 company）。</summary>
    public async Task<ScheduleDto> CreateCompanyAsync(CreateScheduleRequest req, CancellationToken ct = default)
    {
        var userId = string.IsNullOrWhiteSpace(req.UserId) ? CompanyUserId : req.UserId.Trim();
        var schedule = BuildSchedule(req, ScheduleScope.Company, userId);
        await _repo.AddAsync(schedule, ct);
        return await ToDtoAsync(schedule, ct);
    }

    /// <summary>依使用者列出個人排程（含最近一次 thread；不含公司列）。</summary>
    public async Task<IReadOnlyList<ScheduleDto>> ListAsync(string userId, CancellationToken ct = default)
    {
        var list = await _repo.ListByUserAsync(userId, ct);
        var result = new List<ScheduleDto>();
        foreach (var s in list)
            result.Add(await ToDtoAsync(s, ct));
        return result;
    }

    /// <summary>列出全部公司排程（維運／internal）。</summary>
    public async Task<IReadOnlyList<ScheduleDto>> ListCompanyAsync(CancellationToken ct = default)
    {
        var list = await _repo.ListCompanyAsync(ct);
        var result = new List<ScheduleDto>();
        foreach (var s in list)
            result.Add(await ToDtoAsync(s, ct));
        return result;
    }

    /// <summary>取得單一排程；不存在回傳 null。</summary>
    public async Task<ScheduleDto?> GetAsync(Guid id, CancellationToken ct = default)
    {
        var s = await _repo.GetAsync(id, ct);
        return s is null ? null : await ToDtoAsync(s, ct);
    }

    /// <summary>部分更新；變更週期欄位時重算 NextRunAt。</summary>
    public async Task<ScheduleDto?> PatchAsync(Guid id, PatchScheduleRequest req, CancellationToken ct = default)
    {
        var s = await _repo.GetAsync(id, ct);
        if (s is null) return null;
        ValidateMonthly(req.Kind ?? s.Kind, req.DayOfMonth ?? s.DayOfMonth);
        if (req.Title is not null) s.Title = req.Title.Trim();
        if (req.Prompt is not null) s.Prompt = req.Prompt;
        if (req.Enabled is not null) s.Enabled = req.Enabled.Value;
        if (req.Kind is not null) s.Kind = req.Kind.Value;
        if (req.TimeOfDay is not null) s.TimeOfDay = req.TimeOfDay;
        if (req.Weekday is not null) s.Weekday = req.Weekday;
        if (req.IntervalHours is not null) s.IntervalHours = req.IntervalHours;
        if (req.DayOfMonth is not null) s.DayOfMonth = req.DayOfMonth;
        if (req.AutoSendMail is not null) s.AutoSendMail = req.AutoSendMail.Value;
        if (req.NotifyEnabled is not null) s.NotifyEnabled = req.NotifyEnabled.Value;
        if (req.EmailTo is not null) s.EmailTo = NormalizeAddresses(req.EmailTo);
        if (req.EmailCc is not null) s.EmailCc = NormalizeAddresses(req.EmailCc);
        s.UpdatedAt = DateTimeOffset.UtcNow;
        s.NextRunAt = NextRunCalculator.ComputeNext(
            s.Kind, DateTimeOffset.UtcNow, s.TimeOfDay, s.Weekday, s.IntervalHours,
            s.TimeZone, s.DayOfMonth);
        await _repo.UpdateAsync(s, ct);
        return await ToDtoAsync(s, ct);
    }

    /// <summary>刪除排程列。</summary>
    public Task DeleteAsync(Guid id, CancellationToken ct = default) => _repo.DeleteAsync(id, ct);

    /// <summary>列出到期實體（給 internal／除錯用）。</summary>
    public Task<IReadOnlyList<Schedule>> ListDueEntitiesAsync(
        DateTimeOffset untilUtc,
        bool includeCompany,
        CancellationToken ct = default)
        => _repo.ListDueAsync(untilUtc, includeCompany, ct);

    /// <summary>列出某排程的執行紀錄。</summary>
    public async Task<IReadOnlyList<ScheduleRunDto>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var runs = await _repo.ListRunsAsync(scheduleId, ct);
        var schedule = await _repo.GetAsync(scheduleId, ct);
        if (schedule is not null)
            foreach (var run in runs)
                await RefreshWaitingRunAsync(schedule, run, ct);
        return runs.Select(r => new ScheduleRunDto(
            r.Id, r.ScheduleId, r.Status, r.ThreadId, r.Error, r.NotifyOutcome, r.StartedAt, r.FinishedAt)).ToList();
    }

    /// <summary>組裝實體列（公開與公司建立共用）。</summary>
    static Schedule BuildSchedule(CreateScheduleRequest req, ScheduleScope scope, string userId)
    {
        var now = DateTimeOffset.UtcNow;
        ValidateMonthly(req.Kind, req.DayOfMonth);
        return new Schedule
        {
            Id = Guid.NewGuid(),
            UserId = userId,
            Scope = scope,
            Title = req.Title.Trim(),
            Prompt = req.Prompt,
            AssistantId = string.IsNullOrWhiteSpace(req.AssistantId) ? "agent" : req.AssistantId!,
            ApiUrl = string.IsNullOrWhiteSpace(req.ApiUrl) ? "http://127.0.0.1:2024" : req.ApiUrl!,
            Kind = req.Kind,
            TimeOfDay = req.TimeOfDay,
            Weekday = req.Weekday,
            IntervalHours = req.IntervalHours,
            DayOfMonth = req.DayOfMonth,
            AutoSendMail = req.AutoSendMail,
            NotifyEnabled = req.NotifyEnabled,
            EmailTo = NormalizeAddresses(req.EmailTo),
            EmailCc = NormalizeAddresses(req.EmailCc),
            Enabled = true,
            CreatedAt = now,
            UpdatedAt = now,
            // 以台北牆鐘規則算出下次觸發，寫入 UTC
            NextRunAt = NextRunCalculator.ComputeNext(
                req.Kind, now, req.TimeOfDay, req.Weekday, req.IntervalHours,
                dayOfMonth: req.DayOfMonth),
        };
    }

    /// <summary>組裝 API DTO，並附上最近一次成功／失敗的 threadId。</summary>
    async Task<ScheduleDto> ToDtoAsync(Schedule s, CancellationToken ct)
    {
        var last = await _repo.GetLatestRunAsync(s.Id, ct);
        if (last is not null)
            await RefreshWaitingRunAsync(s, last, ct);
        return new ScheduleDto(
            s.Id, s.UserId, s.Scope, s.Title, s.Prompt, s.AssistantId, s.ApiUrl, s.Kind,
            s.TimeOfDay, s.Weekday, s.IntervalHours, s.Enabled,
            s.NotifyEnabled, s.EmailTo, s.EmailCc,
            s.NextRunAt, s.LastRunAt, last?.ThreadId, s.DayOfMonth, s.AutoSendMail);
    }

    /// <summary>拒絕超出月份日期範圍的設定，不允許默默修正輸入。</summary>
    static void ValidateMonthly(ScheduleKind kind, int? day)
    {
        if (!Enum.IsDefined(kind))
            throw new ArgumentException("不支援的排程週期。");
        if (kind == ScheduleKind.Monthly && day is < 1 or > 31)
            throw new ArgumentException("每月日期必須介於 1 與 31。");
    }

    /// <summary>使用者在原對話確認後，查詢紀錄時同步完成狀態；連線失敗不冒稱完成。</summary>
    async Task RefreshWaitingRunAsync(Schedule schedule, ScheduleRun run, CancellationToken ct)
    {
        if (run.Status != ScheduleRunStatus.WaitingForConfirmation || run.ThreadId is null)
            return;
        var result = await _lg.GetThreadResultAsync(schedule.ApiUrl, run.ThreadId, ct);
        if (!result.Ok || result.WaitingForConfirmation)
            return;
        run.Status = ScheduleRunStatus.Succeeded;
        run.FinishedAt = DateTimeOffset.UtcNow;
        await _repo.UpdateRunAsync(run, ct);
    }

    /// <summary>正規化 To／Cc：trim；空白則存 null。</summary>
    static string? NormalizeAddresses(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return null;
        var trimmed = raw.Trim();
        return trimmed.Length == 0 ? null : trimmed;
    }
}
