import type {
  AnalysisRecord,
  Corporation,
  DashboardSummary,
  DocumentRecord,
  NaraNoticeSearchItem,
  NaraNoticeSearchResponse,
  NaraIntegrationStatus,
  NaraIntegrationTestResult,
  Project,
  SavedNaraNotice,
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
  analyzeDocument: (documentId: number) =>
    request<{ analysis_id: number; status: string; message: string }>(`/api/documents/${documentId}/analyze`, {
      method: "POST",
    }),
  reanalyzeDocument: (documentId: number) =>
    request<{ analysis_id: number; status: string; message: string }>(`/api/documents/${documentId}/reanalyze`, {
      method: "POST",
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
  saveAndAnalyzeNaraNotice: (notice: NaraNoticeSearchItem) =>
    request<{ status: string; notice: SavedNaraNotice }>("/api/nara/notices/save-and-analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notice: notice.raw }),
    }),
  listSavedNaraNotices: (keyword = "") => {
    const query = new URLSearchParams();
    if (keyword) query.set("keyword", keyword);
    return request<SavedNaraNotice[]>(`/api/nara/saved-notices?${query.toString()}`);
  },
  getSavedNaraNotice: (id: number) => request<SavedNaraNotice>(`/api/nara/saved-notices/${id}`),
  reanalyzeSavedNaraNotice: (id: number) =>
    request<{ status: string; notice: SavedNaraNotice }>(`/api/nara/saved-notices/${id}/reanalyze`, {
      method: "POST",
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
