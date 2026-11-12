"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { ScheduleDraft } from "@/lib/scheduleDraftParser";
import { LoaderCircle } from "lucide-react";
import { ScheduleBadge } from "./ScheduleBadge";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

/** 聊天輸入攔截排程意圖後，在送出前讓使用者確認摘要與 prompt。 */
export function ScheduleConfirmCard({
  draft,
  creating,
  onConfirm,
  onCancel,
}: {
  draft: ScheduleDraft;
  creating?: boolean;
  onConfirm: (autoSendMail: boolean) => void;
  onCancel: () => void;
}) {
  const [autoSendMail, setAutoSendMail] = useState(false);
  return (
    <Card className="border-border bg-panel/90 mx-auto mb-2 w-full max-w-3xl gap-3 border p-4 shadow-sm backdrop-blur-md">
      <div className="flex flex-wrap items-center gap-2">
        <ScheduleBadge />
        <span className="text-foreground text-sm font-medium">建立排程？</span>
      </div>
      <p className="text-muted-foreground text-sm">{draft.summary}</p>
      <p className="text-foreground text-sm">
        <span className="text-muted-foreground">執行內容：</span>
        {draft.prompt}
      </p>
      <label className="flex items-center justify-between gap-3 text-sm">
        <span>
          信件自動發送
          <span className="text-muted-foreground block text-xs">
            {autoSendMail
              ? "確認建立即授權自動寄信，不再逐封詢問。"
              : "關閉時，寄信會等待你在對話中確認。"}
          </span>
        </span>
        <Switch
          checked={autoSendMail}
          onCheckedChange={setAutoSendMail}
          disabled={creating}
          aria-label="信件自動發送"
        />
      </label>
      <div className="flex justify-end gap-2 pt-1">
        <Button
          type="button"
          variant="ghost"
          onClick={onCancel}
          disabled={creating}
        >
          取消
        </Button>
        <Button
          type="button"
          variant="accent"
          onClick={() => onConfirm(autoSendMail)}
          disabled={creating}
        >
          {creating ? (
            <>
              <LoaderCircle className="mr-1 size-4 animate-spin" />
              建立中…
            </>
          ) : (
            "確認建立"
          )}
        </Button>
      </div>
    </Card>
  );
}
