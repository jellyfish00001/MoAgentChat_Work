import { Button } from "@/components/ui/button";
import { useThreads } from "@/providers/Thread";
import { useStreamContext } from "@/providers/Stream";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

import { getContentString } from "../utils";
import { useQueryState, parseAsBoolean } from "nuqs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { PanelRightOpen, PanelRightClose } from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { GraphSwitcher } from "../graph-switcher";
import { Separator } from "@/components/ui/separator";

function ThreadList({
  threads,
  onThreadClick,
}: {
  threads: Thread[];
  onThreadClick?: (threadId: string) => void;
}) {
  const [threadId] = useQueryState("threadId");
  // [ai_prepare 修改] 用 SDK switchThread 清掉舊 stream，再載入選中對話
  const stream = useStreamContext();

  return (
    <div className="scrollbar-ocean flex h-full w-full flex-col items-start justify-start gap-2 overflow-y-scroll">
      {threads.map((t) => {
        let itemText = t.thread_id;
        if (
          typeof t.values === "object" &&
          t.values &&
          "messages" in t.values &&
          Array.isArray(t.values.messages) &&
          t.values.messages?.length > 0
        ) {
          const firstMessage = t.values.messages[0];
          itemText = getContentString(firstMessage.content);
        }
        const selected = t.thread_id === threadId;
        return (
          <div
            key={t.thread_id}
            className="w-full px-1"
          >
            <Button
              variant="ghost"
              className={cn(
                "w-[280px] items-start justify-start rounded-xl border-l-2 text-left font-normal",
                selected
                  ? "border-accent bg-muted text-foreground"
                  : "border-transparent",
              )}
              onClick={(e) => {
                e.preventDefault();
                onThreadClick?.(t.thread_id);
                if (t.thread_id === threadId) return;
                stream.switchThread(t.thread_id);
              }}
            >
              <p className="truncate text-ellipsis">{itemText}</p>
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function ThreadHistoryLoading() {
  return (
    <div className="scrollbar-ocean flex h-full w-full flex-col items-start justify-start gap-2 overflow-y-scroll">
      {Array.from({ length: 30 }).map((_, i) => (
        <Skeleton
          key={`skeleton-${i}`}
          className="h-10 w-[280px]"
        />
      ))}
    </div>
  );
}

export default function ThreadHistory() {
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  const [mounted, setMounted] = useState(false);
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false),
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

  return (
    <>
      <div className="border-sidebar-border bg-sidebar shadow-inner-right hidden h-screen w-[300px] shrink-0 flex-col items-start justify-start gap-4 border-r lg:flex">
        <div className="flex w-full items-center justify-between px-4 pt-1.5">
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
          <h1 className="font-mono text-xl font-semibold tracking-tight">
            Thread History
          </h1>
        </div>
        <GraphSwitcher compact />
        <Separator className="bg-sidebar-border mx-3 w-auto" />
        <div className="text-muted-foreground w-full px-4 text-xs font-medium tracking-wide uppercase">
          Threads
        </div>
        {threadsLoading ? (
          <ThreadHistoryLoading />
        ) : (
          <ThreadList threads={threads} />
        )}
      </div>
      {mounted && (
        <div className="lg:hidden">
          <Sheet
            open={!!chatHistoryOpen && !isLargeScreen}
            onOpenChange={(open) => {
              if (isLargeScreen) return;
              setChatHistoryOpen(open);
            }}
          >
            <SheetContent
              side="left"
              className="flex flex-col gap-4 lg:hidden"
            >
              <SheetHeader>
                <SheetTitle>Thread History</SheetTitle>
              </SheetHeader>
              <GraphSwitcher />
              <Separator />
              <ThreadList
                threads={threads}
                onThreadClick={() => setChatHistoryOpen(false)}
              />
            </SheetContent>
          </Sheet>
        </div>
      )}
    </>
  );
}
