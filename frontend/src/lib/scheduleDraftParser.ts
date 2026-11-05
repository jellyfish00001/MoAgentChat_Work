import { ScheduleKind } from "@/lib/schedule-api";

/** 從聊天自然語句解析出的排程草稿，供確認卡與 createSchedule 使用。 */
export type ScheduleDraft = {
  title: string;
  prompt: string;
  kind: ScheduleKind;
  timeOfDay: string | null;
  weekday: number | null;
  intervalHours: number | null;
  /** 確認卡上顯示的可讀摘要 */
  summary: string;
};

const WEEKDAY_ZH: Record<string, number> = {
  日: 0,
  天: 0,
  週日: 0,
  周日: 0,
  星期日: 0,
  星期天: 0,
  一: 1,
  週一: 1,
  周一: 1,
  星期一: 1,
  二: 2,
  週二: 2,
  周二: 2,
  星期二: 2,
  三: 3,
  週三: 3,
  周三: 3,
  星期三: 3,
  四: 4,
  週四: 4,
  周四: 4,
  星期四: 4,
  五: 5,
  週五: 5,
  周五: 5,
  星期五: 5,
  六: 6,
  週六: 6,
  周六: 6,
  星期六: 6,
};

const WEEKDAY_EN: Record<string, number> = {
  sunday: 0,
  sun: 0,
  monday: 1,
  mon: 1,
  tuesday: 2,
  tue: 2,
  tues: 2,
  wednesday: 3,
  wed: 3,
  thursday: 4,
  thu: 4,
  thur: 4,
  thurs: 4,
  friday: 5,
  fri: 5,
  saturday: 6,
  sat: 6,
};

const WEEKDAY_LABEL = ["週日", "週一", "週二", "週三", "週四", "週五", "週六"];

/** 將時分轉成 Scheduler API 要求的 HH:mm:ss。 */
function padTime(h: number, m: number): string {
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`;
}

/**
 * 從整句文字抽出時刻；支援中文「9點／9：30」與英文 am/pm。
 * 無明確時段時，中文日常用語預設上午解讀。
 */
function parseClock(text: string): string | null {
  // --- 中文／混合格式（點、冒號、時）---
  const m =
    text.match(
      /(?:^|[^\d])(\d{1,2})\s*[:：點时時]\s*(\d{1,2})?\s*(?:分)?/,
    ) ??
    text.match(/(?:^|[^\d])(\d{1,2})\s*[:：](\d{2})/);
  if (m) {
    let h = Number(m[1]);
    const min = m[2] ? Number(m[2]) : 0;
    if (Number.isNaN(h) || Number.isNaN(min)) return null;
    const lower = text.toLowerCase();
    const pm =
      /下午|晚上|傍晚|pm\b/.test(text) ||
      (/am\b/.test(lower) ? false : false);
    const am = /早上|上午|清晨|am\b/.test(text) || /am\b/.test(lower);
    if (pm && h < 12) h += 12;
    if (am && h === 12) h = 0;
    if (!am && !pm && h <= 12 && /(\d)\s*點/.test(text) && h >= 1 && h <= 11) {
      // 僅「9點」且句中有每天／每週等 → 維持上午習慣，不擅自加 12 小時
      if (/早上|上午|每天|每日|每週|每星期/.test(text)) {
        // keep h
      }
    }
    if (h < 0 || h > 23 || min < 0 || min > 59) return null;
    return padTime(h, min);
  }

  // --- 英文 9am / 9:30pm ---
  const en = text.match(
    /(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/i,
  );
  if (en) {
    let h = Number(en[1]);
    const min = en[2] ? Number(en[2]) : 0;
    const ap = en[3].toLowerCase();
    if (ap === "pm" && h < 12) h += 12;
    if (ap === "am" && h === 12) h = 0;
    return padTime(h, min);
  }
  return null;
}

/**
 * 去掉排程時間片語，留下要送給 Agent 的 prompt；
 * 優先匹配「提醒我…」句型以保留使用者原意。
 */
function extractPrompt(text: string): string {
  const remind = text.match(
    /(?:提醒我|提醒|通知我|remind\s+me(?:\s+to)?|notify\s+me(?:\s+to)?)\s*(.+)$/i,
  );
  if (remind?.[1]?.trim()) return remind[1].trim();

  const stripped = text
    .replace(
      /^(?:請|请)?(?:幫我|帮我)?(?:設定|设定|建立|创建|安排)?/,
      "",
    )
    .replace(
      /(?:每\s*\d+\s*小時|every\s+\d+\s+hours?)[^，,。]*[，,]?\s*/gi,
      "",
    )
    .replace(
      /(?:每週|每星期|每周|every\s+(?:week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun))[^，,。]*[，,]?\s*/gi,
      "",
    )
    .replace(
      /(?:每天|每日|every\s+day)[^，,。]*[，,]?\s*/gi,
      "",
    )
    .trim();
  return stripped || text.trim();
}

/** 側欄／API 標題欄長度上限，避免過長 prompt 撐破 UI。 */
function makeTitle(prompt: string): string {
  const t = prompt.trim();
  if (t.length <= 40) return t || "排程提醒";
  return `${t.slice(0, 37)}…`;
}

/** 句中是否含可辨識的排程週期關鍵字（中英）。 */
function hasScheduleIntent(text: string): boolean {
  return (
    /每\s*\d+\s*小時|every\s+\d+\s+hours?/i.test(text) ||
    /每週|每星期|每周|every\s+(?:week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i.test(
      text,
    ) ||
    /每天|每日|every\s+day/i.test(text)
  );
}

/** 解析每週排程的 weekday（0=週日）；無法對應時回傳 null。 */
function parseWeekday(text: string): number | null {
  const zh = text.match(/每(?:週|星期|周)([一二三四五六日天])/);
  if (zh) {
    const d = WEEKDAY_ZH[zh[1]];
    if (d !== undefined) return d;
  }
  const zhLong = text.match(/每(?:週|星期|周)(週[一二三四五六日天]|周[一二三四五六日天])/);
  if (zhLong) {
    const d = WEEKDAY_ZH[zhLong[1]];
    if (d !== undefined) return d;
  }
  const en = text.match(
    /every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)\b/i,
  );
  if (en) {
    const d = WEEKDAY_EN[en[1].toLowerCase()];
    if (d !== undefined) return d;
  }
  return null;
}

/**
 * 辨識聊天輸入中的排程意圖（繁中／英文）；
 * 非排程句或無法解析時回傳 null。
 */
export function parseScheduleDraft(text: string): ScheduleDraft | null {
  const raw = text.trim();
  if (!raw || !hasScheduleIntent(raw)) return null;

  // --- 每 N 小時（與每日／每週互斥，優先判斷）---
  const hoursMatch = raw.match(/每\s*(\d+)\s*小時|every\s+(\d+)\s+hours?/i);
  if (hoursMatch) {
    const n = Number(hoursMatch[1] ?? hoursMatch[2]);
    if (!Number.isFinite(n) || n < 1 || n > 168) return null;
    const prompt = extractPrompt(raw);
    return {
      title: makeTitle(prompt),
      prompt,
      kind: ScheduleKind.EveryNHours,
      timeOfDay: null,
      weekday: null,
      intervalHours: n,
      summary: `每 ${n} 小時 · ${prompt}`,
    };
  }

  // --- 每週或每日：共用時刻解析，每週需 weekday ---
  const weekday = parseWeekday(raw);
  const isWeekly =
    weekday !== null ||
    /每週|每星期|每周|every\s+(?:week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i.test(
      raw,
    );

  // 未寫明時間時預設 09:00，與表單預設一致
  const timeOfDay = parseClock(raw) ?? (isWeekly ? "09:00:00" : "09:00:00");
  const prompt = extractPrompt(raw);

  if (isWeekly) {
    const wd = weekday ?? 1;
    return {
      title: makeTitle(prompt),
      prompt,
      kind: ScheduleKind.Weekly,
      timeOfDay,
      weekday: wd,
      intervalHours: null,
      summary: `每${WEEKDAY_LABEL[wd] ?? "週"} ${timeOfDay.slice(0, 5)} · ${prompt}`,
    };
  }

  if (/每天|每日|every\s+day/i.test(raw)) {
    return {
      title: makeTitle(prompt),
      prompt,
      kind: ScheduleKind.Daily,
      timeOfDay,
      weekday: null,
      intervalHours: null,
      summary: `每日 ${timeOfDay.slice(0, 5)} · ${prompt}`,
    };
  }

  return null;
}
