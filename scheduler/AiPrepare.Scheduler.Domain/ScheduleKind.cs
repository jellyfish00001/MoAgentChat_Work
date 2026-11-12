namespace AiPrepare.Scheduler.Domain;

/// <summary>週期：每日／每週／每 N 小時／每月；既有數值維持不變。</summary>
public enum ScheduleKind
{
    Daily = 0,
    Weekly = 1,
    EveryNHours = 2,
    Monthly = 3,
}
