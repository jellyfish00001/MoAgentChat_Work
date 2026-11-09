import { parseScheduleDraft } from "./scheduleDraftParser";
import { ScheduleKind } from "./schedule-api";

type Case = { input: string; expect: "null" | Partial<ReturnType<typeof parseScheduleDraft>> };

const CASES: Case[] = [
  {
    input: "每天早上9點提醒我檢查郵件",
    expect: { kind: ScheduleKind.Daily, timeOfDay: "09:00:00", prompt: "檢查郵件" },
  },
  {
    input: "每週一早上9點提醒開會",
    expect: { kind: ScheduleKind.Weekly, weekday: 1, timeOfDay: "09:00:00" },
  },
  {
    input: "每3小時提醒我喝水",
    expect: { kind: ScheduleKind.EveryNHours, intervalHours: 3 },
  },
  {
    input: "every day at 9am remind me to stand up",
    expect: { kind: ScheduleKind.Daily, timeOfDay: "09:00:00" },
  },
  { input: "hello world", expect: "null" },
];

/** 執行 parseScheduleDraft 固定案例；供腳本或 CI 手動 smoke。 */
export function runScheduleDraftParserTests(): {
  ok: boolean;
  failures: string[];
} {
  const failures: string[] = [];
  for (const c of CASES) {
    const got = parseScheduleDraft(c.input);
    if (c.expect === "null") {
      if (got !== null) failures.push(`${c.input}: expected null, got ${JSON.stringify(got)}`);
      continue;
    }
    if (!got) {
      failures.push(`${c.input}: expected draft, got null`);
      continue;
    }
    for (const [k, v] of Object.entries(c.expect ?? {})) {
      if ((got as Record<string, unknown>)[k] !== v) {
        failures.push(
          `${c.input}: ${k} expected ${v}, got ${(got as Record<string, unknown>)[k]}`,
        );
      }
    }
  }
  return { ok: failures.length === 0, failures };
}

/** 直接以 tsx 執行本檔時跑測試並以 exit code 回報結果。 */
const isMain =
  typeof process !== "undefined" &&
  process.argv[1]?.replace(/\\/g, "/").includes("scheduleDraftParser.test");

if (isMain) {
  const { ok, failures } = runScheduleDraftParserTests();
  if (!ok) {
    console.error("scheduleDraftParser tests failed:");
    failures.forEach((f) => console.error(" -", f));
    process.exit(1);
  }
  console.log("scheduleDraftParser tests OK");
}
