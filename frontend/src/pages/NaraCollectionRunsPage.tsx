import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { NaraCollectionRun } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

type NaraBusinessType = "" | "all" | "construction" | "service" | "goods" | "etc";

const naraBusinessTypeOptions: Array<{ value: NaraBusinessType; label: string }> = [
  { value: "", label: "업무 유형을 선택하세요" },
  { value: "all", label: "전체" },
  { value: "construction", label: "공사" },
  { value: "service", label: "용역" },
  { value: "goods", label: "물품" },
  { value: "etc", label: "기타" },
];

function businessTypeLabel(value: unknown, label?: unknown) {
  if (label) return String(label);
  const normalized = String(value || "all");
  return naraBusinessTypeOptions.find((option) => option.value === normalized)?.label ?? normalized;
}

function statusTone(status: string) {
  if (status === "completed") return "active";
  if (status === "not_configured" || status === "failed" || status === "partial_failed") return "pending";
  return "muted";
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function daysAgoIso(days: number) {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

function formatDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR");
}

export function NaraCollectionRunsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [runs, setRuns] = useState<NaraCollectionRun[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [keywordFilter, setKeywordFilter] = useState("");
  const [keyword, setKeyword] = useState("");
  const [businessType, setBusinessType] = useState<NaraBusinessType>("");
  const [startDate, setStartDate] = useState(daysAgoIso(3));
  const [endDate, setEndDate] = useState(todayIso());
  const [pageSize, setPageSize] = useState("50");
  const [save, setSave] = useState(true);
  const [dryRun, setDryRun] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeRun = useMemo(() => runs.find((run) => run.id === activeId) ?? runs[0] ?? null, [runs, activeId]);

  const refresh = async (nextActiveId?: number | null) => {
    setLoading(true);
    try {
      const data = await api.listNaraCollectionRuns({ status: statusFilter, keyword: keywordFilter });
      setRuns(data);
      setActiveId(nextActiveId === null ? data[0]?.id ?? null : nextActiveId ?? activeId ?? data[0]?.id ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "자동 수집 이력을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onFilter = (event: FormEvent) => {
    event.preventDefault();
    refresh(null);
  };

  const onCreate = async (event: FormEvent) => {
    event.preventDefault();
    await runWithOverlay(
      {
        title: "나라장터 자동 수집 실행 중",
        description: "나라장터 API로 공고를 조회하고 새 공고를 저장합니다.",
        steps: ["API 조회", "중복 확인", "저장 결과 기록"],
        successMessage: "자동 수집 실행을 기록했습니다.",
        failureMessage: "자동 수집 실행에 실패했습니다.",
      },
      async () => {
        let createdId: number | null = null;
        try {
          const created = await api.createNaraCollectionRun({
            keyword,
            business_type: businessType || "all",
            start_date: startDate,
            end_date: endDate,
            page_size: Number(pageSize) || 50,
            save,
            dry_run: dryRun,
          });
          createdId = created.id;
        } finally {
          await refresh(createdId);
        }
      },
    );
  };

  const resultItems = (activeRun?.result.items ?? []).slice(0, 20);

  return (
    <section className="page-grid" data-demo-id="demo-nara-collection-runs-page">
      <div className="page-title">
        <p className="eyebrow">나라장터 자동 수집</p>
        <h1>나라장터 자동 수집 관리</h1>
        <p>API 기반 공고 수집을 실행하고 저장 결과, 스킵 수, 실패 사유를 확인합니다.</p>
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
            <p className="eyebrow">수집 실행</p>
            <h3>수집 실행</h3>
          </div>
          <button type="submit" data-demo-id="demo-nara-collection-run-create">수집 실행</button>
        </div>
        <div className="form-grid">
          <label className="field">
            <span>검색어</span>
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="조경, 전기, 정보통신" />
          </label>
          <label className="field">
            <span>업무유형</span>
            <select
              value={businessType}
              onChange={(event) => setBusinessType(event.target.value as NaraBusinessType)}
              data-demo-id="demo-nara-collection-business-type"
            >
              {naraBusinessTypeOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>시작일</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>
          <label className="field">
            <span>종료일</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>
          <label className="field">
            <span>조회 건수</span>
            <input type="number" min="1" max="100" value={pageSize} onChange={(event) => setPageSize(event.target.value)} />
          </label>
          <label className="check-row">
            <input type="checkbox" checked={save} onChange={(event) => setSave(event.target.checked)} />
            <span>새 공고 저장</span>
          </label>
          <label className="check-row">
            <input type="checkbox" checked={dryRun} onChange={(event) => setDryRun(event.target.checked)} />
            <span>Dry run</span>
          </label>
        </div>
      </form>

      <form className="surface-card" onSubmit={onFilter}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">실행 이력</p>
            <h3>실행 이력</h3>
          </div>
          <div className="toolbar">
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">상태를 선택하세요</option>
              <option value="completed">completed</option>
              <option value="partial_failed">partial_failed</option>
              <option value="failed">failed</option>
              <option value="not_configured">not_configured</option>
            </select>
            <input className="search-input" value={keywordFilter} onChange={(event) => setKeywordFilter(event.target.value)} placeholder="검색어 필터" />
            <button type="submit">조회</button>
          </div>
        </div>

        {!runs.length ? (
          <div className="empty-state">
            <strong>{loading ? "불러오는 중입니다." : "실행 이력이 없습니다."}</strong>
            <p>수집 조건을 입력하고 실행하면 이력이 여기에 표시됩니다.</p>
          </div>
        ) : (
          <div className="collection-run-list" data-demo-id="demo-nara-collection-run-list">
            {runs.map((run) => (
              <button
                type="button"
                className={`collection-run-row${activeRun?.id === run.id ? " active" : ""}`}
                key={run.id}
                onClick={() => setActiveId(run.id)}
                data-demo-id="demo-nara-collection-run-row"
                data-demo-row-id={run.id}
              >
                <span className={`status-badge status-badge--${statusTone(run.status)}`}>{run.status}</span>
                <strong>{run.keyword || "검색어 없음"}</strong>
                <span>{businessTypeLabel(run.criteria.business_type, run.result.business_type_label)}</span>
                <span>{run.start_date} ~ {run.end_date}</span>
                <small>
                  조회 {run.searched_count} · 저장 {run.saved_count} · 스킵 {run.skipped_count}
                </small>
              </button>
            ))}
          </div>
        )}
      </form>

      {activeRun ? (
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">수집 결과</p>
              <h3>수집 결과</h3>
            </div>
            <span>{formatDate(activeRun.created_at)}</span>
          </div>

          <div className="metric-grid">
            <article>
              <span>조회</span>
              <strong>{activeRun.searched_count}</strong>
            </article>
            <article>
              <span>저장</span>
              <strong>{activeRun.saved_count}</strong>
            </article>
            <article>
              <span>스킵</span>
              <strong>{activeRun.skipped_count}</strong>
            </article>
            <article>
              <span>모드</span>
              <strong>{activeRun.mode}</strong>
            </article>
            <article>
              <span>업무유형</span>
              <strong>{businessTypeLabel(activeRun.criteria.business_type, activeRun.result.business_type_label)}</strong>
            </article>
          </div>

          {activeRun.error_message ? (
            <div className="empty-state empty-state--warning">
              <strong>실패 사유</strong>
              <p>{activeRun.error_message}</p>
              {activeRun.result.retryable ? <small>조건을 확인한 뒤 다시 실행할 수 있습니다.</small> : null}
            </div>
          ) : null}

          {activeRun.result.saved_notice_ids?.length ? (
            <div className="comparison-chip-list">
              {activeRun.result.saved_notice_ids.map((id) => (
                <Link className="comparison-chip" to={`/nara-saved-notices/${id}`} key={id}>
                  저장 공고 #{id}
                </Link>
              ))}
            </div>
          ) : null}

          {resultItems.length ? (
            <div className="result-list">
              {resultItems.map((item, index) => (
                <article className="result-row" key={`${item.bid_ntce_no ?? index}-${item.bid_ntce_ord ?? ""}`}>
                  <div>
                    <strong>{String(item.bid_ntce_nm ?? "공고명 없음")}</strong>
                    <span>
                      {businessTypeLabel(item.business_type, item.business_type_label)} · {String(item.bid_ntce_no ?? "-")} / 첨부{" "}
                      {String(item.attachment_count ?? 0)}
                    </span>
                  </div>
                  <small>{String(item.ntce_instt_nm ?? "")} · {String(item.bid_clse_dt ?? "")}</small>
                </article>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
