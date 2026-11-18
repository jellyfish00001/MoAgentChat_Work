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
                name: "schedule_runs",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false, comment: "主鍵"),
                    schedule_id = table.Column<Guid>(type: "uuid", nullable: false, comment: "所屬排程 Id（無 FK 強制）"),
                    status = table.Column<int>(type: "integer", nullable: false, comment: "Pending／Running／Succeeded／Failed"),
                    thread_id = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: true, comment: "LangGraph thread id"),
                    error = table.Column<string>(type: "text", nullable: true, comment: "失敗訊息"),
                    notify_outcome = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: true, comment: "通知摘要：Skipped／Draft:…／Failed:…"),
                    started_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false, comment: "開始時間（UTC）"),
                    finished_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true, comment: "結束時間（UTC）")
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_schedule_runs", x => x.id);
                },
                comment: "單次排程執行紀錄（對應一次 LangGraph thread）");

            migrationBuilder.CreateTable(
                name: "schedules",
                columns: table => new
                {
                    id = table.Column<Guid>(type: "uuid", nullable: false, comment: "主鍵"),
                    user_id = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false, comment: "擁有者；公司列常用 company"),
                    scope = table.Column<int>(type: "integer", nullable: false, comment: "0=User 個人／1=Company 公司（一般列表不回傳）"),
                    title = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false, comment: "標題（亦可當通知主旨前綴）"),
                    prompt = table.Column<string>(type: "text", nullable: false, comment: "送給 LangGraph 的 human message"),
                    assistant_id = table.Column<string>(type: "character varying(128)", maxLength: 128, nullable: false, comment: "LangGraph assistant／graph id，預設 agent"),
                    api_url = table.Column<string>(type: "character varying(512)", maxLength: 512, nullable: false, comment: "LangGraph base URL"),
                    kind = table.Column<int>(type: "integer", nullable: false, comment: "週期：Daily／Weekly／EveryNHours／Monthly"),
                    time_of_day = table.Column<TimeOnly>(type: "time without time zone", nullable: true, comment: "日／週觸發的牆鐘時間"),
                    weekday = table.Column<int>(type: "integer", nullable: true, comment: "每週觸發的星期（Weekly）"),
                    interval_hours = table.Column<int>(type: "integer", nullable: true, comment: "每 N 小時觸發（EveryNHours）"),
                    day_of_month = table.Column<int>(type: "integer", nullable: true, comment: "每月幾號（Monthly，1–31）"),
                    auto_send_mail = table.Column<bool>(type: "boolean", nullable: false, comment: "此排程 Agent 寄信是否免逐封確認"),
                    time_zone = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false, comment: "計算下次執行用時區，預設 Asia/Taipei"),
                    enabled = table.Column<bool>(type: "boolean", nullable: false, comment: "是否納入 due 掃描"),
                    notify_enabled = table.Column<bool>(type: "boolean", nullable: false, comment: "執行結束後是否走通知管線"),
                    email_to = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: true, comment: "收件 To（逗號或分號分隔）"),
                    email_cc = table.Column<string>(type: "character varying(1024)", maxLength: 1024, nullable: true, comment: "副本 Cc（可空）"),
                    next_run_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false, comment: "下次到期時間（UTC）"),
                    last_run_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true, comment: "上次執行結束時間（UTC）"),
                    created_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false, comment: "建立時間（UTC）"),
                    updated_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false, comment: "最後更新時間（UTC）")
                },
                constraints: table =>
                {
                    table.PrimaryKey("pk_schedules", x => x.id);
                },
                comment: "排程定義（個人或公司）；到期掃描看 enabled／next_run_at");

            migrationBuilder.CreateIndex(
                name: "ix_schedule_runs_schedule_id",
                table: "schedule_runs",
                column: "schedule_id");

            migrationBuilder.CreateIndex(
                name: "ix_schedules_enabled_next_run_at",
                table: "schedules",
                columns: new[] { "enabled", "next_run_at" });

            migrationBuilder.CreateIndex(
                name: "ix_schedules_scope_enabled_next_run_at",
                table: "schedules",
                columns: new[] { "scope", "enabled", "next_run_at" });

            migrationBuilder.CreateIndex(
                name: "ix_schedules_user_id",
                table: "schedules",
                column: "user_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "schedule_runs");

            migrationBuilder.DropTable(
                name: "schedules");
        }
    }
}
