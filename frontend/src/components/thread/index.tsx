import { v4 as uuidv4 } from "uuid";
import { ReactNode, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";
import { useMemo, useState, FormEvent } from "react";
import { Button } from "../ui/button";
import { Checkpoint, Message } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "./messages/ai";
import { HumanMessage } from "./messages/human";
import {
  DO_NOT_RENDER_ID_PREFIX,
  ensureToolCallsHaveResponses,
} from "@/lib/ensure-tool-responses";
import { LangGraphLogoSVG } from "../icons/langgraph";
import { TooltipIconButton } from "./tooltip-icon-button";
import {
  ArrowDown,
  LoaderCircle,
  PanelRightOpen,
  PanelRightClose,
  SquarePen,
  XIcon,
  Plus,
} from "lucide-react";
import { useQueryState, parseAsBoolean } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import ThreadHistory from "./history";
import { CurrentGraphBadge } from "./graph-switcher";
import { FinanceAccessToggle } from "./finance-access-toggle";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { useFileUpload } from "@/hooks/use-file-upload";
import { useOceanSettings } from "@/hooks/use-ocean-settings";
import { AsciiOcean } from "@/components/ascii-ocean";
import { OceanSettings } from "@/components/ocean-settings";
import type { SharkSpec } from "@/lib/ascii-sharks";
import { ContentBlocksPreview } from "./ContentBlocksPreview";
import { Textarea } from "../ui/textarea";
import { useScheduleComposer } from "@/hooks/useScheduleComposer";
import { ScheduleConfirmCard } from "@/components/schedule/ScheduleConfirmCard";
import { ScheduleThreadHeader } from "@/components/schedule/ScheduleThreadHeader";
import { ScheduleKind } from "@/lib/schedule-api";
import type { ScheduleDraft } from "@/lib/scheduleDraftParser";

// [ai_prepare 修改] 依數量／體型／速度產生鯊魚陣容（classic，大小交錯，決定性不閃爍）
function buildSharkRoster(
  count: number,
  sizeScale: number,
  speedScale: number,
): SharkSpec[] {
  const sizes = [1, 0.7, 0.84, 0.77, 0.62, 0.9, 0.55, 0.8];
  return Array.from({ length: count }, (_, i) => ({
    kind: "classic" as const,
    size: sizes[i % sizes.length],
    sizeScale,
    speedScale,
  }));
}
import {
  useArtifactOpen,
  ArtifactContent,
  ArtifactTitle,
  useArtifactContext,
} from "./artifact";

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  return (
    <div
      ref={context.scrollRef}
      style={{ width: "100%" }}
      className={cn("h-full", props.className)}
    >
      <div
        ref={context.contentRef}
        className={props.contentClassName}
      >
        {props.content}
      </div>

      {props.footer}
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="h-4 w-4" />
      <span>Scroll to bottom</span>
    </Button>
  );
}

function ConnectedHost({ apiUrl }: { apiUrl: string }) {
  let host: string;
  try {
    host = new URL(apiUrl).host;
  } catch {
    host = apiUrl;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="text-muted-foreground hidden max-w-40 truncate text-xs sm:inline">
            {host}
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Connected to {apiUrl}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function Thread() {
  const [artifactContext, setArtifactContext] = useArtifactContext();
  const [artifactOpen, closeArtifact] = useArtifactOpen();

  const [threadId, _setThreadId] = useQueryState("threadId");
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: process.env.NEXT_PUBLIC_ASSISTANT_ID || "",
  });
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false).withOptions({
      history: "replace",
      shallow: true,
    }),
  );
  const [hideToolCalls, setHideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );
  const [input, setInput] = useState("");
  const {
    contentBlocks,
    setContentBlocks,
    handleFileUpload,
    dropRef,
    removeBlock,
    resetBlocks: _resetBlocks,
    dragOver,
    handlePaste,
  } = useFileUpload();
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  // [ai_prepare 修改] ASCII 海洋背景設定（開關／鯊魚數量／色系，存 localStorage）
  const ocean = useOceanSettings();
  // 鯊魚陣容只在數量／體型／速度改變時重建（避免每次 render 新陣列導致 engine 重建）
  const sharkRoster = useMemo(
    () =>
      buildSharkRoster(
        ocean.sharkCount,
        ocean.sharkSizeScale,
        ocean.sharkSpeedScale,
      ),
    [ocean.sharkCount, ocean.sharkSizeScale, ocean.sharkSpeedScale],
  );

  const stream = useStreamContext();
  const messages = stream.messages;
  const isLoading = stream.isLoading;

  // [ai_prepare] 自然語句排程：攔截 submit、顯示確認卡而非直接送訊息
  const scheduleComposer = useScheduleComposer({
    assistantId: assistantId || process.env.NEXT_PUBLIC_ASSISTANT_ID || "agent",
    apiUrl: stream.apiUrl,
    envApiUrl: process.env.NEXT_PUBLIC_API_URL,
  });
  // 驗收用：?scheduleConfirmPreview=1 顯示靜態確認卡（不寫庫、不送訊）
  const [scheduleConfirmPreview] = useQueryState(
    "scheduleConfirmPreview",
    parseAsBoolean.withDefault(false),
  );
  const previewDraft: ScheduleDraft | null = scheduleConfirmPreview
    ? {
        title: "檢查排程側欄",
        prompt: "檢查排程側欄",
        kind: ScheduleKind.Daily,
        timeOfDay: "09:00:00",
        weekday: null,
        intervalHours: null,
        summary: "每日 09:00 · 檢查排程側欄",
      }
    : null;

  const lastError = useRef<string | undefined>(undefined);

  const setThreadId = (id: string | null) => {
    _setThreadId(id);

    // close artifact and reset artifact context
    closeArtifact();
    setArtifactContext({});
  };

  useEffect(() => {
    if (!stream.error) {
      lastError.current = undefined;
      return;
    }
    try {
      const message = (stream.error as any).message;
      if (!message || lastError.current === message) {
        // Message has already been logged. do not modify ref, return early.
        return;
      }

      // Message is defined, and it has not been logged yet. Save it, and send the error
      lastError.current = message;
      toast.error("An error occurred. Please try again.", {
        description: (
          <p>
            <strong>Error:</strong> <code>{message}</code>
          </p>
        ),
        richColors: true,
        closeButton: true,
      });
    } catch {
      // no-op
    }
  }, [stream.error]);

  // [upstream TODO] first-token flag belongs in useStream — keep until vendor upgrade (open-decisions D3)
  const prevMessageLength = useRef(0);
  useEffect(() => {
    if (
      messages.length !== prevMessageLength.current &&
      messages?.length &&
      messages[messages.length - 1].type === "ai"
    ) {
      setFirstTokenReceived(true);
    }

    prevMessageLength.current = messages.length;
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if ((input.trim().length === 0 && contentBlocks.length === 0) || isLoading)
      return;
    // 辨識排程意圖時改走確認流程
    if (scheduleComposer.tryIntercept(input, contentBlocks.length)) return;
    setFirstTokenReceived(false);

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content: [
        ...(input.trim().length > 0 ? [{ type: "text", text: input }] : []),
        ...contentBlocks,
      ] as Message["content"],
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);

    const context =
      Object.keys(artifactContext).length > 0 ? artifactContext : undefined;

    // [ai_prepare 修改] 建立 thread 時寫入 graph_id，歷史才能依 Graph 過濾
    const graphId =
      assistantId || process.env.NEXT_PUBLIC_ASSISTANT_ID || "agent";

    stream.submit(
      { messages: [...toolMessages, newHumanMessage], context },
      {
        streamMode: ["values"],
        streamSubgraphs: true,
        streamResumable: true,
        metadata: { graph_id: graphId },
        optimisticValues: (prev) => ({
          ...prev,
          context,
          messages: [
            ...(prev.messages ?? []),
            ...toolMessages,
            newHumanMessage,
          ],
        }),
      },
    );

    setInput("");
    setContentBlocks([]);
  };

  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    // Do this so the loading state is correct
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
    });
  };

  const chatStarted = !!threadId || !!messages.length;
  const hasNoAIOrToolMessages = !messages.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  return (
    <div className="relative flex h-screen w-full overflow-hidden">
      {/* 全視窗海洋／聚光：不隨側欄開合 resize，避免 canvas 重建閃爍 */}
      {ocean.enabled && (
        <div
          className={cn(
            "pointer-events-none absolute inset-0 z-0 overflow-hidden",
            chatStarted && "opacity-40",
          )}
        >
          <AsciiOcean sharks={sharkRoster} />
          <div className="from-background/90 via-background/30 absolute inset-x-0 top-0 h-24 bg-gradient-to-b to-transparent" />
        </div>
      )}
      <div
        aria-hidden
        className="spotlight-focus pointer-events-none absolute inset-0 z-[5]"
      />

      <div className="relative z-20 hidden lg:flex">
        <motion.div
          className="border-sidebar-border bg-sidebar/95 absolute h-full overflow-hidden border-r backdrop-blur-md"
          style={{ width: 300 }}
          animate={{ x: chatHistoryOpen ? 0 : -300 }}
          initial={{ x: -300 }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          <div
            className="relative h-full"
            style={{ width: 300 }}
          >
            <ThreadHistory />
          </div>
        </motion.div>
      </div>

      <div
        className={cn(
          "relative z-10 grid w-full grid-cols-[1fr_0fr] transition-all duration-500",
          artifactOpen && "grid-cols-[3fr_2fr]",
        )}
      >
        <motion.div
          className={cn(
            "relative flex min-w-0 flex-1 flex-col overflow-hidden",
            !chatStarted && "grid-rows-[1fr]",
          )}
          animate={{
            marginLeft: chatHistoryOpen ? (isLargeScreen ? 300 : 0) : 0,
            width: chatHistoryOpen
              ? isLargeScreen
                ? "calc(100% - 300px)"
                : "100%"
              : "100%",
          }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          {/* Sticky top bar — frosted so scrolled messages don't collide with logo */}
          <div className="border-border/40 bg-background/75 absolute top-0 left-0 z-10 flex w-full items-center justify-between gap-3 border-b p-2 pl-4 backdrop-blur-md">
            <div className="relative flex min-w-0 flex-1 items-center justify-start gap-2">
              {(!chatHistoryOpen || !isLargeScreen) && (
                <Button
                  variant="ghost"
                  onClick={() => setChatHistoryOpen((p) => !p)}
                >
                  {chatHistoryOpen ? (
                    <PanelRightOpen className="size-5" />
                  ) : (
                    <PanelRightClose className="size-5" />
                  )}
                </Button>
              )}
              {chatStarted && (
                <>
                  <motion.button
                    className="flex shrink-0 cursor-pointer items-center gap-2"
                    onClick={() => setThreadId(null)}
                    type="button"
                  >
                    <LangGraphLogoSVG className="text-foreground h-8 w-8" />
                    <span className="text-xl font-semibold tracking-tight">
                      W.AgentChat
                    </span>
                  </motion.button>
                  {/* [ai_prepare 修改] 標示目前所屬 LangGraph */}
                  <CurrentGraphBadge />
                  {/* [ai_prepare] 排程執行產生的 thread 顯示標題 */}
                  <ScheduleThreadHeader
                    apiUrl={stream.apiUrl}
                    envApiUrl={process.env.NEXT_PUBLIC_API_URL}
                    authScheme={process.env.NEXT_PUBLIC_AUTH_SCHEME}
                  />
                  <ConnectedHost apiUrl={stream.apiUrl} />
                </>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-1">
              {/* [ai_prepare 修改] 本機模擬：一般／財務權限 */}
              <FinanceAccessToggle />
              <OceanSettings
                enabled={ocean.enabled}
                sharkCount={ocean.sharkCount}
                sharkSizeScale={ocean.sharkSizeScale}
                sharkSpeedScale={ocean.sharkSpeedScale}
                theme={ocean.theme}
                onEnabledChange={ocean.setEnabled}
                onSharkCountChange={ocean.setSharkCount}
                onSharkSizeScaleChange={ocean.setSharkSizeScale}
                onSharkSpeedScaleChange={ocean.setSharkSpeedScale}
                onThemeChange={ocean.setTheme}
              />
              {chatStarted && (
                <TooltipIconButton
                  size="lg"
                  className="p-4"
                  tooltip="New thread"
                  variant="ghost"
                  onClick={() => setThreadId(null)}
                >
                  <SquarePen className="size-5" />
                </TooltipIconButton>
              )}
            </div>
          </div>

          {/* inset-0 + pt-16: clear frosted header without breaking sticky input (avoid top+height:100%) */}
          <StickToBottom className="relative z-[1] min-h-0 flex-1 overflow-hidden">
            <StickyToBottomContent
              className={cn(
                "scrollbar-ocean absolute inset-0 overflow-y-scroll px-4",
                chatStarted && "pt-16",
                !chatStarted && "mt-[20vh] flex flex-col items-stretch",
                chatStarted && "grid grid-rows-[1fr_auto]",
              )}
              contentClassName="pt-4 pb-16 max-w-3xl mx-auto flex flex-col gap-4 w-full relative z-[1]"
              content={
                <>
                  {messages
                    .filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX))
                    .map((message, index) =>
                      message.type === "human" ? (
                        <HumanMessage
                          key={message.id || `${message.type}-${index}`}
                          message={message}
                          isLoading={isLoading}
                        />
                      ) : (
                        <AssistantMessage
                          key={message.id || `${message.type}-${index}`}
                          message={message}
                          isLoading={isLoading}
                          handleRegenerate={handleRegenerate}
                        />
                      ),
                    )}
                  {/* Special rendering case where there are no AI/tool messages, but there is an interrupt.
                    We need to render it outside of the messages list, since there are no messages to render */}
                  {hasNoAIOrToolMessages && !!stream.interrupt && (
                    <AssistantMessage
                      key="interrupt-msg"
                      message={undefined}
                      isLoading={isLoading}
                      handleRegenerate={handleRegenerate}
                    />
                  )}
                  {isLoading && !firstTokenReceived && (
                    <AssistantMessageLoading />
                  )}
                </>
              }
              footer={
                <div className="sticky bottom-0 z-[1] flex flex-col items-center gap-8 bg-transparent">
                  {!chatStarted && (
                    <div className="border-border bg-panel/75 text-panel-foreground flex flex-col items-center gap-2 rounded-3xl border px-5 py-3 shadow-sm backdrop-blur-md">
                      <div className="flex items-center gap-3">
                        <LangGraphLogoSVG className="text-foreground h-8 w-8 flex-shrink-0" />
                        <h1 className="text-2xl font-semibold tracking-tight">
                          W.AgentChat
                        </h1>
                      </div>
                      {/* [ai_prepare 修改] 空對話也顯示目前 Graph */}
                      <CurrentGraphBadge />
                    </div>
                  )}

                  <ScrollToBottom className="animate-in fade-in-0 zoom-in-95 absolute bottom-full left-1/2 mb-4 -translate-x-1/2" />

                  {/* [ai_prepare] 排程草稿確認（取代一般輸入送出；preview 僅視覺驗收） */}
                  {scheduleComposer.draft || previewDraft ? (
                    <ScheduleConfirmCard
                      draft={scheduleComposer.draft ?? previewDraft!}
                      creating={scheduleComposer.creating}
                      onCancel={
                        scheduleComposer.draft
                          ? scheduleComposer.cancelDraft
                          : () => undefined
                      }
                      onConfirm={async () => {
                        if (!scheduleComposer.draft) return;
                        const ok = await scheduleComposer.confirmDraft();
                        if (ok) setInput("");
                      }}
                    />
                  ) : null}

                  <div
                    ref={dropRef}
                    className={cn(
                      "border-border bg-panel/75 relative z-10 mx-auto mb-8 w-full max-w-3xl rounded-3xl border shadow-sm backdrop-blur-md transition-all",
                      dragOver && "border-accent border-2 border-dotted",
                    )}
                  >
                    <form
                      onSubmit={handleSubmit}
                      className="mx-auto grid max-w-3xl grid-rows-[1fr_auto] gap-2"
                    >
                      <ContentBlocksPreview
                        blocks={contentBlocks}
                        onRemove={removeBlock}
                      />
                      <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onPaste={handlePaste}
                        onKeyDown={(e) => {
                          if (
                            e.key === "Enter" &&
                            !e.shiftKey &&
                            !e.metaKey &&
                            !e.nativeEvent.isComposing
                          ) {
                            e.preventDefault();
                            const el = e.target as HTMLElement | undefined;
                            const form = el?.closest("form");
                            form?.requestSubmit();
                          }
                        }}
                        placeholder="Type your message..."
                        className="field-sizing-content min-h-0 resize-none rounded-2xl border-none bg-transparent p-3.5 pb-0 shadow-none focus-visible:ring-0"
                      />

                      <div className="flex items-center gap-6 p-2 pt-4">
                        <div>
                          <div className="flex items-center space-x-2">
                            <Switch
                              id="render-tool-calls"
                              checked={hideToolCalls ?? false}
                              onCheckedChange={setHideToolCalls}
                            />
                            <Label
                              htmlFor="render-tool-calls"
                              className="text-muted-foreground text-sm"
                            >
                              Hide Tool Calls
                            </Label>
                          </div>
                        </div>
                        <Label
                          htmlFor="file-input"
                          className="text-muted-foreground flex cursor-pointer items-center gap-2"
                        >
                          <Plus className="size-5" />
                          <span className="text-sm">Upload PDF or Image</span>
                        </Label>
                        <input
                          id="file-input"
                          type="file"
                          onChange={handleFileUpload}
                          multiple
                          accept="image/jpeg,image/png,image/gif,image/webp,application/pdf"
                          className="hidden"
                        />
                        {stream.isLoading ? (
                          <Button
                            key="stop"
                            variant="outline"
                            onClick={() => stream.stop()}
                            className="ml-auto"
                          >
                            <LoaderCircle className="h-4 w-4 animate-spin" />
                            Cancel
                          </Button>
                        ) : (
                          <Button
                            type="submit"
                            variant="accent"
                            className="ml-auto"
                            disabled={
                              isLoading ||
                              (!input.trim() && contentBlocks.length === 0)
                            }
                          >
                            Send
                          </Button>
                        )}
                      </div>
                    </form>
                  </div>
                </div>
              }
            />
          </StickToBottom>
        </motion.div>
        <div className="relative flex flex-col border-l">
          <div className="absolute inset-0 flex min-w-[30vw] flex-col">
            <div className="grid grid-cols-[1fr_auto] border-b p-4">
              <ArtifactTitle className="truncate overflow-hidden" />
              <button
                onClick={closeArtifact}
                className="cursor-pointer"
              >
                <XIcon className="size-5" />
              </button>
            </div>
            <ArtifactContent className="relative flex-grow" />
          </div>
        </div>
      </div>
    </div>
  );
}
