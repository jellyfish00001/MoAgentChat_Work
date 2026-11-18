namespace AiPrepare.Scheduler.Domain;

/// <summary>單次排程執行紀錄（對應一次 LangGraph thread；可附通知結果摘要）。</summary>
public sealed class ScheduleRun
{
    /// <summary>主鍵。</summary>
    public Guid Id { get; set; }

    /// <summary>所屬排程 Id。</summary>
    public Guid ScheduleId { get; set; }

    /// <summary>執行狀態。</summary>
    public ScheduleRunStatus Status { get; set; }

    /// <summary>LangGraph thread id。</summary>
    public string? ThreadId { get; set; }

    /// <summary>失敗訊息。</summary>
    public string? Error { get; set; }

    /// <summary>通知結果摘要（Skipped／Drafted／Failed…）；不實發時仍寫 Drafted 以利本機驗收。</summary>
    public string? NotifyOutcome { get; set; }

    /// <summary>開始時間（UTC）。</summary>
    public DateTimeOffset StartedAt { get; set; }

    /// <summary>結束時間（UTC）。</summary>
    public DateTimeOffset? FinishedAt { get; set; }
}
