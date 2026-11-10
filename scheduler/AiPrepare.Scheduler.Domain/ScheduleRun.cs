namespace AiPrepare.Scheduler.Domain;

/// <summary>單次排程執行紀錄（對應一次 LangGraph thread；可附通知結果摘要）。</summary>
public sealed class ScheduleRun
{
    public Guid Id { get; set; }
    public Guid ScheduleId { get; set; }
    public ScheduleRunStatus Status { get; set; }
    public string? ThreadId { get; set; }
    public string? Error { get; set; }
    /// <summary>通知結果摘要（Skipped／Drafted／Failed…）；不實發時仍寫 Drafted 以利本機驗收。</summary>
    public string? NotifyOutcome { get; set; }
    public DateTimeOffset StartedAt { get; set; }
    public DateTimeOffset? FinishedAt { get; set; }
}
