using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

public sealed class EfScheduleRepository : IScheduleRepository
{
    private readonly SchedulerDbContext _db;

    public EfScheduleRepository(SchedulerDbContext db) => _db = db;

    public Task<Schedule?> GetAsync(Guid id, CancellationToken ct = default)
        => _db.Schedules.AsNoTracking().FirstOrDefaultAsync(x => x.Id == id, ct);

    public async Task<IReadOnlyList<Schedule>> ListByUserAsync(string userId, CancellationToken ct = default)
    {
        // SQLite provider cannot ORDER BY DateTimeOffset in SQL — sort in memory.
        var rows = await _db.Schedules.AsNoTracking()
            .Where(x => x.UserId == userId)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.UpdatedAt).ToList();
    }

    public async Task AddAsync(Schedule schedule, CancellationToken ct = default)
    {
        _db.Schedules.Add(schedule);
        await _db.SaveChangesAsync(ct);
    }

    public async Task UpdateAsync(Schedule schedule, CancellationToken ct = default)
    {
        _db.Schedules.Update(schedule);
        await _db.SaveChangesAsync(ct);
    }

    public async Task DeleteAsync(Guid id, CancellationToken ct = default)
    {
        var s = await _db.Schedules.FindAsync([id], ct);
        if (s is null) return;
        _db.Schedules.Remove(s);
        await _db.SaveChangesAsync(ct);
    }

    public async Task<IReadOnlyList<Schedule>> ListDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default)
    {
        // SQLite cannot translate DateTimeOffset comparisons — filter in memory.
        var rows = await _db.Schedules.Where(x => x.Enabled).ToListAsync(ct);
        return rows.Where(x => x.NextRunAt <= untilUtc).OrderBy(x => x.NextRunAt).ToList();
    }

    public Task<ScheduleRun?> GetRunAsync(Guid runId, CancellationToken ct = default)
        => _db.ScheduleRuns.AsNoTracking().FirstOrDefaultAsync(x => x.Id == runId, ct);

    public async Task AddRunAsync(ScheduleRun run, CancellationToken ct = default)
    {
        _db.ScheduleRuns.Add(run);
        await _db.SaveChangesAsync(ct);
    }

    public async Task UpdateRunAsync(ScheduleRun run, CancellationToken ct = default)
    {
        _db.ScheduleRuns.Update(run);
        await _db.SaveChangesAsync(ct);
    }

    public async Task<ScheduleRun?> GetLatestRunAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var rows = await _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.StartedAt).FirstOrDefault();
    }

    public async Task<IReadOnlyList<ScheduleRun>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default)
    {
        var rows = await _db.ScheduleRuns.AsNoTracking()
            .Where(x => x.ScheduleId == scheduleId)
            .ToListAsync(ct);
        return rows.OrderByDescending(x => x.StartedAt).ToList();
    }
}
