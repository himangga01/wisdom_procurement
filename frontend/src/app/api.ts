import type {
  AiModelSelection,
  AiModelSettings,
  AnalysisRecord,
  Corporation,
  CorporationEvidenceApplyResult,
  CorporationEvidenceDocument,
  CorporationReadiness,
  DashboardSummary,
  DocumentRecord,
  NaraNoticeSearchItem,
  NaraNoticeSearchResponse,
  NoticeCorporationComparison,
  NoticeRequirementPayload,
  NaraIntegrationStatus,
  NaraIntegrationTestResult,
  Project,
  SavedNaraNotice,
  CorporationComparisonProfile,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:18000";

function buildApiUrl(path: string) {
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
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
  getAiModelSettings: () => request<AiModelSettings>("/api/settings/ai-models"),
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
