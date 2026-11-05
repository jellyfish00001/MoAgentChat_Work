namespace AiPrepare.Scheduler.Domain;

/// <summary>單次執行狀態。</summary>
public enum ScheduleRunStatus
{
    Pending = 0,
    Running = 1,
    Succeeded = 2,
    Failed = 3,
}
