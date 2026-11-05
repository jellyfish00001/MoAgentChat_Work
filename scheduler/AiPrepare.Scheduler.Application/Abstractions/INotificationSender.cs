namespace AiPrepare.Scheduler.Application.Abstractions;

/// <summary>排程結束後的郵件／通知發送介面；本機預設 Draft，不打外部 Logic App。</summary>
public interface INotificationSender
{
    /// <summary>送出一則通知；Mode=Draft 時只記錄、不實際寄信。</summary>
    Task<NotificationSendResult> SendAsync(NotificationMessage message, CancellationToken ct = default);
}

/// <summary>通知內容（對齊 Logic App 常見欄位：To／Cc／主旨／內文）。</summary>
public sealed record NotificationMessage(
    Guid ScheduleId,
    Guid RunId,
    string Title,
    string PipelineName,
    IReadOnlyList<string> To,
    IReadOnlyList<string> Cc,
    string Subject,
    string Body,
    bool RunSucceeded,
    string? ErrorMessage);

/// <summary>發送結果；Draft 時 Ok=true 且 Mode=Draft。</summary>
public sealed record NotificationSendResult(
    bool Ok,
    string Mode,
    string Summary,
    string? Error = null);
