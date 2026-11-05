import type { Thread } from "@langchain/langgraph-sdk";

type ThreadMeta = Record<string, unknown>;

/** 安全取出 LangGraph thread 的 metadata 物件。 */
export function getThreadMetadata(thread: Thread): ThreadMeta | undefined {
  const m = thread.metadata;
  if (m && typeof m === "object") return m as ThreadMeta;
  return undefined;
}

/** 是否為排程執行產生的對話（metadata.source === "schedule"）。 */
export function isScheduleThread(thread: Thread): boolean {
  return getThreadMetadata(thread)?.source === "schedule";
}

/** 從 thread metadata 讀取排程顯示標題。 */
export function getScheduleTitleFromThread(thread: Thread): string | undefined {
  const title = getThreadMetadata(thread)?.schedule_title;
  return typeof title === "string" && title.trim() ? title.trim() : undefined;
}

/** 純 metadata 判斷是否排程來源（不綁 Thread 型別，供 header 等場景）。 */
export function isScheduleMetadata(meta: ThreadMeta | undefined): boolean {
  return meta?.source === "schedule";
}

/** 從 metadata 讀取排程標題（與 getScheduleTitleFromThread 邏輯一致）。 */
export function getScheduleTitleFromMetadata(
  meta: ThreadMeta | undefined,
): string | undefined {
  const title = meta?.schedule_title;
  return typeof title === "string" && title.trim() ? title.trim() : undefined;
}
