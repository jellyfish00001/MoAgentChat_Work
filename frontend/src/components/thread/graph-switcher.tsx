// [ai_prepare 修改] Thread History 上方：依權限切換 LangGraph

"use client";

import { useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  graphsForAccess,
  isFinanceGraph,
  PUBLIC_GRAPH_ID,
  resolveGraphLabel,
  type LocalGraphOption,
} from "@/lib/local-graphs";
import { useLocalAccess } from "@/hooks/use-local-access";
import { useQueryState } from "nuqs";

function GraphGroup({
  title,
  options,
  current,
  compact,
  onSelect,
}: {
  title: string;
  options: LocalGraphOption[];
  current: string;
  compact: boolean;
  onSelect: (id: string) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
      <div className="text-muted-foreground px-1 text-[11px] font-medium tracking-wide uppercase">
        {title}
      </div>
      {options.map((g) => {
        const selected = g.id === current;
        return (
          <Button
            key={g.id}
            type="button"
            role="tab"
            aria-selected={selected}
            variant="ghost"
            className={cn(
              "h-auto w-full justify-start rounded-xl border px-3 py-2 text-left font-normal whitespace-normal",
              selected
                ? "border-accent bg-muted text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
            onClick={() => onSelect(g.id)}
            title={`${g.id} → LangSmith: ${g.langsmithProject}`}
          >
            <span className="truncate text-sm">
              {compact ? g.shortLabel : g.label}
            </span>
          </Button>
        );
      })}
    </div>
  );
}

export function GraphSwitcher({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  const envAssistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
  const [assistantId, setAssistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const [, setThreadId] = useQueryState("threadId");
  const { hasFinance, hydrated } = useLocalAccess();

  const current = assistantId || envAssistantId || "";
  const allowed = useMemo(
    () => graphsForAccess(hasFinance),
    [hasFinance],
  );
  const publicGraphs = allowed.filter((g) => g.access === "public");
  const financeGraphs = allowed.filter((g) => g.access === "finance");

  useEffect(() => {
    if (!hydrated) return;
    if (!isFinanceGraph(current)) return;
    if (hasFinance) return;
    void setAssistantId(PUBLIC_GRAPH_ID);
    void setThreadId(null);
  }, [hydrated, hasFinance, current, setAssistantId, setThreadId]);

  const selectGraph = (id: string) => {
    if (id === current) return;
    if (!allowed.some((g) => g.id === id)) return;
    // 一次更新，避免連續改 URL 造成閃爍；清對話由 StreamSession 聽 assistantId
    void setThreadId(null);
    void setAssistantId(id);
  };

  return (
    <div className={cn("flex w-full flex-col gap-3 px-3", className)}>
      <div className="text-muted-foreground px-1 text-xs font-medium tracking-wide uppercase">
        LangGraph
      </div>
      <div
        className="flex flex-col gap-3"
        role="tablist"
        aria-label="選擇 LangGraph 流程"
      >
        <GraphGroup
          title="全員 · Demo"
          options={publicGraphs}
          current={current}
          compact={compact}
          onSelect={selectGraph}
        />
        {hasFinance ? (
          <GraphGroup
            title="財務專用"
            options={financeGraphs}
            current={current}
            compact={compact}
            onSelect={selectGraph}
          />
        ) : (
          <p className="text-muted-foreground px-1 text-[11px] leading-snug">
            財務三條路線已隱藏。右上角切換為「財務」後可見。
          </p>
        )}
      </div>
      <p className="text-muted-foreground px-1 text-[11px] leading-snug">
        目前：{resolveGraphLabel(current)}
        {hydrated ? (hasFinance ? " · 財務權限" : " · 一般") : ""}
      </p>
    </div>
  );
}

export function CurrentGraphBadge({ className }: { className?: string }) {
  const envAssistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const current = assistantId || envAssistantId || "";
  const label = resolveGraphLabel(current);
  const finance = isFinanceGraph(current);

  return (
    <span
      className={cn(
        "border-border bg-panel/80 text-muted-foreground inline-flex max-w-[16rem] items-center gap-1.5 truncate rounded-full border px-2.5 py-0.5 text-xs backdrop-blur-sm",
        className,
      )}
      title={current || undefined}
    >
      <span className="truncate">{label}</span>
      <span
        className={cn(
          "shrink-0 rounded-full px-1.5 py-px text-[10px]",
          finance
            ? "bg-accent text-accent-foreground"
            : "bg-muted text-muted-foreground",
        )}
      >
        {finance ? "財務" : "Demo"}
      </span>
    </span>
  );
}
