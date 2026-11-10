using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Domain.Tests;

/// <summary>NextRunCalculator 行為單測。</summary>
public class NextRunCalculatorTests
{
    /// <summary>每 N 小時應依間隔往前推。</summary>
    [Fact]
    public void EveryNHours_advances_by_interval()
    {
        var from = new DateTimeOffset(2026, 11, 4, 10, 0, 0, TimeSpan.Zero);
        var next = NextRunCalculator.ComputeNext(ScheduleKind.EveryNHours, from, null, null, 2);
        Assert.Equal(from.AddHours(2), next);
    }

    /// <summary>每日：當日時刻已過則落到明日之後。</summary>
    [Fact]
    public void Daily_moves_to_tomorrow_if_tod_passed()
    {
        var from = new DateTimeOffset(2026, 11, 4, 12, 0, 0, TimeSpan.Zero);
        var next = NextRunCalculator.ComputeNext(
            ScheduleKind.Daily, from, new TimeOnly(9, 0), null, null, "UTC");
        Assert.True(next > from);
    }
}
