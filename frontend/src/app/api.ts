import type {
  AiModelSelection,
  AiModelSettings,
  AnalysisRecord,
  BackupRestorePlan,
  BackupRun,
  BackupValidation,
  BasisDocument,
  BasisChunkDetail,
  BasisDocumentChunk,
  BasisIndexStatus,
  BasisRuleCandidate,
  BasisRuleCandidateList,
  BasisRetrievalEvaluation,
  BasisSearchResponse,
  ContractCustomFields,
  ContractDocument,
  ContractPreview,
  Corporation,
  CorporationEvidenceApplyResult,
  CorporationEvidenceDocument,
  CorporationReadiness,
  DashboardSummary,
  DocumentRecord,
  ExternalAccessStatus,
  NaraNoticeSearchItem,
  NaraNoticeSearchResponse,
  NoticeCorporationComparison,
  NoticeRequirementDetail,
  NoticeRequirementPayload,
  NaraIntegrationStatus,
  NaraIntegrationTestResult,
  OperationRun,
  OperationsSummary,
  PdfReaderStatus,
  Project,
  SavedNaraNotice,
  CorporationComparisonProfile,
  JudgmentRun,
  NaraCollectionRun,
} from "./types";

function normalizeApiBase(value: string | undefined) {
  return String(value || "").replace(/\/+$/, "");
}

function isNgrokHostname(hostname: string) {
  return [".ngrok-free.app", ".ngrok-free.dev", ".ngrok.app", ".ngrok.pro"].some((suffix) => hostname.endsWith(suffix));
}

const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);
const NEEDS_NGROK_SKIP_HEADER = (() => {
  try {
    const hostname = API_BASE
      ? new URL(API_BASE).hostname
      : typeof window !== "undefined"
        ? window.location.hostname
        : "";
    return isNgrokHostname(hostname);
  } catch {
    return false;
  }
})();

export function buildApiUrl(path: string) {
  return `${API_BASE}${path}`;
}

function withRuntimeHeaders(init?: RequestInit): RequestInit | undefined {
  if (!NEEDS_NGROK_SKIP_HEADER) {
    return init;
  }
  const headers = new Headers(init?.headers);
  headers.set("ngrok-skip-browser-warning", "1");
  return { ...init, headers };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, withRuntimeHeaders(init));
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed");
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export const api = {
  getDashboard: () => request<DashboardSummary>("/api/dashboard/summary"),
  getOperationsSummary: () => request<OperationsSummary>("/api/operations/summary"),
  getExternalAccessStatus: () => request<ExternalAccessStatus>("/api/external-access/status"),
  listOperationRuns: (params: Record<string, string | undefined> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    return request<OperationRun[]>(`/api/operation-runs?${query.toString()}`);
  },
  getOperationRun: (id: number) => request<OperationRun>(`/api/operation-runs/${id}`),
  retryOperationRun: (id: number) =>
    request<OperationRun>(`/api/operation-runs/${id}/retry`, {
      method: "POST",
    }),
  listBackups: () => request<BackupRun[]>("/api/backups"),
  createBackup: () =>
    request<BackupRun>("/api/backups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }),
  validateBackup: (backupId: number) =>
    request<BackupValidation>("/api/backups/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backup_id: backupId }),
    }),
  createBackupRestorePlan: (backupId: number) =>
    request<BackupRestorePlan>("/api/backups/restore-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ backup_id: backupId }),
    }),
  dryRunBackupRestore: (backupId: number) =>
    request<BackupRestorePlan>(`/api/backups/${backupId}/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dry_run: true }),
    }),
  listContracts: (params: Record<string, string | number | undefined> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        query.set(key, String(value));
      }
    });
    return request<ContractDocument[]>(`/api/contracts?${query.toString()}`);
  },
  previewContract: (body: {
    nara_notice_id: number;
    corporation_id: number;
    judgment_run_id?: number | null;
    custom_fields?: ContractCustomFields;
  }) =>
    request<ContractPreview>("/api/contracts/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  createContract: (body: {
    nara_notice_id: number;
    corporation_id: number;
    judgment_run_id?: number | null;
    title?: string;
    custom_fields?: ContractCustomFields;
  }) =>
    request<ContractDocument>("/api/contracts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getContract: (id: number) => request<ContractDocument>(`/api/contracts/${id}`),
  updateContractReview: (id: number, body: { review_status?: string; review_note?: string }) =>
    request<ContractDocument>(`/api/contracts/${id}/review`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteContract: (id: number) =>
    request<{ status: string; contract: ContractDocument }>(`/api/contracts/${id}`, {
      method: "DELETE",
    }),
  getContractDownloadUrl: (id: number) => buildApiUrl(`/api/contracts/${id}/download`),
  getAiModelSettings: () => request<AiModelSettings>("/api/settings/ai-models"),
  getPdfReaderStatus: () => request<PdfReaderStatus>("/api/settings/pdf-reader/status"),
  listCorporations: () => request<Corporation[]>("/api/corporations"),
  createCorporation: (body: Record<string, unknown>) =>
    request<Corporation>("/api/corporations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  updateCorporation: (id: number, body: Record<string, unknown>) =>
    request<Corporation>(`/api/corporations/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteCorporation: (id: number) =>
    request<{ status: string }>(`/api/corporations/${id}`, {
      method: "DELETE",
    }),
  listCorporationReadiness: () => request<CorporationReadiness[]>("/api/corporations/readiness"),
  getCorporationComparisonProfile: (corporationId: number) =>
    request<CorporationComparisonProfile>(`/api/corporations/${corporationId}/comparison-profile`),
  listCorporationEvidenceDocuments: (corporationId: number) =>
    request<CorporationEvidenceDocument[]>(`/api/corporations/${corporationId}/evidence-documents`),
  listAllCorporationEvidenceDocuments: () =>
    request<CorporationEvidenceDocument[]>("/api/corporation-evidence-documents"),
  getCorporationEvidenceDocument: (id: number) =>
    request<CorporationEvidenceDocument>(`/api/corporation-evidence-documents/${id}`),
  uploadCorporationEvidenceDocument: (formData: FormData) =>
    request<CorporationEvidenceDocument>("/api/corporation-evidence-documents", {
      method: "POST",
      body: formData,
    }),
  updateCorporationEvidenceDocument: (id: number, body: Record<string, unknown>) =>
    request<CorporationEvidenceDocument>(`/api/corporation-evidence-documents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  reprocessCorporationEvidenceDocument: (id: number, body: Record<string, unknown> = {}) =>
    request<CorporationEvidenceDocument>(`/api/corporation-evidence-documents/${id}/reprocess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  reanalyzeCorporationEvidenceText: (id: number, body: Record<string, unknown>) =>
    request<CorporationEvidenceDocument>(`/api/corporation-evidence-documents/${id}/reanalyze-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  approveCorporationEvidenceDocument: (id: number, body: Record<string, unknown> = {}) =>
    request<CorporationEvidenceApplyResult>(`/api/corporation-evidence-documents/${id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteCorporationEvidenceDocument: (id: number) =>
    request<{ status: string }>(`/api/corporation-evidence-documents/${id}`, {
      method: "DELETE",
    }),
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (body: Record<string, unknown>) =>
    request<Project>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  updateProject: (id: number, body: Record<string, unknown>) =>
    request<Project>(`/api/projects/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteProject: (id: number) =>
    request<{ status: string }>(`/api/projects/${id}`, {
      method: "DELETE",
    }),
  listDocuments: () => request<DocumentRecord[]>("/api/documents"),
  uploadDocument: (formData: FormData) =>
    request<DocumentRecord>("/api/documents", {
      method: "POST",
      body: formData,
    }),
  updateDocument: (id: number, body: Record<string, unknown>) =>
    request<DocumentRecord>(`/api/documents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteDocument: (id: number) =>
    request<{ status: string }>(`/api/documents/${id}`, {
      method: "DELETE",
    }),
  analyzeDocument: (documentId: number, selection?: AiModelSelection) =>
    request<{ analysis_id: number; status: string; message: string }>(`/api/documents/${documentId}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(selection ?? {}),
    }),
  reanalyzeDocument: (documentId: number, selection?: AiModelSelection) =>
    request<{ analysis_id: number; status: string; message: string }>(`/api/documents/${documentId}/reanalyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(selection ?? {}),
    }),
  getLatestAnalysisByDocument: (documentId: number) =>
    request<AnalysisRecord>(`/api/analyses/latest/by-document/${documentId}`),
  listBasisDocuments: (params: Record<string, string | undefined> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    return request<BasisDocument[]>(`/api/basis-documents?${query.toString()}`);
  },
  uploadBasisDocument: (formData: FormData) =>
    request<BasisDocument>("/api/basis-documents", {
      method: "POST",
      body: formData,
    }),
  getBasisDocument: (id: number) => request<BasisDocument>(`/api/basis-documents/${id}`),
  listBasisDocumentChunks: (id: number) => request<BasisDocumentChunk[]>(`/api/basis-documents/${id}/chunks`),
  getBasisDocumentChunk: (basisDocumentId: number, chunkId: number) =>
    request<BasisChunkDetail>(`/api/basis-documents/${basisDocumentId}/chunks/${chunkId}`),
  updateBasisDocument: (id: number, body: Record<string, unknown>) =>
    request<BasisDocument>(`/api/basis-documents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  reprocessBasisDocument: (id: number, body: Record<string, unknown> = {}) =>
    request<BasisDocument>(`/api/basis-documents/${id}/reprocess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteBasisDocument: (id: number) =>
    request<{ status: string }>(`/api/basis-documents/${id}`, {
      method: "DELETE",
    }),
  searchBasisDocuments: (body: Record<string, unknown>) =>
    request<BasisSearchResponse>("/api/basis-search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getBasisIndexStatus: () => request<BasisIndexStatus>("/api/basis-index/status"),
  validateBasisIndex: () =>
    request<BasisIndexStatus>("/api/basis-index/validate", {
      method: "POST",
    }),
  rebuildBasisIndex: () =>
    request<BasisIndexStatus>("/api/basis-index/rebuild", {
      method: "POST",
    }),
  listBasisRuleCandidates: (params: Record<string, string | number | undefined> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") query.set(key, String(value));
    });
    return request<BasisRuleCandidateList>(`/api/basis-rule-candidates?${query.toString()}`);
  },
  getBasisRuleCandidate: (id: number) => request<BasisRuleCandidate>(`/api/basis-rule-candidates/${id}`),
  updateBasisRuleCandidate: (id: number, body: Record<string, unknown>) =>
    request<BasisRuleCandidate>(`/api/basis-rule-candidates/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  approveBasisRuleCandidate: (id: number, body: Record<string, unknown> = {}) =>
    request<BasisRuleCandidate>(`/api/basis-rule-candidates/${id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  rejectBasisRuleCandidate: (id: number, body: Record<string, unknown> = {}) =>
    request<BasisRuleCandidate>(`/api/basis-rule-candidates/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  extractBasisRuleCandidates: (basisDocumentId: number) =>
    request<BasisRuleCandidateList & { basis_document_id: number; status: string; note: string }>(
      `/api/basis-documents/${basisDocumentId}/rule-candidates/extract`,
      { method: "POST" },
    ),
  listBasisRetrievalEvaluations: () => request<BasisRetrievalEvaluation[]>("/api/basis-retrieval-evaluations"),
  createBasisRetrievalEvaluation: (body: Record<string, unknown>) =>
    request<BasisRetrievalEvaluation>("/api/basis-retrieval-evaluations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getBasisRetrievalEvaluation: (id: number) => request<BasisRetrievalEvaluation>(`/api/basis-retrieval-evaluations/${id}`),
  getNaraIntegrationStatus: () =>
    request<NaraIntegrationStatus>("/api/settings/integrations/nara/status"),
  testNaraIntegration: () =>
    request<NaraIntegrationTestResult>("/api/settings/integrations/nara/test", {
      method: "POST",
    }),
  searchNaraNotices: (params: Record<string, string | number | undefined>) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        query.set(key, String(value));
      }
    });
    return request<NaraNoticeSearchResponse>(`/api/nara/notices/search?${query.toString()}`);
  },
  saveAndAnalyzeNaraNotice: (notice: NaraNoticeSearchItem, selection?: AiModelSelection) =>
    request<{ status: string; notice: SavedNaraNotice }>("/api/nara/notices/save-and-analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notice: notice.raw, ...(selection ?? {}) }),
    }),
  listSavedNaraNotices: (keyword = "") => {
    const query = new URLSearchParams();
    if (keyword) query.set("keyword", keyword);
    return request<SavedNaraNotice[]>(`/api/nara/saved-notices?${query.toString()}`);
  },
  getSavedNaraNotice: (id: number) => request<SavedNaraNotice>(`/api/nara/saved-notices/${id}`),
  getSavedNaraNoticeRequirements: (id: number) =>
    request<NoticeRequirementPayload>(`/api/nara/saved-notices/${id}/requirements`),
  getNoticeRequirement: (id: number) => request<NoticeRequirementDetail>(`/api/notice-requirements/${id}`),
  extractSavedNaraNoticeRequirements: (id: number) =>
    request<NoticeRequirementPayload>(`/api/nara/saved-notices/${id}/requirements/extract`, {
      method: "POST",
    }),
  listNoticeComparisons: () => request<NoticeCorporationComparison[]>("/api/notice-comparisons"),
  listNoticeComparisonsByNotice: (noticeId: number) =>
    request<NoticeCorporationComparison[]>(`/api/nara/saved-notices/${noticeId}/comparisons`),
  createNoticeComparison: (noticeId: number, corporationId: number) =>
    request<NoticeCorporationComparison>("/api/notice-comparisons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nara_notice_id: noticeId, corporation_id: corporationId }),
    }),
  getNoticeComparison: (id: number) => request<NoticeCorporationComparison>(`/api/notice-comparisons/${id}`),
  listJudgmentRuns: () => request<JudgmentRun[]>("/api/judgment-runs"),
  getJudgmentRun: (id: number) => request<JudgmentRun>(`/api/judgment-runs/${id}`),
  createJudgmentRun: (noticeId: number, corporationId: number, topK = 3) =>
    request<JudgmentRun>("/api/judgment-runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nara_notice_id: noticeId, corporation_id: corporationId, top_k: topK }),
    }),
  updateJudgmentRunReview: (id: number, body: Record<string, unknown>) =>
    request<JudgmentRun>(`/api/judgment-runs/${id}/review`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  listNaraCollectionRuns: (params: Record<string, string | undefined> = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    return request<NaraCollectionRun[]>(`/api/nara/collection-runs?${query.toString()}`);
  },
  createNaraCollectionRun: (body: Record<string, unknown>) =>
    request<NaraCollectionRun>("/api/nara/collection-runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  getNaraCollectionRun: (id: number) => request<NaraCollectionRun>(`/api/nara/collection-runs/${id}`),
  reanalyzeSavedNaraNotice: (id: number, selection?: AiModelSelection) =>
    request<{ status: string; notice: SavedNaraNotice }>(`/api/nara/saved-notices/${id}/reanalyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(selection ?? {}),
    }),
  deleteSavedNaraNotice: (id: number) =>
    request<{ status: string }>(`/api/nara/saved-notices/${id}`, {
      method: "DELETE",
    }),
  getNaraAttachmentPreviewUrl: (url: string, name: string) => {
    const query = new URLSearchParams({ url, name });
    return buildApiUrl(`/api/nara/attachments/preview?${query.toString()}`);
  },
};
