namespace AiPrepare.Scheduler.Domain;

/// <summary>User-owned schedule row; Hangfire only scans due rows, one system job.</summary>
public sealed class Schedule
{
    public Guid Id { get; set; }
    public string UserId { get; set; } = "";
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
