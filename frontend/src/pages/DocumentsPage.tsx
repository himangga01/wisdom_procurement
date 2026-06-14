import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import {
  defaultSelection,
  loadStoredSelection,
  optionsFromSettings,
  keyToSelection,
  saveStoredSelection,
  selectionToKey,
} from "../app/aiModel";
import type { AiModelSelection, AiModelSettings, Corporation, DocumentRecord, Project } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "completed" || status === "cached") return "active";
  if (status === "pending") return "pending";
  return "muted";
}

export function DocumentsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [aiSettings, setAiSettings] = useState<AiModelSettings | null>(null);
  const [aiSelection, setAiSelection] = useState<AiModelSelection>(defaultSelection());
  const [loading, setLoading] = useState(true);

  const [projectId, setProjectId] = useState<number | "">("");
  const [documentType, setDocumentType] = useState("");
  const [memo, setMemo] = useState("");
  const [revisionNote, setRevisionNote] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({
    document_type: "general",
    memo: "",
    revision_note: "",
  });

  const refresh = async () => {
    setLoading(true);
    try {
      const [documentList, projectList, corporationList] = await Promise.all([
        api.listDocuments(),
        api.listProjects(),
        api.listCorporations(),
      ]);
      setDocuments(documentList);
      setProjects(projectList);
      setCorporations(corporationList);

    } catch (error) {
      setError(error instanceof Error ? error.message : "문서 이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    api
      .getAiModelSettings()
      .then((settings) => {
        setAiSettings(settings);
        setAiSelection(loadStoredSelection(settings));
      })
      .catch(() => {
        setAiSelection(loadStoredSelection(null));
      });
  }, []);

  const onAiModelChange = (value: string) => {
    const next = keyToSelection(value);
    setAiSelection(next);
    saveStoredSelection(next);
  };

  const onUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !projectId || !documentType) return;

    const formData = new FormData();
    formData.append("project_id", String(projectId));
    formData.append("document_type", documentType);
    formData.append("memo", memo);
    formData.append("revision_note", revisionNote);
    formData.append("file", file);

    try {
      await runWithOverlay(
        {
          title: "문서 업로드 처리 중",
          description: "파일과 메타데이터를 저장하고 문서 이력을 새로 고칩니다.",
          steps: ["파일 업로드", "문서 메타데이터 저장", "업로드 이력 갱신"],
          successMessage: "문서 업로드가 완료되었습니다.",
          failureMessage: "문서 업로드를 완료하지 못했습니다.",
        },
        async () => {
          await api.uploadDocument(formData);
          setMemo("");
          setRevisionNote("");
          setDocumentType("");
          setFile(null);
          setError("");
          await refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "문서 업로드에 실패했습니다.");
    }
  };

  const onAnalyze = async (id: number) => {
    try {
      await runWithOverlay(
        {
          title: "문서 분석 중",
          description: "PDF/DOCX 텍스트 추출, OCR 확인, AI 요약을 순서대로 처리합니다.",
          steps: ["문서 텍스트 추출", "OCR 필요 여부 확인", "AI 요약 생성", "분석 결과 저장"],
          successMessage: "문서 분석이 완료되었습니다.",
          failureMessage: "문서 분석을 완료하지 못했습니다.",
          minVisibleMs: 650,
        },
        async () => {
          await api.analyzeDocument(id, aiSelection);
          setError("");
          await refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "문서 분석에 실패했습니다.");
    }
  };

  const onDelete = async (item: DocumentRecord) => {
    if (!window.confirm(`${item.original_file_name} 문서를 삭제할까요? 분석 결과도 함께 삭제됩니다.`)) return;
    try {
      await runWithOverlay(
        {
          title: "문서 삭제 중",
          steps: ["삭제 요청 전송", "연결된 분석 결과 정리", "문서 이력 갱신"],
          successMessage: "문서를 삭제했습니다.",
          failureMessage: "문서 삭제를 완료하지 못했습니다.",
        },
        async () => {
          await api.deleteDocument(item.id);
          setError("");
          await refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "문서 삭제에 실패했습니다.");
    }
  };

  const startEdit = (item: DocumentRecord) => {
    setEditingId(item.id);
    setEditForm({
      document_type: item.document_type,
      memo: item.memo,
      revision_note: item.revision_note,
    });
  };

  const onUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingId) return;

    try {
      await runWithOverlay(
        {
          title: "문서 메타데이터 저장 중",
          steps: ["수정 내용 검증", "메타데이터 저장", "문서 이력 갱신"],
          successMessage: "문서 메타데이터를 저장했습니다.",
          failureMessage: "문서 메타데이터 저장을 완료하지 못했습니다.",
        },
        async () => {
          await api.updateDocument(editingId, editForm);
          setEditingId(null);
          setError("");
          await refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "문서 메타데이터 수정에 실패했습니다.");
    }
  };

  const projectMap = projects.reduce<Record<number, Project>>((acc, item) => {
    acc[item.id] = item;
    return acc;
  }, {});

  const corporationMap = corporations.reduce<Record<number, Corporation>>((acc, item) => {
    acc[item.id] = item;
    return acc;
  }, {});

  const filtered = documents.filter((item) => {
    const keyword = search.trim().toLowerCase();
    const projectName = projectMap[item.project_id]?.name ?? "";
    const corporationName = corporationMap[projectMap[item.project_id]?.corporation_id ?? 0]?.name ?? "";
    const matchesKeyword =
      !keyword ||
      [item.original_file_name, projectName, corporationName, item.document_type].some((value) =>
        value.toLowerCase().includes(keyword),
      );
    const matchesStatus = !statusFilter || item.analysis_status === statusFilter;
    return matchesKeyword && matchesStatus;
  });

  const selectedProject = typeof projectId === "number" ? projectMap[projectId] : null;
  const selectedCorporation = selectedProject
    ? corporationMap[selectedProject.corporation_id]
    : null;
  const aiOptions = optionsFromSettings(aiSettings);

  return (
    <section className="content-stack">
      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onUpload}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">문서 업로드</p>
              <h3>문서 파일 등록</h3>
              <p className="section-copy">프로젝트, 문서 유형, 메모를 지정하고 PDF/DOCX 파일을 업로드합니다.</p>
            </div>
          </div>

          {projects.length === 0 ? (
            <div className="empty-state">
              <strong>먼저 프로젝트를 만들어야 문서를 업로드할 수 있습니다.</strong>
              <p>프로젝트를 만든 뒤 문서를 업로드해 주세요.</p>
              <Link to="/projects" className="link-button">
                프로젝트 관리로 이동
              </Link>
            </div>
          ) : (
            <>
              <div className="form-grid">
                <label className="field">
                  <span>프로젝트 선택</span>
                  <select value={projectId} onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : "")} required>
                    <option value="">프로젝트를 선택하세요</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>문서 유형</span>
                  <select value={documentType} onChange={(e) => setDocumentType(e.target.value)} required>
                    <option value="">문서 유형을 선택하세요</option>
                    <option value="notice">공고문</option>
                    <option value="spec">제안요청/규격</option>
                    <option value="general">일반 문서</option>
                  </select>
                </label>

                <label className="field field--full">
                  <span>파일 업로드</span>
                  <input type="file" accept=".pdf,.docx" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
                </label>

                <label className="field">
                  <span>업로드 메모</span>
                  <input value={memo} onChange={(e) => setMemo(e.target.value)} placeholder="예: 본문 요건 먼저 확인 필요" />
                </label>

                <label className="field">
                  <span>개정 메모</span>
                  <input value={revisionNote} onChange={(e) => setRevisionNote(e.target.value)} placeholder="예: 2차 수정본" />
                </label>
              </div>

              <div className="upload-hint">
                <strong>현재 선택된 문맥</strong>
                <p>
                  프로젝트: {selectedProject?.name ?? "-"} / 법인: {selectedCorporation?.name ?? "-"}
                </p>
                <span>지원 포맷은 PDF, DOCX만 허용됩니다.</span>
              </div>

              <div className="form-actions">
                <button type="submit" disabled={!projectId || !documentType || !file}>문서 업로드</button>
              </div>
            </>
          )}
        </form>

        <aside className="surface-card accent-card accent-card--petal">
          <p className="eyebrow">등록 정보</p>
          <h3>문서에 저장되는 항목</h3>
          <ul className="feature-list">
            <li>프로젝트와 연결 법인</li>
            <li>문서 유형과 업로드 메모</li>
            <li>분석 상태와 처리 이력</li>
          </ul>
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
            <p className="eyebrow">문서 이력</p>
            <h3>프로젝트 기준 문서 이력</h3>
          </div>
          <div className="toolbar">
            <input
              className="search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="파일명, 프로젝트명, 법인명 검색"
            />
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">상태를 선택하세요</option>
              <option value="pending">pending</option>
              <option value="completed">completed</option>
              <option value="cached">cached</option>
            </select>
            <select
              className="ai-model-select"
              value={selectionToKey(aiSelection)}
              onChange={(e) => onAiModelChange(e.target.value)}
              title="분석 실행에 사용할 AI 모델"
            >
              {aiOptions.map((option) => (
                <option key={`${option.provider}:${option.model}`} value={`${option.provider}:${option.model}`}>
                  {option.label}
                  {option.recommended ? " 추천" : ""}
                  {option.configured ? "" : " · 키 미설정"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            <strong>문서 이력을 불러오는 중입니다.</strong>
            <p>잠시만 기다리면 프로젝트 기준 이력이 정리되어 표시됩니다.</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <strong>조건에 맞는 문서가 없습니다.</strong>
            <p>검색어를 지우거나 첫 문서를 업로드해보세요.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>파일명</th>
                  <th>프로젝트</th>
                  <th>법인</th>
                  <th>문서 유형</th>
                  <th>분석 상태</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => {
                  const project = projectMap[d.project_id];
                  const corporation = corporationMap[project?.corporation_id ?? 0];
                  return (
                    <tr key={d.id}>
                      <td>
                        <strong>{d.original_file_name}</strong>
                        <div className="table-subcopy">{d.memo || "메모 없음"}</div>
                      </td>
                      <td>{project?.name ?? `#${d.project_id}`}</td>
                      <td>{corporation?.name ?? "-"}</td>
                      <td>{d.document_type}</td>
                      <td>
                        <span className={`status-badge status-badge--${statusTone(d.analysis_status)}`}>
                          {d.analysis_status}
                        </span>
                      </td>
                      <td>
                        <div className="row">
                          <button type="button" onClick={() => onAnalyze(d.id)}>
                            분석
                          </button>
                          <button type="button" className="button-secondary" onClick={() => startEdit(d)}>
                            편집
                          </button>
                          <Link to={`/documents/${d.id}/analysis`} className="link-button link-button--soft">
                            결과
                          </Link>
                          <button type="button" className="button-danger" onClick={() => onDelete(d)}>
                            삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editingId ? (
        <form className="surface-card form-card inline-editor" onSubmit={onUpdate}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">문서 정보 편집</p>
              <h3>문서 메타데이터 편집</h3>
              <p className="section-copy">원본 파일은 유지하고 문서 유형, 메모, 개정 메모만 수정합니다.</p>
            </div>
            <button type="button" className="button-secondary" onClick={() => setEditingId(null)}>
              취소
            </button>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>문서 유형</span>
              <select
                value={editForm.document_type}
                onChange={(e) => setEditForm((prev) => ({ ...prev, document_type: e.target.value }))}
              >
                <option value="notice">공고문</option>
                <option value="spec">제안요청/규격</option>
                <option value="general">일반 문서</option>
              </select>
            </label>

            <label className="field">
              <span>개정 메모</span>
              <input
                value={editForm.revision_note}
                onChange={(e) => setEditForm((prev) => ({ ...prev, revision_note: e.target.value }))}
              />
            </label>

            <label className="field field--full">
              <span>업로드 메모</span>
              <textarea
                value={editForm.memo}
                onChange={(e) => setEditForm((prev) => ({ ...prev, memo: e.target.value }))}
                rows={4}
              />
            </label>
          </div>

          <div className="form-actions">
            <button type="submit">수정 저장</button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
