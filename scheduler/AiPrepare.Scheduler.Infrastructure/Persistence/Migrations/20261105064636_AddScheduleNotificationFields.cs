using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AiPrepare.Scheduler.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class AddScheduleNotificationFields : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "EmailCc",
                table: "Schedules",
                type: "TEXT",
                maxLength: 1024,
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "EmailTo",
                table: "Schedules",
                type: "TEXT",
                maxLength: 1024,
                nullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "NotifyEnabled",
                table: "Schedules",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<string>(
                name: "NotifyOutcome",
                table: "ScheduleRuns",
                type: "TEXT",
                maxLength: 512,
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "EmailCc",
                table: "Schedules");

            migrationBuilder.DropColumn(
                name: "EmailTo",
                table: "Schedules");

            migrationBuilder.DropColumn(
                name: "NotifyEnabled",
                table: "Schedules");

            migrationBuilder.DropColumn(
                name: "NotifyOutcome",
                table: "ScheduleRuns");
        }
    }
}
