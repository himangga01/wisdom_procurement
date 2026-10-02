import { FormEvent, useEffect, useState } from "react";

import { api } from "../app/api";
import type { BasisDocumentRecord } from "../app/types";

const DEFAULT_CATEGORY = "direct_production_certificate";
const DEFAULT_PATH =
  "H:/다른 컴퓨터/내 노트북/구글/행정사/인증/직접생산확인증명/전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf";

function statusTone(status: string) {
  if (status === "completed" || status === "cached") return "active";
  if (status === "pending") return "pending";
  return "muted";
}

export function BasisDocumentsPage() {
  const [documents, setDocuments] = useState<BasisDocumentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "직접생산확인증명 기준문서",
    category: DEFAULT_CATEGORY,
    file_path: DEFAULT_PATH,
    memo: "직접생산확인증명 기준 검토용",
  });

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.listBasisDocuments();
      setDocuments(data);
      setError("");
    } catch (err) {
      const nextError =
        err instanceof Error ? err.message : "기준문서 목록을 불러오지 못했습니다.";
      setError(nextError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage("");
    setError("");

    try {
      const created = await api.importBasisDocumentFromLocal(form);
      await api.analyzeBasisDocument(created.id);
      setMessage("기준문서를 등록하고 분석까지 완료했습니다.");
      await refresh();
    } catch (err) {
      const nextError =
        err instanceof Error ? err.message : "기준문서 등록 또는 분석에 실패했습니다.";
      setError(nextError);
    } finally {
      setSubmitting(false);
    }
  };

  const onReanalyze = async (id: number) => {
    setMessage("");
    setError("");

    try {
      await api.reanalyzeBasisDocument(id);
      setMessage("기준문서를 다시 분석했습니다.");
      await refresh();
    } catch (err) {
      const nextError =
        err instanceof Error ? err.message : "기준문서 재분석에 실패했습니다.";
      setError(nextError);
    }
  };

  return (
    <section className="content-stack">
      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Basis Ingestion</p>
              <h3>기준문서 로컬 등록</h3>
              <p className="section-copy">
                공고 문서와 분리된 기준문서를 별도로 관리합니다. 현재는 로컬 PC
                운영 전제에 맞춰 PDF 경로를 직접 입력해서 등록할 수 있습니다.
              </p>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>기준문서 제목</span>
              <input
                value={form.title}
                onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="예: 직접생산확인증명 기준문서"
                required
              />
            </label>

            <label className="field">
              <span>카테고리</span>
              <input
                value={form.category}
                onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
                placeholder="예: direct_production_certificate"
                required
              />
            </label>

            <label className="field field--full">
              <span>로컬 PDF 경로</span>
              <input
                value={form.file_path}
                onChange={(e) => setForm((prev) => ({ ...prev, file_path: e.target.value }))}
                placeholder="H:/.../기준문서.pdf"
                required
              />
            </label>

            <label className="field field--full">
              <span>메모</span>
              <input
                value={form.memo}
                onChange={(e) => setForm((prev) => ({ ...prev, memo: e.target.value }))}
                placeholder="기준문서 용도나 비고를 적어둘 수 있습니다."
              />
            </label>
          </div>

          <div className="form-actions">
            <button type="submit" disabled={submitting}>
              {submitting ? "등록 및 분석 중..." : "기준문서 등록 후 분석"}
            </button>
          </div>
        </form>

        <aside className="surface-card accent-card accent-card--leaf">
          <p className="eyebrow">Why Basis Docs</p>
          <h3>기준문서를 따로 분석하는 이유</h3>
          <ul className="feature-list">
            <li>공고가 요구하는 자격요건과 기준문서 요건을 한 화면에서 비교할 수 있습니다.</li>
            <li>직접생산확인증명 같은 반복 기준은 한 번 정리해두면 여러 프로젝트에서 재사용할 수 있습니다.</li>
            <li>일반 업로드 문서와 분리해 두면 향후 RAG 확장에도 구조를 그대로 이어갈 수 있습니다.</li>
          </ul>
        </aside>
      </div>

      {message ? (
        <div className="surface-card accent-card">
          <strong>{message}</strong>
        </div>
      ) : null}

      {error ? (
        <div className="empty-state">
          <strong>기준문서 처리 중 문제가 있었습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Basis Library</p>
            <h3>등록된 기준문서</h3>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            <strong>기준문서 목록을 불러오는 중입니다.</strong>
            <p>잠시만 기다리면 분석 상태와 파일 정보를 확인할 수 있습니다.</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <strong>아직 등록된 기준문서가 없습니다.</strong>
            <p>위 입력 폼에서 직접생산확인증명 기준 PDF를 등록해 주세요.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>제목</th>
                  <th>카테고리</th>
                  <th>파일명</th>
                  <th>분석 상태</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.title}</strong>
                      <div className="table-subcopy">{item.memo || "메모 없음"}</div>
                    </td>
                    <td>{item.category}</td>
                    <td>{item.original_file_name}</td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(item.analysis_status)}`}>
                        {item.analysis_status}
                      </span>
                    </td>
                    <td>
                      <button type="button" onClick={() => void onReanalyze(item.id)}>
                        재분석
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
