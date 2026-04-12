import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { Corporation, Project } from "../app/types";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [search, setSearch] = useState("");
  const [corporationId, setCorporationId] = useState<number | "">("");

  const refresh = () => {
    api.listProjects().then(setProjects).catch(console.error);
    api
      .listCorporations()
      .then((data) => {
        setCorporations(data);
        if (!corporationId && data.length) {
          setCorporationId(data[0].id);
        }
      })
      .catch(console.error);
  };

  useEffect(() => {
    refresh();
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!corporationId) return;
    await api.createProject({ name, corporation_id: corporationId, notes, status: "active" });
    setName("");
    setNotes("");
    refresh();
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
              <p className="eyebrow">Project Setup</p>
              <h3>프로젝트를 먼저 만들어 흐름을 묶기</h3>
              <p className="section-copy">
                업로드 이력은 파일보다 프로젝트 기준으로 보는 것이 훨씬 읽기 쉽습니다. 그래서 생성 폼 자체를 더 안내형으로 바꿨습니다.
              </p>
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
                  <select value={corporationId} onChange={(e) => setCorporationId(Number(e.target.value))} required>
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
          <p className="eyebrow">Project First</p>
          <h3>프로젝트 기준 UX로 바꾼 이유</h3>
          <ul className="feature-list">
            <li>같은 공고 관련 문서를 한 흐름으로 다시 보기 쉽습니다.</li>
            <li>나중에 분석 결과와 근거 문서를 묶어 관리하기 좋습니다.</li>
            <li>Phase 2, 3 확장 시 판단 단위를 유지하기 쉽습니다.</li>
          </ul>
        </aside>
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Project Directory</p>
            <h3>운영 중인 프로젝트</h3>
          </div>
          <input
            className="search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="프로젝트명, 법인명, 상태 검색"
          />
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
                    <p className="eyebrow eyebrow--soft">PROJECT #{item.id}</p>
                    <h4>{item.name}</h4>
                  </div>
                  <span className="status-badge status-badge--active">{item.status}</span>
                </div>
                <p className="project-meta">연결 법인: {corporationMap[item.corporation_id]?.name ?? `#${item.corporation_id}`}</p>
                <p className="project-copy">{item.notes || "아직 프로젝트 메모가 없습니다."}</p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
