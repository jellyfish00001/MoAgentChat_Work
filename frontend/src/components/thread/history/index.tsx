"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useThreads } from "@/providers/Thread";
import { useStreamContext } from "@/providers/Stream";
import { createClient } from "@/providers/client";
import { getApiKey } from "@/lib/api-key";
import { resolveApiUrl } from "@/lib/resolve-api-url";
import { getThreadMetadata } from "@/lib/schedule-thread-meta";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

import { getContentString } from "../utils";
import { useQueryState, parseAsBoolean } from "nuqs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ChevronDown,
  ChevronRight,
  MoreHorizontal,
  PanelRightOpen,
  PanelRightClose,
  Pencil,
  Trash2,
} from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { GraphSwitcher } from "../graph-switcher";
import { ScheduleSidebar } from "@/components/schedule/ScheduleSidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/** 顯示名稱：自訂標題優先，否則取首則訊息。 */
function getThreadDisplayTitle(thread: Thread): string {
  const custom = getThreadMetadata(thread)?.thread_title;
  if (typeof custom === "string" && custom.trim()) return custom.trim();

  if (
    typeof thread.values === "object" &&
    thread.values &&
    "messages" in thread.values &&
    Array.isArray(thread.values.messages) &&
    thread.values.messages.length > 0
  ) {
    return getContentString(thread.values.messages[0].content);
  }
  return thread.thread_id;
}

/** 建立目前環境的 LangGraph client。 */
function useLangGraphClient() {
  const envApiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL;
  const envAuthScheme: string | undefined = process.env.NEXT_PUBLIC_AUTH_SCHEME;
  const [apiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || "",
  });
  const [authScheme] = useQueryState("authScheme", {
    defaultValue: envAuthScheme || "",
  });

  /** 依目前 URL／env 組出 client。 */
  const getClient = () => {
    const finalUrl = resolveApiUrl(apiUrl, envApiUrl);
    return createClient(
      finalUrl,
      getApiKey(finalUrl) ?? undefined,
      authScheme || undefined,
    );
  };

  return { getClient };
}

/** 單列「…」選單：fixed 掛在按鈕右上（避開側欄 overflow 裁切）。 */
function ThreadRowMenu({
  open,
  anchorRef,
  onClose,
  onRename,
  onDelete,
}: {
  open: boolean;
  anchorRef: React.RefObject<HTMLElement | null>;
  onClose: () => void;
  onRename: () => void;
  onDelete: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);

  /** 依「…」按鈕算出選單右上錨點（開啟於按鈕右上方）。 */
  useLayoutEffect(() => {
    if (!open) {
      setPos(null);
      return;
    }
    const el = anchorRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    // 錨在「…」右上角外側：選單往上、往右（主內容區）展開
    setPos({ top: r.top - 4, left: r.right + 4 });
  }, [open, anchorRef]);

  useEffect(() => {
    if (!open) return;
    /** 點外面或捲動／縮放時關閉。 */
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (ref.current?.contains(t) || anchorRef.current?.contains(t)) return;
      onClose();
    };
    const onRepositionClose = () => onClose();
    document.addEventListener("mousedown", onDoc);
    window.addEventListener("resize", onRepositionClose);
    window.addEventListener("scroll", onRepositionClose, true);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      window.removeEventListener("resize", onRepositionClose);
      window.removeEventListener("scroll", onRepositionClose, true);
    };
  }, [open, onClose, anchorRef]);

  if (!open || !pos || typeof document === "undefined") return null;

  return createPortal(
    <div
      ref={ref}
      className="bg-panel border-border fixed z-[80] min-w-[9rem] rounded-xl border py-1 shadow-md"
      style={{
        top: pos.top,
        left: pos.left,
        transform: "translateY(-100%)",
      }}
      role="menu"
    >
      <button
        type="button"
        role="menuitem"
        className="hover:bg-muted flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm"
        onClick={(e) => {
          e.stopPropagation();
          onRename();
        }}
      >
        <Pencil className="size-3.5 shrink-0" />
        重新命名
      </button>
      <button
        type="button"
        role="menuitem"
        className="text-destructive hover:bg-muted flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm"
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
      >
        <Trash2 className="size-3.5 shrink-0" />
        刪除對話
      </button>
    </div>,
    document.body,
  );
}

/** 單一對話列：標題＋「…」選單錨點。 */
function ThreadRow({
  title,
  selected,
  busy,
  menuOpen,
  onSelect,
  onToggleMenu,
  onCloseMenu,
  onRename,
  onDelete,
}: {
  title: string;
  selected: boolean;
  busy: boolean;
  menuOpen: boolean;
  onSelect: () => void;
  onToggleMenu: () => void;
  onCloseMenu: () => void;
  onRename: () => void;
  onDelete: () => void;
}) {
  const menuBtnRef = useRef<HTMLButtonElement>(null);

  return (
    <div className="group relative w-full px-1">
      <div
        className={cn(
          "flex w-full items-center gap-0.5 rounded-xl border-l-2",
          selected
            ? "border-accent bg-muted text-foreground"
            : "border-transparent",
        )}
      >
        <Button
          variant="ghost"
          disabled={busy}
          className="h-auto min-w-0 flex-1 items-start justify-start rounded-xl py-2 pr-1 text-left font-normal hover:bg-transparent"
          onClick={(e) => {
            e.preventDefault();
            onSelect();
          }}
        >
          <p className="w-full truncate text-left text-ellipsis">{title}</p>
        </Button>
        <Button
          ref={menuBtnRef}
          type="button"
          variant="ghost"
          size="icon"
          disabled={busy}
          className={cn(
            "text-muted-foreground size-7 shrink-0 opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
            (menuOpen || selected) && "opacity-100",
          )}
          aria-label="對話選單"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleMenu();
          }}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </div>
      <ThreadRowMenu
        open={menuOpen}
        anchorRef={menuBtnRef}
        onClose={onCloseMenu}
        onRename={onRename}
        onDelete={onDelete}
      />
    </div>
  );
}

/** 對話列表：點列切換 thread，右側「…」可改名／刪除。 */
function ThreadList({
  threads,
  onThreadClick,
}: {
  threads: Thread[];
  onThreadClick?: (threadId: string) => void;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");
  const stream = useStreamContext();
  const { setThreads } = useThreads();
  const { getClient } = useLangGraphClient();

  const [menuThreadId, setMenuThreadId] = useState<string | null>(null);
  const [renameTarget, setRenameTarget] = useState<Thread | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [busy, setBusy] = useState(false);

  /** 開啟重新命名彈窗。 */
  const openRename = (t: Thread) => {
    setMenuThreadId(null);
    setRenameTarget(t);
    setRenameValue(getThreadDisplayTitle(t));
  };

  /** 儲存對話自訂標題到 metadata.thread_title。 */
  const saveRename = async () => {
    if (!renameTarget) return;
    const next = renameValue.trim();
    if (!next) {
      toast.error("請輸入對話名稱");
      return;
    }
    setBusy(true);
    try {
      const updated = await getClient().threads.update(renameTarget.thread_id, {
        metadata: { thread_title: next },
      });
      setThreads((prev) =>
        prev.map((t) =>
          t.thread_id === renameTarget.thread_id
            ? { ...t, metadata: updated.metadata ?? { ...getThreadMetadata(t), thread_title: next } }
            : t,
        ),
      );
      toast.success("已更新對話名稱");
      setRenameTarget(null);
    } catch (err) {
      console.error(err);
      toast.error("重新命名失敗");
    } finally {
      setBusy(false);
    }
  };

  /** 刪除對話；若正在檢視則切回空白。 */
  const deleteThread = async (t: Thread) => {
    setMenuThreadId(null);
    const ok = window.confirm(`確定刪除「${getThreadDisplayTitle(t)}」？`);
    if (!ok) return;
    setBusy(true);
    try {
      await getClient().threads.delete(t.thread_id);
      setThreads((prev) => prev.filter((x) => x.thread_id !== t.thread_id));
      if (threadId === t.thread_id) {
        await setThreadId(null);
        stream.switchThread(null);
      }
      toast.success("已刪除對話");
    } catch (err) {
      console.error(err);
      toast.error("刪除失敗");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {/* 側欄聊天列表：可滾動但不顯示滾輪條 */}
      <div className="scrollbar-hidden flex h-full w-full flex-col items-start justify-start gap-1 overflow-y-auto">
        {threads.map((t) => (
          <ThreadRow
            key={t.thread_id}
            title={getThreadDisplayTitle(t)}
            selected={t.thread_id === threadId}
            busy={busy}
            menuOpen={menuThreadId === t.thread_id}
            onSelect={() => {
              onThreadClick?.(t.thread_id);
              if (t.thread_id === threadId) return;
              stream.switchThread(t.thread_id);
            }}
            onToggleMenu={() =>
              setMenuThreadId((cur) =>
                cur === t.thread_id ? null : t.thread_id,
              )
            }
            onCloseMenu={() => setMenuThreadId(null)}
            onRename={() => openRename(t)}
            onDelete={() => void deleteThread(t)}
          />
        ))}
      </div>

      <Dialog
        open={Boolean(renameTarget)}
        onOpenChange={(open) => {
          if (!open) setRenameTarget(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>重新命名對話</DialogTitle>
            <DialogDescription>此名稱只用於側欄列表顯示。</DialogDescription>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            placeholder="對話名稱"
            maxLength={120}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void saveRename();
              }
            }}
          />
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => setRenameTarget(null)}
            >
              取消
            </Button>
            <Button
              type="button"
              disabled={busy}
              onClick={() => void saveRename()}
            >
              儲存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/** 載入中骨架。 */
function ThreadHistoryLoading() {
  return (
    <div className="scrollbar-hidden flex h-full w-full flex-col items-start justify-start gap-2 overflow-y-auto">
      {Array.from({ length: 30 }).map((_, i) => (
        <Skeleton
          key={`skeleton-${i}`}
          className="h-10 w-full max-w-full"
        />
      ))}
    </div>
  );
}

/** 聊天區塊展開／收合橫幅（tooltip 在箭頭上方）。 */
function ChatSectionBanner({
  expanded,
  onToggle,
  count,
}: {
  expanded: boolean;
  onToggle: () => void;
  count?: number;
}) {
  return (
    <div className="flex items-center gap-0.5 px-2">
      <button
        type="button"
        className="hover:bg-muted text-foreground flex min-w-0 flex-1 items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-sm font-medium"
        onClick={onToggle}
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
          <TooltipContent side="top" sideOffset={6}>
            {expanded ? "摺疊聊天" : "展開聊天"}
          </TooltipContent>
        </Tooltip>
        <span className="truncate">聊天</span>
        {typeof count === "number" && count > 0 ? (
          <span className="text-muted-foreground text-xs font-normal">
            {count}
          </span>
        ) : null}
      </button>
    </div>
  );
}

/** 側欄：Graph／排程／可摺疊聊天紀錄。 */
export default function ThreadHistory() {
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  const [mounted, setMounted] = useState(false);
  const [threadsExpanded, setThreadsExpanded] = useState(true);
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false).withOptions({
      history: "replace",
      shallow: true,
    }),
  );

  const { getThreads, threads, setThreads, threadsLoading, setThreadsLoading } =
    useThreads();

  useEffect(() => {
    setMounted(true);
  }, []);

  // [ai_prepare 修改] 軟換列表：不先清空、不打 skeleton，避免切 Agent 閃爍
  useEffect(() => {
    if (typeof window === "undefined") return;
    let cancelled = false;
    const showSkeleton = threads.length === 0;
    if (showSkeleton) setThreadsLoading(true);
    getThreads()
      .then((next) => {
        if (!cancelled) setThreads(next);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setThreadsLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // threads.length 只用於「是否首次」判斷，刻意不列入 deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getThreads, setThreads, setThreadsLoading]);

  /** 側欄主體（桌面／Sheet 共用結構）。 */
  const sidebarBody = (
    <>
      <GraphSwitcher compact />
      <ScheduleSidebar compact />
      <div className="flex min-h-0 w-full flex-1 flex-col gap-1">
        <ChatSectionBanner
          expanded={threadsExpanded}
          onToggle={() => setThreadsExpanded((v) => !v)}
          count={threads.length}
        />
        {threadsExpanded ? (
          <div className="min-h-0 flex-1">
            {threadsLoading ? (
              <ThreadHistoryLoading />
            ) : (
              <ThreadList threads={threads} />
            )}
          </div>
        ) : null}
      </div>
    </>
  );

  return (
    <>
      {/* h-full／w-full：由外層 aside 控制 0↔248 寬度 */}
      <div className="border-sidebar-border bg-sidebar shadow-inner-right hidden h-full w-full shrink-0 flex-col items-stretch justify-start gap-3 border-r lg:flex">
        <div className="flex w-full shrink-0 items-center justify-between px-4 pt-1.5">
          <Button
            variant="ghost"
            onClick={() => setChatHistoryOpen((p) => !p)}
          >
            {chatHistoryOpen ? (
              <PanelRightOpen className="size-5" />
            ) : (
              <PanelRightClose className="size-5" />
            )}
          </Button>
          <h1 className="text-xl font-semibold tracking-tight">W.AgentChat</h1>
        </div>
        {sidebarBody}
      </div>
      {mounted && (
        <div className="lg:hidden">
          <Sheet
            modal={false}
            open={!!chatHistoryOpen && !isLargeScreen}
            onOpenChange={(open) => {
              if (isLargeScreen) return;
              setChatHistoryOpen(open);
            }}
          >
            <SheetContent
              side="left"
              showOverlay={false}
              className="flex flex-col gap-3 lg:hidden"
            >
              <SheetHeader>
                <SheetTitle>W.AgentChat</SheetTitle>
              </SheetHeader>
              <GraphSwitcher />
              <ScheduleSidebar />
              <div className="flex min-h-0 w-full flex-1 flex-col gap-1">
                <ChatSectionBanner
                  expanded={threadsExpanded}
                  onToggle={() => setThreadsExpanded((v) => !v)}
                  count={threads.length}
                />
                {threadsExpanded ? (
                  <ThreadList
                    threads={threads}
                    onThreadClick={() => setChatHistoryOpen(false)}
                  />
                ) : null}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      )}
    </>
  );
}
