import { readFile } from "node:fs/promises";
import path from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ runId: string; filename: string }> },
): Promise<Response> {
  const { runId, filename } = await params;
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
      runId,
    ) ||
    filename !== "Cover_updated.xlsx"
  ) {
    return Response.json({ error: "Invalid DMS artifact" }, { status: 400 });
  }
  // 本機前後端共用輸出目錄；正式部署須明確掛載同一目錄才能提供下載。
  const root =
    process.env.QV_DMS_OUTPUTS_DIR ??
    path.resolve(process.cwd(), "..", "server", "outputs", "qv_dms");
  try {
    const data = await readFile(path.join(root, runId, filename));
    return new Response(data, {
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="Cover_updated.xlsx"',
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      return Response.json(
        { error: "DMS artifact not found" },
        { status: 404 },
      );
    }
    throw error;
  }
}
