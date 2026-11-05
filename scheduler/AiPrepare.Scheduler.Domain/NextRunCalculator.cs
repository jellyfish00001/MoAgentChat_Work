namespace AiPrepare.Scheduler.Domain;

/// <summary>純計算下次觸發時間（Asia/Taipei 牆鐘；無 IO）。</summary>
public static class NextRunCalculator
{
    /// <summary>依排程種類計算下一次 UTC 觸發點。</summary>
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

    /// <summary>解析時區；Windows 可能沒有 IANA id 時改用台北標準時間。</summary>
    static TimeZoneInfo ResolveTz(string id)
    {
        try
        {
            return TimeZoneInfo.FindSystemTimeZoneById(id);
        }
        catch (TimeZoneNotFoundException)
        {
            return TimeZoneInfo.FindSystemTimeZoneById("Taipei Standard Time");
        }
    }

    /// <summary>每日：若今日時刻已過則加一天，再轉回 UTC。</summary>
    static DateTimeOffset NextDaily(DateTimeOffset localNow, TimeOnly tod, TimeZoneInfo tz)
    {
        var candidate = new DateTimeOffset(
            localNow.Year, localNow.Month, localNow.Day,
            tod.Hour, tod.Minute, 0, localNow.Offset);
        if (candidate <= localNow)
            candidate = candidate.AddDays(1);
        return TimeZoneInfo.ConvertTime(candidate, TimeZoneInfo.Utc);
    }

    /// <summary>每週：對齊目標星期；若已過則加七天。</summary>
    static DateTimeOffset NextWeekly(DateTimeOffset localNow, TimeOnly tod, DayOfWeek weekday, TimeZoneInfo tz)
    {
        var daysAhead = ((int)weekday - (int)localNow.DayOfWeek + 7) % 7;
        var day = localNow.Date.AddDays(daysAhead);
        var candidate = new DateTimeOffset(day.Year, day.Month, day.Day, tod.Hour, tod.Minute, 0, localNow.Offset);
        if (candidate <= localNow)
            candidate = candidate.AddDays(7);
        return TimeZoneInfo.ConvertTime(candidate, TimeZoneInfo.Utc);
    }

    /// <summary>固定間隔小時（以 UTC 加法，不綁牆鐘）。</summary>
    static DateTimeOffset NextEveryNHours(DateTimeOffset fromUtc, int hours)
        => fromUtc.AddHours(hours);
}
