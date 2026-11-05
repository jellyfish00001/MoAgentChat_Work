"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { SelectField } from "@/components/ui/select-field";
import { NumberStepper } from "@/components/ui/number-stepper";
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
      className={cn("flex min-h-0 min-w-0 flex-col gap-3", className)}
    >
      {/* 可捲區：小視窗時欄位不撐破 Dialog；底部按鈕固定可見 */}
      <div className="scrollbar-ocean flex min-h-0 min-w-0 flex-1 flex-col gap-3 overflow-x-hidden overflow-y-auto overscroll-contain pr-0.5">
        <div className="flex shrink-0 flex-col gap-1.5">
          <Label htmlFor="schedule-title">標題</Label>
          <Input
            id="schedule-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="排程名稱"
            className="h-9 min-w-0 max-w-full text-sm"
          />
        </div>
        <div className="flex shrink-0 flex-col gap-1.5">
          <Label htmlFor="schedule-prompt" className="shrink-0">
            提示內容
          </Label>
          <Textarea
            id="schedule-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="執行時送給 Agent 的提示（可寫較長內容）"
            rows={4}
            className="field-sizing-fixed max-h-[min(28dvh,12rem)] min-h-[4.5rem] w-full min-w-0 resize-y text-sm leading-relaxed"
          />
        </div>
        <div className="flex shrink-0 flex-col gap-1.5">
          <Label htmlFor="schedule-kind">週期</Label>
          <SelectField
            id="schedule-kind"
            aria-label="週期"
            value={String(kind)}
            onChange={(v) => setKind(Number(v) as ScheduleKind)}
            options={[
              { value: String(ScheduleKind.Daily), label: "每日" },
              { value: String(ScheduleKind.Weekly), label: "每週" },
              { value: String(ScheduleKind.EveryNHours), label: "每 N 小時" },
            ]}
          />
        </div>
        {kind !== ScheduleKind.EveryNHours && (
          <div className="flex shrink-0 flex-col gap-1.5">
            <Label htmlFor="schedule-time">時間</Label>
            <Input
              id="schedule-time"
              type="time"
              value={timeOfDay}
              onChange={(e) => setTimeOfDay(e.target.value)}
              className="h-9 w-full min-w-0 max-w-full text-sm"
            />
          </div>
        )}
        {kind === ScheduleKind.Weekly && (
          <div className="flex shrink-0 flex-col gap-1.5">
            <Label htmlFor="schedule-weekday">星期</Label>
            <SelectField
              id="schedule-weekday"
              aria-label="星期"
              value={String(weekday)}
              onChange={(v) => setWeekday(Number(v))}
              options={WEEKDAYS.map((d) => ({
                value: String(d.value),
                label: d.label,
              }))}
            />
          </div>
        )}
        {kind === ScheduleKind.EveryNHours && (
          <div className="flex shrink-0 flex-col gap-1.5">
            <Label htmlFor="schedule-interval">間隔（小時）</Label>
            <NumberStepper
              id="schedule-interval"
              aria-label="間隔（小時）"
              min={1}
              max={168}
              value={intervalHours}
              onChange={setIntervalHours}
            />
          </div>
        )}
        <div className="border-border flex shrink-0 items-center justify-between gap-3 rounded-xl border px-3 py-2.5">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">暫不執行</p>
            <p className="text-muted-foreground text-xs break-words">
              開啟後排程不會自動跑，可稍後再開
            </p>
          </div>
          <Switch
            checked={paused}
            onCheckedChange={setPaused}
            aria-label="暫不執行"
            className="shrink-0"
          />
        </div>
      </div>
      <div className="bg-background flex shrink-0 justify-end gap-2 pt-2">
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
