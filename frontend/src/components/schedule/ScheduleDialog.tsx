"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScheduleForm } from "./ScheduleForm";
import type { ScheduleDto } from "@/lib/schedule-api";

/** 新增／編輯排程的置中彈窗（寬高跟視窗比例，絕不超出可視區）。 */
export function ScheduleDialog({
  open,
  onOpenChange,
  assistantId,
  apiUrl,
  envApiUrl,
  editing,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assistantId: string;
  apiUrl: string;
  envApiUrl?: string;
  /** null／undefined＝新增；有值＝編輯該筆。 */
  editing?: ScheduleDto | null;
  onSaved?: () => void;
}) {
  const isEdit = Boolean(editing);

  /** 關閉彈窗。 */
  const close = () => onOpenChange(false);

  /** 儲存成功後關閉並通知父層刷新。 */
  const handleDone = () => {
    onSaved?.();
    close();
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent
        className={
          // 覆蓋預設：用 100dvh／100vw 扣邊距；min-h-0＋內部捲動，避免小視窗底部被裁
          "flex !h-auto max-h-[calc(100dvh-1.5rem)] min-h-0 w-[calc(100vw-1.5rem)] max-w-2xl flex-col gap-3 !overflow-hidden p-4 sm:gap-4 sm:p-6"
        }
      >
        <DialogHeader className="shrink-0 pr-8">
          <DialogTitle>{isEdit ? "編輯排程" : "新增排程"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "修改週期、提示或暫不執行狀態。"
              : "設定名稱、提示、執行週期與寄信確認方式。"}
          </DialogDescription>
        </DialogHeader>
        <ScheduleForm
          key={editing?.id ?? "create"}
          className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden"
          assistantId={assistantId}
          apiUrl={apiUrl}
          envApiUrl={envApiUrl}
          initial={editing}
          onDone={handleDone}
          onCancel={close}
        />
      </DialogContent>
    </Dialog>
  );
}
