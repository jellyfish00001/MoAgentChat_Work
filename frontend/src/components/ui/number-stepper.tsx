"use client";

import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

/** 主題化數字加減（隱藏原生 number spinner）。 */
export function NumberStepper({
  id,
  value,
  min = 1,
  max = 168,
  onChange,
  className,
  "aria-label": ariaLabel,
}: {
  id?: string;
  value: number;
  min?: number;
  max?: number;
  onChange: (value: number) => void;
  className?: string;
  "aria-label"?: string;
}) {
  /** 夾在 min～max 後回傳。 */
  const clamp = (n: number) => Math.min(max, Math.max(min, n));

  /** 輸入框變更（允許暫時空字，失焦再校正）。 */
  const handleChange = (raw: string) => {
    if (raw === "") {
      onChange(min);
      return;
    }
    const n = Number(raw);
    if (Number.isFinite(n)) onChange(clamp(n));
  };

  return (
    <div
      className={cn(
        "border-input bg-panel focus-within:border-ring focus-within:ring-ring/40 flex h-9 w-full items-stretch overflow-hidden rounded-xl border focus-within:ring-[2px]",
        className,
      )}
    >
      <input
        id={id}
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        value={value}
        aria-label={ariaLabel}
        onChange={(e) => handleChange(e.target.value)}
        className={cn(
          "text-foreground min-w-0 flex-1 bg-transparent px-3 text-sm outline-none",
          // 隱藏瀏覽器預設上下箭頭（與主題不相容）
          "[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none",
        )}
      />
      <div className="border-border flex shrink-0 flex-col border-l">
        <button
          type="button"
          className="text-muted-foreground hover:bg-muted hover:text-foreground flex h-1/2 items-center justify-center px-2"
          aria-label="增加"
          onClick={() => onChange(clamp(value + 1))}
        >
          <ChevronUp className="size-3.5" />
        </button>
        <button
          type="button"
          className="text-muted-foreground hover:bg-muted hover:text-foreground border-border flex h-1/2 items-center justify-center border-t px-2"
          aria-label="減少"
          onClick={() => onChange(clamp(value - 1))}
        >
          <ChevronDown className="size-3.5" />
        </button>
      </div>
    </div>
  );
}
