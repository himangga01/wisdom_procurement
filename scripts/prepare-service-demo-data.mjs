#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  apiRequest,
  artifactsDir,
  createSimplePdfBuffer,
  ensureDir,
  makeSeed,
  normalizeUrl,
  parseArgs,
  wait,
  waitForEndpoint,
  writeJson,
} from "./demo-video-utils.mjs";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:18111";

function demoBusinessNumber(seed) {
  const numeric = String(seed).replace(/\D/g, "").slice(-5).padStart(5, "0");
  return `142-81-${numeric}`;
}

async function createOrReuseCorporation(backendUrl, seed) {
  const name = `시연 법인 ${seed}`;
  const existing = await apiRequest(backendUrl, "/api/corporations");
  const match = Array.isArray(existing) ? existing.find((item) => item.name === name) : null;
  if (match) {
    return match;
  }
  return apiRequest(backendUrl, "/api/corporations", {
    json: {
      name,
      management_group_name: `제품 시연 그룹 ${seed}`,
      business_registration_number: demoBusinessNumber(seed),
      representative_name: "김시연",
      business_address: "경기도 성남시 분당구 데모로 10",
      headquarters_address: "경기도 성남시 분당구 데모로 10",
      business_category: "정보통신 서비스",
      business_type: "소프트웨어 개발 및 정보통신 공사업",
      business_item: "공공기관 업무 포털 구축, 영상정보 처리장치 유지관리",
      region: "경기도",
      company_size_classification: "소기업",
      certifications_json: ["중소기업확인서"],
      preference_tags_json: ["공공조달 시연용"],
      direct_production_items_json: ["정보시스템 유지관리 서비스"],
      license_summary: "정보통신공사업 등록 준비 필요",
      procurement_registration_status: "조달업체 등록 완료",
      evidence_expiry_summary: "중소기업확인서 2026-12-31 만료",
      evidence_verification_status: "evidence_reviewed",
      internal_notes: "서비스 시연 영상 자동 생성 데이터",
    },
  });
}

async function uploadDemoEvidence(backendUrl, corporationId, seed, runDir) {
  const pdfBuffer = createSimplePdfBuffer([
    "Business Registration Certificate",
    `Corporation: Demo Smart Procurement ${seed}`,
    `Business registration number: ${demoBusinessNumber(seed)}`,
    "Representative: Demo Owner",
    "Address: Demo-ro 10, Seongnam-si, Gyeonggi-do",
  ]);
  const fixturePath = path.join(runDir, "fixtures", `demo-business-registration-${seed}.pdf`);
  await ensureDir(path.dirname(fixturePath));
  await fs.writeFile(fixturePath, pdfBuffer);

  const formData = new FormData();
  formData.append("corporation_id", String(corporationId));
  formData.append("document_type", "business_registration_certificate");
  formData.append("memo", "제품 시연 영상용 사업자등록 증빙 샘플");
  formData.append("file", new Blob([pdfBuffer], { type: "application/pdf" }), `사업자등록증명-${seed}.pdf`);
  return apiRequest(backendUrl, "/api/corporation-evidence-documents", {
    method: "POST",
    body: formData,
  });
}

async function createNotice(backendUrl, seed) {
  const noticePayload = {
    bidNtceNo: `DEMO${seed}`.slice(0, 40),
    bidNtceOrd: "000",
    bidNtceNm: `제품 시연용 정보통신 용역 공고 ${seed}`,
    ntceInsttNm: "시연 발주기관",
    dminsttNm: "시연 수요기관",
    bidNtceDt: "2026-06-14 09:00",
    bidBeginDt: "2026-06-15 09:00",
    bidClseDt: "2026-06-30 17:00",
    opengDt: "2026-07-01 10:00",
    presmptPrce: "25000000",
    bssamt: "23000000",
    prtcptPsblRgnNm: "경기도",
    lcnsLmtNm: "information communication construction license",
    bidNtceDtlUrl: "https://example.go.kr/demo-notice",
    business_type: "service",
  };
  const response = await apiRequest(backendUrl, "/api/nara/notices/save-and-analyze", {
    json: { notice: noticePayload },
  });
  return response.notice || response;
}

async function waitForSavedNotice(backendUrl, noticeId) {
  let latest = null;
  for (let index = 0; index < 50; index += 1) {
    latest = await apiRequest(backendUrl, `/api/nara/saved-notices/${noticeId}`);
    const status = latest.analysis_status || latest.status || "";
    if (!["pending", "queued", "saving", "analyzing", "running"].includes(status)) {
      return latest;
    }
    await wait(500);
  }
  return latest;
}

async function uploadBasisDocument(backendUrl, seed, runDir) {
  const pdfBuffer = createSimplePdfBuffer([
    "SMART Procurement Demo Basis Document",
    "Information communication construction license is a citation candidate for bidder qualification review.",
    "Small business certificate is a required document candidate for company type review.",
    "Business registration certificate must be submitted before contract review.",
    "Contract officers should verify missing documents before deciding readiness.",
    "If a requirement is not supported by corporation evidence, mark it as needs review.",
  ]);
  const fixturePath = path.join(runDir, "fixtures", `demo-basis-${seed}.pdf`);
  await ensureDir(path.dirname(fixturePath));
  await fs.writeFile(fixturePath, pdfBuffer);

  const formData = new FormData();
  formData.append("title", `제품 시연 기준문서 ${seed}`);
  formData.append("category", "demo");
  formData.append("document_version", "2026.06-demo");
  formData.append("issuing_agency", "SMART Procurement Demo");
  formData.append("effective_date", "2026-06-14");
  formData.append("memo", "제품 시연 영상 자동 생성 기준문서");
  formData.append("force_ocr", "false");
  formData.append("file", new Blob([pdfBuffer], { type: "application/pdf" }), `demo-basis-${seed}.pdf`);
  return apiRequest(backendUrl, "/api/basis-documents", {
    method: "POST",
    body: formData,
  });
}

export async function prepareDemoData(options = {}) {
  const backendUrl = normalizeUrl(options.backendUrl, DEFAULT_BACKEND_URL);
  const seed = makeSeed(options.seed);
  const outDir = path.resolve(options.outDir || artifactsDir);
  const runDir = path.join(outDir, "runs", seed);
  const warnings = [];
  await ensureDir(runDir);

  await waitForEndpoint(`${backendUrl}/api/dashboard/summary`, { timeoutMs: 30000 });

  const corporation = await createOrReuseCorporation(backendUrl, seed);
  let evidence = null;
  try {
    evidence = await uploadDemoEvidence(backendUrl, corporation.id, seed, runDir);
  } catch (error) {
    warnings.push({
      step: "upload_demo_evidence",
      message: error.message,
    });
  }

  const noticeInitial = await createNotice(backendUrl, seed);
  const notice = await waitForSavedNotice(backendUrl, noticeInitial.id);
  const requirements = await apiRequest(backendUrl, `/api/nara/saved-notices/${notice.id}/requirements`);
  const structuredRequirements = await apiRequest(
    backendUrl,
    `/api/nara/saved-notices/${notice.id}/requirements/structured`,
  );

  const basisDocument = await uploadBasisDocument(backendUrl, seed, runDir);
  const basisSearch = await apiRequest(backendUrl, "/api/basis-search", {
    json: { query: "information communication construction license", top_k: 3 },
  });

  const comparison = await apiRequest(backendUrl, "/api/notice-comparisons", {
    json: { nara_notice_id: notice.id, corporation_id: corporation.id },
  });

  const judgmentRun = await apiRequest(backendUrl, "/api/judgment-runs", {
    json: { nara_notice_id: notice.id, corporation_id: corporation.id, top_k: 3 },
  });

  const contractPreview = await apiRequest(backendUrl, "/api/contracts/preview", {
    json: {
      nara_notice_id: notice.id,
      corporation_id: corporation.id,
      judgment_run_id: judgmentRun.id,
      custom_fields: {
        contract_number: `DEMO-${seed}`,
        contract_amount: "25,000,000원",
        contract_period: "2026.07.01 ~ 2026.12.31",
      },
    },
  });

  const contract = await apiRequest(backendUrl, "/api/contracts", {
    json: {
      nara_notice_id: notice.id,
      corporation_id: corporation.id,
      judgment_run_id: judgmentRun.id,
      title: `제품 시연 계약서 초안 ${seed}`,
      custom_fields: {
        contract_number: `DEMO-${seed}`,
        contract_amount: "25,000,000원",
        contract_period: "2026.07.01 ~ 2026.12.31",
      },
    },
  });

  const operationRuns = await apiRequest(backendUrl, "/api/operation-runs");
  const result = {
    seed,
    backend_url: backendUrl,
    run_dir: runDir,
    warnings,
    corporation,
    evidence,
    notice,
    requirements_summary: {
      count: requirements.requirements?.length || 0,
      structured_count: structuredRequirements.requirement_count || 0,
      contract_version: structuredRequirements.contract_version || "",
    },
    basis_document: basisDocument,
    basis_search_summary: {
      index_source: basisSearch.index_source,
      result_count: basisSearch.result_count,
    },
    comparison,
    judgment_run: judgmentRun,
    contract_preview: {
      valid: contractPreview.valid,
      warnings: contractPreview.warnings || [],
      errors: contractPreview.errors || [],
    },
    contract,
    operation_summary: {
      count: Array.isArray(operationRuns) ? operationRuns.length : 0,
      types: Array.isArray(operationRuns) ? [...new Set(operationRuns.map((item) => item.operation_type))] : [],
    },
    routes: {
      dashboard: "/",
      corporations: "/corporations",
      nara_board: "/nara-board",
      saved_notice: `/nara-saved-notices/${notice.id}`,
      basis_documents: "/basis-documents",
      notice_comparison: "/notice-comparison",
      judgment_runs: "/judgment-runs",
      contracts: `/contracts?notice_id=${notice.id}&corporation_id=${corporation.id}&judgment_run_id=${judgmentRun.id}`,
      operations: "/operations",
      operation_runs: "/operation-runs",
    },
  };
  await writeJson(path.join(runDir, "demo-data.json"), result);
  await writeJson(path.join(outDir, "latest-demo-data.json"), result);
  return result;
}

async function main() {
  const args = parseArgs();
  const data = await prepareDemoData({
    backendUrl: args["backend-url"],
    seed: args.seed,
    outDir: args["out-dir"],
  });
  console.log(JSON.stringify({ seed: data.seed, run_dir: data.run_dir, warnings: data.warnings }, null, 2));
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
