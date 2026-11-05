"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  createSchedule,
  patchSchedule,
  ScheduleKind,
  type CreateSchedulePayload,
  type ScheduleDto,
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

/** API timeOfDay（含秒）轉成 time input 用的 HH:mm。 */
function apiTimeToInput(value: string | null | undefined): string {
  if (!value) return "09:00";
  return value.slice(0, 5);
}

/** 新增／編輯排程表單（含「暫不執行」對應 enabled=false）。 */
export function ScheduleForm({
  className,
  assistantId,
  apiUrl,
  envApiUrl,
  initial,
  onDone,
  onCancel,
}: {
  className?: string;
  assistantId: string;
  apiUrl: string;
  envApiUrl?: string;
  /** 有值＝編輯模式；無＝新增。 */
  initial?: ScheduleDto | null;
  onDone?: () => void;
  onCancel?: () => void;
}) {
  const userId = useLocalUser();
  const editing = Boolean(initial);
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [kind, setKind] = useState<ScheduleKind>(ScheduleKind.Daily);
  const [timeOfDay, setTimeOfDay] = useState("09:00");
  const [weekday, setWeekday] = useState(1);
  const [intervalHours, setIntervalHours] = useState(3);
  /** true＝暫不執行 → API enabled=false。 */
  const [paused, setPaused] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  /** 開啟編輯時灌入既有欄位。 */
  useEffect(() => {
    if (!initial) {
      setTitle("");
      setPrompt("");
      setKind(ScheduleKind.Daily);
      setTimeOfDay("09:00");
      setWeekday(1);
      setIntervalHours(3);
      setPaused(false);
      return;
    }
    setTitle(initial.title);
    setPrompt(initial.prompt);
    setKind(initial.kind);
    setTimeOfDay(apiTimeToInput(initial.timeOfDay));
    setWeekday(initial.weekday ?? 1);
    setIntervalHours(initial.intervalHours ?? 3);
    setPaused(!initial.enabled);
  }, [initial]);

  /** 依 kind 組 payload；新增後若暫不執行再 patch enabled。 */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !prompt.trim()) {
      toast.error("請填寫標題與提示內容");
      return;
    }
    setSubmitting(true);
    try {
      const fields = {
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
      };

      if (editing && initial) {
        await patchSchedule(initial.id, {
          ...fields,
          enabled: !paused,
        });
        toast.success("排程已更新");
      } else {
        const body: CreateSchedulePayload = {
          userId,
          ...fields,
          assistantId: assistantId || "agent",
          apiUrl:
            resolveApiUrl(apiUrl, envApiUrl) || "http://127.0.0.1:2024",
        };
        // Create 契約無 enabled；暫不執行時建立後再 PATCH。
        const created = await createSchedule(body);
        if (paused) {
          await patchSchedule(created.id, { enabled: false });
        }
        toast.success("排程已建立");
      }
      onDone?.();
    } catch (err) {
      toast.error(editing ? "更新失敗" : "建立失敗", {
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("flex flex-col gap-3", className)}
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="schedule-title">標題</Label>
        <Input
          id="schedule-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="排程名稱"
          className="h-9 text-sm"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="schedule-prompt">提示內容</Label>
        <Textarea
          id="schedule-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="執行時送給 Agent 的提示"
          rows={3}
          className="min-h-0 resize-none text-sm"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="schedule-kind">週期</Label>
        <select
          id="schedule-kind"
          value={kind}
          onChange={(e) => setKind(Number(e.target.value) as ScheduleKind)}
          className="border-input bg-background text-foreground h-9 w-full rounded-md border px-2 text-sm"
        >
          <option value={ScheduleKind.Daily}>每日</option>
          <option value={ScheduleKind.Weekly}>每週</option>
          <option value={ScheduleKind.EveryNHours}>每 N 小時</option>
        </select>
      </div>
      {kind !== ScheduleKind.EveryNHours && (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="schedule-time">時間</Label>
          <Input
            id="schedule-time"
            type="time"
            value={timeOfDay}
            onChange={(e) => setTimeOfDay(e.target.value)}
            className="h-9 text-sm"
          />
        </div>
      )}
      {kind === ScheduleKind.Weekly && (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="schedule-weekday">星期</Label>
          <select
            id="schedule-weekday"
            value={weekday}
            onChange={(e) => setWeekday(Number(e.target.value))}
            className="border-input bg-background h-9 w-full rounded-md border px-2 text-sm"
          >
            {WEEKDAYS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      )}
      {kind === ScheduleKind.EveryNHours && (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="schedule-interval">間隔（小時）</Label>
          <Input
            id="schedule-interval"
            type="number"
            min={1}
            max={168}
            value={intervalHours}
            onChange={(e) => setIntervalHours(Number(e.target.value))}
            className="h-9 text-sm"
          />
        </div>
      )}
      <div className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2.5">
        <div className="min-w-0">
          <p className="text-sm font-medium">暫不執行</p>
          <p className="text-muted-foreground text-xs">
            開啟後排程不會自動跑，可稍後再開
          </p>
        </div>
        <Switch
          checked={paused}
          onCheckedChange={setPaused}
          aria-label="暫不執行"
        />
      </div>
      <div className="flex justify-end gap-2 pt-1">
        {onCancel ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onCancel}
            disabled={submitting}
          >
            取消
          </Button>
        ) : null}
        <Button type="submit" variant="accent" size="sm" disabled={submitting}>
          {submitting ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : editing ? (
            "儲存"
          ) : (
            "建立"
          )}
        </Button>
      </div>
    </form>
  );
}
