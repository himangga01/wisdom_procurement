import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { Corporation, DocumentRecord, Project } from "../app/types";

function statusTone(status: string) {
  if (status === "completed" || status === "cached") return "active";
  if (status === "pending") return "pending";
  return "muted";
}

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [loading, setLoading] = useState(true);

  const [projectId, setProjectId] = useState<number | "">("");
  const [documentType, setDocumentType] = useState("general");
  const [memo, setMemo] = useState("");
  const [revisionNote, setRevisionNote] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

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

      if (!projectId && projectList.length) {
        setProjectId(projectList[0].id);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !projectId) return;

    const formData = new FormData();
    formData.append("project_id", String(projectId));
    formData.append("document_type", documentType);
    formData.append("memo", memo);
    formData.append("revision_note", revisionNote);
    formData.append("file", file);

    await api.uploadDocument(formData);
    setMemo("");
    setRevisionNote("");
    setFile(null);
    refresh();
  };

  const onAnalyze = async (id: number) => {
    await api.analyzeDocument(id);
    refresh();
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
    const matchesStatus = statusFilter === "all" || item.analysis_status === statusFilter;
    return matchesKeyword && matchesStatus;
  });

  const selectedProject = typeof projectId === "number" ? projectMap[projectId] : null;
  const selectedCorporation = selectedProject
    ? corporationMap[selectedProject.corporation_id]
    : null;

  return (
    <section className="content-stack">
      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onUpload}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Upload Flow</p>
              <h3>메타데이터와 함께 문서 업로드</h3>
              <p className="section-copy">
                업로드 자체보다 어떤 프로젝트 맥락에 올리는지가 중요해서, 프로젝트와 문서 유형을 먼저 선택하도록 UX를 정리했습니다.
              </p>
            </div>
          </div>

          {projects.length === 0 ? (
            <div className="empty-state">
              <strong>먼저 프로젝트를 만들어야 문서를 업로드할 수 있습니다.</strong>
              <p>프로젝트 없이 올린 파일은 나중에 다시 봤을 때 업무 맥락이 흐려집니다.</p>
              <Link to="/projects" className="link-button">
                프로젝트 관리로 이동
              </Link>
            </div>
          ) : (
            <>
              <div className="form-grid">
                <label className="field">
                  <span>프로젝트 선택</span>
                  <select value={projectId} onChange={(e) => setProjectId(Number(e.target.value))} required>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>문서 유형</span>
                  <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
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
                <button type="submit">문서 업로드</button>
              </div>
            </>
          )}
        </form>

        <aside className="surface-card accent-card accent-card--petal">
          <p className="eyebrow">Usability Upgrade</p>
          <h3>업로드 화면에서 바꾼 점</h3>
          <ul className="feature-list">
            <li>프로젝트와 법인 문맥을 바로 보이게 노출</li>
            <li>문서 유형, 메모, 개정 메모를 한 흐름으로 정리</li>
            <li>문서 이력을 검색/필터로 다시 찾기 쉽게 개선</li>
          </ul>
        </aside>
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">History</p>
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
              <option value="all">모든 상태</option>
              <option value="pending">pending</option>
              <option value="completed">completed</option>
              <option value="cached">cached</option>
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
                          <Link to={`/documents/${d.id}/analysis`} className="link-button link-button--soft">
                            결과
                          </Link>
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
    </section>
  );
}
