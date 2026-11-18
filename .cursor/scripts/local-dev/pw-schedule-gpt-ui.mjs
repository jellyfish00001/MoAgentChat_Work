/**
 * GPT 式排程側欄截圖 → .cursor/temp/ui-shots/schedule/
 * 產物：p-ui-banner-collapsed / expanded / create-dialog
 */
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from "node:fs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "../../..");
const outDir = path.resolve(__dirname, "../../temp/ui-shots/schedule");
fs.mkdirSync(outDir, { recursive: true });

/** 優先 pw-tools（與本機 browser cache 對齊），再試 frontend。 */
function loadPlaywright() {
  const candidates = [
    path.join(root, ".cursor", "temp", "pw-tools", "package.json"),
    path.join(root, "frontend", "package.json"),
  ];
  for (const pkg of candidates) {
    if (!fs.existsSync(pkg)) continue;
    try {
      return createRequire(pkg)("playwright");
    } catch {}
  }
  throw new Error("找不到 playwright（pw-tools 或 frontend）");
}

const { chromium } = loadPlaywright();

const base = process.env.CHAT_URL || "http://localhost:3000";

/** 等到 URL 可連。 */
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
await page.waitForTimeout(3500);

// 關掉 Next.js issue toast（若有）
await page
  .getByRole("button", { name: /Close|Collapse/i })
  .first()
  .click()
  .catch(() => {});

const banner = page.getByRole("button", { name: /排程/ }).filter({ hasNotText: "新增" }).first();
// 橫幅文字按鈕：展開狀態先確保收合 → 截 collapsed
const expanded = await banner.getAttribute("aria-expanded");
if (expanded === "true") {
  await banner.click();
  await page.waitForTimeout(400);
}
await page.locator(".border-sidebar-border.bg-sidebar").first().screenshot({
  path: path.join(outDir, "p-ui-banner-collapsed.png"),
});

// 展開
await banner.click();
await page.waitForTimeout(500);
await page.locator(".border-sidebar-border.bg-sidebar").first().screenshot({
  path: path.join(outDir, "p-ui-banner-expanded.png"),
});

// 加號開新增彈窗
await page.getByRole("button", { name: "新增排程" }).first().click();
await page.waitForTimeout(600);
await page.getByRole("dialog").waitFor({ state: "visible", timeout: 10_000 });
await page.screenshot({
  path: path.join(outDir, "p-ui-create-dialog.png"),
});

await browser.close();
console.log("OK GPT UI shots →", outDir);
