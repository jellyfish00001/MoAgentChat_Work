"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import {
  deleteSchedule,
  listSchedules,
  patchSchedule,
  runScheduleNow,
  ScheduleKind,
  type ScheduleDto,
} from "@/lib/schedule-api";
import { useLocalUser } from "@/hooks/useLocalUser";
import { useQueryState } from "nuqs";
import { useStreamContext } from "@/providers/Stream";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  ExternalLink,
  LoaderCircle,
  Play,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { ScheduleForm } from "./ScheduleForm";
import { Separator } from "@/components/ui/separator";

/** 依 kind 產生側欄一列的週期摘要文字。 */
function kindLabel(s: ScheduleDto): string {
  if (s.kind === ScheduleKind.EveryNHours) {
    return `每 ${s.intervalHours ?? "?"} 小時`;
  }
  const t = s.timeOfDay?.slice(0, 5) ?? "??:??";
  if (s.kind === ScheduleKind.Weekly) {
    const days = ["日", "一", "二", "三", "四", "五", "六"];
    const d = s.weekday != null ? days[s.weekday] : "?";
    return `每週${d} ${t}`;
  }
  return `每日 ${t}`;
}

/** 單筆排程：啟用開關、立即執行、上次對話與刪除。 */
function ScheduleRow({
  item,
  busy,
  onToggle,
  onDelete,
  onRunNow,
  onOpenThread,
}: {
  item: ScheduleDto;
  busy: boolean;
  onToggle: (enabled: boolean) => void;
  onDelete: () => void;
  onRunNow: () => void;
  onOpenThread: (threadId: string) => void;
}) {
  return (
    <div className="border-border bg-background/50 flex flex-col gap-2 rounded-xl border p-2.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{item.title}</p>
          <p className="text-muted-foreground text-[11px]">{kindLabel(item)}</p>
        </div>
        <Switch
          checked={item.enabled}
          disabled={busy}
          onCheckedChange={onToggle}
          aria-label={item.enabled ? "停用排程" : "啟用排程"}
        />
      </div>
      <div className="flex flex-wrap gap-1">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs"
          disabled={busy}
          onClick={onRunNow}
        >
          {busy ? (
            <LoaderCircle className="size-3.5 animate-spin" />
          ) : (
            <Play className="size-3.5" />
          )}
          立即執行
        </Button>
        {item.lastThreadId ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => onOpenThread(item.lastThreadId!)}
          >
            <ExternalLink className="size-3.5" />
            上次對話
          </Button>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-destructive hover:text-destructive ml-auto h-7 px-2 text-xs"
          disabled={busy}
          onClick={onDelete}
        >
          <Trash2 className="size-3.5" />
        </Button>
      </div>
    </div>
  );
}

/** 歷史側欄中的排程列表與底部新增表單。 */
export function ScheduleSidebar({
  className,
  compact,
}: {
  className?: string;
  compact?: boolean;
}) {
  const userId = useLocalUser();
  const stream = useStreamContext();
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: process.env.NEXT_PUBLIC_ASSISTANT_ID || "",
  });
  const [, setThreadId] = useQueryState("threadId");
  const [items, setItems] = useState<ScheduleDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [rowBusy, setRowBusy] = useState<string | null>(null);

  /** 依本機 userId 重新拉取排程列表。 */
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listSchedules(userId);
      setItems(list);
    } catch (err) {
      console.error(err);
      toast.error("無法載入排程", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  /** 切換 query threadId 並載入 LangGraph 對話。 */
  const openThread = (id: string) => {
    void setThreadId(id);
    stream.switchThread(id);
  };

  /** 列操作共用：鎖定該列、執行 API、失敗 toast、成功後 refresh。 */
  const wrapRow = async (id: string, fn: () => Promise<void>) => {
    setRowBusy(id);
    try {
      await fn();
      await refresh();
    } catch (err) {
      toast.error("操作失敗", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setRowBusy(null);
    }
  };

  return (
    <div className={cn("flex w-full flex-col gap-2", className)}>
      <div className="flex items-center justify-between px-3">
        <span className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
          排程
        </span>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-7"
          onClick={() => void refresh()}
          title="重新整理"
        >
          <RefreshCw className="size-3.5" />
        </Button>
      </div>
      <div
        className={cn(
          "scrollbar-ocean max-h-48 flex flex-col gap-2 overflow-y-auto px-1",
          compact && "max-h-36",
        )}
      >
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))
        ) : items.length === 0 ? (
          <p className="text-muted-foreground px-3 text-xs">尚無排程</p>
        ) : (
          items.map((item) => (
            <ScheduleRow
              key={item.id}
              item={item}
              busy={rowBusy === item.id}
              onToggle={(enabled) =>
                void wrapRow(item.id, () =>
                  patchSchedule(item.id, { enabled }).then(() => undefined),
                )
              }
              onDelete={() =>
                void wrapRow(item.id, () =>
                  deleteSchedule(item.id).then(() => undefined),
                )
              }
              onRunNow={() =>
                void wrapRow(item.id, async () => {
                  const run = await runScheduleNow(item.id);
                  if (run.threadId) openThread(run.threadId);
                  toast.success("已觸發執行");
                })
              }
              onOpenThread={openThread}
            />
          ))
        )}
      </div>
      <Separator className="bg-sidebar-border mx-3 w-auto" />
      <ScheduleForm
        assistantId={assistantId || "agent"}
        apiUrl={stream.apiUrl}
        envApiUrl={process.env.NEXT_PUBLIC_API_URL}
        onCreated={() => void refresh()}
      />
    </div>
  );
}
