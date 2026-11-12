using System.Net;
using System.Text;
using System.Text.Json;
using AiPrepare.Scheduler.Application.Abstractions;
using AiPrepare.Scheduler.Infrastructure.LangGraph;
using Microsoft.Extensions.Logging.Abstractions;

namespace AiPrepare.Scheduler.Domain.Tests;

public sealed class LangGraphHttpClientTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task ClientUsesConfiguredHostAndPassesTestPreference(bool autoSend)
    {
        var oldUrl = Environment.GetEnvironmentVariable("LANGGRAPH_API_URL");
        try
        {
            Environment.SetEnvironmentVariable("LANGGRAPH_API_URL", "http://trusted.invalid:2024");
            var handler = new CaptureHandler();
            var client = new LangGraphHttpClient(new ClientFactory(handler),
                NullLogger<LangGraphHttpClient>.Instance);
            var result = await client.CreateThreadAndRunAsync(new LangGraphRunRequest(
                "https://untrusted.invalid", "agent", "測試寄信內容", Guid.NewGuid(), "test", "user",
                autoSend, Guid.NewGuid()));
            Assert.True(result.Ok);
            Assert.True(result.WaitingForConfirmation);
            Assert.All(handler.Uris, uri => Assert.Equal("trusted.invalid", uri.Host));
            Assert.NotNull(handler.RunBody);
            using var document = JsonDocument.Parse(handler.RunBody);
            Assert.Equal(autoSend, document.RootElement.GetProperty("metadata")
                .GetProperty("schedule_auto_send_mail").GetBoolean());
            var configurable = document.RootElement.GetProperty("config").GetProperty("configurable");
            Assert.Equal(autoSend, configurable.GetProperty("schedule_auto_send_mail").GetBoolean());
            Assert.False(configurable.TryGetProperty("schedule_mail_authorized", out _));
        }
        finally
        {
            Environment.SetEnvironmentVariable("LANGGRAPH_API_URL", oldUrl);
        }
    }

    private sealed class ClientFactory(CaptureHandler handler) : IHttpClientFactory
    {
        public HttpClient CreateClient(string name) => new(handler, disposeHandler: false);
    }

    private sealed class CaptureHandler : HttpMessageHandler
    {
        public List<Uri> Uris { get; } = [];
        public byte[]? RunBody { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var uri = request.RequestUri!;
            Uris.Add(uri);
            Assert.DoesNotContain(request.Headers, header =>
                header.Key.StartsWith("X-Schedule-", StringComparison.OrdinalIgnoreCase));
            if (uri.AbsolutePath.EndsWith("/runs/wait"))
                RunBody = await request.Content!.ReadAsByteArrayAsync(cancellationToken);
            var json = uri.AbsolutePath.EndsWith("/threads")
                ? """{"thread_id":"00000000-0000-0000-0000-000000000001"}"""
                : request.Method == HttpMethod.Get ? """{"status":"interrupted"}""" : "{}";
            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json"),
            };
        }
    }
}
