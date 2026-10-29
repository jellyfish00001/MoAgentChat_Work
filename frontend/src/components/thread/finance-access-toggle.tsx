// [ai_prepare 修改] 右上角：本機模擬「有無財務權限」

"use client";

import { useEffect } from "react";
import { useQueryState } from "nuqs";
import { BriefcaseBusiness } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLocalAccess } from "@/hooks/use-local-access";
import {
  isFinanceGraph,
  PUBLIC_GRAPH_ID,
} from "@/lib/local-graphs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function FinanceAccessToggle() {
  const { hasFinance, hydrated, setHasFinance } = useLocalAccess();
  const envAssistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
  const [assistantId, setAssistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const [, setThreadId] = useQueryState("threadId");

  const current = assistantId || envAssistantId || "";

  // 關閉財務權限時，若停在財務 Graph → 退回 Demo
  useEffect(() => {
    if (!hydrated) return;
    if (hasFinance) return;
    if (!isFinanceGraph(current)) return;
    void setThreadId(null);
    void setAssistantId(PUBLIC_GRAPH_ID);
  }, [hydrated, hasFinance, current, setAssistantId, setThreadId]);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            aria-label={
              hasFinance ? "目前：財務權限（點擊改為一般）" : "目前：一般（點擊改為財務）"
            }
            aria-pressed={hasFinance}
            onClick={() => setHasFinance(!hasFinance)}
            className={cn(
              "flex h-9 items-center gap-1.5 rounded-full border px-3 text-xs font-medium transition-colors",
              hasFinance
                ? "border-accent bg-accent text-accent-foreground"
                : "border-border bg-panel/80 text-muted-foreground hover:text-foreground",
            )}
          >
            <BriefcaseBusiness className="size-4 shrink-0" />
            <span className="hidden sm:inline">
              {hasFinance ? "財務" : "一般"}
            </span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-56">
          <p>
            本機模擬權限（非真 SSO）。一般＝僅 Demo；財務＝可切換三條業務
            Graph。
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
