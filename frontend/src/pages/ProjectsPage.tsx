import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { Corporation, Project } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

export function ProjectsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [projects, setProjects] = useState<Project[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [search, setSearch] = useState("");
  const [corporationId, setCorporationId] = useState<number | "">("");
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    corporation_id: 0,
    status: "active",
    notes: "",
  });

  const refresh = () => {
    api
      .listProjects()
      .then((data) => {
        setProjects(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "프로젝트 목록을 불러오지 못했습니다."));
    api
      .listCorporations()
      .then((data) => {
        setCorporations(data);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "법인 목록을 불러오지 못했습니다."));
  };

  useEffect(() => {
    refresh();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!corporationId) return;
    try {
      await runWithOverlay(
        {
          title: "프로젝트 생성 중",
          steps: ["입력값 확인", "프로젝트 저장", "프로젝트 목록 갱신"],
          successMessage: "프로젝트를 생성했습니다.",
          failureMessage: "프로젝트 생성을 완료하지 못했습니다.",
        },
        async () => {
          await api.createProject({ name, corporation_id: corporationId, notes, status: "active" });
          setName("");
          setNotes("");
          setError("");
          refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로젝트 생성에 실패했습니다.");
    }
  };

  const onDelete = async (item: Project) => {
    if (!window.confirm(`${item.name} 프로젝트를 삭제할까요? 연결 문서와 분석 결과도 함께 삭제됩니다.`)) return;
    try {
      await runWithOverlay(
        {
          title: "프로젝트 삭제 중",
          steps: ["삭제 요청 전송", "연결 이력 정리", "프로젝트 목록 갱신"],
          successMessage: "프로젝트를 삭제했습니다.",
          failureMessage: "프로젝트 삭제를 완료하지 못했습니다.",
        },
        async () => {
          await api.deleteProject(item.id);
          refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로젝트 삭제에 실패했습니다.");
    }
  };

  const startEdit = (item: Project) => {
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      corporation_id: item.corporation_id,
      status: item.status,
      notes: item.notes,
    });
  };

  const onUpdate = async (e: FormEvent) => {
    e.preventDefault();
    if (!editingId) return;

    try {
      await runWithOverlay(
        {
          title: "프로젝트 수정 중",
          steps: ["수정 내용 확인", "프로젝트 저장", "프로젝트 목록 갱신"],
          successMessage: "프로젝트 정보를 저장했습니다.",
          failureMessage: "프로젝트 수정을 완료하지 못했습니다.",
        },
        async () => {
          await api.updateProject(editingId, editForm);
          setEditingId(null);
          setError("");
          refresh();
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로젝트 수정에 실패했습니다.");
    }
  };

  const corporationMap = corporations.reduce<Record<number, Corporation>>((acc, item) => {
    acc[item.id] = item;
    return acc;
  }, {});

  const filtered = projects.filter((item) => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return true;
    const corpName = corporationMap[item.corporation_id]?.name ?? "";
    return [item.name, corpName, item.status].some((value) => value.toLowerCase().includes(keyword));
  });

  return (
    <section className="content-stack">
      <div className="two-column-grid two-column-grid--wide-left">
        <form className="surface-card form-card" onSubmit={onSubmit}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">프로젝트 등록</p>
              <h3>프로젝트 생성</h3>
              <p className="section-copy">공고 대응 업무를 프로젝트 단위로 등록하고 연결 법인을 지정합니다.</p>
            </div>
          </div>

          {corporations.length === 0 ? (
            <div className="empty-state">
              <strong>먼저 법인을 등록해야 프로젝트를 만들 수 있습니다.</strong>
              <p>법인 정보가 있어야 프로젝트와 문서가 같은 맥락으로 연결됩니다.</p>
              <Link to="/corporations" className="link-button">
                법인 관리로 이동
              </Link>
            </div>
          ) : (
            <>
              <div className="form-grid">
                <label className="field">
                  <span>프로젝트명</span>
                  <input value={name} onChange={(e) => setName(e.target.value)} placeholder="예: 2026 서울시 공공SW 용역 대응" required />
                </label>

                <label className="field">
                  <span>연결 법인</span>
                  <select value={corporationId} onChange={(e) => setCorporationId(e.target.value ? Number(e.target.value) : "")} required>
                    <option value="">법인을 선택하세요</option>
                    {corporations.map((corp) => (
                      <option key={corp.id} value={corp.id}>
                        {corp.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field field--full">
                  <span>프로젝트 메모</span>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="현재 검토 목적이나 대응 전략 메모를 간단히 적어둘 수 있습니다."
                    rows={4}
                  />
                </label>
              </div>

              <div className="form-actions">
                <button type="submit">프로젝트 생성</button>
              </div>
            </>
          )}
        </form>

        <aside className="surface-card accent-card accent-card--leaf">
          <p className="eyebrow">관리 항목</p>
          <h3>프로젝트에 연결되는 정보</h3>
          <ul className="feature-list">
            <li>연결 법인</li>
            <li>업로드 문서와 분석 이력</li>
            <li>업무 메모와 진행 상태</li>
          </ul>
        </aside>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="surface-card project-list-panel">
        <div className="section-heading project-list-heading">
          <div>
            <p className="eyebrow">프로젝트 목록</p>
            <h3>운영 중인 프로젝트</h3>
          </div>
          <label className="project-search-field">
            <input
              className="search-input"
              aria-label="프로젝트 검색"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="프로젝트명, 법인명, 상태 검색"
            />
          </label>
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state">
            <strong>아직 프로젝트가 없습니다.</strong>
            <p>프로젝트를 생성하면 문서 이력과 분석 결과가 하나의 업무 단위로 정리됩니다.</p>
          </div>
        ) : (
          <div className="project-grid">
            {filtered.map((item) => (
              <article key={item.id} className="project-card">
                <div className="project-card__top">
                  <div>
                    <p className="eyebrow eyebrow--soft">프로젝트 #{item.id}</p>
                    <h4>{item.name}</h4>
                  </div>
                  <span className="status-badge status-badge--active">{item.status}</span>
                </div>
                <p className="project-meta">연결 법인: {corporationMap[item.corporation_id]?.name ?? `#${item.corporation_id}`}</p>
                <p className="project-copy">{item.notes || "아직 프로젝트 메모가 없습니다."}</p>
                <div className="project-card-actions">
                  <button type="button" className="button-secondary" onClick={() => startEdit(item)}>
                    편집
                  </button>
                  <button type="button" className="button-danger" onClick={() => onDelete(item)}>
                    프로젝트 삭제
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {editingId ? (
        <form className="surface-card form-card inline-editor" onSubmit={onUpdate}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">프로젝트 편집</p>
              <h3>프로젝트 정보 편집</h3>
              <p className="section-copy">프로젝트명, 연결 법인, 상태, 메모를 수정합니다.</p>
            </div>
            <button type="button" className="button-secondary" onClick={() => setEditingId(null)}>
              취소
            </button>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>프로젝트명</span>
              <input
                value={editForm.name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                required
              />
            </label>

            <label className="field">
              <span>연결 법인</span>
              <select
                value={editForm.corporation_id}
                onChange={(e) => setEditForm((prev) => ({ ...prev, corporation_id: Number(e.target.value) }))}
                required
              >
                <option value="">법인을 선택하세요</option>
                {corporations.map((corp) => (
                  <option key={corp.id} value={corp.id}>
                    {corp.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>상태</span>
              <select
                value={editForm.status}
                onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))}
              >
                <option value="">상태를 선택하세요</option>
                <option value="active">active</option>
                <option value="paused">paused</option>
                <option value="archived">archived</option>
              </select>
            </label>

            <label className="field field--full">
              <span>프로젝트 메모</span>
              <textarea
                value={editForm.notes}
                onChange={(e) => setEditForm((prev) => ({ ...prev, notes: e.target.value }))}
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
