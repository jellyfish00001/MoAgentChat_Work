using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Dtos;

/// <summary>建立排程請求。</summary>
public sealed record CreateScheduleRequest(
    string UserId,
    string Title,
    string Prompt,
    ScheduleKind Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours,
    string? AssistantId = null,
    string? ApiUrl = null);

/// <summary>部分更新請求（null 表示不改）。</summary>
public sealed record PatchScheduleRequest(
    string? Title,
    string? Prompt,
    bool? Enabled,
    ScheduleKind? Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours);

/// <summary>排程 API 回應（含最近 thread）。</summary>
public sealed record ScheduleDto(
    Guid Id,
    string UserId,
    string Title,
    string Prompt,
    string AssistantId,
    string ApiUrl,
    ScheduleKind Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours,
    bool Enabled,
    DateTimeOffset NextRunAt,
    DateTimeOffset? LastRunAt,
    string? LastThreadId);

/// <summary>單次執行 API 回應。</summary>
public sealed record ScheduleRunDto(
    Guid Id,
    Guid ScheduleId,
    ScheduleRunStatus Status,
    string? ThreadId,
    string? Error,
    DateTimeOffset StartedAt,
    DateTimeOffset? FinishedAt);
