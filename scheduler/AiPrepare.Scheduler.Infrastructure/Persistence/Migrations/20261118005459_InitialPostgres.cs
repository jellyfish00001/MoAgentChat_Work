using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AiPrepare.Scheduler.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class InitialPostgres : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "ScheduleRuns",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ScheduleId = table.Column<Guid>(type: "uuid", nullable: false),
                    Status = table.Column<int>(type: "integer", nullable: false),
                    ThreadId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: true),
                    Error = table.Column<string>(type: "text", nullable: true),
                    NotifyOutcome = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: true),
                    StartedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                    FinishedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ScheduleRuns", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Schedules",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    UserId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    Scope = table.Column<int>(type: "integer", nullable: false),
                    Title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    Prompt = table.Column<string>(type: "text", nullable: false),
                    AssistantId = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false),
                    ApiUrl = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false),
                    Kind = table.Column<int>(type: "integer", nullable: false),
                    TimeOfDay = table.Column<TimeOnly>(type: "time without time zone", nullable: true),
                    Weekday = table.Column<int>(type: "integer", nullable: true),
                    IntervalHours = table.Column<int>(type: "integer", nullable: true),
                    DayOfMonth = table.Column<int>(type: "integer", nullable: true),
                    AutoSendMail = table.Column<bool>(type: "boolean", nullable: false),
                    TimeZone = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    Enabled = table.Column<bool>(type: "boolean", nullable: false),
                    NotifyEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    EmailTo = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: true),
                    EmailCc = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: true),
                    NextRunAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                    LastRunAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false)
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
