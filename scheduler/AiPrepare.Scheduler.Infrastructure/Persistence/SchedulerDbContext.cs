using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

/// <summary>排程 PostgreSQL DbContext（schema：public；實體 PascalCase → 欄位 snake_case）。</summary>
public sealed class SchedulerDbContext : DbContext
{
    /// <summary>標準 EF 建構。</summary>
    public SchedulerDbContext(DbContextOptions<SchedulerDbContext> options) : base(options) { }

    public DbSet<Schedule> Schedules => Set<Schedule>();
    public DbSet<ScheduleRun> ScheduleRuns => Set<ScheduleRun>();

    /// <summary>表／欄註解、索引與長度；實際欄名由 SnakeCaseNamingConvention 轉成 snake_case。</summary>
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Schedule>(e =>
        {
            e.ToTable(t => t.HasComment("排程定義（個人或公司）；到期掃描看 enabled／next_run_at"));
            e.HasKey(x => x.Id);
            e.HasIndex(x => new { x.Enabled, x.NextRunAt });
            e.HasIndex(x => new { x.Scope, x.Enabled, x.NextRunAt });
            e.HasIndex(x => x.UserId);

            e.Property(x => x.Id).HasComment("主鍵");
            e.Property(x => x.UserId).HasMaxLength(128).HasComment("擁有者；公司列常用 company");
            e.Property(x => x.Scope).HasComment("0=User 個人／1=Company 公司（一般列表不回傳）");
            e.Property(x => x.Title).HasMaxLength(200).HasComment("標題（亦可當通知主旨前綴）");
            e.Property(x => x.Prompt).HasComment("送給 LangGraph 的 human message");
            e.Property(x => x.AssistantId).HasMaxLength(128).HasComment("LangGraph assistant／graph id，預設 agent");
            e.Property(x => x.ApiUrl).HasMaxLength(512).HasComment("LangGraph base URL");
            e.Property(x => x.Kind).HasComment("週期：Daily／Weekly／EveryNHours／Monthly");
            e.Property(x => x.TimeOfDay).HasComment("日／週觸發的牆鐘時間");
            e.Property(x => x.Weekday).HasComment("每週觸發的星期（Weekly）");
            e.Property(x => x.IntervalHours).HasComment("每 N 小時觸發（EveryNHours）");
            e.Property(x => x.DayOfMonth).HasComment("每月幾號（Monthly，1–31）");
            e.Property(x => x.AutoSendMail).HasComment("此排程 Agent 寄信是否免逐封確認");
            e.Property(x => x.TimeZone).HasMaxLength(64).HasComment("計算下次執行用時區，預設 Asia/Taipei");
            e.Property(x => x.Enabled).HasComment("是否納入 due 掃描");
            e.Property(x => x.NotifyEnabled).HasComment("執行結束後是否走通知管線");
            e.Property(x => x.EmailTo).HasMaxLength(1024).HasComment("收件 To（逗號或分號分隔）");
            e.Property(x => x.EmailCc).HasMaxLength(1024).HasComment("副本 Cc（可空）");
            e.Property(x => x.NextRunAt).HasComment("下次到期時間（UTC）");
            e.Property(x => x.LastRunAt).HasComment("上次執行結束時間（UTC）");
            e.Property(x => x.CreatedAt).HasComment("建立時間（UTC）");
            e.Property(x => x.UpdatedAt).HasComment("最後更新時間（UTC）");
        });

        modelBuilder.Entity<ScheduleRun>(e =>
        {
            e.ToTable(t => t.HasComment("單次排程執行紀錄（對應一次 LangGraph thread）"));
            e.HasKey(x => x.Id);
            e.HasIndex(x => x.ScheduleId);

            e.Property(x => x.Id).HasComment("主鍵");
            e.Property(x => x.ScheduleId).HasComment("所屬排程 Id（無 FK 強制）");
            e.Property(x => x.Status).HasComment("Pending／Running／Succeeded／Failed");
            e.Property(x => x.ThreadId).HasMaxLength(128).HasComment("LangGraph thread id");
            e.Property(x => x.Error).HasComment("失敗訊息");
            e.Property(x => x.NotifyOutcome).HasMaxLength(512)
                .HasComment("通知摘要：Skipped／Draft:…／Failed:…");
            e.Property(x => x.StartedAt).HasComment("開始時間（UTC）");
            e.Property(x => x.FinishedAt).HasComment("結束時間（UTC）");
        });
    }
}
