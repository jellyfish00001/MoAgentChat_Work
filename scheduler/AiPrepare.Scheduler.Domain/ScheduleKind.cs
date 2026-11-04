namespace AiPrepare.Scheduler.Domain;

/// <summary>Fixed MVP schedule presets (not free-form cron).</summary>
public enum ScheduleKind
{
    Daily = 0,
    Weekly = 1,
    EveryNHours = 2,
}
