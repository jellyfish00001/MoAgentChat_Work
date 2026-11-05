"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { ScheduleDraft } from "@/lib/scheduleDraftParser";
import { LoaderCircle } from "lucide-react";
import { ScheduleBadge } from "./ScheduleBadge";

/** 聊天輸入攔截排程意圖後，在送出前讓使用者確認摘要與 prompt。 */
export function ScheduleConfirmCard({
  draft,
  creating,
  onConfirm,
  onCancel,
}: {
  draft: ScheduleDraft;
  creating?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
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
      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={creating}>
          取消
        </Button>
        <Button type="button" variant="accent" onClick={onConfirm} disabled={creating}>
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
