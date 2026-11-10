namespace AiPrepare.Scheduler.Application;

/// <summary>通知通道設定；本機固定 Draft，正式才改 Http 並填 InvokeUrl。</summary>
public sealed class NotificationOptions
{
    public const string SectionName = "Notification";

    /// <summary>Draft＝不實發（預設）；Http＝打 Logic App（正式／明確開啟才用）。</summary>
    public string Mode { get; set; } = "Draft";

    /// <summary>Logic App invoke URL（含 sig）；僅 Mode=Http 使用，勿寫進文件或 git。</summary>
    public string? InvokeUrl { get; set; }
}
