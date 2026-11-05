using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Application.Dtos;
using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application;

/// <summary>排程 CRUD／到期列表；本身不呼叫 LangGraph。</summary>
public sealed class ScheduleService
{
    private readonly IScheduleRepository _repo;

    /// <summary>注入排程仓储。</summary>
    public ScheduleService(IScheduleRepository repo) => _repo = repo;

    /// <summary>建立排程並計算首次 NextRunAt。</summary>
    public async Task<ScheduleDto> CreateAsync(CreateScheduleRequest req, CancellationToken ct = default)
    {
        var now = DateTimeOffset.UtcNow;
        var schedule = new Schedule
        {
            Id = Guid.NewGuid(),
            UserId = req.UserId,
            Title = req.Title.Trim(),
            Prompt = req.Prompt,
            AssistantId = string.IsNullOrWhiteSpace(req.AssistantId) ? "agent" : req.AssistantId!,
            ApiUrl = string.IsNullOrWhiteSpace(req.ApiUrl) ? "http://127.0.0.1:2024" : req.ApiUrl!,
            Kind = req.Kind,
            TimeOfDay = req.TimeOfDay,
            Weekday = req.Weekday,
            IntervalHours = req.IntervalHours,
            Enabled = true,
            CreatedAt = now,
            UpdatedAt = now,
            // 以台北牆鐘規則算出下次觸發，寫入 UTC
            NextRunAt = NextRunCalculator.ComputeNext(
                req.Kind, now, req.TimeOfDay, req.Weekday, req.IntervalHours),
        };
        await _repo.AddAsync(schedule, ct);
        return await ToDtoAsync(schedule, ct);
    }

    /// <summary>依使用者列出排程（含最近一次 thread）。</summary>
    public async Task<IReadOnlyList<ScheduleDto>> ListAsync(string userId, CancellationToken ct = default)
    {
        var list = await _repo.ListByUserAsync(userId, ct);
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
        if (req.Title is not null) s.Title = req.Title.Trim();
        if (req.Prompt is not null) s.Prompt = req.Prompt;
        if (req.Enabled is not null) s.Enabled = req.Enabled.Value;
        if (req.Kind is not null) s.Kind = req.Kind.Value;
        if (req.TimeOfDay is not null) s.TimeOfDay = req.TimeOfDay;
        if (req.Weekday is not null) s.Weekday = req.Weekday;
        if (req.IntervalHours is not null) s.IntervalHours = req.IntervalHours;
        s.UpdatedAt = DateTimeOffset.UtcNow;
        s.NextRunAt = NextRunCalculator.ComputeNext(
            s.Kind, DateTimeOffset.UtcNow, s.TimeOfDay, s.Weekday, s.IntervalHours);
        await _repo.UpdateAsync(s, ct);
        return await ToDtoAsync(s, ct);
    }

    /// <summary>刪除排程列。</summary>
    public Task DeleteAsync(Guid id, CancellationToken ct = default) => _repo.DeleteAsync(id, ct);

    /// <summary>列出到期實體（給 internal／除錯用）。</summary>
    public Task<IReadOnlyList<Schedule>> ListDueEntitiesAsync(DateTimeOffset untilUtc, CancellationToken ct = default)
        => _repo.ListDueAsync(untilUtc, ct);

    /// <summary>列出某排程的執行紀錄。</summary>
    public async Task<IReadOnlyList<ScheduleRunDto>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var runs = await _repo.ListRunsAsync(scheduleId, ct);
        return runs.Select(r => new ScheduleRunDto(
            r.Id, r.ScheduleId, r.Status, r.ThreadId, r.Error, r.StartedAt, r.FinishedAt)).ToList();
    }

    /// <summary>組裝 API DTO，並附上最近一次成功／失敗的 threadId。</summary>
    async Task<ScheduleDto> ToDtoAsync(Schedule s, CancellationToken ct)
    {
        var last = await _repo.GetLatestRunAsync(s.Id, ct);
        return new ScheduleDto(
            s.Id, s.UserId, s.Title, s.Prompt, s.AssistantId, s.ApiUrl, s.Kind,
            s.TimeOfDay, s.Weekday, s.IntervalHours, s.Enabled, s.NextRunAt, s.LastRunAt,
            last?.ThreadId);
    }
}
