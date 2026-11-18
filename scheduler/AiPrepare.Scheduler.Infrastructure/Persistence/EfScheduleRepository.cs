using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

/// <summary>PostgreSQL EF 仓储；DateTimeOffset 比較／排序交由 SQL 下推。</summary>
public sealed class EfScheduleRepository : IScheduleRepository
{
    private readonly SchedulerDbContext _db;

    /// <summary>注入 DbContext。</summary>
    public EfScheduleRepository(SchedulerDbContext db) => _db = db;

    /// <summary>依 Id 取得排程（無追蹤）。</summary>
    public Task<Schedule?> GetAsync(Guid id, CancellationToken ct = default)
        => _db.Schedules.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, ct);

    /// <summary>依使用者列出個人排程；依 UpdatedAt 降序。</summary>
    public async Task<IReadOnlyList<Schedule>> ListByUserAsync(string userId, CancellationToken ct = default)
        => await _db.Schedules.AsNoTracking()
            .Where(x => x.UserId == userId && x.Scope == ScheduleScope.User)
            .OrderByDescending(x => x.UpdatedAt)
            .ToListAsync(ct);

    /// <summary>列出公司排程；依 UpdatedAt 降序。</summary>
    public async Task<IReadOnlyList<Schedule>> ListCompanyAsync(CancellationToken ct = default)
        => await _db.Schedules.AsNoTracking()
            .Where(x => x.Scope == ScheduleScope.Company)
            .OrderByDescending(x => x.UpdatedAt)
            .ToListAsync(ct);

    /// <summary>新增排程列。</summary>
    public async Task AddAsync(Schedule schedule, CancellationToken ct = default)
    {
        _db.Schedules.Add(schedule);
        await _db.SaveChangesAsync(ct);
    }

    /// <summary>更新排程列。</summary>
    public async Task UpdateAsync(Schedule schedule, CancellationToken ct = default)
    {
        _db.Schedules.Update(schedule);
        await _db.SaveChangesAsync(ct);
    }

    /// <summary>刪除排程列（不存在則略過）。</summary>
    public async Task DeleteAsync(Guid id, CancellationToken ct = default)
    {
        var s = await _db.Schedules.FindAsync([id], ct);
        if (s is null) return;
        _db.Schedules.Remove(s);
        await _db.SaveChangesAsync(ct);
    }

    /// <summary>列出已啟用且 NextRunAt &lt;= until 的到期列；可選擇是否含公司。</summary>
    public async Task<IReadOnlyList<Schedule>> ListDueAsync(
        DateTimeOffset untilUtc,
        bool includeCompany,
        CancellationToken ct = default)
    {
        // AsNoTracking：Executor 之後會用 GetAsync 取另一個實例再 Update，避免追蹤 Id 衝突
        var q = _db.Schedules.AsNoTracking()
            .Where(x => x.Enabled && x.NextRunAt <= untilUtc);
        if (!includeCompany)
            q = q.Where(x => x.Scope == ScheduleScope.User);
        return await q.OrderBy(x => x.NextRunAt).ToListAsync(ct);
    }

    /// <summary>依 Id 取得執行紀錄。</summary>
    public Task<ScheduleRun?> GetRunAsync(Guid runId, CancellationToken ct = default)
        => _db.ScheduleRuns.AsNoTracking().FirstOrDefaultAsync(x => x.Id == runId, ct);

    /// <summary>新增執行紀錄。</summary>
    public async Task AddRunAsync(ScheduleRun run, CancellationToken ct = default)
    {
        _db.ScheduleRuns.Add(run);
        await _db.SaveChangesAsync(ct);
    }

    /// <summary>更新執行紀錄。</summary>
    public async Task UpdateRunAsync(ScheduleRun run, CancellationToken ct = default)
    {
        _db.ScheduleRuns.Update(run);
        await _db.SaveChangesAsync(ct);
    }

    /// <summary>最近一次執行（依 StartedAt）。</summary>
    public Task<ScheduleRun?> GetLatestRunAsync(Guid scheduleId, CancellationToken ct = default)
        => _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .OrderByDescending(x => x.StartedAt)
            .FirstOrDefaultAsync(ct);

    /// <summary>某排程全部執行紀錄（新到舊）。</summary>
    public async Task<IReadOnlyList<ScheduleRun>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default)
        => await _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .OrderByDescending(x => x.StartedAt)
            .ToListAsync(ct);
}
