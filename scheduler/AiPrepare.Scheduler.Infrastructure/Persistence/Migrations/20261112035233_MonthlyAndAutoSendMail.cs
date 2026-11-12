using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AiPrepare.Scheduler.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class MonthlyAndAutoSendMail : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "AutoSendMail",
                table: "Schedules",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<int>(
                name: "DayOfMonth",
                table: "Schedules",
                type: "INTEGER",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "AutoSendMail",
                table: "Schedules");

            migrationBuilder.DropColumn(
                name: "DayOfMonth",
                table: "Schedules");
        }
    }
}
