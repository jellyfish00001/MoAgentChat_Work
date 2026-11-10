namespace AiPrepare.Scheduler.Application;

/// <summary>公司排程週期掃描開關；false 時 due-scanner 跳過 Scope=Company（run-now 不受影響）。</summary>
public sealed class CompanySchedulesOptions
{
    public const string SectionName = "CompanySchedules";

    /// <summary>是否將公司排程納入到期掃描；可用環境變數 COMPANY_SCHEDULES_ENABLED 覆寫。</summary>
    public bool Enabled { get; set; } = true;
}
