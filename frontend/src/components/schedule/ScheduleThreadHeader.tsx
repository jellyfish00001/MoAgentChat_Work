"use client";

import { useEffect, useState } from "react";
import { useQueryState } from "nuqs";
import { getApiKey } from "@/lib/api-key";
import { resolveApiUrl } from "@/lib/resolve-api-url";
import { createClient } from "@/providers/client";
import {
  getScheduleTitleFromMetadata,
  isScheduleMetadata,
} from "@/lib/schedule-thread-meta";
import { ScheduleBadge } from "./ScheduleBadge";

/**
 * 目前 thread 若為排程執行產生，在對話頂欄顯示 badge 與 schedule_title。
 */
export function ScheduleThreadHeader({
  apiUrl,
  envApiUrl,
  authScheme,
}: {
  apiUrl: string;
  envApiUrl?: string;
  authScheme?: string;
}) {
  const [threadId] = useQueryState("threadId");
  const [title, setTitle] = useState<string | null>(null);

  /** 依 threadId 讀 metadata，非排程來源則隱藏。 */
  useEffect(() => {
    if (!threadId) {
      setTitle(null);
      return;
    }
    let cancelled = false;
    const finalUrl = resolveApiUrl(apiUrl, envApiUrl);
    const client = createClient(
      finalUrl,
      getApiKey(finalUrl) ?? undefined,
      authScheme,
    );
    client.threads
      .get(threadId)
      .then((thread) => {
        if (cancelled) return;
        const meta = thread.metadata as Record<string, unknown> | undefined;
        if (!isScheduleMetadata(meta)) {
          setTitle(null);
          return;
        }
        setTitle(getScheduleTitleFromMetadata(meta) ?? "排程對話");
      })
      .catch(() => {
        if (!cancelled) setTitle(null);
      });
    return () => {
      cancelled = true;
    };
  }, [threadId, apiUrl, envApiUrl, authScheme]);

  if (!title) return null;

  return (
    <span className="text-muted-foreground flex min-w-0 max-w-[12rem] items-center gap-1.5 truncate text-xs sm:max-w-xs sm:text-sm">
      <ScheduleBadge />
      <span className="truncate">{title}</span>
    </span>
  );
}
