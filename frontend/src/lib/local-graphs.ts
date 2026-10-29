// [ai_prepare 修改] 本機多 graph 選單（對齊 server/langgraph.dev.json）

export type GraphAccess = "public" | "finance";

export type LocalGraphOption = {
  id: string;
  label: string;
  shortLabel: string;
  /** public＝全員 Demo；finance＝財務專用（本機用右上角開關模擬） */
  access: GraphAccess;
  /** 建議對應的 LangSmith Project 名稱（本機 .env LANGCHAIN_PROJECT） */
  langsmithProject: string;
};

/** Demo：一 URL／一 Graph／全員。Finance：同入口下多 Graph／僅財務。 */
export const LOCAL_GRAPH_OPTIONS: LocalGraphOption[] = [
  {
    id: "agent",
    label: "Demo Agent",
    shortLabel: "Demo",
    access: "public",
    langsmithProject: "ai_prepare_demo",
  },
  {
    id: "rework_mo_detective",
    label: "Rework MO 偵探",
    shortLabel: "Rework",
    access: "finance",
    langsmithProject: "ai_prepare_finance",
  },
  {
    id: "rd_risk_dashboard",
    label: "RD Risk 看板",
    shortLabel: "RD Risk",
    access: "finance",
    langsmithProject: "ai_prepare_finance",
  },
  {
    id: "qv_dms_pipeline",
    label: "QV DMS Pipeline",
    shortLabel: "QV DMS",
    access: "finance",
    langsmithProject: "ai_prepare_finance",
  },
];

export const PUBLIC_GRAPH_ID = "agent";

export function resolveGraphLabel(
  assistantId: string | null | undefined,
): string {
  if (!assistantId) return "未選擇";
  const hit = LOCAL_GRAPH_OPTIONS.find((g) => g.id === assistantId);
  return hit?.label ?? assistantId;
}

export function getGraphOption(
  assistantId: string | null | undefined,
): LocalGraphOption | undefined {
  if (!assistantId) return undefined;
  return LOCAL_GRAPH_OPTIONS.find((g) => g.id === assistantId);
}

export function isFinanceGraph(assistantId: string | null | undefined): boolean {
  return getGraphOption(assistantId)?.access === "finance";
}

export function graphsForAccess(hasFinance: boolean): LocalGraphOption[] {
  if (hasFinance) return LOCAL_GRAPH_OPTIONS;
  return LOCAL_GRAPH_OPTIONS.filter((g) => g.access === "public");
}
