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
    public int? DayOfMonth { get; set; }
    /// <summary>此排程的 Agent 寄信是否免逐封確認；預設關閉。</summary>
    public bool AutoSendMail { get; set; }
    public string TimeZone { get; set; } = "Asia/Taipei";
    public bool Enabled { get; set; } = true;
    /// <summary>是否在執行結束後走通知管線（實際發送與否由 Notification:Mode 決定）。</summary>
    public bool NotifyEnabled { get; set; }
    /// <summary>收件者 To（逗號或分號分隔多位）；NotifyEnabled 時必填才會寄。</summary>
    public string? EmailTo { get; set; }
    /// <summary>副本 Cc（逗號或分號分隔多位）；可空。</summary>
    public string? EmailCc { get; set; }
    public DateTimeOffset NextRunAt { get; set; }
    public DateTimeOffset? LastRunAt { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset UpdatedAt { get; set; }
}
