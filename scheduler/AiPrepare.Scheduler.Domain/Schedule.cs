namespace AiPrepare.Scheduler.Domain;

/// <summary>排程列（個人或公司）；Hangfire 只掃到期列，系統僅一條 due-scanner。</summary>
public sealed class Schedule
{
    /// <summary>主鍵。</summary>
    public Guid Id { get; set; }

    /// <summary>擁有者；公司列常用 company。</summary>
    public string UserId { get; set; } = "";

    /// <summary>User＝個人可見；Company＝僅維運／內部 API，一般列表不回傳。</summary>
    public ScheduleScope Scope { get; set; } = ScheduleScope.User;

    /// <summary>標題（亦可當通知主旨前綴）。</summary>
    public string Title { get; set; } = "";

    /// <summary>送給 LangGraph 的 human message。</summary>
    public string Prompt { get; set; } = "";

    /// <summary>LangGraph assistant／graph id，預設 agent。</summary>
    public string AssistantId { get; set; } = "agent";

    /// <summary>LangGraph base URL。</summary>
    public string ApiUrl { get; set; } = "http://127.0.0.1:2024";

    /// <summary>週期種類。</summary>
    public ScheduleKind Kind { get; set; }

    /// <summary>日／週觸發的牆鐘時間。</summary>
    public TimeOnly? TimeOfDay { get; set; }

    /// <summary>每週觸發的星期（Weekly）。</summary>
    public DayOfWeek? Weekday { get; set; }

    /// <summary>每 N 小時觸發（EveryNHours）。</summary>
    public int? IntervalHours { get; set; }

    /// <summary>每月幾號（Monthly，1–31）。</summary>
    public int? DayOfMonth { get; set; }

    /// <summary>此排程的 Agent 寄信是否免逐封確認；預設關閉。</summary>
    public bool AutoSendMail { get; set; }

    /// <summary>計算下次執行用時區，預設 Asia/Taipei。</summary>
    public string TimeZone { get; set; } = "Asia/Taipei";

    /// <summary>是否納入 due 掃描。</summary>
    public bool Enabled { get; set; } = true;

    /// <summary>是否在執行結束後走通知管線（實際發送與否由 Notification:Mode 決定）。</summary>
    public bool NotifyEnabled { get; set; }

    /// <summary>收件者 To（逗號或分號分隔多位）；NotifyEnabled 時必填才會寄。</summary>
    public string? EmailTo { get; set; }

    /// <summary>副本 Cc（逗號或分號分隔多位）；可空。</summary>
    public string? EmailCc { get; set; }

    /// <summary>下次到期時間（UTC）。</summary>
    public DateTimeOffset NextRunAt { get; set; }

    /// <summary>上次執行結束時間（UTC）。</summary>
    public DateTimeOffset? LastRunAt { get; set; }

    /// <summary>建立時間（UTC）。</summary>
    public DateTimeOffset CreatedAt { get; set; }

    /// <summary>最後更新時間（UTC）。</summary>
    public DateTimeOffset UpdatedAt { get; set; }
}
