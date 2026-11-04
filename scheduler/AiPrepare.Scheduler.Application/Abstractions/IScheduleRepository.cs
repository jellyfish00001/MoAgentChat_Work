using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Abstractions;

public interface IScheduleRepository
{
    Task<Schedule?> GetAsync(Guid id, CancellationToken ct = default);
    Task<IReadOnlyList<Schedule>> ListByUserAsync(string userId, CancellationToken ct = default);
    Task AddAsync(Schedule schedule, CancellationToken ct = default);
    Task UpdateAsync(Schedule schedule, CancellationToken ct = default);
    Task DeleteAsync(Guid id, CancellationToken ct = default);
    Task<IReadOnlyList<Schedule>> ListDueAsync(DateTimeOffset untilUtc, CancellationToken ct = default);
    Task<ScheduleRun?> GetRunAsync(Guid runId, CancellationToken ct = default);
    Task AddRunAsync(ScheduleRun run, CancellationToken ct = default);
    Task UpdateRunAsync(ScheduleRun run, CancellationToken ct = default);
    Task<ScheduleRun?> GetLatestRunAsync(Guid scheduleId, CancellationToken ct = default);
    Task<IReadOnlyList<ScheduleRun>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default);
}
