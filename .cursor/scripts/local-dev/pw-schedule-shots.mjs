/**
 * 本機排程 UI 截圖 → .cursor/temp/ui-shots/schedule/
 * 需：frontend :3000、Schedule API :5055
 */
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../../temp/ui-shots/schedule");
fs.mkdirSync(outDir, { recursive: true });

const base = process.env.CHAT_URL || "http://localhost:3000";

async function waitOk(url, tries = 60) {
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url);
      if (r.ok || r.status < 500) return;
    } catch {}
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error(`not ready: ${url}`);
}

await waitOk(base);
await waitOk("http://127.0.0.1:5055/health");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(`${base}/?chatHistoryOpen=true`, {
  waitUntil: "domcontentloaded",
  timeout: 120_000,
});
await page.waitForTimeout(3000);

// 關掉 Next.js issue toast（若有）
await page.getByRole("button", { name: /Close|Collapse/i }).first().click().catch(() => {});

await page.screenshot({
  path: path.join(outDir, "p3-sidebar-overview.png"),
});

const formTitle = page.getByPlaceholder("標題").first();
await formTitle.scrollIntoViewIfNeeded();
await page.screenshot({
  path: path.join(outDir, "p3-schedule-form.png"),
});

// 建立一筆側欄排程（不經聊天）
await formTitle.fill("P3 側欄建立");
await page.getByPlaceholder("執行時送給 Agent 的提示").first().fill("側欄 smoke：回覆 ok");
await page.getByRole("button", { name: "建立" }).first().click();
await page.waitForTimeout(2000);
await page.screenshot({
  path: path.join(outDir, "p3-after-create.png"),
});

// 開啟排程 thread（徽章／頂欄）
const badgeThread = page.getByRole("button", { name: /排程/ }).filter({ hasText: "schedule-ok" }).first();
if (await badgeThread.count()) {
  await badgeThread.click();
  await page.waitForTimeout(2000);
}
await page.screenshot({
  path: path.join(outDir, "p4-schedule-badge-header.png"),
});

// 意圖確認卡：composer 攔截（本機 UI，不對外發訊）
await page.getByRole("button", { name: "New thread" }).click().catch(() => {});
await page.waitForTimeout(800);
const box = page.getByPlaceholder("Type your message...");
await box.click();
await box.fill("每天早上9點提醒我檢查排程側欄");
await page.getByRole("button", { name: "Send" }).click();
await page.waitForTimeout(1500);
await page.screenshot({
  path: path.join(outDir, "p5-intent-confirm-card.png"),
});

const confirm = page.getByRole("button", { name: "確認建立" });
if (await confirm.count()) {
  await confirm.click();
  await page.waitForTimeout(2000);
  await page.goto(`${base}/?chatHistoryOpen=true`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: path.join(outDir, "p5-after-confirm-sidebar.png"),
  });
}

await browser.close();
console.log("OK shots →", outDir);
