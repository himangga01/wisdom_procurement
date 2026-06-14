#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  artifactsDir,
  backendDir,
  ensureDir,
  frontendDir,
  makeSeed,
  normalizeUrl,
  parseArgs,
  readJsonIfExists,
  repoRoot,
  requireFromFrontend,
  runCommand,
  wait,
  waitForEndpoint,
  writeJson,
} from "./demo-video-utils.mjs";
import { prepareDemoData } from "./prepare-service-demo-data.mjs";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:18111";
const DEFAULT_FRONTEND_URL = "http://127.0.0.1:5199";

const SCENES = [
  {
    id: "intro",
    title: "SMART 조달청 계산기",
    subtitle: "공고, 법인 증빙, 기준문서, 계약서 초안을 하나의 흐름으로 확인합니다.",
    route: "/",
    holdMs: 1800,
  },
  {
    id: "corporations",
    title: "1. 법인 등록과 증빙 준비",
    subtitle: "법인과 업로드된 증빙자료 상태를 확인합니다.",
    route: "/corporations",
    expect: (data) => [data.corporation.name],
    holdMs: 2200,
  },
  {
    id: "dashboard",
    title: "2. 대시보드에서 오늘 업무 확인",
    subtitle: "저장 공고, 문서, 처리 상태를 운영 화면에서 확인합니다.",
    route: "/",
    holdMs: 1800,
  },
  {
    id: "nara-board",
    title: "3. 나라장터 공고 검색",
    subtitle: "업무유형별 공고 검색과 저장 흐름으로 이어지는 화면입니다.",
    route: "/nara-board",
    holdMs: 1800,
  },
  {
    id: "saved-notice",
    title: "4. 저장 공고 요구조건 확인",
    subtitle: "저장한 공고의 요구조건 후보와 분석 상태를 확인합니다.",
    route: (data) => data.routes.saved_notice,
    expect: (data) => [data.notice.bid_ntce_nm || data.notice.bidNtceNm],
    holdMs: 2400,
  },
  {
    id: "basis-documents",
    title: "5. 기준문서/RAG 준비 상태",
    subtitle: "기준문서가 파싱, 청킹, JSON basis index로 검색 가능해졌는지 확인합니다.",
    route: "/basis-documents",
    expect: (data) => [data.basis_document.title],
    holdMs: 2400,
  },
  {
    id: "notice-comparison",
    title: "6. 부족조건 미리보기",
    subtitle: "공고 요구조건과 법인 준비상태를 비교합니다.",
    route: "/notice-comparison",
    expect: (data) => [data.corporation.name],
    holdMs: 2200,
  },
  {
    id: "judgment-runs",
    title: "7. 부족조건 중심 판단 검토",
    subtitle: "준비됨, 확인 필요, 부족 조건과 citation 후보를 검토합니다.",
    route: "/judgment-runs",
    expect: (data) => [data.corporation.name],
    holdMs: 2200,
  },
  {
    id: "contracts",
    title: "8. 계약서 DOCX 초안 생성",
    subtitle: "법인 기본정보와 공고 정보를 바탕으로 계약서 초안을 확인합니다.",
    route: (data) => data.routes.contracts,
    expect: (data) => [data.contract.title],
    holdMs: 2400,
  },
  {
    id: "operations",
    title: "9. 운영 상태 확인",
    subtitle: "실행 이력과 실패 사유를 관리자 화면에서 추적합니다.",
    route: "/operations",
    holdMs: 1800,
  },
  {
    id: "operation-runs",
    title: "10. 작업 이력",
    subtitle: "기준문서 처리, 판단 실행, 계약서 생성 이력을 확인합니다.",
    route: "/operation-runs",
    expect: () => ["기준문서 처리"],
    holdMs: 2200,
  },
];

const INTERACTIVE_DEMO_MODES = new Set(["interactive-demo", "real-pdf-demo", "live-nara-demo"]);

const ROUTE_SIDEBAR_DEMO_IDS = [
  ["/operation-runs", "sidebar-operation-runs"],
  ["/operations", "sidebar-operations"],
  ["/backups", "sidebar-backups"],
  ["/nara-saved-notices", "sidebar-nara-saved-notices"],
  ["/nara-board", "sidebar-nara-board"],
  ["/notice-comparison", "sidebar-notice-comparison"],
  ["/judgment-runs", "sidebar-judgment-runs"],
  ["/contracts", "sidebar-contracts"],
  ["/nara-collection-runs", "sidebar-nara-collection-runs"],
  ["/documents", "sidebar-documents"],
  ["/basis-documents", "sidebar-basis-documents"],
  ["/basis-rule-candidates", "sidebar-basis-rule-candidates"],
  ["/basis-retrieval-evaluations", "sidebar-basis-retrieval-evaluations"],
  ["/corporations", "sidebar-corporations"],
  ["/projects", "sidebar-projects"],
  ["/settings/integrations/nara", "sidebar-settings-nara"],
  ["/settings/external-access", "sidebar-settings-external-access"],
  ["/", "sidebar-dashboard"],
];

const INTERACTIVE_SCENE_ACTIONS = {
  corporations: ["demo-corporation-directory-tab", "demo-corporation-upload-tab"],
  "basis-documents": ["demo-basis-document-detail", "demo-basis-chunk-list-toggle", "demo-basis-chunk-expand"],
  "notice-comparison": ["demo-notice-comparison-run"],
  "judgment-runs": ["demo-judgment-run-row"],
  contracts: ["demo-contract-preview"],
  "operation-runs": ["demo-operation-run-row"],
};

async function runPreflight(outDir) {
  const startedAt = new Date().toISOString();
  const checks = [];
  async function check(name, command, args, cwd, timeoutMs) {
    const item = { name, command: [command, ...args].join(" "), cwd, status: "running", started_at: new Date().toISOString() };
    checks.push(item);
    try {
      await runCommand(command, args, { cwd, timeoutMs });
      item.status = "passed";
    } catch (error) {
      item.status = "failed";
      item.error = error.message;
      throw error;
    } finally {
      item.finished_at = new Date().toISOString();
    }
  }

  try {
    await check(
      "rocket_pitch_demo_pipeline",
      "py",
      ["-3.13", "-m", "unittest", "tests.test_api_flows.ApiFlowTests.test_service_rocket_pitch_demo_pipeline_flow", "-v"],
      backendDir,
      120000,
    );
    await check("frontend_build", "npm", ["run", "build"], frontendDir, 120000);
    const report = { status: "passed", started_at: startedAt, finished_at: new Date().toISOString(), checks };
    await writeJson(path.join(outDir, "preflight.json"), report);
    return report;
  } catch (error) {
    const report = { status: "failed", started_at: startedAt, finished_at: new Date().toISOString(), checks, error: error.message };
    await writeJson(path.join(outDir, "preflight.json"), report);
    throw error;
  }
}

async function addSceneOverlay(page, scene) {
  await page.addStyleTag({
    content: `
      .codex-demo-overlay {
        position: fixed;
        right: 24px;
        top: 24px;
        z-index: 2147483647;
        width: min(460px, calc(100vw - 48px));
        padding: 16px 18px;
        border-radius: 14px;
        border: 1px solid rgba(37, 99, 235, 0.22);
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
        color: #111827;
        font-family: "Pretendard", "Noto Sans KR", Arial, sans-serif;
        pointer-events: none;
      }
      .codex-demo-overlay strong {
        display: block;
        color: #123c8c;
        font-size: 18px;
        line-height: 1.35;
        letter-spacing: 0;
      }
      .codex-demo-overlay span {
        display: block;
        margin-top: 6px;
        color: #4b5563;
        font-size: 13px;
        line-height: 1.5;
        letter-spacing: 0;
      }
    `,
  });
  await page.evaluate(({ title, subtitle }) => {
    document.querySelectorAll(".codex-demo-overlay").forEach((node) => node.remove());
    const overlay = document.createElement("div");
    overlay.className = "codex-demo-overlay";
    overlay.innerHTML = `<strong></strong><span></span>`;
    overlay.querySelector("strong").textContent = title;
    overlay.querySelector("span").textContent = subtitle || "";
    document.body.appendChild(overlay);
  }, { title: scene.title, subtitle: scene.subtitle || "" });
}

async function waitForText(page, text, timeoutMs = 10000) {
  if (!text) return true;
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const bodyText = await page.locator("body").innerText({ timeout: 1000 });
      if (bodyText.includes(text)) {
        return true;
      }
    } catch {
      // Keep polling until the per-scene timeout expires.
    }
    await wait(500);
  }
  return false;
}

function withTimeout(promise, timeoutMs, label) {
  let timeoutId = null;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error(`${label} timed out after ${timeoutMs}ms`)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => {
    if (timeoutId) clearTimeout(timeoutId);
  });
}

function isInteractiveDemoMode(mode) {
  return INTERACTIVE_DEMO_MODES.has(mode);
}

function routeToSidebarDemoId(route) {
  return ROUTE_SIDEBAR_DEMO_IDS.find(([prefix]) => route === prefix || route.startsWith(`${prefix}/`))?.[1] || null;
}

function demoLocator(page, demoId) {
  return page.locator(`[data-demo-id="${demoId}"]`).first();
}

async function installDemoCursor(page) {
  await page.addStyleTag({
    content: `
      .codex-demo-cursor {
        position: fixed;
        left: 0;
        top: 0;
        z-index: 2147483647;
        width: 18px;
        height: 18px;
        border: 2px solid #123c8c;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
        pointer-events: none;
        transform: translate3d(28px, 28px, 0);
        transition: transform 180ms ease, width 120ms ease, height 120ms ease;
      }
      .codex-demo-cursor::after {
        content: "";
        position: absolute;
        left: 50%;
        top: 50%;
        width: 4px;
        height: 4px;
        border-radius: 999px;
        background: #123c8c;
        transform: translate(-50%, -50%);
      }
      .codex-demo-cursor--down {
        width: 14px;
        height: 14px;
      }
      .codex-demo-click-ripple {
        position: fixed;
        z-index: 2147483646;
        width: 36px;
        height: 36px;
        margin-left: -18px;
        margin-top: -18px;
        border: 2px solid rgba(29, 78, 216, 0.5);
        border-radius: 999px;
        pointer-events: none;
        animation: codexDemoRipple 520ms ease-out forwards;
      }
      @keyframes codexDemoRipple {
        from { opacity: 0.85; transform: scale(0.35); }
        to { opacity: 0; transform: scale(1.35); }
      }
    `,
  });
  await page.evaluate(() => {
    if (!document.querySelector(".codex-demo-cursor")) {
      const cursor = document.createElement("div");
      cursor.className = "codex-demo-cursor";
      document.body.appendChild(cursor);
    }
  });
}

async function moveCursorTo(page, locator, options = {}) {
  await locator.scrollIntoViewIfNeeded({ timeout: Number(options.timeoutMs || 6000) }).catch(() => {});
  const box = await locator.boundingBox({ timeout: Number(options.timeoutMs || 6000) }).catch(() => null);
  if (!box) {
    throw new Error(`Cursor target is not visible: ${options.label || "locator"}`);
  }
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.evaluate(({ x, y }) => {
    const cursor = document.querySelector(".codex-demo-cursor");
    if (cursor instanceof HTMLElement) {
      cursor.style.transform = `translate3d(${x - 9}px, ${y - 9}px, 0)`;
    }
  }, { x, y });
  await wait(Number(options.settleMs || 220));
  return { x, y };
}

async function showClickRipple(page, point) {
  await page.evaluate(({ x, y }) => {
    const cursor = document.querySelector(".codex-demo-cursor");
    if (cursor instanceof HTMLElement) {
      cursor.classList.add("codex-demo-cursor--down");
      window.setTimeout(() => cursor.classList.remove("codex-demo-cursor--down"), 160);
    }
    const ripple = document.createElement("div");
    ripple.className = "codex-demo-click-ripple";
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    document.body.appendChild(ripple);
    window.setTimeout(() => ripple.remove(), 580);
  }, point);
  await wait(90);
}

async function clickWithCursor(page, locator, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.click({ timeout: Number(options.timeoutMs || 10000) });
  await wait(Number(options.afterMs || 450));
}

async function typeWithCursor(page, locator, text, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.fill(String(text || ""), { timeout: Number(options.timeoutMs || 10000) });
  await wait(Number(options.afterMs || 250));
}

async function setInputFilesWithCursor(page, locator, filePath, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.setInputFiles(filePath, { timeout: Number(options.timeoutMs || 10000) });
  await wait(Number(options.afterMs || 500));
}

async function safeClickDemoId(page, demoId, context = {}) {
  const locator = demoLocator(page, demoId);
  const count = await locator.count().catch(() => 0);
  if (!count) {
    context.warnings?.push({ scene: context.sceneId, type: "missing_demo_selector", selector: demoId });
    return false;
  }
  const visible = await locator.isVisible({ timeout: Number(context.timeoutMs || 3500) }).catch(() => false);
  if (!visible) {
    context.warnings?.push({ scene: context.sceneId, type: "hidden_demo_selector", selector: demoId });
    return false;
  }
  const enabled = await locator.isEnabled({ timeout: 1500 }).catch(() => true);
  if (!enabled) {
    context.warnings?.push({ scene: context.sceneId, type: "disabled_demo_selector", selector: demoId });
    return false;
  }
  await clickWithCursor(page, locator, { label: demoId, afterMs: Number(context.afterMs || 550) });
  return true;
}

async function navigateBySidebar(page, sidebarDemoId, frontendUrl, context = {}) {
  if (!page.url() || page.url() === "about:blank") {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(700);
  }
  let locator = demoLocator(page, sidebarDemoId);
  if (!(await locator.count().catch(() => 0))) {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(700);
    locator = demoLocator(page, sidebarDemoId);
  }
  await installDemoCursor(page);
  await clickWithCursor(page, locator, { label: sidebarDemoId, afterMs: 800 });
  context.trace?.(`sidebar-click ${sidebarDemoId}`);
}

async function findDefaultEvidencePdf() {
  const testDocDir = path.join(repoRoot, "source", "test_doc");
  const entries = await fs.readdir(testDocDir, { withFileTypes: true }).catch(() => []);
  const pdf = entries.find((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".pdf"));
  return pdf ? path.join(testDocDir, pdf.name) : null;
}

async function runRealPdfEvidenceScene(page, options = {}) {
  await safeClickDemoId(page, "demo-corporation-upload-tab", options);
  const pdfPath = options.pdfPath || (await findDefaultEvidencePdf());
  if (!pdfPath) {
    options.warnings?.push({ scene: options.sceneId, type: "missing_real_pdf_fixture", path: "source/test_doc" });
    return;
  }
  await setInputFilesWithCursor(page, demoLocator(page, "demo-evidence-file-input"), pdfPath, { label: "demo-evidence-file-input" });
  if (options.dryRun) {
    options.warnings?.push({ scene: options.sceneId, type: "real_pdf_upload_skipped_in_dry_run", file: pdfPath });
    return;
  }
  await safeClickDemoId(page, "demo-evidence-upload-submit", options);
  await page
    .locator('[data-demo-id="demo-latest-evidence-result"]')
    .first()
    .waitFor({ state: "visible", timeout: Number(options.realPdfTimeoutMs || 180000) })
    .catch((error) => {
      options.warnings?.push({ scene: options.sceneId, type: "real_pdf_result_wait_failed", message: error.message });
    });
}

async function runLiveNaraSearchScene(page, options = {}) {
  const keyword = options.naraKeyword ?? "";
  if (keyword) {
    await typeWithCursor(page, demoLocator(page, "demo-nara-search-keyword"), keyword, { label: "demo-nara-search-keyword" });
  }
  if (options.dryRun) {
    options.warnings?.push({ scene: options.sceneId, type: "live_nara_search_skipped_in_dry_run" });
    return;
  }
  await safeClickDemoId(page, "demo-nara-search-submit", { ...options, timeoutMs: 6000, afterMs: 1000 });
  await Promise.race([
    page.locator('[data-demo-id="demo-nara-result-list"]').first().waitFor({ state: "visible", timeout: 45000 }),
    page.locator('[data-demo-id="demo-nara-partial-error"]').first().waitFor({ state: "visible", timeout: 45000 }),
  ]).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "live_nara_result_wait_failed", message: error.message });
  });
}

async function runInteractiveScene(page, scene, data, options = {}) {
  const route = typeof scene.route === "function" ? scene.route(data) : scene.route;
  const frontendUrl = options.frontendUrl;
  const sidebarDemoId = routeToSidebarDemoId(route);
  if (scene.id === "intro") {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(700);
    return route;
  }

  if (scene.id === "saved-notice") {
    await navigateBySidebar(page, "sidebar-nara-saved-notices", frontendUrl, options);
    const clicked = await safeClickDemoId(page, "demo-saved-notice-detail-link", { ...options, sceneId: scene.id });
    if (!clicked) {
      await page.goto(`${frontendUrl}${route}`, { waitUntil: "commit", timeout: 45000 });
    }
    await wait(900);
    return route;
  }

  if (sidebarDemoId) {
    await navigateBySidebar(page, sidebarDemoId, frontendUrl, options);
    if (route.includes("?")) {
      await page.goto(`${frontendUrl}${route}`, { waitUntil: "commit", timeout: 45000 });
      await installDemoCursor(page);
      await wait(700);
    }
  } else {
    await page.goto(`${frontendUrl}${route}`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(700);
  }

  if (options.mode === "real-pdf-demo" && scene.id === "corporations") {
    await runRealPdfEvidenceScene(page, { ...options, sceneId: scene.id });
    return route;
  }

  if (options.mode === "live-nara-demo" && scene.id === "nara-board") {
    await runLiveNaraSearchScene(page, { ...options, sceneId: scene.id });
    return route;
  }

  const actionIds = INTERACTIVE_SCENE_ACTIONS[scene.id] || [];
  for (const actionId of actionIds) {
    await safeClickDemoId(page, actionId, { ...options, sceneId: scene.id });
  }
  return route;
}

async function recordDemoVideo(options = {}) {
  const backendUrl = normalizeUrl(options.backendUrl, DEFAULT_BACKEND_URL);
  const frontendUrl = normalizeUrl(options.frontendUrl, DEFAULT_FRONTEND_URL);
  const mode = String(options.mode || "stable-demo");
  const outDir = path.resolve(options.outDir || artifactsDir);
  let seed = makeSeed(options.seed);
  let runDir = path.join(outDir, "runs", seed);
  let screenshotsDir = path.join(runDir, "screenshots");
  let rawVideoDir = path.join(runDir, "raw-video");
  const warnings = [];
  const sceneResults = [];
  await ensureDir(screenshotsDir);
  await ensureDir(rawVideoDir);

  await waitForEndpoint(`${backendUrl}/api/dashboard/summary`, { timeoutMs: 30000 });
  await waitForEndpoint(`${frontendUrl}/`, { timeoutMs: 30000 });

  let data = null;
  if (options["reuse-data"]) {
    data = await readJsonIfExists(path.join(outDir, "latest-demo-data.json"));
    if (!data) {
      throw new Error("latest-demo-data.json was not found. Run demo:prepare or demo:record without --reuse-data first.");
    }
    seed = data.seed;
    runDir = data.run_dir || path.join(outDir, "runs", seed);
    screenshotsDir = path.join(runDir, "screenshots");
    rawVideoDir = path.join(runDir, "raw-video");
    await ensureDir(screenshotsDir);
    await ensureDir(rawVideoDir);
  } else {
    data = await prepareDemoData({ backendUrl, seed, outDir });
  }
  const tracePath = path.join(runDir, "record-trace.log");
  const trace = async (message) => {
    const line = `[${new Date().toISOString()}] ${message}\n`;
    await fs.appendFile(tracePath, line, "utf8");
    console.log(message);
  };
  await trace(`data-ready seed=${seed}`);
  const sceneFilter =
    options.scene && options.scene !== "all"
      ? new Set(String(options.scene).split(",").map((item) => item.trim()).filter(Boolean))
      : null;
  const scenes = SCENES.filter((scene) => !sceneFilter || sceneFilter.has(scene.id));
  if (!scenes.length) {
    throw new Error(`No matching scene found for --scene ${options.scene}`);
  }

  const { chromium } = requireFromFrontend("playwright");
  const browser = await chromium.launch({
    headless: options.headed ? false : true,
    slowMo: Number(options["slow-mo"] || 0),
  });
  const context = await browser.newContext({
    viewport: { width: Number(options.width || 1440), height: Number(options.height || 900) },
    recordVideo: options.dryRun ? undefined : { dir: rawVideoDir, size: { width: Number(options.width || 1440), height: Number(options.height || 900) } },
  });
  const page = await context.newPage();
  if (isInteractiveDemoMode(mode) || options.cursor) {
    await installDemoCursor(page);
  }
  const consoleErrors = [];
  const consoleWarnings = [];
  const requestFailures = [];
  page.on("console", (message) => {
    const text = message.text();
    if (message.type() === "error") {
      consoleErrors.push({ type: message.type(), text });
    }
    if (message.type() === "warning" && !text.includes("React Router Future Flag Warning")) {
      consoleWarnings.push({ type: message.type(), text });
    }
  });
  page.on("pageerror", (error) => {
    consoleErrors.push({ type: "pageerror", text: error.message });
  });
  page.on("requestfailed", (request) => {
    const url = request.url();
    const failure = request.failure()?.errorText || "";
    if (request.resourceType() === "websocket" || url.includes("/@vite/") || failure.includes("ERR_ABORTED")) {
      return;
    }
    requestFailures.push({ url, method: request.method(), failure });
  });

  for (const scene of scenes) {
    const route = typeof scene.route === "function" ? scene.route(data) : scene.route;
    const url = `${frontendUrl}${route}`;
    await trace(`scene ${scene.id}: open ${url} mode=${mode}`);
    const result = {
      id: scene.id,
      title: scene.title,
      route,
      url,
      status: "running",
      started_at: new Date().toISOString(),
    };
    sceneResults.push(result);
    if (isInteractiveDemoMode(mode)) {
      await runInteractiveScene(page, scene, data, {
        mode,
        frontendUrl,
        backendUrl,
        warnings,
        trace,
        dryRun: Boolean(options.dryRun),
        pdfPath: options["pdf-path"],
        naraKeyword: options["nara-keyword"],
      });
      await trace(`scene ${scene.id}: interactive navigation done`);
    } else {
      await page.goto(url, { waitUntil: "commit", timeout: 45000 });
      await trace(`scene ${scene.id}: goto committed`);
    }
    await wait(900);
    await trace(`scene ${scene.id}: overlay start`);
    await withTimeout(addSceneOverlay(page, scene), 5000, `scene ${scene.id} overlay`).catch((error) => {
      warnings.push({ scene: scene.id, type: "overlay_failed", message: error.message });
    });
    await trace(`scene ${scene.id}: overlay done`);
    const expectedTexts = typeof scene.expect === "function" ? scene.expect(data) : scene.expect || [];
    const missingTexts = [];
    for (const expected of expectedTexts) {
      const found = await waitForText(page, expected);
      if (!found) {
        missingTexts.push(expected);
      }
    }
    await trace(`scene ${scene.id}: text checks done`);
    if (missingTexts.length) {
      const warning = { scene: scene.id, type: "missing_expected_text", values: missingTexts };
      warnings.push(warning);
      result.warning = warning;
    }
    await wait(Number(scene.holdMs || 1500));
    const screenshotPath = path.join(screenshotsDir, `${String(sceneResults.length).padStart(2, "0")}-${scene.id}.png`);
    await trace(`scene ${scene.id}: screenshot start`);
    await page.screenshot({ path: screenshotPath, fullPage: false, timeout: 15000 });
    await trace(`scene ${scene.id}: screenshot done`);
    result.screenshot = screenshotPath;
    result.status = "passed";
    result.finished_at = new Date().toISOString();
    await trace(`scene ${scene.id}: captured`);
  }

  const videoHandle = page.video();
  await trace("browser close start");
  await withTimeout(page.close({ runBeforeUnload: false }).catch(() => {}), 15000, "page.close");
  await withTimeout(context.close(), 30000, "context.close");
  await withTimeout(browser.close(), 30000, "browser.close");
  await trace("browser close done");

  let rawVideoPath = null;
  if (!options.dryRun && videoHandle) {
    const generatedPath = await videoHandle.path();
    rawVideoPath = path.join(rawVideoDir, `service-demo-${seed}.webm`);
    await fs.rm(rawVideoPath, { force: true }).catch(() => {});
    await fs.rename(generatedPath, rawVideoPath);
  }

  const report = {
    status: warnings.length || consoleErrors.length || requestFailures.length ? "completed_with_warnings" : "completed",
    mode,
    seed,
    frontend_url: frontendUrl,
    backend_url: backendUrl,
    run_dir: runDir,
    raw_video_path: rawVideoPath,
    data_path: path.join(runDir, "demo-data.json"),
    scenes: sceneResults,
    warnings,
    console_errors: consoleErrors,
    console_warnings: consoleWarnings,
    request_failures: requestFailures,
    started_at: sceneResults[0]?.started_at || new Date().toISOString(),
    finished_at: new Date().toISOString(),
  };
  await writeJson(path.join(runDir, "record-report.json"), report);
  await writeJson(path.join(outDir, "latest-report.json"), report);
  console.log(JSON.stringify({ status: report.status, seed, raw_video_path: rawVideoPath, warnings: warnings.length }, null, 2));
  return report;
}

async function main() {
  const args = parseArgs();
  const outDir = path.resolve(args["out-dir"] || artifactsDir);
  await ensureDir(outDir);
  if (args["preflight-only"]) {
    await runPreflight(outDir);
    return;
  }
  if (args.preflight !== false && !args["skip-preflight"]) {
    await runPreflight(outDir);
  }
  await recordDemoVideo({
    ...args,
    backendUrl: args["backend-url"],
    frontendUrl: args["frontend-url"],
    outDir,
    dryRun: Boolean(args["dry-run"]),
    headed: Boolean(args.headed),
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
