import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { OperationRun } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

const operationTypeLabels: Record<string, string> = {
  nara_collection: "나라장터 수집",
  judgment_run: "판단 실행",
  basis_document_processing: "기준문서 처리",
  basis_rule_candidate_extraction: "규칙 후보 추출",
  backup_create: "백업 생성",
  backup_restore: "복원 검증",
  contract_create: "계약서 생성",
  contract_review_update: "계약서 검토 변경",
  contract_delete: "계약서 삭제",
};

function statusTone(status: string) {
  if (status === "completed") return "active";
  if (["failed", "partial_failed", "not_configured", "needs_ocr_setup", "unavailable"].includes(status)) return "pending";
  return "muted";
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR");
}

function canRetry(run: OperationRun | null) {
  return Boolean(
    run &&
      ["nara_collection", "judgment_run", "basis_document_processing", "basis_rule_candidate_extraction"].includes(run.operation_type),
  );
}

function stringifySummary(value: Record<string, unknown>) {
  const text = JSON.stringify(value, null, 2);
  return text.length > 1800 ? `${text.slice(0, 1800)}\n...` : text;
}

export function OperationRunsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [runs, setRuns] = useState<OperationRun[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [operationType, setOperationType] = useState("");
  const [keyword, setKeyword] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeRun = useMemo(() => runs.find((run) => run.id === activeId) ?? runs[0] ?? null, [runs, activeId]);

  const refresh = async (nextActiveId?: number | null) => {
    setLoading(true);
    try {
      const data = await api.listOperationRuns({ status, operation_type: operationType, keyword });
      setRuns(data);
      setActiveId(nextActiveId === null ? data[0]?.id ?? null : nextActiveId ?? activeId ?? data[0]?.id ?? null);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "작업 이력을 불러오지 못했습니다.");
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

  const onRetry = async () => {
    if (!activeRun) return;
    await runWithOverlay(
      {
        title: "작업 재시도 중",
        description: "기존 요청값을 사용해 새 실행 이력을 만듭니다.",
        steps: ["요청값 확인", "작업 재실행", "새 이력 기록"],
        successMessage: "재시도 이력을 만들었습니다.",
        failureMessage: "재시도에 실패했습니다.",
      },
      async () => {
        const retried = await api.retryOperationRun(activeRun.id);
        await refresh(retried.id);
      },
    );
  };

  return (
    <section className="page-grid" data-demo-id="demo-operation-runs-page">
      <div className="page-title">
        <p className="eyebrow">작업 이력</p>
        <h1>작업/실패 관리</h1>
        <p>나라장터 수집, 판단 실행, 기준문서 처리 같은 운영 작업의 실행 이력과 실패 사유를 확인합니다.</p>
      </div>

      {error ? (
        <div className="notice notice--error">
          <strong>확인 필요</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <form className="surface-card" onSubmit={onFilter} data-demo-id="demo-operation-run-list">
        <div className="section-heading">
          <div>
            <p className="eyebrow">작업 목록</p>
            <h3>작업 이력</h3>
          </div>
          <div className="toolbar">
            <select value={operationType} onChange={(event) => setOperationType(event.target.value)}>
              <option value="">전체 작업</option>
              {Object.entries(operationTypeLabels).map(([value, label]) => (
                <option value={value} key={value}>
                  {label}
                </option>
              ))}
            </select>
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">전체 상태</option>
              <option value="completed">completed</option>
              <option value="failed">failed</option>
              <option value="partial_failed">partial_failed</option>
              <option value="not_configured">not_configured</option>
            </select>
            <input className="search-input" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="검색어" />
            <button type="submit">조회</button>
          </div>
        </div>

        {!runs.length ? (
          <div className="empty-state">
            <strong>{loading ? "불러오는 중입니다." : "작업 이력이 없습니다."}</strong>
            <p>운영 작업이 실행되면 이력이 여기에 표시됩니다.</p>
          </div>
        ) : (
          <div className="collection-run-list">
            {runs.map((run) => (
              <button
                type="button"
                className={`collection-run-row${activeRun?.id === run.id ? " active" : ""}`}
                key={run.id}
                onClick={() => setActiveId(run.id)}
                data-demo-id="demo-operation-run-row"
                data-demo-row-id={run.id}
              >
                <span className={`status-badge status-badge--${statusTone(run.status)}`}>{run.status}</span>
                <strong>{operationTypeLabels[run.operation_type] ?? run.operation_type}</strong>
                <span>{run.target_type || "-"} #{run.target_id ?? "-"}</span>
                <small>{formatDate(run.created_at)}</small>
              </button>
            ))}
          </div>
        )}
      </form>

      {activeRun ? (
        <div className="surface-card" data-demo-id="demo-operation-run-detail">
          <div className="section-heading">
            <div>
              <p className="eyebrow">작업 상세</p>
              <h3>작업 상세</h3>
            </div>
            <button type="button" className="button-secondary" onClick={onRetry} disabled={!canRetry(activeRun)}>
              재시도
            </button>
          </div>

          <div className="metric-grid">
            <article>
              <span>작업 유형</span>
              <strong>{operationTypeLabels[activeRun.operation_type] ?? activeRun.operation_type}</strong>
            </article>
            <article>
              <span>상태</span>
              <strong>{activeRun.status}</strong>
            </article>
            <article>
              <span>대상</span>
              <strong>#{activeRun.target_id ?? "-"}</strong>
            </article>
            <article>
              <span>재시도 원본</span>
              <strong>{activeRun.retry_of_run_id ? `#${activeRun.retry_of_run_id}` : "-"}</strong>
            </article>
          </div>

          {activeRun.error_message ? (
            <div className="empty-state empty-state--warning" data-demo-id="demo-operation-error-detail">
              <strong>{activeRun.error_code || "failure"}</strong>
              <p>{activeRun.error_message}</p>
            </div>
          ) : null}

          <div className="comparison-chip-list">
            {activeRun.operation_type === "nara_collection" ? (
              <Link className="comparison-chip" to="/nara-collection-runs">
                수집 이력 열기
              </Link>
            ) : null}
            {activeRun.operation_type === "judgment_run" ? (
              <Link className="comparison-chip" to="/judgment-runs">
                판단 이력 열기
              </Link>
            ) : null}
            {activeRun.operation_type.startsWith("basis") ? (
              <Link className="comparison-chip" to="/basis-documents">
                기준문서 열기
              </Link>
            ) : null}
          </div>

          <div className="comparison-layout">
            <article className="empty-state empty-state--info">
              <strong>요청값</strong>
              <pre>{stringifySummary(activeRun.request)}</pre>
            </article>
            <article className="empty-state empty-state--info">
              <strong>결과값</strong>
              <pre>{stringifySummary(activeRun.result)}</pre>
            </article>
          </div>
        </div>
      ) : null}
    </section>
  );
}
