#!/usr/bin/env node

import { createRequire } from "node:module";

const DEFAULT_ROUTES = [
  "/",
  "/operations",
  "/operation-runs",
  "/backups",
  "/nara-board",
  "/nara-saved-notices",
  "/notice-comparison",
  "/judgment-runs",
  "/nara-collection-runs",
  "/documents",
  "/basis-documents",
  "/basis-rule-candidates",
  "/basis-retrieval-evaluations",
  "/corporations",
  "/projects",
  "/settings/integrations/nara",
];

const HELP = `
UX monkey smoke test for the local SMART Procurement frontend.

Usage:
  node scripts/ux-monkey-test.mjs --base-url http://127.0.0.1:5199 --steps 80 --seed 20260531

Required runtime:
  npm install -D playwright
  npx playwright install chromium

Recommended server setup:
  powershell -ExecutionPolicy Bypass -File scripts/manage-servers.ps1 -Action start

Options:
  --base-url <url>       Frontend base URL. Default: http://127.0.0.1:5199
  --steps <number>       Random action count. Default: 60
  --seed <number>        Deterministic random seed. Default: 20260531
  --timeout <ms>         Per-navigation timeout. Default: 10000
  --allow-dangerous      Allow clicking buttons that may mutate data. Default: false
  --screenshot-dir <dir> Save a final screenshot for each visited route.
  --help                 Show this help.
`;

function parseArgs(argv) {
  const args = {
    baseUrl: "http://127.0.0.1:5199",
    steps: 60,
    seed: 20260531,
    timeout: 10000,
    allowDangerous: false,
    screenshotDir: "",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--base-url") {
      args.baseUrl = argv[++index];
    } else if (arg === "--steps") {
      args.steps = Number(argv[++index]);
    } else if (arg === "--seed") {
      args.seed = Number(argv[++index]);
    } else if (arg === "--timeout") {
      args.timeout = Number(argv[++index]);
    } else if (arg === "--allow-dangerous") {
      args.allowDangerous = true;
    } else if (arg === "--screenshot-dir") {
      args.screenshotDir = argv[++index];
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function seededRandom(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function pick(items, random) {
  return items[Math.floor(random() * items.length)];
}

function isDangerousLabel(label) {
  return /delete|remove|restore|approve|reject|backup|retry|run|save|submit|삭제|제거|복원|승인|반려|백업|재시도|실행|저장|등록|생성/i.test(
    label,
  );
}

async function importPlaywright() {
  try {
    const requireFromCwd = createRequire(`${process.cwd()}/package.json`);
    return requireFromCwd("playwright");
  } catch {
    // Fall through to ESM resolution from this script's directory.
  }
  try {
    return await import("playwright");
  } catch (error) {
    console.error("Playwright is not installed for this workspace.");
    console.error("Install it with: npm install -D playwright && npx playwright install chromium");
    console.error(`Original import error: ${error.message}`);
    process.exit(2);
  }
}

async function visibleLocators(page, selector) {
  const locators = [];
  const count = await page.locator(selector).count();
  for (let index = 0; index < count; index += 1) {
    const locator = page.locator(selector).nth(index);
    if (await locator.isVisible().catch(() => false)) {
      locators.push(locator);
    }
  }
  return locators;
}

async function randomSafeClick(page, random, allowDangerous) {
  const candidates = await visibleLocators(page, "a[href], button, [role='button']");
  const safe = [];
  for (const locator of candidates) {
    const label = ((await locator.innerText().catch(() => "")) || (await locator.getAttribute("aria-label").catch(() => "")) || "").trim();
    if (allowDangerous || !isDangerousLabel(label)) {
      safe.push(locator);
    }
  }
  if (!safe.length) return "no-safe-click";
  const target = pick(safe, random);
  await target.click({ timeout: 2000 }).catch(() => {});
  return "click";
}

async function randomInput(page, random, seed) {
  const inputs = await visibleLocators(page, "input:not([type='file']), textarea");
  if (!inputs.length) return "no-input";
  const target = pick(inputs, random);
  const value = `ux-${seed}-${Math.floor(random() * 1000)}`;
  await target.fill(value, { timeout: 2000 }).catch(() => {});
  return "input";
}

async function assertPageUsable(page) {
  const bodyText = await page.locator("body").innerText({ timeout: 3000 });
  if (!bodyText.trim()) {
    throw new Error("Page body is blank.");
  }
  const mainCount = await page.locator("main").count();
  if (mainCount < 1) {
    throw new Error("Page has no main landmark.");
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(HELP.trimStart());
    return;
  }

  const { chromium } = await importPlaywright();
  const random = seededRandom(args.seed);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
  const errors = [];
  const visited = new Set();

  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(`console error: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => errors.push(`page error: ${error.message}`));
  page.on("requestfailed", (request) => {
    const url = request.url();
    if (!url.includes("/api/")) {
      errors.push(`request failed: ${url} ${request.failure()?.errorText || ""}`);
    }
  });

  try {
    for (const route of DEFAULT_ROUTES) {
      await page.goto(new URL(route, args.baseUrl).toString(), { timeout: args.timeout, waitUntil: "networkidle" });
      await assertPageUsable(page);
      visited.add(route);
    }

    for (let step = 0; step < args.steps; step += 1) {
      const actionRoll = random();
      if (actionRoll < 0.25) {
        const route = pick(DEFAULT_ROUTES, random);
        await page.goto(new URL(route, args.baseUrl).toString(), { timeout: args.timeout, waitUntil: "networkidle" });
        visited.add(route);
      } else if (actionRoll < 0.65) {
        await randomSafeClick(page, random, args.allowDangerous);
      } else {
        await randomInput(page, random, args.seed);
      }
      await assertPageUsable(page);
    }

    if (args.screenshotDir) {
      const fs = await import("node:fs/promises");
      await fs.mkdir(args.screenshotDir, { recursive: true });
      for (const route of visited) {
        await page.goto(new URL(route, args.baseUrl).toString(), { timeout: args.timeout, waitUntil: "networkidle" });
        const fileName = route === "/" ? "root.png" : `${route.slice(1).replaceAll("/", "__")}.png`;
        await page.screenshot({ path: `${args.screenshotDir}/${fileName}`, fullPage: true });
      }
    }
  } finally {
    await browser.close();
  }

  if (errors.length) {
    console.error(JSON.stringify({ status: "failed", seed: args.seed, visited: [...visited], errors }, null, 2));
    process.exit(1);
  }

  console.log(JSON.stringify({ status: "ok", seed: args.seed, steps: args.steps, visited: [...visited] }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
