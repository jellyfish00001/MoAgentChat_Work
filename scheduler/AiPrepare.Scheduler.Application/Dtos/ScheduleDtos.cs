using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Dtos;

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

public sealed record PatchScheduleRequest(
    string? Title,
    string? Prompt,
    bool? Enabled,
    ScheduleKind? Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours);

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

public sealed record ScheduleRunDto(
    Guid Id,
    Guid ScheduleId,
    ScheduleRunStatus Status,
    string? ThreadId,
    string? Error,
    DateTimeOffset StartedAt,
    DateTimeOffset? FinishedAt);
