namespace AiPrepare.Scheduler.Domain;

/// <summary>單次排程執行紀錄（對應一次 LangGraph thread）。</summary>
public sealed class ScheduleRun
{
    public Guid Id { get; set; }
    public Guid ScheduleId { get; set; }
    public ScheduleRunStatus Status { get; set; }
    public string? ThreadId { get; set; }
    public string? Error { get; set; }
    public DateTimeOffset StartedAt { get; set; }
    public DateTimeOffset? FinishedAt { get; set; }
}
