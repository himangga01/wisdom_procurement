import type {
  AnalysisRecord,
  Corporation,
  DashboardSummary,
  DocumentRecord,
  Project,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:18000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    throw new Error(payload.detail || "Request failed");
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
  listProjects: () => request<Project[]>("/api/projects"),
  createProject: (body: Record<string, unknown>) =>
    request<Project>("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  listDocuments: () => request<DocumentRecord[]>("/api/documents"),
  uploadDocument: (formData: FormData) =>
    request<DocumentRecord>("/api/documents", {
      method: "POST",
      body: formData,
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
};
