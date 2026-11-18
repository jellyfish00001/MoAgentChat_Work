/**
 * Headed Chromium (Playwright) with fixed CDP port + persistent profile
 * so LangSmith login cookies survive across sessions.
 *
 * Port: 9333
 * Profile: .cursor/temp/pw-langsmith-profile (gitignored)
 *
 * Usage:
 *   node .cursor/scripts/local-dev/start-playwright-langsmith.mjs
 *   node .cursor/scripts/local-dev/start-playwright-langsmith.mjs --studio
 *   node .cursor/scripts/local-dev/start-playwright-langsmith.mjs --formal
 *   node .cursor/scripts/local-dev/start-playwright-langsmith.mjs --studio --formal
 */
import { createRequire } from "node:module";
import { mkdirSync, existsSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..", "..", "..");
const profileDir = join(root, ".cursor", "temp", "pw-langsmith-profile");
const metaPath = join(root, ".cursor", "temp", "pw-langsmith-meta.json");
const CDP_PORT = 9333;
const openStudio = process.argv.includes("--studio");
const openFormal = process.argv.includes("--formal") || !openStudio;

/** Columbus 正式環境（self-hosted LangSmith org） */
const formalUrl =
  "https://columbus-langsmith.wistron.com/o/f679e495-9a73-469f-a922-f4c3b165ff3a";
/** 本機 Studio（需 langgraph dev 在 :2024；目前亦可改 :2025） */
const studioUrl =
  "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2025";

mkdirSync(profileDir, { recursive: true });

function loadPlaywright() {
  const toolsPkg = join(root, ".cursor", "temp", "pw-tools", "package.json");
  if (existsSync(toolsPkg)) {
    return createRequire(toolsPkg)("playwright");
  }
  try {
    return createRequire(import.meta.url)("playwright");
  } catch (e) {
    throw new Error(
      "Playwright missing. Run: cd .cursor/temp/pw-tools && npm i playwright@1.49.1",
    );
  }
}

const { chromium } = loadPlaywright();

console.log(`CDP port: ${CDP_PORT}`);
console.log(`Profile: ${profileDir}`);
console.log(
  "Open the window, confirm Columbus formal (and Studio if requested) stay logged in.",
);

const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  channel: "chrome",
  args: [`--remote-debugging-port=${CDP_PORT}`, "--start-maximized"],
  viewport: null,
  ignoreDefaultArgs: ["--enable-automation"],
});

writeFileSync(
  metaPath,
  JSON.stringify(
    {
      cdpPort: CDP_PORT,
      cdpUrl: `http://127.0.0.1:${CDP_PORT}`,
      profileDir,
      formalUrl,
      studioUrl,
      startedAt: new Date().toISOString(),
    },
    null,
    2,
  ),
  "utf8",
);

async function gotoKeep(page, url, label) {
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });
  console.log(`[${label}] ${page.url()}`);
}

const page = context.pages()[0] || (await context.newPage());

if (openFormal) {
  await gotoKeep(page, formalUrl, "formal");
}

if (openStudio) {
  const studioPage = openFormal ? await context.newPage() : page;
  await gotoKeep(studioPage, studioUrl, "studio");
}

if (!openFormal && !openStudio) {
  await gotoKeep(page, formalUrl, "formal");
}

console.log(`Connect via CDP: http://127.0.0.1:${CDP_PORT}`);
console.log("Keep this process running to preserve the session.");

context.on("close", () => process.exit(0));
await new Promise(() => {});
