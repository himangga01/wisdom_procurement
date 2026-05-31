import { FormEvent, useEffect, useMemo, useState } from "react";

import { api } from "../app/api";
import type { BasisDocument, BasisSearchResponse } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "completed" || status === "indexed") return "active";
  if (["pending", "parsing", "processing", "empty", "needs_ocr_setup", "skipped"].includes(status)) return "pending";
  return "muted";
}

function formatBytes(value: number) {
  if (!value) return "0 KB";
  if (value < 1024 * 1024) return `${Math.ceil(value / 1024)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

const emptyEditForm = {
  title: "",
  category: "",
  document_version: "",
  issuing_agency: "",
  effective_date: "",
  source_url: "",
  memo: "",
};

export function BasisDocumentsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [documents, setDocuments] = useState<BasisDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<BasisDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [documentVersion, setDocumentVersion] = useState("");
  const [issuingAgency, setIssuingAgency] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [memo, setMemo] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [keyword, setKeyword] = useState("");
  const [editForm, setEditForm] = useState(emptyEditForm);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchCategory, setSearchCategory] = useState("");
  const [searchResult, setSearchResult] = useState<BasisSearchResponse | null>(null);

  const loadDetail = async (id: number) => {
    const detail = await api.getBasisDocument(id);
    setSelectedDoc(detail);
    setEditForm({
      title: detail.title,
      category: detail.category,
      document_version: detail.document_version,
      issuing_agency: detail.issuing_agency,
      effective_date: detail.effective_date,
      source_url: detail.source_url,
      memo: detail.memo,
    });
  };

  const refresh = async (nextSelectedId?: number | null, nextKeyword = keyword) => {
    setLoading(true);
    try {
      const data = await api.listBasisDocuments({ keyword: nextKeyword });
      setDocuments(data);
      setError("");
      const targetId = nextSelectedId === null ? data[0]?.id : nextSelectedId ?? selectedDoc?.id ?? data[0]?.id;
      if (targetId) {
        const target = data.find((item) => item.id === targetId);
        await loadDetail(target?.id ?? targetId);
      } else {
        setSelectedDoc(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const categories = useMemo(() => {
    return Array.from(new Set(documents.map((item) => item.category).filter(Boolean))).sort();
  }, [documents]);

  const onUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append("title", title);
    formData.append("category", category);
    formData.append("document_version", documentVersion);
    formData.append("issuing_agency", issuingAgency);
    formData.append("effective_date", effectiveDate);
    formData.append("source_url", sourceUrl);
    formData.append("memo", memo);
    formData.append("file", file);

    try {
      await runWithOverlay(
        {
          title: "기준문서 처리 중",
          description: "PDF 저장, 텍스트 추출, 청킹, 로컬 인덱싱을 순서대로 실행합니다.",
          steps: ["파일 저장", "텍스트 추출", "청크 생성", "검색 인덱스 갱신"],
          successMessage: "기준문서를 저장했습니다.",
          failureMessage: "기준문서 저장을 완료하지 못했습니다.",
          minVisibleMs: 700,
        },
        async () => {
          const created = await api.uploadBasisDocument(formData);
          setTitle("");
          setCategory("");
          setDocumentVersion("");
          setIssuingAgency("");
          setEffectiveDate("");
          setSourceUrl("");
          setMemo("");
          setFile(null);
          setKeyword("");
          await refresh(created.id, "");
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 업로드에 실패했습니다.");
    }
  };

  const onSelect = async (item: BasisDocument) => {
    try {
      await loadDetail(item.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 상세를 불러오지 못했습니다.");
    }
  };

  const onUpdate = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedDoc) return;
    try {
      await runWithOverlay(
        {
          title: "기준문서 메타데이터 저장 중",
          steps: ["입력값 확인", "메타데이터 저장", "상세 갱신"],
          successMessage: "기준문서 메타데이터를 저장했습니다.",
          failureMessage: "기준문서 메타데이터 저장을 완료하지 못했습니다.",
        },
        async () => {
          const updated = await api.updateBasisDocument(selectedDoc.id, editForm);
          setSelectedDoc({ ...selectedDoc, ...updated });
          await refresh(updated.id);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 수정에 실패했습니다.");
    }
  };

  const onReprocess = async () => {
    if (!selectedDoc) return;
    try {
      await runWithOverlay(
        {
          title: "기준문서 재처리 중",
          description: "기존 청크와 검색 인덱스를 교체합니다.",
          steps: ["이전 청크 정리", "텍스트 재추출", "청크 재생성", "인덱스 재생성"],
          successMessage: "기준문서 재처리가 완료되었습니다.",
          failureMessage: "기준문서 재처리를 완료하지 못했습니다.",
          minVisibleMs: 700,
        },
        async () => {
          const updated = await api.reprocessBasisDocument(selectedDoc.id);
          await refresh(updated.id);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 재처리에 실패했습니다.");
    }
  };

  const onDelete = async (item: BasisDocument) => {
    if (!window.confirm(`${item.title} 기준문서를 삭제할까요? 생성된 청크와 인덱스도 함께 정리됩니다.`)) return;
    try {
      await runWithOverlay(
        {
          title: "기준문서 삭제 중",
          steps: ["삭제 요청 전송", "청크/인덱스 정리", "목록 갱신"],
          successMessage: "기준문서를 삭제했습니다.",
          failureMessage: "기준문서 삭제를 완료하지 못했습니다.",
        },
        async () => {
          await api.deleteBasisDocument(item.id);
          setSelectedDoc(null);
          await refresh(null);
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 삭제에 실패했습니다.");
    }
  };

  const onSearch = async (event: FormEvent) => {
    event.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const data = await api.searchBasisDocuments({
        query: searchQuery,
        category: searchCategory,
        top_k: 5,
      });
      setSearchResult(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "기준문서 검색에 실패했습니다.");
    }
  };

  return (
    <section className="content-stack">
      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onUpload}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Basis Ingestion</p>
              <h3>기준문서 업로드</h3>
              <p className="section-copy">PDF 기준문서를 저장하면 텍스트 추출, 청킹, 로컬 검색 인덱싱까지 자동으로 처리합니다.</p>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>문서명</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="예: 지방계약법 시행령" />
            </label>

            <label className="field">
              <span>카테고리</span>
              <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="예: local_contract" />
            </label>

            <label className="field">
              <span>버전</span>
              <input value={documentVersion} onChange={(e) => setDocumentVersion(e.target.value)} placeholder="예: 2026.05" />
            </label>

            <label className="field">
              <span>발행기관</span>
              <input value={issuingAgency} onChange={(e) => setIssuingAgency(e.target.value)} placeholder="예: 행정안전부" />
            </label>

            <label className="field">
              <span>시행일</span>
              <input value={effectiveDate} onChange={(e) => setEffectiveDate(e.target.value)} placeholder="YYYY-MM-DD" />
            </label>

            <label className="field">
              <span>출처 URL</span>
              <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://..." />
            </label>

            <label className="field field--full">
              <span>PDF 파일</span>
              <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
            </label>

            <label className="field field--full">
              <span>운영 메모</span>
              <textarea value={memo} onChange={(e) => setMemo(e.target.value)} rows={3} />
            </label>
          </div>

          <div className="form-actions">
            <button type="submit">기준문서 업로드</button>
          </div>
        </form>

        <aside className="surface-card accent-card accent-card--leaf">
          <p className="eyebrow">Pipeline Status</p>
          <h3>Phase 2 처리 현황</h3>
          <div className="metric-list">
            <div>
              <span>기준문서</span>
              <strong>{documents.length}</strong>
            </div>
            <div>
              <span>청크</span>
              <strong>{documents.reduce((sum, item) => sum + item.chunk_count, 0)}</strong>
            </div>
            <div>
              <span>검색 벡터</span>
              <strong>{documents.reduce((sum, item) => sum + item.vector_count, 0)}</strong>
            </div>
          </div>
        </aside>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Basis Library</p>
            <h3>기준문서 목록</h3>
          </div>
          <div className="toolbar">
            <input
              className="search-input"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="문서명, 파일명, 메모 검색"
            />
            <button type="button" className="button-secondary" onClick={() => refresh()}>
              검색
            </button>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            <strong>기준문서를 불러오는 중입니다.</strong>
            <p>로컬 기준문서 라이브러리를 확인하고 있습니다.</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <strong>등록된 기준문서가 없습니다.</strong>
            <p>PDF 기준문서를 업로드하면 청크와 검색 후보가 생성됩니다.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>문서</th>
                  <th>상태</th>
                  <th>청크/벡터</th>
                  <th>파일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.title}</strong>
                      <div className="table-subcopy">
                        {item.category || "-"} · {item.document_version || "버전 없음"}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(item.processing_status)}`}>
                        {item.processing_status}
                      </span>
                      {item.error_message ? <div className="table-subcopy">{item.error_message}</div> : null}
                    </td>
                    <td>
                      {item.chunk_count} / {item.vector_count}
                    </td>
                    <td>
                      {item.original_file_name}
                      <div className="table-subcopy">{formatBytes(item.file_size)}</div>
                    </td>
                    <td>
                      <div className="row">
                        <button type="button" className="button-secondary" onClick={() => onSelect(item)}>
                          상세
                        </button>
                        <button type="button" className="button-danger" onClick={() => onDelete(item)}>
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedDoc ? (
        <div className="basis-detail-grid">
          <form className="surface-card form-card" onSubmit={onUpdate}>
            <div className="section-heading">
              <div>
                <p className="eyebrow">Basis Detail</p>
                <h3>{selectedDoc.title}</h3>
                <p className="section-copy">{selectedDoc.original_file_name}</p>
              </div>
              <button type="button" className="button-secondary" onClick={onReprocess}>
                재처리
              </button>
            </div>

            <div className="status-strip">
              <span className={`status-badge status-badge--${statusTone(selectedDoc.parse_status)}`}>
                parse {selectedDoc.parse_status}
              </span>
              <span className={`status-badge status-badge--${statusTone(selectedDoc.ocr_status)}`}>
                ocr {selectedDoc.ocr_status}
              </span>
              <span className={`status-badge status-badge--${statusTone(selectedDoc.chunk_status)}`}>
                chunk {selectedDoc.chunk_status}
              </span>
              <span className={`status-badge status-badge--${statusTone(selectedDoc.index_status)}`}>
                index {selectedDoc.index_status}
              </span>
            </div>

            <div className="form-grid">
              <label className="field">
                <span>문서명</span>
                <input
                  value={editForm.title}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, title: e.target.value }))}
                  required
                />
              </label>
              <label className="field">
                <span>카테고리</span>
                <input
                  value={editForm.category}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, category: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>버전</span>
                <input
                  value={editForm.document_version}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, document_version: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>발행기관</span>
                <input
                  value={editForm.issuing_agency}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, issuing_agency: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>시행일</span>
                <input
                  value={editForm.effective_date}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, effective_date: e.target.value }))}
                />
              </label>
              <label className="field">
                <span>출처 URL</span>
                <input
                  value={editForm.source_url}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, source_url: e.target.value }))}
                />
              </label>
              <label className="field field--full">
                <span>운영 메모</span>
                <textarea value={editForm.memo} onChange={(e) => setEditForm((prev) => ({ ...prev, memo: e.target.value }))} />
              </label>
            </div>

            <div className="form-actions">
              <button type="submit">메타데이터 저장</button>
            </div>

            <div className="basis-preview">
              <strong>텍스트 미리보기</strong>
              <p>{selectedDoc.extracted_text_preview || "추출된 텍스트가 없습니다."}</p>
            </div>
          </form>

          <div className="surface-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Chunks</p>
                <h3>생성된 청크</h3>
              </div>
              <span className="status-badge status-badge--muted">{selectedDoc.chunks?.length ?? 0}개</span>
            </div>

            {!selectedDoc.chunks?.length ? (
              <div className="empty-state">
                <strong>청크가 없습니다.</strong>
                <p>텍스트 추출이 불가능하거나 OCR 설정이 필요한 문서입니다.</p>
              </div>
            ) : (
              <div className="chunk-list">
                {selectedDoc.chunks.map((chunk) => (
                  <article key={chunk.id} className="chunk-row">
                    <div className="chunk-row__meta">
                      <strong>#{chunk.chunk_index + 1}</strong>
                      <span>{chunk.section_title || "섹션 없음"}</span>
                      <small>
                        page {chunk.page_start ?? "-"} · tokens {chunk.token_count}
                      </small>
                    </div>
                    <p>{chunk.chunk_text}</p>
                    <span className={`status-badge status-badge--${statusTone(chunk.vector_status)}`}>
                      {chunk.vector_status}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}

      <form className="surface-card" onSubmit={onSearch}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Basis Search</p>
            <h3>청크 후보 검색</h3>
          </div>
          <div className="toolbar">
            <select value={searchCategory} onChange={(e) => setSearchCategory(e.target.value)}>
              <option value="">전체 카테고리</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <input
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="예: 직접생산확인증명서 제출서류"
            />
            <button type="submit">검색</button>
          </div>
        </div>

        {searchResult ? (
          searchResult.results.length ? (
            <div className="result-list">
              {searchResult.results.map((item) => (
                <article key={item.citation_candidate_id} className="result-row">
                  <div>
                    <strong>{item.document.title}</strong>
                    <span>{item.citation_candidate_id}</span>
                  </div>
                  <p>{item.chunk.chunk_text}</p>
                  <small>
                    score {item.score} · {item.document.category || "uncategorized"} · {item.document.document_version || "no version"}
                  </small>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <strong>검색 결과가 없습니다.</strong>
              <p>다른 키워드나 카테고리로 다시 검색해보세요.</p>
            </div>
          )
        ) : null}
      </form>
    </section>
  );
}
