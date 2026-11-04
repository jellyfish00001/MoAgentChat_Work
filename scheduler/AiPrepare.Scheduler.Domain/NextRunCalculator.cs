namespace AiPrepare.Scheduler.Domain;

/// <summary>Pure next-fire calculation in Asia/Taipei wall clock (no I/O).</summary>
public static class NextRunCalculator
{
    public static DateTimeOffset ComputeNext(
        ScheduleKind kind,
        DateTimeOffset fromUtc,
        TimeOnly? timeOfDay,
        DayOfWeek? weekday,
        int? intervalHours,
        string timeZoneId = "Asia/Taipei")
    {
        var tz = ResolveTz(timeZoneId);
        var local = TimeZoneInfo.ConvertTime(fromUtc, tz);

        return kind switch
        {
            ScheduleKind.Daily => NextDaily(local, timeOfDay ?? new TimeOnly(9, 0), tz),
            ScheduleKind.Weekly => NextWeekly(local, timeOfDay ?? new TimeOnly(9, 0), weekday ?? DayOfWeek.Monday, tz),
            ScheduleKind.EveryNHours => NextEveryNHours(fromUtc, Math.Max(1, intervalHours ?? 1)),
            _ => fromUtc.AddHours(1),
        };
    }

    static TimeZoneInfo ResolveTz(string id)
    {
        try
        {
            return TimeZoneInfo.FindSystemTimeZoneById(id);
        }
        catch (TimeZoneNotFoundException)
        {
            // Windows often uses this id for Taipei
            return TimeZoneInfo.FindSystemTimeZoneById("Taipei Standard Time");
        }
    }

    static DateTimeOffset NextDaily(DateTimeOffset localNow, TimeOnly tod, TimeZoneInfo tz)
    {
        var candidate = new DateTimeOffset(
            localNow.Year, localNow.Month, localNow.Day,
            tod.Hour, tod.Minute, 0, localNow.Offset);
        if (candidate <= localNow)
            candidate = candidate.AddDays(1);
        return TimeZoneInfo.ConvertTime(candidate, TimeZoneInfo.Utc);
    }

    static DateTimeOffset NextWeekly(DateTimeOffset localNow, TimeOnly tod, DayOfWeek weekday, TimeZoneInfo tz)
    {
        var daysAhead = ((int)weekday - (int)localNow.DayOfWeek + 7) % 7;
        var day = localNow.Date.AddDays(daysAhead);
        var candidate = new DateTimeOffset(day.Year, day.Month, day.Day, tod.Hour, tod.Minute, 0, localNow.Offset);
        if (candidate <= localNow)
            candidate = candidate.AddDays(7);
        return TimeZoneInfo.ConvertTime(candidate, TimeZoneInfo.Utc);
    }

    static DateTimeOffset NextEveryNHours(DateTimeOffset fromUtc, int hours)
        => fromUtc.AddHours(hours);
}
