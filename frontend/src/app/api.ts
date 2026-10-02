import type {
  AnalysisRecord,
  BasisAnalysisRecord,
  BasisDocumentBundle,
  BasisDocumentRecord,
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
  listBasisDocuments: () => request<BasisDocumentRecord[]>("/api/basis-documents"),
  importBasisDocumentFromLocal: (body: Record<string, unknown>) =>
    request<BasisDocumentRecord>("/api/basis-documents/import-local", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  analyzeBasisDocument: (basisDocumentId: number) =>
    request<{ analysis_id: number; status: string; message: string }>(
      `/api/basis-documents/${basisDocumentId}/analyze`,
      {
        method: "POST",
      },
    ),
  reanalyzeBasisDocument: (basisDocumentId: number) =>
    request<{ analysis_id: number; status: string; message: string }>(
      `/api/basis-documents/${basisDocumentId}/reanalyze`,
      {
        method: "POST",
      },
    ),
  getLatestBasisAnalysis: (basisDocumentId: number) =>
    request<BasisAnalysisRecord>(`/api/basis-documents/${basisDocumentId}/analysis/latest`),
  getLatestBasisByCategory: (category: string) =>
    request<BasisDocumentBundle>(`/api/basis-documents/latest/by-category/${category}`),
};
