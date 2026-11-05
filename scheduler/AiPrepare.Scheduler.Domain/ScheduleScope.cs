namespace AiPrepare.Scheduler.Domain;

/// <summary>排程可見／掃描範圍：個人或公司（公司不對一般使用者列表開放）。</summary>
public enum ScheduleScope
{
    User = 0,
    Company = 1,
}
