import { FormEvent, useEffect, useMemo, useState } from "react";

import { api } from "../app/api";
import type { BasisRetrievalEvaluation } from "../app/types";

function asPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR");
}

function parseEvaluationQueries(raw: string) {
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [queryPart, expectedPart = ""] = line.split("|");
      const query = queryPart.trim();
      const expected = expectedPart
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      return expected.length ? { query, expected_citation_candidate_ids: expected } : query;
    });
}

export function BasisRetrievalEvaluationsPage() {
  const [items, setItems] = useState<BasisRetrievalEvaluation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState("5");
  const [category, setCategory] = useState("");
  const [documentVersion, setDocumentVersion] = useState("");

  const active = useMemo(() => items.find((item) => item.id === activeId) ?? items[0] ?? null, [items, activeId]);
  const metrics = active?.result.metrics ?? {};
  const queryResults = active?.result.query_results ?? [];

  const refresh = async (nextActiveId?: number | null) => {
    setLoading(true);
    try {
      const data = await api.listBasisRetrievalEvaluations();
      setItems(data);
      setActiveId(nextActiveId === null ? data[0]?.id ?? null : nextActiveId ?? activeId ?? data[0]?.id ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "검색 평가 이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onRefresh = (event: FormEvent) => {
    event.preventDefault();
    refresh(activeId);
  };

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    const queries = parseEvaluationQueries(queryText);
    if (!queries.length) {
      setError("평가할 검색 질의를 한 줄 이상 입력하세요.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await api.createBasisRetrievalEvaluation({
        name,
        queries,
        top_k: Number(topK) || 5,
        category,
        document_version: documentVersion,
      });
      setName("");
      setQueryText("");
      setError("");
      await refresh(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "검색 평가를 실행하지 못했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="page-grid">
      <div className="page-title">
        <p className="eyebrow">검색 평가</p>
        <h1>검색 / citation 평가</h1>
        <p>기준문서 검색 결과가 기대 citation을 얼마나 찾는지 확인합니다.</p>
      </div>

      {error ? (
        <div className="notice notice--error">
          <strong>확인 필요</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <form className="surface-card" onSubmit={onCreate}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">평가 실행</p>
            <h3>평가 실행</h3>
          </div>
          <button type="submit" disabled={submitting}>{submitting ? "실행 중" : "평가 실행"}</button>
        </div>

        <div className="form-grid">
          <label>
            <span>평가명</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="예: 면허/제출서류 기준 검색" />
          </label>
          <label>
            <span>Top K</span>
            <input value={topK} onChange={(event) => setTopK(event.target.value)} inputMode="numeric" />
          </label>
          <label>
            <span>카테고리</span>
            <input value={category} onChange={(event) => setCategory(event.target.value)} placeholder="선택 필터" />
          </label>
          <label>
            <span>문서 버전</span>
            <input value={documentVersion} onChange={(event) => setDocumentVersion(event.target.value)} placeholder="선택 필터" />
          </label>
        </div>

        <label className="stacked-field">
          <span>검색 질의</span>
          <textarea
            value={queryText}
            onChange={(event) => setQueryText(event.target.value)}
            rows={5}
            placeholder={"small business certificate\nlicense requirement | basis:1:chunk:2, basis:1:chunk:3"}
          />
        </label>
      </form>

      <form className="surface-card" onSubmit={onRefresh}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">평가 이력</p>
            <h3>평가 이력</h3>
          </div>
          <button type="submit">새로고침</button>
        </div>

        {!items.length ? (
          <div className="empty-state">
            <strong>{loading ? "불러오는 중입니다." : "평가 이력이 없습니다."}</strong>
            <p>백엔드 평가 API로 질의셋을 실행하면 이 화면에서 coverage와 누락 citation을 확인할 수 있습니다.</p>
          </div>
        ) : (
          <div className="comparison-item-list">
            {items.map((item) => (
              <button
                type="button"
                className={`quick-action${active?.id === item.id ? " active" : ""}`}
                key={item.id}
                onClick={() => setActiveId(item.id)}
              >
                <span className="status-badge status-badge--active">{item.status}</span>
                <strong>{item.name}</strong>
                <small>
                  질의 {item.query_count} / citation coverage {asPercent(item.citation_coverage)} / {formatDate(item.created_at)}
                </small>
              </button>
            ))}
          </div>
        )}
      </form>

      {active ? (
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">평가 결과</p>
              <h3>{active.name}</h3>
            </div>
            <span>{formatDate(active.created_at)}</span>
          </div>

          <div className="metric-grid">
            <article>
              <span>검색 결과 coverage</span>
              <strong>{asPercent(metrics.result_coverage)}</strong>
            </article>
            <article>
              <span>기대 citation coverage</span>
              <strong>{asPercent(metrics.expected_citation_coverage)}</strong>
            </article>
            <article>
              <span>평균 top score</span>
              <strong>{active.average_top_score}</strong>
            </article>
            <article>
              <span>기대 citation 질의</span>
              <strong>{metrics.expected_citation_query_count ?? 0}</strong>
            </article>
          </div>

          {active.result.policy ? <p className="section-copy">{active.result.policy}</p> : null}

          <div className="result-list">
            {queryResults.map((query) => (
              <article className="result-row" key={query.id}>
                <div>
                  <strong>{query.query}</strong>
                  <span>
                    결과 {query.result_count} / top score {query.top_score} / 기대 citation {query.expected_citation_hit === null ? "-" : query.expected_citation_hit ? "hit" : "miss"}
                  </span>
                  {query.missed_expected_citation_ids.length ? (
                    <small>누락: {query.missed_expected_citation_ids.join(", ")}</small>
                  ) : null}
                </div>
                <small>{query.citation_candidate_ids.slice(0, 3).join(", ") || "근거 후보 없음"}</small>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
