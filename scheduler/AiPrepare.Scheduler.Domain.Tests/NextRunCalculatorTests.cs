using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Domain.Tests;

/// <summary>NextRunCalculator 行為單測。</summary>
public class NextRunCalculatorTests
{
    /// <summary>每月 31 日以月底執行，隔月仍回到 31 日。</summary>
    [Fact]
    public void Monthly_clamps_to_month_end_without_drift()
    {
        var january = new DateTimeOffset(2026, 1, 31, 10, 0, 0, TimeSpan.Zero);
        var february = NextRunCalculator.ComputeNext(
            ScheduleKind.Monthly, january, new TimeOnly(9, 0), null, null, "UTC", 31);
        Assert.Equal(new DateTimeOffset(2026, 2, 28, 9, 0, 0, TimeSpan.Zero), february);
        var march = NextRunCalculator.ComputeNext(
            ScheduleKind.Monthly, february, new TimeOnly(9, 0), null, null, "UTC", 31);
        Assert.Equal(new DateTimeOffset(2026, 3, 31, 9, 0, 0, TimeSpan.Zero), march);
    }

    /// <summary>每月支援閏年、台北時區以及當月尚未到時刻。</summary>
    [Theory]
    [InlineData(2028, 2, 1, 31, 29)]
    [InlineData(2026, 11, 1, 12, 12)]
    public void Monthly_uses_taipei_wall_clock(int year, int month, int fromDay, int requested, int expected)
    {
        var from = new DateTimeOffset(year, month, fromDay, 0, 0, 0, TimeSpan.FromHours(8));
        var next = NextRunCalculator.ComputeNext(
            ScheduleKind.Monthly, from, new TimeOnly(9, 0), null, null, dayOfMonth: requested);
        Assert.Equal(new DateTimeOffset(year, month, expected, 1, 0, 0, TimeSpan.Zero), next);
    }

    /// <summary>日期非法時明確報錯。</summary>
    [Theory]
    [InlineData(0)]
    [InlineData(32)]
    public void Monthly_rejects_invalid_day(int day)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => NextRunCalculator.ComputeNext(
            ScheduleKind.Monthly, DateTimeOffset.UtcNow, null, null, null, dayOfMonth: day));
    }

    /// <summary>既有排程預設不自動寄信。</summary>
    [Fact]
    public void Auto_send_mail_defaults_off()
    {
        Assert.False(new Schedule().AutoSendMail);
    }

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
