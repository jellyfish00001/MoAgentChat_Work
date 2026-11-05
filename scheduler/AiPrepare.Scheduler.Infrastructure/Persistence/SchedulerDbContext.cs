using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

/// <summary>排程 SQLite DbContext。</summary>
public sealed class SchedulerDbContext : DbContext
{
    /// <summary>標準 EF 建構。</summary>
    public SchedulerDbContext(DbContextOptions<SchedulerDbContext> options) : base(options) { }

    public DbSet<Schedule> Schedules => Set<Schedule>();
    public DbSet<ScheduleRun> ScheduleRuns => Set<ScheduleRun>();

    /// <summary>索引與長度限制（利於 due 掃描與使用者列表）。</summary>
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Schedule>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasIndex(x => new { x.Enabled, x.NextRunAt });
            e.HasIndex(x => new { x.Scope, x.Enabled, x.NextRunAt });
            e.HasIndex(x => x.UserId);
            e.Property(x => x.Title).HasMaxLength(200);
            e.Property(x => x.UserId).HasMaxLength(128);
            e.Property(x => x.AssistantId).HasMaxLength(128);
            e.Property(x => x.ApiUrl).HasMaxLength(512);
            e.Property(x => x.TimeZone).HasMaxLength(64);
        });
        modelBuilder.Entity<ScheduleRun>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasIndex(x => x.ScheduleId);
            e.Property(x => x.ThreadId).HasMaxLength(128);
        });
    }
}
