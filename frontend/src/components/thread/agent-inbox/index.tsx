import { useEffect, useMemo, useState } from "react";
import { Interrupt } from "@langchain/langgraph-sdk";
import { cn } from "@/lib/utils";
import { HITLRequest } from "./types";
import { ThreadActionsView } from "./components/thread-actions-view";

interface ThreadViewProps {
  interrupt: Interrupt<HITLRequest> | Interrupt<HITLRequest>[];
}

export function ThreadView({ interrupt }: ThreadViewProps) {
  const interrupts = useMemo(
    () =>
      (Array.isArray(interrupt) ? interrupt : [interrupt]).filter(
        (item): item is Interrupt<HITLRequest> => !!item,
      ),
    [interrupt],
  );
  const [activeInterruptIndex, setActiveInterruptIndex] = useState(0);

  useEffect(() => {
    setActiveInterruptIndex(0);
  }, [interrupts.length]);

  const activeInterrupt = interrupts[activeInterruptIndex];

  if (!activeInterrupt) {
    return null;
  }

  return (
    <div className="border-border bg-panel flex w-full flex-col rounded-xl border p-4 sm:p-6">
      <div className="flex w-full flex-col gap-6">
        {interrupts.length > 1 && (
          <div className="flex flex-wrap items-center gap-2">
            {interrupts.map((it, idx) => {
              const title =
                (it.value?.action_requests?.[0]?.name === "send_mail"
                  ? "確認寄信"
                  : it.value?.action_requests?.[0]?.name) ??
                `待確認項目 ${idx + 1}`;
              return (
                <button
                  key={it.id ?? idx}
                  type="button"
                  onClick={() => setActiveInterruptIndex(idx)}
                  className={cn(
                    "rounded-sm border px-3 py-1 text-sm transition-colors",
                    idx === activeInterruptIndex
                      ? "border-accent bg-accent/15 text-foreground"
                      : "hover:border-primary hover:text-primary border-border bg-panel text-muted-foreground",
                  )}
                >
                  {title}
                </button>
              );
            })}
          </div>
        )}
        <ThreadActionsView interrupt={activeInterrupt} />
      </div>
    </div>
  );
}
