namespace AiPrepare.Scheduler.Application.Abstractions;

public sealed record LangGraphRunRequest(
    string ApiUrl,
    string AssistantId,
    string Prompt,
    Guid ScheduleId,
    string ScheduleTitle,
    string UserId);

public sealed record LangGraphRunResult(string ThreadId, bool Ok, string? Error);

/// <summary>Creates a new thread and runs the assistant with the schedule prompt.</summary>
public interface ILangGraphClient
{
    Task<LangGraphRunResult> CreateThreadAndRunAsync(LangGraphRunRequest request, CancellationToken ct = default);
}
