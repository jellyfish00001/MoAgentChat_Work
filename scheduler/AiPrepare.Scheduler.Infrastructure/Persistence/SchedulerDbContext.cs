using AiPrepare.Scheduler.Domain;
using Microsoft.EntityFrameworkCore;

namespace AiPrepare.Scheduler.Infrastructure.Persistence;

public sealed class SchedulerDbContext : DbContext
{
    public SchedulerDbContext(DbContextOptions<SchedulerDbContext> options) : base(options) { }

    public DbSet<Schedule> Schedules => Set<Schedule>();
    public DbSet<ScheduleRun> ScheduleRuns => Set<ScheduleRun>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Schedule>(e =>
        {
            e.HasKey(x => x.Id);
            e.HasIndex(x => new { x.Enabled, x.NextRunAt });
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
