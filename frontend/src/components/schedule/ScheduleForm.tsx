"use client";

import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  createSchedule,
  ScheduleKind,
  type CreateSchedulePayload,
} from "@/lib/schedule-api";
import { useLocalUser } from "@/hooks/useLocalUser";
import { resolveApiUrl } from "@/lib/resolve-api-url";
import { toast } from "sonner";
import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const WEEKDAYS = [
  { value: 0, label: "週日" },
  { value: 1, label: "週一" },
  { value: 2, label: "週二" },
  { value: 3, label: "週三" },
  { value: 4, label: "週四" },
  { value: 5, label: "週五" },
  { value: 6, label: "週六" },
];

/** 將 `<input type="time">` 的值轉成 API 的 timeOfDay（秒固定 :00）。 */
function timeInputToApi(value: string): string | null {
  if (!value) return null;
  const [h, m] = value.split(":");
  if (!h) return null;
  return `${h.padStart(2, "0")}:${(m ?? "00").padStart(2, "0")}:00`;
}

/** 側欄手動新增排程（標題、prompt、週期欄位）。 */
export function ScheduleForm({
  className,
  assistantId,
  apiUrl,
  envApiUrl,
  onCreated,
}: {
  className?: string;
  assistantId: string;
  apiUrl: string;
  envApiUrl?: string;
  onCreated?: () => void;
}) {
  const userId = useLocalUser();
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [kind, setKind] = useState<ScheduleKind>(ScheduleKind.Daily);
  const [timeOfDay, setTimeOfDay] = useState("09:00");
  const [weekday, setWeekday] = useState(1);
  const [intervalHours, setIntervalHours] = useState(3);
  const [submitting, setSubmitting] = useState(false);

  /** 依 kind 組 payload 並呼叫 createSchedule。 */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !prompt.trim()) {
      toast.error("請填寫標題與提示內容");
      return;
    }
    setSubmitting(true);
    try {
      const body: CreateSchedulePayload = {
        userId,
        title: title.trim(),
        prompt: prompt.trim(),
        kind,
        timeOfDay:
          kind === ScheduleKind.EveryNHours
            ? null
            : timeInputToApi(timeOfDay),
        weekday: kind === ScheduleKind.Weekly ? weekday : null,
        intervalHours:
          kind === ScheduleKind.EveryNHours ? intervalHours : null,
        assistantId: assistantId || "agent",
        apiUrl:
          resolveApiUrl(apiUrl, envApiUrl) || "http://127.0.0.1:2024",
      };
      await createSchedule(body);
      toast.success("排程已建立");
      setTitle("");
      setPrompt("");
      onCreated?.();
    } catch (err) {
      toast.error("建立失敗", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("flex flex-col gap-2 px-3 pb-2", className)}
    >
      <Label className="text-muted-foreground text-[11px] uppercase tracking-wide">
        新增排程
      </Label>
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="標題"
        className="h-8 text-sm"
      />
      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="執行時送給 Agent 的提示"
        rows={2}
        className="min-h-0 resize-none text-sm"
      />
      <select
        value={kind}
        onChange={(e) => setKind(Number(e.target.value) as ScheduleKind)}
        className="border-input bg-background text-foreground h-8 w-full rounded-md border px-2 text-sm"
      >
        <option value={ScheduleKind.Daily}>每日</option>
        <option value={ScheduleKind.Weekly}>每週</option>
        <option value={ScheduleKind.EveryNHours}>每 N 小時</option>
      </select>
      {kind !== ScheduleKind.EveryNHours && (
        <Input
          type="time"
          value={timeOfDay}
          onChange={(e) => setTimeOfDay(e.target.value)}
          className="h-8 text-sm"
        />
      )}
      {kind === ScheduleKind.Weekly && (
        <select
          value={weekday}
          onChange={(e) => setWeekday(Number(e.target.value))}
          className="border-input bg-background h-8 w-full rounded-md border px-2 text-sm"
        >
          {WEEKDAYS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </select>
      )}
      {kind === ScheduleKind.EveryNHours && (
        <Input
          type="number"
          min={1}
          max={168}
          value={intervalHours}
          onChange={(e) => setIntervalHours(Number(e.target.value))}
          className="h-8 text-sm"
          placeholder="小時"
        />
      )}
      <Button type="submit" variant="accent" size="sm" disabled={submitting}>
        {submitting ? (
          <LoaderCircle className="size-4 animate-spin" />
        ) : (
          "建立"
        )}
      </Button>
    </form>
  );
}
