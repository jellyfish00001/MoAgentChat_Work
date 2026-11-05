using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Abstractions;

/// <summary>排程與執行紀錄仓储合約（Application 不依賴 EF）。</summary>
public interface IScheduleRepository
{
    /// <summary>依 Id 取得排程。</summary>
    Task<Schedule?> GetAsync(Guid id, CancellationToken ct = default);

    /// <summary>依使用者列出個人排程（僅 Scope=User）。</summary>
    Task<IReadOnlyList<Schedule>> ListByUserAsync(string userId, CancellationToken ct = default);

    /// <summary>列出全部公司排程（Scope=Company）。</summary>
    Task<IReadOnlyList<Schedule>> ListCompanyAsync(CancellationToken ct = default);

    /// <summary>新增排程。</summary>
    Task AddAsync(Schedule schedule, CancellationToken ct = default);

    /// <summary>更新排程。</summary>
    Task UpdateAsync(Schedule schedule, CancellationToken ct = default);

    /// <summary>刪除排程。</summary>
    Task DeleteAsync(Guid id, CancellationToken ct = default);

    /// <summary>列出到期且啟用的排程；includeCompany=false 時略過公司列。</summary>
    Task<IReadOnlyList<Schedule>> ListDueAsync(
        DateTimeOffset untilUtc,
        bool includeCompany,
        CancellationToken ct = default);

    /// <summary>取得單筆執行紀錄。</summary>
    Task<ScheduleRun?> GetRunAsync(Guid runId, CancellationToken ct = default);

    /// <summary>新增執行紀錄。</summary>
    Task AddRunAsync(ScheduleRun run, CancellationToken ct = default);

    /// <summary>更新執行紀錄。</summary>
    Task UpdateRunAsync(ScheduleRun run, CancellationToken ct = default);

    /// <summary>最近一次執行。</summary>
    Task<ScheduleRun?> GetLatestRunAsync(Guid scheduleId, CancellationToken ct = default);

    /// <summary>某排程全部執行紀錄。</summary>
    Task<IReadOnlyList<ScheduleRun>> ListRunsAsync(Guid scheduleId, CancellationToken ct = default);
}
