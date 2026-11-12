"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  deleteSchedule,
  listSchedules,
  runScheduleNow,
  type ScheduleDto,
} from "@/lib/schedule-api";
import { useLocalUser } from "@/hooks/useLocalUser";
import { useQueryState } from "nuqs";
import { useStreamContext } from "@/providers/Stream";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  ChevronDown,
  ChevronRight,
  LoaderCircle,
  Pencil,
  Play,
  Plus,
  Trash2,
} from "lucide-react";
import { ScheduleDialog } from "./ScheduleDialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/** localStorage：排程側欄是否展開（預設收合）。 */
const SCHEDULE_EXPANDED_KEY = "aipark.scheduleSidebar.expanded";

/** 啟用排程在前、暫不執行在後；同組依標題排序。 */
function sortSchedules(list: ScheduleDto[]): ScheduleDto[] {
  return [...list].sort((a, b) => {
    if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
    return a.title.localeCompare(b.title, "zh-Hant");
  });
}

/** 單列：名稱開上次對話；圖示左→右為刪除／立即執行／編輯。 */
function ScheduleRow({
  item,
  busy,
  onDelete,
  onRunNow,
  onEdit,
  onOpenLast,
}: {
  item: ScheduleDto;
  busy: boolean;
  onDelete: () => void;
  onRunNow: () => void;
  onEdit: () => void;
  onOpenLast: () => void;
}) {
  return (
    <div
      className={cn(
        "group flex items-center gap-0.5 rounded-lg px-1.5 py-1",
        !item.enabled && "opacity-45",
      )}
    >
      <button
        type="button"
        className="text-foreground hover:bg-muted min-w-0 flex-1 truncate rounded-md px-1.5 py-1 text-left text-sm"
        onClick={onOpenLast}
        title={`${item.title}｜信件自動發送：${item.autoSendMail ? "開啟" : "關閉"}`}
      >
        {item.title}
      </button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="text-muted-foreground hover:text-destructive size-7 shrink-0 opacity-70 group-hover:opacity-100"
        disabled={busy}
        onClick={onDelete}
        title="刪除"
        aria-label="刪除排程"
      >
        <Trash2 className="size-3.5" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="text-muted-foreground size-7 shrink-0 opacity-70 group-hover:opacity-100"
        disabled={busy}
        onClick={onRunNow}
        title="立即執行"
        aria-label="立即執行"
      >
        {busy ? (
          <LoaderCircle className="size-3.5 animate-spin" />
        ) : (
          <Play className="size-3.5" />
        )}
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="text-muted-foreground size-7 shrink-0 opacity-70 group-hover:opacity-100"
        disabled={busy}
        onClick={onEdit}
        title="編輯"
        aria-label="編輯排程"
      >
        <Pencil className="size-3.5" />
      </Button>
    </div>
  );
}

/** GPT 專案式橫幅：左側展開／收合，右側加號開新增彈窗。 */
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
  /** 預設收合；記住使用者上次展開／收合，避免每次開側欄又自動展開。 */
  const [expanded, setExpanded] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return window.localStorage.getItem(SCHEDULE_EXPANDED_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [rowBusy, setRowBusy] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<ScheduleDto | null>(null);

  const sorted = useMemo(() => sortSchedules(items), [items]);

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
    if (!stream.isLoading) void refresh();
  }, [refresh, stream.isLoading]);

  /** 持久化排程區塊展開狀態。 */
  useEffect(() => {
    try {
      window.localStorage.setItem(SCHEDULE_EXPANDED_KEY, expanded ? "1" : "0");
    } catch {
      /* ignore quota／私密模式 */
    }
  }, [expanded]);

  /** 切換至指定 thread；無 lastThreadId 時由呼叫端 toast。 */
  const openThread = (id: string) => {
    void setThreadId(id);
    stream.switchThread(id);
  };

  /** 點名稱：有 lastThreadId 則開對話，否則提示。 */
  const handleOpenLast = (item: ScheduleDto) => {
    if (!item.lastThreadId) {
      toast.message("尚無執行紀錄", {
        description: "此排程還沒有上次對話可開啟。",
      });
      return;
    }
    openThread(item.lastThreadId);
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

  /** 開啟新增彈窗。 */
  const openCreate = () => {
    setEditing(null);
    setDialogOpen(true);
  };

  /** 開啟編輯彈窗。 */
  const openEdit = (item: ScheduleDto) => {
    setEditing(item);
    setDialogOpen(true);
  };

  return (
    <div className={cn("flex w-full flex-col gap-1", className)}>
      <div className="flex items-center gap-0.5 px-2">
        <button
          type="button"
          className="hover:bg-muted text-foreground flex min-w-0 flex-1 items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-sm font-medium"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex shrink-0">
                {expanded ? (
                  <ChevronDown className="text-muted-foreground size-4" />
                ) : (
                  <ChevronRight className="text-muted-foreground size-4" />
                )}
              </span>
            </TooltipTrigger>
            <TooltipContent
              side="top"
              sideOffset={6}
            >
              {expanded ? "摺疊聊天" : "展開聊天"}
            </TooltipContent>
          </Tooltip>
          <span className="truncate">排程</span>
          {!loading && items.length > 0 ? (
            <span className="text-muted-foreground text-xs font-normal">
              {items.length}
            </span>
          ) : null}
        </button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="size-7 shrink-0"
          onClick={openCreate}
          title="新增排程"
          aria-label="新增排程"
        >
          <Plus className="size-4" />
        </Button>
      </div>

      {expanded ? (
        <div
          className={cn(
            // 可滾動但不顯示滾輪條；展開高度維持原 10rem／13rem
            "scrollbar-hidden flex flex-col gap-0.5 overflow-y-auto px-1",
            compact ? "max-h-40" : "max-h-52",
          )}
        >
          {loading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <Skeleton
                key={i}
                className="mx-1 h-8 rounded-lg"
              />
            ))
          ) : sorted.length === 0 ? (
            <p className="text-muted-foreground px-3 py-1 text-xs">
              尚無排程，點 ＋ 新增
            </p>
          ) : (
            sorted.map((item) => (
              <ScheduleRow
                key={item.id}
                item={item}
                busy={rowBusy === item.id}
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
                onEdit={() => openEdit(item)}
                onOpenLast={() => handleOpenLast(item)}
              />
            ))
          )}
        </div>
      ) : null}

      <ScheduleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        assistantId={assistantId || "agent"}
        apiUrl={stream.apiUrl}
        envApiUrl={process.env.NEXT_PUBLIC_API_URL}
        editing={editing}
        onSaved={() => void refresh()}
      />
    </div>
  );
}
