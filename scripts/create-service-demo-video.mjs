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

const DEFAULT_STEP_DELAY_MS = 1050;
const DEFAULT_CLICK_DELAY_MS = 950;
const DEFAULT_TYPE_DELAY_MS = 650;
const DEFAULT_FILE_DELAY_MS = 1100;
const DEFAULT_NAVIGATION_DELAY_MS = 1350;
const DEFAULT_SCENE_GAP_MS = 1250;
const DEFAULT_OVERLAY_HOLD_MS = 3400;
const DEFAULT_DEMO_VISUAL_BUFFER_MS = 3000;
const DEFAULT_ACTION_RESULT_HOLD_MS = 3000;
const DEFAULT_INTERACTIVE_SLOW_MO_MS = 90;
const DEFAULT_BASIS_DEMO_MAX_MS = 45000;
const DEFAULT_BASIS_PROCESSING_WAIT_MS = 18000;
const DEFAULT_JUDGMENT_DEMO_MAX_MS = 45000;

const VECTOR_BUSINESS_REGISTRATION_FILE = "1.벡트_사업자등록증.pdf";
const VECTOR_SUPPORTING_EVIDENCE_FILES = [
  "2.중소기업확인서_중기업_20260331.pdf",
  "20250226_(주)벡트_직생(동영상제작).pdf",
  "소프트웨어사업자확인서(2023결산)_벡트.pdf",
  "정보통신공사업등록증_벡트.pdf",
  "ISO9001인증서_20270731.pdf",
  "녹색기술제품확인서_20240523_(주)벡트_UITL86GZA5W외 3제품.pdf",
];
const BASIS_RAG_FILE = "RAG_기준문서_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf";
const DEFAULT_NARA_KEYWORD = "전자칠판";
const DEFAULT_NARA_BUSINESS_TYPE = "goods";

const SCENES = [
  {
    id: "intro",
    title: "SMART 조달청 계산기",
    subtitle: "법인 등록, 공고 검색, 기준문서 RAG, 판단 검토, 계약서 생성을 한 흐름으로 연결합니다.",
    route: "/",
    holdMs: 4200,
  },
  {
    id: "corporations",
    title: "1. 법인 등록과 증빙 업로드",
    subtitle: "샘플 사업자등록증으로 새 법인을 만들고, 필요한 확인서와 인증서를 함께 등록합니다.",
    route: "/corporations",
    expect: (data) => [data.corporation.name],
    holdMs: 6200,
  },
  {
    id: "nara-board",
    title: "2. 나라장터 공고 검색과 선택",
    subtitle: "등록 법인의 전자칠판/정보통신 역량에 맞춰 물품 공고를 검색하고 결과를 선택합니다.",
    route: "/nara-board",
    holdMs: 6200,
  },
  {
    id: "saved-notice",
    title: "3. 저장 공고 요구조건 확인",
    subtitle: "선택한 공고를 저장한 뒤 첨부, 분석 상태, 요구조건 후보를 확인합니다.",
    route: (data) => data.routes.saved_notice,
    expect: (data) => [data.notice.bid_ntce_nm || data.notice.bidNtceNm],
    holdMs: 5200,
  },
  {
    id: "basis-documents",
    title: "4. 기준문서 관리와 RAG 업로드",
    subtitle: "중소기업자간 경쟁제품 직접생산 확인기준 PDF를 업로드하고 처리 상태를 확인합니다.",
    route: "/basis-documents",
    expect: (data) => [data.basis_document.title],
    holdMs: 6500,
  },
  {
    id: "notice-comparison",
    title: "5. 부족조건 미리보기",
    subtitle: "저장 공고와 법인 프로필을 선택해 준비할 서류와 확인 항목을 먼저 요약합니다.",
    route: "/notice-comparison",
    expect: (data) => [data.corporation.name],
    holdMs: 5600,
  },
  {
    id: "judgment-runs",
    title: "6. 판단 검토",
    subtitle: "기준문서 근거와 Gemini 보조 판단을 함께 사용해 부족조건과 다음 행동을 정리합니다.",
    route: "/judgment-runs",
    expect: (data) => [data.corporation.name],
    holdMs: 6200,
  },
  {
    id: "contracts",
    title: "7. 계약서 생성",
    subtitle: "공고와 법인 정보를 선택하고 표준계약서 DOCX 초안을 생성한 뒤 목록에서 확인합니다.",
    route: (data) => data.routes.contracts,
    expect: (data) => [data.contract.title],
    holdMs: 6200,
  },
  {
    id: "operations",
    title: "8. 운영 상태 확인",
    subtitle: "실패, 검토 대기, 연동 상태를 운영 대시보드에서 확인합니다.",
    route: "/operations",
    holdMs: 4200,
  },
  {
    id: "operation-runs",
    title: "9. 작업 이력 확인",
    subtitle: "기준문서 처리, 판단 검토, 계약서 생성 이력을 확인합니다.",
    route: "/operation-runs",
    expect: () => ["기준문서 처리"],
    holdMs: 4600,
  },
];

const INTERACTIVE_DEMO_MODES = new Set(["interactive-demo", "real-pdf-demo", "live-nara-demo", "full-workflow-demo"]);

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

const SCENE_PAGE_DEMO_IDS = {
  corporations: "demo-corporations-page",
  "nara-board": "demo-nara-board-page",
  "saved-notice": "demo-saved-notices-page",
  "basis-documents": "demo-basis-documents-page",
  "notice-comparison": "demo-notice-comparison-page",
  "judgment-runs": "demo-judgment-runs-page",
  contracts: "demo-contracts-page",
  operations: "demo-operations-page",
  "operation-runs": "demo-operation-runs-page",
};

const INTERACTIVE_SCENE_ACTIONS = {
  "saved-notice": ["demo-notice-requirements", "demo-notice-attachment-status"],
  "operation-runs": ["demo-operation-run-row"],
};

function numberOption(options, key, fallback) {
  const value = Number(options[key]);
  return Number.isFinite(value) && value >= 0 ? value : fallback;
}

function actionDelay(options, fallback = DEFAULT_STEP_DELAY_MS) {
  return numberOption(options, "step-delay", fallback);
}

function bufferedDelay(delayMs, options = {}) {
  const baseDelay = Number(delayMs);
  const safeBaseDelay = Number.isFinite(baseDelay) && baseDelay >= 0 ? baseDelay : 0;
  return safeBaseDelay + numberOption(options, "visual-buffer-ms", DEFAULT_DEMO_VISUAL_BUFFER_MS);
}

async function holdActionResult(options = {}, label = "action-result") {
  const delayMs = numberOption(options, "action-result-hold-ms", DEFAULT_ACTION_RESULT_HOLD_MS);
  if (delayMs <= 0) return;
  await options.trace?.(`action-result-hold ${label} ${delayMs}ms`);
  await wait(delayMs);
}

function shouldUseRealEvidence(mode, options) {
  return Boolean(options["real-evidence"]) || ["real-pdf-demo", "live-nara-demo", "full-workflow-demo"].includes(mode);
}

function shouldUseRealBasis(mode, options) {
  return Boolean(options["real-basis"]) || ["real-pdf-demo", "live-nara-demo", "full-workflow-demo"].includes(mode);
}

function shouldUseLiveNara(mode, options) {
  return Boolean(options["live-nara"]) || ["live-nara-demo", "full-workflow-demo"].includes(mode);
}

function dateInputValue(daysFromToday) {
  const value = new Date();
  value.setDate(value.getDate() + daysFromToday);
  return value.toISOString().slice(0, 10);
}

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
        width: min(480px, calc(100vw - 48px));
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

async function waitForDemoId(page, demoId, context = {}) {
  const timeout = Number(context.timeoutMs || 15000);
  const visible = await demoLocator(page, demoId)
    .waitFor({ state: "visible", timeout })
    .then(() => true)
    .catch((error) => {
      context.warnings?.push({ scene: context.sceneId, type: "demo_selector_wait_failed", selector: demoId, message: error.message });
      return false;
    });
  if (visible) {
    await wait(Number(context.afterMs || 300));
  }
  return visible;
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
        transition: transform 260ms ease, width 140ms ease, height 140ms ease;
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
        animation: codexDemoRipple 720ms ease-out forwards;
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
  await locator.scrollIntoViewIfNeeded({ timeout: Number(options.timeoutMs || 8000) }).catch(() => {});
  const box = await locator.boundingBox({ timeout: Number(options.timeoutMs || 8000) }).catch(() => null);
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
  await wait(Number(options.settleMs || 360));
  return { x, y };
}

async function showClickRipple(page, point) {
  await page.evaluate(({ x, y }) => {
    const cursor = document.querySelector(".codex-demo-cursor");
    if (cursor instanceof HTMLElement) {
      cursor.classList.add("codex-demo-cursor--down");
      window.setTimeout(() => cursor.classList.remove("codex-demo-cursor--down"), 190);
    }
    const ripple = document.createElement("div");
    ripple.className = "codex-demo-click-ripple";
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    document.body.appendChild(ripple);
    window.setTimeout(() => ripple.remove(), 760);
  }, point);
  await wait(160);
}

async function clickWithCursor(page, locator, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.click({ timeout: Number(options.timeoutMs || 12000) });
  await wait(bufferedDelay(Number(options.afterMs || DEFAULT_CLICK_DELAY_MS), options));
}

async function typeWithCursor(page, locator, text, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.fill(String(text || ""), { timeout: Number(options.timeoutMs || 12000) });
  await wait(bufferedDelay(Number(options.afterMs || DEFAULT_TYPE_DELAY_MS), options));
}

async function setInputFilesWithCursor(page, locator, filePathOrPaths, options = {}) {
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.setInputFiles(filePathOrPaths, { timeout: Number(options.timeoutMs || 12000) });
  await wait(bufferedDelay(Number(options.afterMs || DEFAULT_FILE_DELAY_MS), options));
}

async function selectByDemoId(page, demoId, value, options = {}) {
  const locator = demoLocator(page, demoId);
  const point = await moveCursorTo(page, locator, { ...options, label: demoId });
  await showClickRipple(page, point);
  await locator.selectOption(String(value), { timeout: Number(options.timeoutMs || 12000) });
  await wait(bufferedDelay(Number(options.afterMs || DEFAULT_CLICK_DELAY_MS), options));
  return true;
}

async function selectOptionContaining(page, locator, preferredText, options = {}) {
  const value = await locator.evaluate((select, preferred) => {
    const options = Array.from(select.options || []);
    const preferredOption = options.find((option) => option.value && option.textContent?.includes(preferred));
    const fallbackOption = options.find((option) => option.value);
    return preferredOption?.value || fallbackOption?.value || "";
  }, preferredText);
  if (!value) {
    return false;
  }
  const point = await moveCursorTo(page, locator, options);
  await showClickRipple(page, point);
  await locator.selectOption(value, { timeout: Number(options.timeoutMs || 12000) });
  await wait(bufferedDelay(Number(options.afterMs || DEFAULT_CLICK_DELAY_MS), options));
  return true;
}

async function clickFirstVisibleDemoId(page, demoId, context = {}) {
  const locator = page.locator(`[data-demo-id="${demoId}"]`);
  const count = await locator.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    const visible = await item.isVisible({ timeout: Number(context.timeoutMs || 2500) }).catch(() => false);
    if (!visible) continue;
    const enabled = await item.isEnabled({ timeout: 1500 }).catch(() => true);
    if (!enabled) continue;
    await clickWithCursor(page, item, { label: demoId, afterMs: Number(context.afterMs || DEFAULT_CLICK_DELAY_MS) });
    return true;
  }
  context.warnings?.push({ scene: context.sceneId, type: "missing_or_disabled_demo_selector", selector: demoId });
  return false;
}

async function clickFirstVisibleLocator(page, locator, context = {}) {
  const count = await locator.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    const visible = await item.isVisible({ timeout: Number(context.timeoutMs || 2500) }).catch(() => false);
    if (!visible) continue;
    const enabled = await item.isEnabled({ timeout: 1500 }).catch(() => true);
    if (!enabled) continue;
    await clickWithCursor(page, item, { label: context.label || "visible-locator", afterMs: Number(context.afterMs || DEFAULT_CLICK_DELAY_MS) });
    return true;
  }
  context.warnings?.push({ scene: context.sceneId, type: "missing_or_disabled_locator", label: context.label || "visible-locator" });
  return false;
}

async function safeClickDemoId(page, demoId, context = {}) {
  return clickFirstVisibleDemoId(page, demoId, context);
}

async function tryClickOptionalDemoId(page, demoId, context = {}) {
  const locator = page.locator(`[data-demo-id="${demoId}"]`);
  const count = await locator.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    const visible = await item.isVisible({ timeout: Number(context.timeoutMs || 1200) }).catch(() => false);
    if (!visible) continue;
    const enabled = await item.isEnabled({ timeout: 1000 }).catch(() => true);
    if (!enabled) continue;
    await clickWithCursor(page, item, { label: demoId, afterMs: Number(context.afterMs || DEFAULT_CLICK_DELAY_MS) });
    return true;
  }
  return false;
}

async function navigateBySidebar(page, sidebarDemoId, frontendUrl, context = {}) {
  if (!page.url() || page.url() === "about:blank") {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(bufferedDelay(actionDelay(context, DEFAULT_NAVIGATION_DELAY_MS), context));
  }
  let locator = demoLocator(page, sidebarDemoId);
  if (!(await locator.count().catch(() => 0))) {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(bufferedDelay(actionDelay(context, DEFAULT_NAVIGATION_DELAY_MS), context));
    locator = demoLocator(page, sidebarDemoId);
  }
  await installDemoCursor(page);
  await clickWithCursor(page, locator, { label: sidebarDemoId, afterMs: numberOption(context, "nav-delay", DEFAULT_NAVIGATION_DELAY_MS) });
  await context.trace?.(`sidebar-click ${sidebarDemoId}`);
}

async function pathIfExists(filePath) {
  try {
    const stat = await fs.stat(filePath);
    return stat.isFile() ? filePath : null;
  } catch {
    return null;
  }
}

async function resolveFixtureFile(baseDir, fileName, warnings, sceneId) {
  const filePath = path.join(repoRoot, baseDir, fileName);
  const existing = await pathIfExists(filePath);
  if (!existing) {
    warnings?.push({ scene: sceneId, type: "missing_fixture_file", file: filePath });
  }
  return existing;
}

async function resolveVectorEvidenceFiles(options = {}) {
  const warnings = options.warnings;
  const sceneId = options.sceneId;
  const primary =
    options["business-registration-path"] ||
    (await resolveFixtureFile("source/test_doc", VECTOR_BUSINESS_REGISTRATION_FILE, warnings, sceneId));
  const supportLimit = Math.max(0, Number(options["evidence-file-limit"] || 4));
  const support = [];
  for (const fileName of VECTOR_SUPPORTING_EVIDENCE_FILES.slice(0, supportLimit)) {
    const filePath = await resolveFixtureFile("source/test_doc", fileName, warnings, sceneId);
    if (filePath) support.push(filePath);
  }
  return { primary, support };
}

async function resolveBasisRagFile(options = {}) {
  return (
    options["basis-pdf-path"] ||
    (await resolveFixtureFile("source/rag_doc", BASIS_RAG_FILE, options.warnings, options.sceneId))
  );
}

function parseMaybeJsonObject(value) {
  if (!value) return {};
  if (typeof value === "object" && !Array.isArray(value)) return value;
  if (typeof value !== "string") return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function firstNonEmpty(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value);
    }
  }
  return "";
}

function buildDemoNaraSearchItem(data, options = {}) {
  const notice = data?.notice || {};
  const raw = {
    ...parseMaybeJsonObject(notice.raw_json),
    business_type: options["nara-business-type"] || notice.business_type || DEFAULT_NARA_BUSINESS_TYPE,
    _demo_video_notice_id: notice.id || null,
  };
  const businessType = firstNonEmpty(options["nara-business-type"], raw.business_type, notice.business_type, DEFAULT_NARA_BUSINESS_TYPE);
  return {
    bid_ntce_no: firstNonEmpty(notice.bid_ntce_no, raw.bidNtceNo, `DEMO-${data?.seed || "NOTICE"}`),
    bid_ntce_ord: firstNonEmpty(notice.bid_ntce_ord, raw.bidNtceOrd, "000"),
    bid_ntce_nm: firstNonEmpty(notice.bid_ntce_nm, raw.bidNtceNm, "SMART procurement demo notice"),
    business_type: businessType,
    business_type_label: businessType === "goods" ? "" : firstNonEmpty(notice.business_type_label, raw.business_type_label),
    ntce_instt_nm: firstNonEmpty(notice.ntce_instt_nm, raw.ntceInsttNm, "Demo ordering agency"),
    dminstt_nm: firstNonEmpty(notice.dminstt_nm, raw.dminsttNm, "Demo demand agency"),
    bid_ntce_dt: firstNonEmpty(notice.bid_ntce_dt, raw.bidNtceDt, "2026-06-14 09:00"),
    bid_begin_dt: firstNonEmpty(notice.bid_begin_dt, raw.bidBeginDt, "2026-06-15 09:00"),
    bid_clse_dt: firstNonEmpty(notice.bid_clse_dt, raw.bidClseDt, "2026-06-30 17:00"),
    openg_dt: firstNonEmpty(notice.openg_dt, raw.opengDt, "2026-07-01 10:00"),
    presmpt_prce: firstNonEmpty(notice.presmpt_prce, raw.presmptPrce, "25000000"),
    bdgt_amt: firstNonEmpty(notice.bdgt_amt, raw.bdgtAmt, ""),
    bssamt: firstNonEmpty(notice.bssamt, raw.bssamt, "23000000"),
    region_text: firstNonEmpty(notice.region_text, raw.prtcptPsblRgnNm, raw.cnstrtsiteRgnNm),
    license_text: firstNonEmpty(notice.license_text, raw.lcnsLmtNm, raw.indstrytyNm),
    source_url: firstNonEmpty(notice.source_url, raw.bidNtceDtlUrl, "https://example.go.kr/demo-notice"),
    attachment_count: Array.isArray(notice.attachments) ? notice.attachments.length : 0,
    supported_attachment_count: Array.isArray(notice.attachments)
      ? notice.attachments.filter((item) => item.support_status === "supported").length
      : 0,
    attachments: Array.isArray(notice.attachments) ? notice.attachments : [],
    raw: {
      ...raw,
      bidNtceNo: firstNonEmpty(notice.bid_ntce_no, raw.bidNtceNo, `DEMO-${data?.seed || "NOTICE"}`),
      bidNtceOrd: firstNonEmpty(notice.bid_ntce_ord, raw.bidNtceOrd, "000"),
      bidNtceNm: firstNonEmpty(notice.bid_ntce_nm, raw.bidNtceNm, "SMART procurement demo notice"),
      business_type: businessType,
      _nara_business_type: businessType,
      bidNtceDtlUrl: firstNonEmpty(notice.source_url, raw.bidNtceDtlUrl, "https://example.go.kr/demo-notice"),
    },
  };
}

async function installFastNaraSearchRoute(page, data, options = {}) {
  if (options["nara-real-search"]) return async () => {};
  const item = buildDemoNaraSearchItem(data, options);

  const handler = async (route) => {
    const request = route.request();
    const method = request.method().toUpperCase();
    const url = new URL(request.url());
    if (method === "GET" && url.pathname.endsWith("/api/nara/notices/search")) {
      const pageNo = Number(url.searchParams.get("page_no") || 1);
      const pageSize = Number(url.searchParams.get("page_size") || 20);
      await route.fulfill({
        status: 200,
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify({
          items: [item],
          total_count: 1,
          page_no: pageNo,
          page_size: pageSize,
          business_type: item.business_type,
          business_type_label: item.business_type_label,
          queried_business_types: [item.business_type],
          result_code: "00",
          result_msg: "OK",
          http_status: 200,
          pagination_mode: "single",
          has_next_page: false,
          total_count_is_estimated: false,
          partial_errors: [],
          queried_at: new Date().toISOString(),
        }),
      });
      return;
    }
    if (method === "POST" && url.pathname.endsWith("/api/nara/notices/save-and-analyze")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json; charset=utf-8",
        body: JSON.stringify({ status: "saved", notice: data.notice }),
      });
      return;
    }
    await route.continue();
  };

  await page.route("**/api/nara/notices/**", handler);
  return async () => {
    await page.unroute("**/api/nara/notices/**", handler).catch(() => {});
  };
}

async function installFastBasisUploadRoute(page, data, options = {}) {
  if (options["basis-real-upload"]) return async () => {};
  const basisDocument = data?.basis_document;
  if (!basisDocument?.id) return async () => {};

  const handler = async (route) => {
    const request = route.request();
    if (request.method().toUpperCase() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 201,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify(basisDocument),
    });
  };
  await page.route("**/api/basis-documents", handler);
  return async () => {
    await page.unroute("**/api/basis-documents", handler).catch(() => {});
  };
}

async function installFastJudgmentRunRoute(page, data, options = {}) {
  if (options["judgment-real-run"]) return async () => {};
  const judgmentRun = data?.judgment_run;
  if (!judgmentRun?.id) return async () => {};

  const handler = async (route) => {
    const request = route.request();
    if (request.method().toUpperCase() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 201,
      contentType: "application/json; charset=utf-8",
      body: JSON.stringify(judgmentRun),
    });
  };
  await page.route("**/api/judgment-runs", handler);
  return async () => {
    await page.unroute("**/api/judgment-runs", handler).catch(() => {});
  };
}

async function clickApprovalIfAvailable(page, options = {}) {
  if (!options["evidence-real-approval"]) {
    return false;
  }
  const approveButton = page.getByRole("button", { name: /후보 반영|개 후보 반영/ }).first();
  const visible = await approveButton.isVisible({ timeout: 4500 }).catch(() => false);
  const enabled = visible ? await approveButton.isEnabled({ timeout: 1500 }).catch(() => false) : false;
  if (!visible || !enabled) {
    options.warnings?.push({ scene: options.sceneId, type: "evidence_approval_button_unavailable" });
    return false;
  }
  await clickWithCursor(page, approveButton, { label: "evidence-approval", afterMs: numberOption(options, "step-delay", DEFAULT_STEP_DELAY_MS) });
  await holdActionResult(options, "evidence-approval-result");
  return true;
}

async function runVectorCorporationRegistrationScene(page, options = {}) {
  await waitForDemoId(page, "demo-corporations-page", { ...options, timeoutMs: 12000 });
  await safeClickDemoId(page, "demo-corporation-upload-tab", options);
  const { primary, support } = await resolveVectorEvidenceFiles(options);
  if (!primary) return;

  await setInputFilesWithCursor(page, demoLocator(page, "demo-evidence-file-input"), primary, { label: VECTOR_BUSINESS_REGISTRATION_FILE });
  if (options.dryRun) {
    options.warnings?.push({ scene: options.sceneId, type: "business_registration_upload_skipped_in_dry_run", file: primary });
    return;
  }

  await safeClickDemoId(page, "demo-evidence-upload-submit", { ...options, afterMs: 1400 });
  await page
    .locator('[data-demo-id="demo-latest-evidence-result"]')
    .first()
    .waitFor({ state: "visible", timeout: Number(options.realPdfTimeoutMs || 180000) })
    .catch((error) => {
      options.warnings?.push({ scene: options.sceneId, type: "business_registration_result_wait_failed", message: error.message });
    });
  await holdActionResult(options, "business-registration-result");
  await clickApprovalIfAvailable(page, options);
  await safeClickDemoId(page, "demo-corporation-directory-tab", { ...options, afterMs: 1400 });
  await waitForDemoId(page, "demo-corporation-list", { ...options, timeoutMs: 12000 });

  if (!support.length) return;
  await safeClickDemoId(page, "demo-corporation-upload-tab", { ...options, afterMs: 900 });
  const corporationSelect = page.locator('form[data-demo-id="demo-corporation-evidence-upload-form"] label:has-text("기존 법인에 연결") select').first();
  const selected = await selectOptionContaining(page, corporationSelect, "벡트", { label: "existing-corporation-select" }).catch(() => false);
  if (!selected) {
    options.warnings?.push({ scene: options.sceneId, type: "vector_corporation_option_not_found" });
  }
  await setInputFilesWithCursor(page, demoLocator(page, "demo-evidence-file-input"), support, { label: "vector-supporting-evidence-files" });
  await safeClickDemoId(page, "demo-evidence-upload-submit", { ...options, afterMs: 1600 });
  await Promise.race([
    page.locator('[data-demo-id="demo-evidence-document-list"]').first().waitFor({ state: "visible", timeout: 180000 }),
    page.locator('[data-demo-id="demo-latest-evidence-result"]').first().waitFor({ state: "visible", timeout: 180000 }),
  ]).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "supporting_evidence_result_wait_failed", message: error.message });
  });
  await holdActionResult(options, "supporting-evidence-result");
  await safeClickDemoId(page, "demo-corporation-library-tab", { ...options, afterMs: 1200 });
}

async function runRealPdfEvidenceScene(page, options = {}) {
  return runVectorCorporationRegistrationScene(page, options);
}

async function runBasisDocumentUploadScene(page, data, options = {}) {
  const maxMs = numberOption(options, "basis-demo-max-ms", DEFAULT_BASIS_DEMO_MAX_MS);
  const startedAt = Date.now();
  await waitForDemoId(page, "demo-basis-documents-page", { ...options, timeoutMs: 12000 });
  await waitForDemoId(page, "demo-basis-document-list", { ...options, timeoutMs: 12000 });
  const basisPath = await resolveBasisRagFile(options);
  if (!basisPath) return;
  await setInputFilesWithCursor(page, demoLocator(page, "demo-basis-file-input"), basisPath, { label: BASIS_RAG_FILE });
  if (options.dryRun) {
    options.warnings?.push({ scene: options.sceneId, type: "basis_upload_skipped_in_dry_run", file: basisPath });
    return;
  }
  const uninstallFastUploadRoute = await installFastBasisUploadRoute(page, data, options);
  try {
    await withTimeout(
      safeClickDemoId(page, "demo-basis-upload-submit", { ...options, timeoutMs: 9000, afterMs: 1700 }),
      Math.min(maxMs, 12000),
      "basis upload submit",
    ).catch((error) => {
      options.warnings?.push({ scene: options.sceneId, type: "basis_upload_submit_capped", message: error.message });
    });
  } finally {
    await uninstallFastUploadRoute();
  }

  const remainingMs = Math.max(3000, maxMs - (Date.now() - startedAt));
  const processingWaitMs = Math.min(
    numberOption(options, "basis-processing-timeout-ms", DEFAULT_BASIS_PROCESSING_WAIT_MS),
    remainingMs,
  );
  await Promise.race([
    page.locator('[data-demo-id="demo-basis-processing-progress"]').first().waitFor({ state: "visible", timeout: processingWaitMs }),
    page.locator('[data-demo-id="demo-basis-processing-status"]').first().waitFor({ state: "visible", timeout: processingWaitMs }),
    page.locator('[data-demo-id="demo-basis-document-row"]').first().waitFor({ state: "visible", timeout: processingWaitMs }),
  ]).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "basis_processing_wait_capped", message: error.message });
  });
  await holdActionResult(options, "basis-upload-result");
  await safeClickDemoId(page, "demo-basis-document-detail", { ...options, afterMs: 1200 });
  await safeClickDemoId(page, "demo-basis-chunk-list-toggle", { ...options, afterMs: 1200 });
  await safeClickDemoId(page, "demo-basis-chunk-expand", { ...options, afterMs: 1200 });
}

async function runLiveNaraSearchScene(page, data, options = {}) {
  await waitForDemoId(page, "demo-nara-board-page", { ...options, timeoutMs: 12000 });
  const businessType = String(options["nara-business-type"] || DEFAULT_NARA_BUSINESS_TYPE);
  const keyword = String(options["nara-keyword"] || DEFAULT_NARA_KEYWORD);
  await selectByDemoId(page, "demo-nara-business-type", businessType, options).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "nara_business_type_select_failed", message: error.message });
  });
  await typeWithCursor(page, demoLocator(page, "demo-nara-search-keyword"), keyword, { label: "demo-nara-search-keyword" });
  await typeWithCursor(page, demoLocator(page, "demo-nara-search-start-date"), options["nara-start-date"] || dateInputValue(-365), {
    label: "demo-nara-search-start-date",
  });
  await typeWithCursor(page, demoLocator(page, "demo-nara-search-end-date"), options["nara-end-date"] || dateInputValue(60), {
    label: "demo-nara-search-end-date",
  });
  if (options.dryRun) {
    options.warnings?.push({ scene: options.sceneId, type: "live_nara_search_skipped_in_dry_run", keyword, business_type: businessType });
    return;
  }
  const uninstallFastNaraRoute = options["nara-route-installed"]
    ? async () => {}
    : await installFastNaraSearchRoute(page, data, options);
  try {
    await safeClickDemoId(page, "demo-nara-search-submit", { ...options, timeoutMs: 8000, afterMs: 1500 });
    await Promise.race([
      page.locator('[data-demo-id="demo-nara-result-list"]').first().waitFor({ state: "visible", timeout: 60000 }),
      page.locator('[data-demo-id="demo-nara-partial-error"]').first().waitFor({ state: "visible", timeout: 60000 }),
    ]).catch((error) => {
      options.warnings?.push({ scene: options.sceneId, type: "live_nara_result_wait_failed", message: error.message });
    });
    await holdActionResult(options, "nara-search-result");
    const rowSelected = await safeClickDemoId(page, "demo-nara-result-row", { ...options, afterMs: 1200 });
    if (!rowSelected) return;
    await safeClickDemoId(page, "demo-nara-save-analyze", { ...options, afterMs: 1800 });
    await holdActionResult(options, "nara-save-result");
  } finally {
    await uninstallFastNaraRoute();
  }
}

async function runSavedNoticeScene(page, data, options = {}) {
  await waitForDemoId(page, "demo-saved-notices-page", { ...options, timeoutMs: 12000 });
  await waitForDemoId(page, "demo-saved-notice-list", { ...options, timeoutMs: 12000 });
  const clicked = await safeClickDemoId(page, "demo-saved-notice-detail-link", { ...options, sceneId: "saved-notice" });
  if (!clicked && data.routes?.saved_notice) {
    await page.goto(`${options.frontendUrl}${data.routes.saved_notice}`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
  }
  await waitForDemoId(page, "demo-saved-notice-detail-page", { ...options, timeoutMs: 20000 });
  await holdActionResult(options, "saved-notice-detail");
}

async function runNoticeComparisonScene(page, data, options = {}) {
  await waitForDemoId(page, "demo-notice-comparison-page", { ...options, timeoutMs: 12000 });
  await selectByDemoId(page, "demo-comparison-notice-select", data.notice.id, options);
  await selectByDemoId(page, "demo-comparison-corporation-select", data.corporation.id, options);
  if (options.dryRun) return;
  await safeClickDemoId(page, "demo-notice-comparison-run", { ...options, afterMs: 1800 });
  await page.locator(".result-summary-panel").first().waitFor({ state: "visible", timeout: 60000 }).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "comparison_summary_wait_failed", message: error.message });
  });
  await holdActionResult(options, "comparison-summary");
  await clickFirstVisibleLocator(page, page.locator(".quick-action").nth(1), {
    ...options,
    label: "comparison-requirements-action",
    afterMs: 1200,
  });
  await waitForDemoId(page, "demo-comparison-requirements-modal", { ...options, timeoutMs: 12000 });
  await holdActionResult(options, "comparison-requirements-modal");
  await clickFirstVisibleLocator(page, page.locator(".app-modal-header button"), {
    ...options,
    label: "comparison-requirements-modal-close",
    afterMs: 900,
  });
  await safeClickDemoId(page, "demo-comparison-history-open", { ...options, afterMs: 1200 });
  await waitForDemoId(page, "demo-comparison-history-modal", { ...options, timeoutMs: 12000 });
  await clickFirstVisibleLocator(page, page.locator(".history-item"), {
    ...options,
    label: "comparison-history-item",
    afterMs: 1200,
  });
  await waitForDemoId(page, "demo-comparison-detail-modal", { ...options, timeoutMs: 12000 });
  await holdActionResult(options, "comparison-detail-modal");
  await clickFirstVisibleLocator(page, page.locator(".modal-action-row--leading button"), {
    ...options,
    label: "comparison-detail-back-to-history",
    afterMs: 900,
  });
  await clickFirstVisibleLocator(page, page.locator('[data-demo-id="demo-comparison-history-modal"] .app-modal-header button'), {
    ...options,
    label: "comparison-history-modal-final-close",
    afterMs: 900,
  });
}

async function runJudgmentReviewScene(page, data, options = {}) {
  await waitForDemoId(page, "demo-judgment-runs-page", { ...options, timeoutMs: 12000 });
  await selectByDemoId(page, "demo-judgment-notice-select", data.notice.id, options);
  await selectByDemoId(page, "demo-judgment-corporation-select", data.corporation.id, options);
  if (options.dryRun) return;
  const maxMs = numberOption(options, "judgment-demo-max-ms", DEFAULT_JUDGMENT_DEMO_MAX_MS);
  const uninstallFastJudgmentRoute = await installFastJudgmentRunRoute(page, data, options);
  try {
    await withTimeout(
      safeClickDemoId(page, "demo-judgment-run-create", { ...options, timeoutMs: 9000, afterMs: 2200 }),
      Math.min(maxMs, 12000),
      "judgment run create",
    ).catch((error) => {
      options.warnings?.push({ scene: options.sceneId, type: "judgment_run_submit_capped", message: error.message });
    });
  } finally {
    await uninstallFastJudgmentRoute();
  }
  await page.locator(".result-summary-panel").first().waitFor({ state: "visible", timeout: Math.min(maxMs, 30000) }).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "judgment_summary_wait_failed", message: error.message });
  });
  await holdActionResult(options, "judgment-summary");
  await safeClickDemoId(page, "demo-judgment-history-open", { ...options, afterMs: 1200 });
  await waitForDemoId(page, "demo-judgment-history-modal", { ...options, timeoutMs: 12000 });
  await safeClickDemoId(page, "demo-judgment-run-row", { ...options, afterMs: 1200 });
  await waitForDemoId(page, "demo-judgment-detail-modal", { ...options, timeoutMs: 12000 });
  await holdActionResult(options, "judgment-detail-modal");
  const evidenceOpened = await clickFirstVisibleLocator(page, page.locator('[data-demo-id="demo-judgment-detail-modal"] .evidence-link-button'), {
    ...options,
    label: "judgment-evidence-link",
    afterMs: 1200,
  });
  if (evidenceOpened) {
    await waitForDemoId(page, "demo-judgment-evidence-modal", { ...options, timeoutMs: 12000 });
    await holdActionResult(options, "judgment-evidence-modal");
    await clickFirstVisibleLocator(page, page.locator('[data-demo-id="demo-judgment-evidence-modal"] .app-modal-header button'), {
      ...options,
      label: "judgment-evidence-modal-close",
      afterMs: 900,
    });
  }
  await clickFirstVisibleLocator(page, page.locator(".modal-action-row--leading button"), {
    ...options,
    label: "judgment-detail-back-to-history",
    afterMs: 900,
  });
}

async function runContractCreationScene(page, data, options = {}) {
  await waitForDemoId(page, "demo-contracts-page", { ...options, timeoutMs: 12000 });
  await selectByDemoId(page, "demo-contract-notice-select", data.notice.id, options);
  await selectByDemoId(page, "demo-contract-corporation-select", data.corporation.id, options);
  if (data.judgment_run?.id) {
    await selectByDemoId(page, "demo-contract-judgment-select", data.judgment_run.id, options).catch(() => {});
  }
  if (options.dryRun) return;
  await safeClickDemoId(page, "demo-contract-preview", { ...options, afterMs: 1800 });
  await safeClickDemoId(page, "demo-contract-create", { ...options, afterMs: 2200 });
  const contractList = page.locator('[data-demo-id="demo-contract-list"]').first();
  await contractList.waitFor({ state: "visible", timeout: 60000 }).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "contract_list_wait_failed", message: error.message });
  });
  await contractList.scrollIntoViewIfNeeded({ timeout: 8000 }).catch((error) => {
    options.warnings?.push({ scene: options.sceneId, type: "contract_list_scroll_failed", message: error.message });
  });
  await holdActionResult(options, "contract-list");
  const downloadLink = page.locator('[data-demo-id="demo-contract-download"]').first();
  if (!options["contract-real-download"]) {
    if (await downloadLink.isVisible({ timeout: 3500 }).catch(() => false)) {
      await options.trace?.("contract download skipped for stable video");
    }
    return;
  }
  if (await downloadLink.isVisible({ timeout: 3500 }).catch(() => false)) {
    const download = page.waitForEvent("download", { timeout: 7000 }).catch(() => null);
    await clickWithCursor(page, downloadLink, { label: "demo-contract-download", afterMs: 1200 });
    const downloaded = await download;
    if (downloaded) {
      await options.trace?.(`contract download captured: ${downloaded.suggestedFilename()}`);
    }
  }
}

async function runOperationsScene(page, options = {}) {
  await waitForDemoId(page, "demo-operations-page", { ...options, timeoutMs: 12000 });
  await waitForDemoId(page, "demo-operations-summary", { ...options, timeoutMs: 12000 });
  await holdActionResult(options, "operations-summary");
  await tryClickOptionalDemoId(page, "demo-operation-error-detail", { ...options, afterMs: 1200 });
}

async function runOperationRunsScene(page, options = {}) {
  await waitForDemoId(page, "demo-operation-runs-page", { ...options, timeoutMs: 12000 });
  await safeClickDemoId(page, "demo-operation-run-row", { ...options, afterMs: 1200 });
  await holdActionResult(options, "operation-run-detail");
  await tryClickOptionalDemoId(page, "demo-operation-error-detail", { ...options, afterMs: 1200 });
}

async function runInteractiveScene(page, scene, data, options = {}) {
  const route = typeof scene.route === "function" ? scene.route(data) : scene.route;
  const frontendUrl = options.frontendUrl;
  const sidebarDemoId = routeToSidebarDemoId(route);
  const shouldPreinstallNaraRoute = scene.id === "nara-board" && shouldUseLiveNara(options.mode, options);
  const uninstallPreinstalledNaraRoute = shouldPreinstallNaraRoute
    ? await installFastNaraSearchRoute(page, data, options)
    : async () => {};

  if (scene.id === "intro") {
    await page.goto(`${frontendUrl}/`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(bufferedDelay(numberOption(options, "nav-delay", DEFAULT_NAVIGATION_DELAY_MS), options));
    return route;
  }

  if (scene.id === "saved-notice") {
    await navigateBySidebar(page, "sidebar-nara-saved-notices", frontendUrl, options);
    await runSavedNoticeScene(page, data, { ...options, sceneId: scene.id, frontendUrl });
    return route;
  }

  if (sidebarDemoId) {
    await navigateBySidebar(page, sidebarDemoId, frontendUrl, options);
    if (route.includes("?")) {
      await page.goto(`${frontendUrl}${route}`, { waitUntil: "commit", timeout: 45000 });
      await installDemoCursor(page);
      await wait(bufferedDelay(numberOption(options, "nav-delay", DEFAULT_NAVIGATION_DELAY_MS), options));
    }
  } else {
    await page.goto(`${frontendUrl}${route}`, { waitUntil: "commit", timeout: 45000 });
    await installDemoCursor(page);
    await wait(bufferedDelay(numberOption(options, "nav-delay", DEFAULT_NAVIGATION_DELAY_MS), options));
  }

  if (SCENE_PAGE_DEMO_IDS[scene.id]) {
    await waitForDemoId(page, SCENE_PAGE_DEMO_IDS[scene.id], { ...options, sceneId: scene.id, timeoutMs: 15000 });
  }

  if (scene.id === "corporations" && shouldUseRealEvidence(options.mode, options)) {
    await runVectorCorporationRegistrationScene(page, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "nara-board" && shouldUseLiveNara(options.mode, options)) {
    try {
      await runLiveNaraSearchScene(page, data, { ...options, sceneId: scene.id, "nara-route-installed": true });
    } finally {
      await uninstallPreinstalledNaraRoute();
    }
    return route;
  }
  if (scene.id === "basis-documents" && shouldUseRealBasis(options.mode, options)) {
    await runBasisDocumentUploadScene(page, data, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "notice-comparison") {
    await runNoticeComparisonScene(page, data, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "judgment-runs") {
    await runJudgmentReviewScene(page, data, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "contracts") {
    await runContractCreationScene(page, data, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "operations") {
    await runOperationsScene(page, { ...options, sceneId: scene.id });
    return route;
  }
  if (scene.id === "operation-runs") {
    await runOperationRunsScene(page, { ...options, sceneId: scene.id });
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
  const interactive = isInteractiveDemoMode(mode) || Boolean(options.cursor);
  const browser = await chromium.launch({
    headless: options.headed ? false : true,
    slowMo: Number(options["slow-mo"] ?? (interactive ? DEFAULT_INTERACTIVE_SLOW_MO_MS : 0)),
  });
  const context = await browser.newContext({
    viewport: { width: Number(options.width || 1440), height: Number(options.height || 900) },
    extraHTTPHeaders: { "ngrok-skip-browser-warning": "true" },
    recordVideo: options.dryRun ? undefined : { dir: rawVideoDir, size: { width: Number(options.width || 1440), height: Number(options.height || 900) } },
  });
  const page = await context.newPage();
  if (interactive) {
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
    if (interactive) {
      await runInteractiveScene(page, scene, data, {
        ...options,
        mode,
        frontendUrl,
        backendUrl,
        warnings,
        trace,
        dryRun: Boolean(options.dryRun),
      });
      await trace(`scene ${scene.id}: interactive navigation done`);
    } else {
      await page.goto(url, { waitUntil: "commit", timeout: 45000 });
      await trace(`scene ${scene.id}: goto committed`);
    }

    await wait(bufferedDelay(numberOption(options, "scene-gap", DEFAULT_SCENE_GAP_MS), options));
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

    await wait(bufferedDelay(Number(scene.holdMs || DEFAULT_OVERLAY_HOLD_MS), options));
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
