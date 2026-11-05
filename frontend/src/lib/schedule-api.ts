/** 排程後端（AiPrepare.Scheduler.Api）的型別化 fetch 客戶端；JSON 為 camelCase。 */

export enum ScheduleKind {
  Daily = 0,
  Weekly = 1,
  EveryNHours = 2,
}

export type ScheduleDto = {
  id: string;
  userId: string;
  title: string;
  prompt: string;
  assistantId: string;
  apiUrl: string;
  kind: ScheduleKind;
  timeOfDay: string | null;
  weekday: number | null;
  intervalHours: number | null;
  enabled: boolean;
  nextRunAt: string;
  lastRunAt: string | null;
  lastThreadId: string | null;
};

export type ScheduleRunDto = {
  id: string;
  scheduleId: string;
  status: number;
  threadId: string | null;
  error: string | null;
  startedAt: string;
  finishedAt: string | null;
};

export type CreateSchedulePayload = {
  userId: string;
  title: string;
  prompt: string;
  kind: ScheduleKind;
  timeOfDay: string | null;
  weekday: number | null;
  intervalHours: number | null;
  assistantId: string;
  apiUrl: string;
};

export type PatchSchedulePayload = {
  title?: string;
  prompt?: string;
  enabled?: boolean;
  kind?: ScheduleKind;
  timeOfDay?: string | null;
  weekday?: number | null;
  intervalHours?: number | null;
};

/** 從環境變數或本機預設取得 Scheduler API 根 URL（不含尾端斜線）。 */
function scheduleBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SCHEDULE_API_URL?.replace(/\/$/, "") ||
    "http://127.0.0.1:5055"
  );
}

/** 對 Scheduler API 發送 JSON 請求；非 2xx 時拋出含 status 與 body 的 Error。 */
async function scheduleFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${scheduleBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${path}: ${body || res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** 依 userId 列出該使用者的所有排程。 */
export function listSchedules(userId: string): Promise<ScheduleDto[]> {
  const q = new URLSearchParams({ userId });
  return scheduleFetch<ScheduleDto[]>(`/api/schedules?${q}`);
}

/** 建立一筆新排程。 */
export function createSchedule(
  body: CreateSchedulePayload,
): Promise<ScheduleDto> {
  return scheduleFetch<ScheduleDto>("/api/schedules", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** 部分更新排程欄位（啟用、時間規則、標題等）。 */
export function patchSchedule(
  id: string,
  body: PatchSchedulePayload,
): Promise<ScheduleDto> {
  return scheduleFetch<ScheduleDto>(`/api/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

/** 刪除排程。 */
export function deleteSchedule(id: string): Promise<void> {
  return scheduleFetch<void>(`/api/schedules/${id}`, { method: "DELETE" });
}

/** 立即觸發一次排程執行（非等到 nextRunAt）。 */
export function runScheduleNow(id: string): Promise<ScheduleRunDto> {
  return scheduleFetch<ScheduleRunDto>(`/api/schedules/${id}/run-now`, {
    method: "POST",
  });
}

/** 查詢某排程的執行紀錄列表。 */
export function listScheduleRuns(id: string): Promise<ScheduleRunDto[]> {
  return scheduleFetch<ScheduleRunDto[]>(`/api/schedules/${id}/runs`);
}
