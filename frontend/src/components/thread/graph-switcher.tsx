// [ai_prepare 修改] Thread History 上方：依權限切換 LangGraph

"use client";

import { useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  getGraphOption,
  graphsForAccess,
  isFinanceGraph,
  PUBLIC_GRAPH_ID,
  type LocalGraphOption,
} from "@/lib/local-graphs";
import { useLocalAccess } from "@/hooks/use-local-access";
import { useQueryState } from "nuqs";

/** 一組可選 Graph tab（無群組標題，僅按鈕列）。 */
function GraphGroup({
  options,
  current,
  compact,
  onSelect,
}: {
  options: LocalGraphOption[];
  current: string;
  compact: boolean;
  onSelect: (id: string) => void;
}) {
  if (options.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
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

/** 側欄角色切換：僅顯示可選 Graph，不含說明文案。 */
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

  /** 無財務權限時強制退回公開 Demo Graph。 */
  useEffect(() => {
    if (!hydrated) return;
    if (!isFinanceGraph(current)) return;
    if (hasFinance) return;
    void setAssistantId(PUBLIC_GRAPH_ID);
    void setThreadId(null);
  }, [hydrated, hasFinance, current, setAssistantId, setThreadId]);

  /** 切換 Graph：清 threadId，由 StreamSession 重建對話。 */
  const selectGraph = (id: string) => {
    if (id === current) return;
    if (!allowed.some((g) => g.id === id)) return;
    void setThreadId(null);
    void setAssistantId(id);
  };

  return (
    <div className={cn("flex w-full flex-col gap-2 px-3", className)}>
      <div
        className="flex flex-col gap-2"
        role="tablist"
        aria-label="選擇 LangGraph 流程"
      >
        <GraphGroup
          options={publicGraphs}
          current={current}
          compact={compact}
          onSelect={selectGraph}
        />
        {hasFinance ? (
          <GraphGroup
            options={financeGraphs}
            current={current}
            compact={compact}
            onSelect={selectGraph}
          />
        ) : null}
      </div>
    </div>
  );
}

/** 主畫面頂欄／空狀態：只顯示 shortLabel（如 Demo），不重複長名與副標。 */
export function CurrentGraphBadge({ className }: { className?: string }) {
  const envAssistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const current = assistantId || envAssistantId || "";
  const option = getGraphOption(current);
  const text = option?.shortLabel ?? (current || "未選擇");

  return (
    <span
      className={cn(
        "border-border bg-panel/80 text-muted-foreground inline-flex max-w-[16rem] items-center truncate rounded-full border px-2.5 py-0.5 text-xs",
        className,
      )}
      title={option?.label ?? current ?? undefined}
    >
      <span className="truncate">{text}</span>
    </span>
  );
}
