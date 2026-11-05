namespace AiPrepare.Scheduler.Domain;

/// <summary>固定三種週期：每日／每週／每 N 小時。</summary>
public enum ScheduleKind
{
    Daily = 0,
    Weekly = 1,
    EveryNHours = 2,
}
