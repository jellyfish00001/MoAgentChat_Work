import { cn } from "@/lib/utils";

/** 「排程」來源標籤（對話頂欄／確認卡使用）。 */
export function ScheduleBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "border-border bg-muted text-muted-foreground inline-flex shrink-0 items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium tracking-wide",
        className,
      )}
    >
      排程
    </span>
  );
}
