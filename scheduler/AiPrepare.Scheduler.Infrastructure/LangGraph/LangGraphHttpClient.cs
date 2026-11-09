using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using AiPrepare.Scheduler.Application.Abstractions;
using Microsoft.Extensions.Logging;

namespace AiPrepare.Scheduler.Infrastructure.LangGraph;

/// <summary>本機 LangGraph Agent Server HTTP 適配（threads + runs/wait）。</summary>
public sealed class LangGraphHttpClient : ILangGraphClient
{
    private readonly IHttpClientFactory _httpFactory;
    private readonly ILogger<LangGraphHttpClient> _log;

    static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    /// <summary>注入具名 HttpClient 與日誌。</summary>
    public LangGraphHttpClient(IHttpClientFactory httpFactory, ILogger<LangGraphHttpClient> log)
    {
        _httpFactory = httpFactory;
        _log = log;
    }

    /// <summary>建立新 thread 並同步跑完一輪；metadata 標記 source=schedule。</summary>
    public async Task<LangGraphRunResult> CreateThreadAndRunAsync(LangGraphRunRequest request, CancellationToken ct = default)
    {
        var client = _httpFactory.CreateClient("langgraph");
        // 前端存的 ApiUrl 是瀏覽器看得到的網址（k8s 上是 https://<前端>/api），
        // 叢集內改用 LANGGRAPH_API_URL 直連 server Service
        var apiUrl = Environment.GetEnvironmentVariable("LANGGRAPH_API_URL") ?? request.ApiUrl;
        client.BaseAddress = new Uri(apiUrl.TrimEnd('/') + "/");
        client.Timeout = TimeSpan.FromMinutes(5);

        try
        {
            // 1. 建立 thread（徽章／頂欄靠 metadata.source）
            var threadBody = new
            {
                metadata = new Dictionary<string, object>
                {
                    ["graph_id"] = request.AssistantId,
                    ["source"] = "schedule",
                    ["schedule_id"] = request.ScheduleId.ToString(),
                    ["schedule_title"] = request.ScheduleTitle,
                    ["user_id"] = request.UserId,
                },
            };
            using var threadRes = await client.PostAsJsonAsync("threads", threadBody, ct);
            var threadJson = await threadRes.Content.ReadAsStringAsync(ct);
            if (!threadRes.IsSuccessStatusCode)
                return new LangGraphRunResult("", false, $"threads create {(int)threadRes.StatusCode}: {threadJson}");

            using var threadDoc = JsonDocument.Parse(threadJson);
            var threadId = threadDoc.RootElement.GetProperty("thread_id").GetString()
                ?? throw new InvalidOperationException("missing thread_id");

            // 2. runs/wait：以排程 Prompt 當 human message
            var runBody = new
            {
                assistant_id = request.AssistantId,
                input = new
                {
                    messages = new object[]
                    {
                        new { type = "human", content = request.Prompt },
                    },
                },
                stream_mode = "values",
            };
            using var runRes = await client.PostAsJsonAsync($"threads/{threadId}/runs/wait", runBody, ct);
            var runText = await runRes.Content.ReadAsStringAsync(ct);
            if (!runRes.IsSuccessStatusCode)
            {
                _log.LogWarning("LangGraph run failed {Status} {Body}", (int)runRes.StatusCode, runText);
                return new LangGraphRunResult(threadId, false, $"run {(int)runRes.StatusCode}: {runText}");
            }

            return new LangGraphRunResult(threadId, true, null);
        }
        catch (Exception ex)
        {
            _log.LogError(ex, "LangGraph call failed for schedule {ScheduleId}", request.ScheduleId);
            return new LangGraphRunResult("", false, ex.Message);
        }
    }
}
