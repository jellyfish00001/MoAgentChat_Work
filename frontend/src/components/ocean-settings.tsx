"use client";

import { useEffect, useRef, useState } from "react";
import { Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { UI_THEMES, type UiTheme } from "@/lib/ui-theme";

const MIN_SHARKS = 0;
const MAX_SHARKS = 8;

interface OceanSettingsProps {
  enabled: boolean;
  sharkCount: number;
  theme: UiTheme;
  onEnabledChange: (v: boolean) => void;
  onSharkCountChange: (v: number) => void;
  onThemeChange: (v: UiTheme) => void;
}

/**
 * 背景設定：動畫開關、鯊魚數量、Theme 色塊 icon（Light / Dark）。
 */
export function OceanSettings({
  enabled,
  sharkCount,
  theme,
  onEnabledChange,
  onSharkCountChange,
  onThemeChange,
}: OceanSettingsProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div
      ref={rootRef}
      className="relative"
    >
      <button
        type="button"
        aria-label="背景設定"
        aria-expanded={open}
        onClick={() => setOpen((p) => !p)}
        className={cn(
          "text-foreground hover:bg-muted flex size-9 items-center justify-center rounded-full transition-colors",
          open && "bg-muted",
        )}
      >
        <Settings2 className="size-5" />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="背景設定"
          className="bg-panel/80 text-panel-foreground border-border absolute top-11 right-0 z-30 w-64 rounded-2xl border p-4 shadow-lg backdrop-blur-md"
        >
          <p className="mb-3 text-sm font-semibold tracking-tight">背景設定</p>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm">背景動畫</span>
            <Switch
              checked={enabled}
              onCheckedChange={onEnabledChange}
            />
          </div>

          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-muted-foreground text-sm">鯊魚數量</span>
              <span className="text-muted-foreground text-sm tabular-nums">
                {sharkCount}
              </span>
            </div>
            <input
              type="range"
              min={MIN_SHARKS}
              max={MAX_SHARKS}
              step={1}
              value={sharkCount}
              disabled={!enabled}
              onChange={(e) => onSharkCountChange(Number(e.target.value))}
              className="accent-accent w-full disabled:opacity-40"
            />
          </div>

          <div className="mt-4">
            <p className="text-muted-foreground mb-2 text-sm">Theme</p>
            <div className="flex items-center gap-2">
              {UI_THEMES.map((t) => {
                const selected = theme === t.value;
                return (
                  <button
                    key={t.value}
                    type="button"
                    title={t.label}
                    aria-label={t.label}
                    aria-pressed={selected}
                    onClick={() => onThemeChange(t.value)}
                    className={cn(
                      "focus-visible:ring-ring relative size-8 overflow-hidden rounded-full border transition-shadow",
                      selected
                        ? "border-accent ring-accent ring-2 ring-offset-2 ring-offset-panel"
                        : "border-border hover:border-primary",
                    )}
                  >
                    <span
                      className="absolute inset-0"
                      style={{
                        background: `linear-gradient(135deg, ${t.swatch[0]} 50%, ${t.swatch[1]} 50%)`,
                      }}
                    />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
