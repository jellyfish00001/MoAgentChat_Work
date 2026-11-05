using AiPrepare.Scheduler.Domain;

namespace AiPrepare.Scheduler.Application.Dtos;

/// <summary>列出個人排程請求（業務 API 統一 POST，userId 放 body）。</summary>
public sealed record ListSchedulesRequest(string UserId);

/// <summary>建立排程請求（公開 API 一律建成 Scope=User）。</summary>
public sealed record CreateScheduleRequest(
    string UserId,
    string Title,
    string Prompt,
    ScheduleKind Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours,
    string? AssistantId = null,
    string? ApiUrl = null,
    bool NotifyEnabled = false,
    string? EmailTo = null,
    string? EmailCc = null);

/// <summary>部分更新請求（null 表示不改）。</summary>
public sealed record PatchScheduleRequest(
    string? Title,
    string? Prompt,
    bool? Enabled,
    ScheduleKind? Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours,
    bool? NotifyEnabled = null,
    string? EmailTo = null,
    string? EmailCc = null);

/// <summary>排程 API 回應（含最近 thread、Scope、通知欄位）。</summary>
public sealed record ScheduleDto(
    Guid Id,
    string UserId,
    ScheduleScope Scope,
    string Title,
    string Prompt,
    string AssistantId,
    string ApiUrl,
    ScheduleKind Kind,
    TimeOnly? TimeOfDay,
    DayOfWeek? Weekday,
    int? IntervalHours,
    bool Enabled,
    bool NotifyEnabled,
    string? EmailTo,
    string? EmailCc,
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
    string? NotifyOutcome,
    DateTimeOffset StartedAt,
    DateTimeOffset? FinishedAt);
