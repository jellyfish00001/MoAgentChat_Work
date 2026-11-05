using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AiPrepare.Scheduler.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreateWithScope : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "ScheduleRuns",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    ScheduleId = table.Column<Guid>(type: "TEXT", nullable: false),
                    Status = table.Column<int>(type: "INTEGER", nullable: false),
                    ThreadId = table.Column<string>(type: "TEXT", maxLength: 128, nullable: true),
                    Error = table.Column<string>(type: "TEXT", nullable: true),
                    StartedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    FinishedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScheduleRuns", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Schedules",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "TEXT", nullable: false),
                    UserId = table.Column<string>(type: "TEXT", maxLength: 128, nullable: false),
                    Scope = table.Column<int>(type: "INTEGER", nullable: false),
                    Title = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false),
                    Prompt = table.Column<string>(type: "TEXT", nullable: false),
                    AssistantId = table.Column<string>(type: "TEXT", maxLength: 128, nullable: false),
                    ApiUrl = table.Column<string>(type: "TEXT", maxLength: 512, nullable: false),
                    Kind = table.Column<int>(type: "INTEGER", nullable: false),
                    TimeOfDay = table.Column<TimeOnly>(type: "TEXT", nullable: true),
                    Weekday = table.Column<int>(type: "INTEGER", nullable: true),
                    IntervalHours = table.Column<int>(type: "INTEGER", nullable: true),
                    TimeZone = table.Column<string>(type: "TEXT", maxLength: 64, nullable: false),
                    Enabled = table.Column<bool>(type: "INTEGER", nullable: false),
                    NextRunAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    LastRunAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Schedules", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_ScheduleRuns_ScheduleId",
                table: "ScheduleRuns",
                column: "ScheduleId");

            migrationBuilder.CreateIndex(
                name: "IX_Schedules_Enabled_NextRunAt",
                table: "Schedules",
                columns: new[] { "Enabled", "NextRunAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Schedules_Scope_Enabled_NextRunAt",
                table: "Schedules",
                columns: new[] { "Scope", "Enabled", "NextRunAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Schedules_UserId",
                table: "Schedules",
                column: "UserId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "ScheduleRuns");

            migrationBuilder.DropTable(
                name: "Schedules");
        }
    }
}
