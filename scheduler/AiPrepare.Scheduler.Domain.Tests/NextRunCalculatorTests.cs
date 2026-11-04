using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Domain.Tests;

public class NextRunCalculatorTests
{
    [Fact]
    public void EveryNHours_advances_by_interval()
    {
        var from = new DateTimeOffset(2026, 11, 4, 10, 0, 0, TimeSpan.Zero);
        var next = NextRunCalculator.ComputeNext(ScheduleKind.EveryNHours, from, null, null, 2);
        Assert.Equal(from.AddHours(2), next);
    }

    [Fact]
    public void Daily_moves_to_tomorrow_if_tod_passed()
    {
        var from = new DateTimeOffset(2026, 11, 4, 12, 0, 0, TimeSpan.Zero);
        var next = NextRunCalculator.ComputeNext(
            ScheduleKind.Daily, from, new TimeOnly(9, 0), null, null, "UTC");
        Assert.True(next > from);
    }
}
