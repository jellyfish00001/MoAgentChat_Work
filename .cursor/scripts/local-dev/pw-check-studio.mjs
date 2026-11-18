/**
 * Attach to the persistent Playwright Chrome on CDP :9333 and verify Studio.
 * Requires start-playwright-langsmith.mjs already running + user logged in.
 */
import { createRequire } from "node:module";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { existsSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..", "..", "..");
const CDP_PORT = 9333;
const studioUrl =
  "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025";
const formalUrl =
  "https://columbus-langsmith.wistron.com/o/f679e495-9a73-469f-a922-f4c3b165ff3a";

function loadPlaywright() {
  try {
    return createRequire(import.meta.url)("playwright");
  } catch {
    const toolsPkg = join(root, ".cursor", "temp", "pw-tools", "package.json");
    if (!existsSync(toolsPkg)) {
      throw new Error("Playwright not installed. Run start-playwright-langsmith.mjs first.");
    }
    return createRequire(toolsPkg)("playwright");
  }
}

const { chromium } = loadPlaywright();
const browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
const context = browser.contexts()[0];
if (!context) throw new Error("No browser context on CDP — is the headed Chrome running?");

async function sniff(url) {
  const page = await context.newPage();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.waitForTimeout(4000);
  const finalUrl = page.url();
  const text = await page.evaluate(() => document.body?.innerText?.slice(0, 2000) || "");
  await page.close();
  return { url: finalUrl, text };
}

const formal = await sniff(formalUrl);
const formalOk =
  /f679e495-9a73-469f-a922-f4c3b165ff3a|Projects|Tracing|LangSmith/i.test(formal.text) &&
  !/Sign in|Log in|Login|請登入/i.test(formal.text);

const studio = await sniff(studioUrl);
const studioOk =
  /list_orders|rework_mo_detective|Graph|agent/i.test(studio.text) &&
  !/Failed to initialize Studio|Failed to fetch assistants/i.test(studio.text);

const ok = formalOk && studioOk;
console.log(
  JSON.stringify(
    {
      ok,
      formalOk,
      studioOk,
      formalUrl,
      studioUrl,
      formalSnippet: formal.text.slice(0, 400),
      studioSnippet: studio.text.slice(0, 400),
    },
    null,
    2,
  ),
);
// Do not close — leave session alive
process.exit(ok ? 0 : 2);
