using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

/// <summary>SQLite EF 仓储；DateTimeOffset 比較／排序在記憶體完成（provider 限制）。</summary>
public sealed class EfScheduleRepository : IScheduleRepository
{
    private readonly SchedulerDbContext _db;

    /// <summary>注入 DbContext。</summary>
    public EfScheduleRepository(SchedulerDbContext db) => _db = db;

    /// <summary>依 Id 取得排程（無追蹤）。</summary>
    public Task<Schedule?> GetAsync(Guid id, CancellationToken ct = default)
        => _db.Schedules.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, ct);

    /// <summary>依使用者列出個人排程；記憶體依 UpdatedAt 降序。</summary>
    public async Task<IReadOnlyList<Schedule>> ListByUserAsync(string userId, CancellationToken ct = default)
    {
        // SQLite 無法在 SQL 對 DateTimeOffset ORDER BY；且必須排除公司列
        var rows = await _db.Schedules.AsNoTracking()
            .Where(x => x.UserId == userId && x.Scope == ScheduleScope.User)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.UpdatedAt).ToList();
    }

    /// <summary>列出公司排程；記憶體依 UpdatedAt 降序。</summary>
    public async Task<IReadOnlyList<Schedule>> ListCompanyAsync(CancellationToken ct = default)
    {
        var rows = await _db.Schedules.AsNoTracking()
            .Where(x => x.Scope == ScheduleScope.Company)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.UpdatedAt).ToList();
    }

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
        // SQLite 無法轉譯 DateTimeOffset 比較 → 先載入 Enabled 再篩選
        // 必須 AsNoTracking：Executor 之後會用 GetAsync 取另一個實例再 Update，若這裡有追蹤會 Id 衝突
        var rows = await _db.Schedules.AsNoTracking().Where(x => x.Enabled).ToListAsync(ct);
        return rows
            .Where(x => x.NextRunAt <= untilUtc)
            .Where(x => includeCompany || x.Scope == ScheduleScope.User)
            .OrderBy(x => x.NextRunAt)
            .ToList();
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
    public async Task<ScheduleRun?> GetLatestRunAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var rows = await _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.StartedAt).FirstOrDefault();
    }

    /// <summary>某排程全部執行紀錄（新到舊）。</summary>
    public async Task<IReadOnlyList<ScheduleRun>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var rows = await _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.StartedAt).ToList();
    }
}
