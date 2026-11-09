// [mo_agentchat 修改] 排程 API 的同網域 proxy：瀏覽器打 /schedule-api/...，再轉給叢集內的 Scheduler Api
// SCHEDULE_API_URL 在執行時設定（例如 http://mo-agentchat-scheduler:8080），QAS 和 PRD 可以用同一個 image
import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

async function proxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const base = process.env.SCHEDULE_API_URL?.replace(/\/$/, "");
  if (!base) {
    return Response.json({ error: "SCHEDULE_API_URL is not set" }, { status: 500 });
  }
  const { path } = await params;
  const target = `${base}/${path.join("/")}${req.nextUrl.search}`;
  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer();
  const res = await fetch(target, {
    method: req.method,
    headers: { "Content-Type": req.headers.get("content-type") ?? "application/json" },
    body,
  });
  return new Response(res.body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") ?? "application/json" },
  });
}

export { proxy as GET, proxy as POST };
