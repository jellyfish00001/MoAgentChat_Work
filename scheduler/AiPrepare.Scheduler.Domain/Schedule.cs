namespace AiPrepare.Scheduler.Domain;

/// <summary>排程列（個人或公司）；Hangfire 只掃到期列，系統僅一條 due-scanner。</summary>
public sealed class Schedule
{
    public Guid Id { get; set; }
    public string UserId { get; set; } = "";
    /// <summary>User＝個人可見；Company＝僅維運／內部 API，一般列表不回傳。</summary>
    public ScheduleScope Scope { get; set; } = ScheduleScope.User;
    public string Title { get; set; } = "";
    public string Prompt { get; set; } = "";
    public string AssistantId { get; set; } = "agent";
    public string ApiUrl { get; set; } = "http://127.0.0.1:2024";
    public ScheduleKind Kind { get; set; }
    public TimeOnly? TimeOfDay { get; set; }
    public DayOfWeek? Weekday { get; set; }
    public int? IntervalHours { get; set; }
    public string TimeZone { get; set; } = "Asia/Taipei";
    public bool Enabled { get; set; } = true;
    public DateTimeOffset NextRunAt { get; set; }
    public DateTimeOffset? LastRunAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }
}
