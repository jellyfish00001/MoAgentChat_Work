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

/** 新增／編輯排程的置中彈窗。 */
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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "編輯排程" : "新增排程"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "修改週期、提示或暫不執行狀態。"
              : "設定名稱、提示與執行週期。"}
          </DialogDescription>
        </DialogHeader>
        <ScheduleForm
          key={editing?.id ?? "create"}
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
