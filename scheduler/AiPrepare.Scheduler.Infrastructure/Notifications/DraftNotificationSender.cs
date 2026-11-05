using AiPrepare.Scheduler.Application.Abstractions;
using Microsoft.Extensions.Logging;

namespace AiPrepare.Scheduler.Infrastructure.Notifications;

/// <summary>本機／預設通知實作：只寫 log，永不 HTTP 外送。</summary>
public sealed class DraftNotificationSender : INotificationSender
{
    private readonly ILogger<DraftNotificationSender> _log;

    /// <summary>注入結構化日誌。</summary>
    public DraftNotificationSender(ILogger<DraftNotificationSender> log) => _log = log;

    /// <summary>組成草稿摘要並記錄；回傳 Ok，證明管線有走到通知步驟。</summary>
    public Task<NotificationSendResult> SendAsync(NotificationMessage message, CancellationToken ct = default)
    {
        // 故意不呼叫外部；與 QV-03「僅草稿」同一精神，避免本機誤寄公司信箱
        var to = string.Join(",", message.To);
        var cc = string.Join(",", message.Cc);
        var summary =
            $"Draft:to={to};cc={cc};subject={message.Subject};ok={message.RunSucceeded}";

        _log.LogInformation(
            "Notification draft schedule={ScheduleId} run={RunId} to={To} cc={Cc} subject={Subject} body={Body}",
            message.ScheduleId,
            message.RunId,
            to,
            cc,
            message.Subject,
            message.Body);

        return Task.FromResult(new NotificationSendResult(true, "Draft", summary));
    }
}
