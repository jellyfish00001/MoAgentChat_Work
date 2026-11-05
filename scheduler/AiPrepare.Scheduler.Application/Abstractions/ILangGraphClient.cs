namespace AiPrepare.Scheduler.Application.Abstractions;

/// <summary>LangGraph HTTP 呼叫合約。</summary>
public interface ILangGraphClient
{
    /// <summary>建立 thread 並 wait 跑完。</summary>
    Task<LangGraphRunResult> CreateThreadAndRunAsync(LangGraphRunRequest request, CancellationToken ct = default);
}

/// <summary>一次排程執行所需參數。</summary>
public sealed record LangGraphRunRequest(
    string ApiUrl,
    string AssistantId,
    string Prompt,
    Guid ScheduleId,
    string ScheduleTitle,
    string UserId);

/// <summary>LangGraph 呼叫結果。</summary>
public sealed record LangGraphRunResult(string ThreadId, bool Ok, string? Error);
