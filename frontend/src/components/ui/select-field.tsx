"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export type SelectFieldOption = {
  value: string;
  label: string;
};

/** 主題一致的下拉（避免原生 select 系統白底方框；選單 portal 避免 Dialog overflow 裁切）。 */
export function SelectField({
  id,
  value,
  options,
  onChange,
  className,
  "aria-label": ariaLabel,
}: {
  id?: string;
  value: string;
  options: SelectFieldOption[];
  onChange: (value: string) => void;
  className?: string;
  "aria-label"?: string;
}) {
  const autoId = useId();
  const listId = `${id ?? autoId}-listbox`;
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const [open, setOpen] = useState(false);
  const [menuPos, setMenuPos] = useState<{
    top: number;
    left: number;
    width: number;
  } | null>(null);
  const selected = options.find((o) => o.value === value) ?? options[0];

  /** 依觸發鈕定位 fixed 選單（對齊寬度）。 */
  useLayoutEffect(() => {
    if (!open) {
      setMenuPos(null);
      return;
    }
    const el = triggerRef.current;
    if (!el) return;
    /** 重新量測位置（resize／scroll）。 */
    const place = () => {
      const r = el.getBoundingClientRect();
      setMenuPos({ top: r.bottom + 6, left: r.left, width: r.width });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [open]);

  /** 點擊外側或 Esc 關閉選單。 */
  useEffect(() => {
    if (!open) return;
    /** 點在觸發鈕／選單外則收合。 */
    const onPointer = (e: MouseEvent) => {
      const t = e.target as Node;
      if (rootRef.current?.contains(t) || listRef.current?.contains(t)) return;
      setOpen(false);
    };
    /** Esc 關閉。 */
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer, true);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer, true);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  /** 選一項後關閉並回傳 value。 */
  const pick = (next: string) => {
    onChange(next);
    setOpen(false);
  };

  const menu =
    open && menuPos && typeof document !== "undefined"
      ? createPortal(
          <ul
            ref={listRef}
            id={listId}
            role="listbox"
            className="border-border bg-panel text-panel-foreground fixed z-[90] max-h-[min(14rem,40vh)] overflow-auto rounded-xl border p-1 shadow-lg"
            style={{
              top: menuPos.top,
              left: menuPos.left,
              width: menuPos.width,
            }}
          >
            {options.map((o) => {
              const active = o.value === value;
              return (
                <li key={o.value} role="option" aria-selected={active}>
                  <button
                    type="button"
                    className={cn(
                      "text-foreground hover:bg-muted w-full rounded-lg px-2.5 py-2 text-left text-sm",
                      active && "bg-muted font-medium",
                    )}
                    onClick={() => pick(o.value)}
                  >
                    {o.label}
                  </button>
                </li>
              );
            })}
          </ul>,
          document.body,
        )
      : null;

  return (
    <div ref={rootRef} className={cn("relative min-w-0 w-full", className)}>
      <button
        ref={triggerRef}
        id={id}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={ariaLabel}
        className={cn(
          "border-input bg-panel text-foreground focus-visible:border-ring focus-visible:ring-ring/40 flex h-9 w-full min-w-0 items-center justify-between gap-2 rounded-xl border px-3 text-left text-sm outline-none focus-visible:ring-[2px]",
          open && "border-ring ring-ring/40 ring-[2px]",
        )}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="min-w-0 truncate">{selected?.label ?? ""}</span>
        <ChevronDown
          className={cn(
            "text-muted-foreground size-4 shrink-0 transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {menu}
    </div>
  );
}
