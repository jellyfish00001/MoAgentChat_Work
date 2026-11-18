using Microsoft.Extensions.Configuration;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

/// <summary>
/// 解析排程庫連線字串：環境變數（部署 Vault Value）優先，其次 Configuration／appsettings。
/// 禁止退回 SQLite 檔案路徑。
/// </summary>
public static class DbConnectionResolver
{
    /// <summary>
    /// 取得 Npgsql 連線字串；皆無則拋錯。
    /// 優先序：SCHEDULE_DB → ConnectionStrings__Scheduler → ConnectionStrings:Scheduler。
    /// </summary>
    public static string Resolve(IConfiguration? configuration = null)
    {
        // 1. 部署／本機環境變數（Vault Value 打在這層）
        var fromEnv = Environment.GetEnvironmentVariable("SCHEDULE_DB")
            ?? Environment.GetEnvironmentVariable("ConnectionStrings__Scheduler");
        if (!string.IsNullOrWhiteSpace(fromEnv))
            return fromEnv.Trim();

        // 2. appsettings／Development 明文（本機可；勿 commit 含密碼檔）
        var fromConfig = configuration?.GetConnectionString("Scheduler")
            ?? configuration?["ConnectionStrings:Scheduler"];
        if (!string.IsNullOrWhiteSpace(fromConfig))
            return fromConfig.Trim();

        throw new InvalidOperationException(
            "缺少排程庫連線：請設定環境變數 SCHEDULE_DB（或 ConnectionStrings__Scheduler），" +
            "或本機 ConnectionStrings:Scheduler（appsettings.Development.json）。部署請由 Vault／Secret 注入。");
    }
}
