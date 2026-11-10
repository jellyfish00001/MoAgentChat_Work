"use client";

import { useCallback, useState } from "react";
import { parseScheduleDraft, type ScheduleDraft } from "@/lib/scheduleDraftParser";
import { createSchedule } from "@/lib/schedule-api";
import { useLocalUser } from "@/hooks/useLocalUser";
import { toast } from "sonner";
import { resolveApiUrl } from "@/lib/resolve-api-url";

/**
 * 攔截聊天輸入：若自然語句像排程意圖，改顯示確認卡而非送訊息給 Agent。
 */
export function useScheduleComposer(options: {
  assistantId: string;
  apiUrl: string;
  envApiUrl?: string;
}) {
  const userId = useLocalUser();
  const [draft, setDraft] = useState<ScheduleDraft | null>(null);
  const [creating, setCreating] = useState(false);

  /** 解析輸入；成功則設定 draft 並回傳 true 以阻止一般 submit。 */
  const tryIntercept = useCallback(
    (text: string, attachmentCount: number) => {
      if (attachmentCount > 0) return false;
      const parsed = parseScheduleDraft(text);
      if (!parsed) return false;
      setDraft(parsed);
      return true;
    },
    [],
  );

  /** 使用者取消確認卡。 */
  const cancelDraft = useCallback(() => setDraft(null), []);

  /** 確認後呼叫 Scheduler API 建立排程。 */
  const confirmDraft = useCallback(async () => {
    if (!draft) return false;
    setCreating(true);
    try {
      const langGraphUrl = resolveApiUrl(
        options.apiUrl,
        options.envApiUrl ?? process.env.NEXT_PUBLIC_API_URL,
      );
      await createSchedule({
        userId,
        title: draft.title,
        prompt: draft.prompt,
        kind: draft.kind,
        timeOfDay: draft.timeOfDay,
        weekday: draft.weekday,
        intervalHours: draft.intervalHours,
        assistantId: options.assistantId || "agent",
        apiUrl: langGraphUrl || "http://127.0.0.1:2024",
      });
      toast.success("排程已建立", { description: draft.summary });
      setDraft(null);
      return true;
    } catch (err) {
      console.error(err);
      toast.error("無法建立排程", {
        description: err instanceof Error ? err.message : String(err),
      });
      return false;
    } finally {
      setCreating(false);
    }
  }, [draft, userId, options.assistantId, options.apiUrl, options.envApiUrl]);

  return {
    draft,
    creating,
    tryIntercept,
    cancelDraft,
    confirmDraft,
  };
}
