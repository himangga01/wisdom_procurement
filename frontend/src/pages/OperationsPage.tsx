import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { OperationsSummary } from "../app/types";

const healthLabels: Record<string, string> = {
  database: "DB",
  storage: "저장소",
  ocr: "OCR",
  nara_api: "나라장터 API",
  ai_provider: "AI 모델",
  basis_index: "기준문서 인덱스",
};

function statusTone(status: string) {
  if (["ok", "completed", "configured", "configured_masked"].includes(status)) return "active";
  if (["warning", "action_required", "failed", "partial_failed", "unavailable", "not_configured"].includes(status)) {
    return "pending";
  }
  return "muted";
}

function statusLabel(status: string) {
  return {
    ok: "정상",
    warning: "주의",
    action_required: "조치 필요",
    configured: "설정됨",
    configured_masked: "설정됨",
    not_configured: "미설정",
    unavailable: "사용 불가",
    failed: "실패",
    partial_failed: "부분 실패",
  }[status] ?? status;
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR");
}

export function OperationsPage() {
  const [summary, setSummary] = useState<OperationsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.getOperationsSummary();
      setSummary(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "운영 상태를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const counts = summary?.counts;

  return (
    <section className="page-grid" data-demo-id="demo-operations-page">
      <div className="page-title">
        <p className="eyebrow">운영 대시보드</p>
        <h1>운영 대시보드</h1>
        <p>실패 작업, 검토 대기, 연동 상태, 백업 상태를 한 화면에서 확인합니다.</p>
      </div>

      {error ? (
        <div className="notice notice--error">
          <strong>확인 필요</strong>
          <span>{error}</span>
        </div>
      ) : null}

      {!summary ? (
        <div className="empty-state">
          <strong>{loading ? "운영 상태를 불러오는 중입니다." : "운영 상태가 없습니다."}</strong>
          <p>운영 요약 API 응답을 기다리고 있습니다.</p>
        </div>
      ) : (
        <>
          <div className="surface-card" data-demo-id="demo-operations-summary">
            <div className="section-heading">
              <div>
                <p className="eyebrow">전체 상태</p>
                <h3>전체 상태</h3>
              </div>
              <button type="button" className="button-secondary" onClick={refresh}>
                새로고침
              </button>
            </div>

            <div className="metric-grid">
              <article>
                <span>전체 상태</span>
                <strong>{statusLabel(summary.overall_status)}</strong>
              </article>
              <article>
                <span>24시간 실패</span>
                <strong>{counts?.failed_jobs_24h ?? 0}</strong>
              </article>
              <article>
                <span>검토 대기</span>
                <strong>{counts?.pending_reviews ?? 0}</strong>
              </article>
              <article>
                <span>마지막 백업</span>
                <strong>{summary.last_backup.created_at ? formatDate(summary.last_backup.created_at) : "없음"}</strong>
              </article>
            </div>

            <div className="comparison-chip-list">
              <Link className="comparison-chip" to="/nara-collection-runs">
                나라장터 수집 이력
              </Link>
              <Link className="comparison-chip" to="/judgment-runs">
                판단 실행 이력
              </Link>
              <Link className="comparison-chip" to="/basis-rule-candidates">
                기준 규칙 후보
              </Link>
              <Link className="comparison-chip" to="/basis-documents">
                기준문서 처리
              </Link>
              <Link className="comparison-chip" to="/operation-runs">
                작업 이력
              </Link>
              <Link className="comparison-chip" to="/backups">
                백업/복원
              </Link>
            </div>
          </div>

          <div className="surface-card" data-demo-id="demo-operations-health">
            <div className="section-heading">
              <div>
                <p className="eyebrow">운영 환경</p>
                <h3>운영 환경</h3>
              </div>
              <span>{formatDate(summary.generated_at)}</span>
            </div>
            <div className="result-list">
              {Object.entries(summary.health).map(([key, item]) => (
                <article className="result-row" key={key}>
                  <div>
                    <strong>{healthLabels[key] ?? key}</strong>
                    <span>{item.message || item.model || item.engine || item.masked_key || "-"}</span>
                  </div>
                  <span className={`status-badge status-badge--${statusTone(item.status)}`}>{statusLabel(item.status)}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="surface-card" data-demo-id="demo-operations-recent-failures">
            <div className="section-heading">
              <div>
                <p className="eyebrow">최근 실패</p>
                <h3>최근 실패</h3>
              </div>
              <span>{summary.recent_failures.length}건</span>
            </div>
            {!summary.recent_failures.length ? (
              <div className="empty-state empty-state--info">
                <strong>최근 실패 작업이 없습니다.</strong>
                <p>24시간 기준 실패 작업이 없으면 이 목록은 비어 있습니다.</p>
              </div>
            ) : (
              <div className="result-list">
                {summary.recent_failures.map((item) => (
                  <article
                    className="result-row"
                    key={`${item.operation_type}-${item.target_type}-${item.target_id}`}
                    data-demo-id="demo-operation-error-detail"
                  >
                    <div>
                      <strong>{item.target_label}</strong>
                      <span>{item.operation_type} · {formatDate(item.occurred_at)}</span>
                      <p>{item.error_message}</p>
                    </div>
                    <Link className="comparison-chip" to={item.detail_url}>
                      상세
                    </Link>
                  </article>
                ))}
              </div>
            )}
          </div>

          <div className="surface-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">검토 대기</p>
                <h3>검토 대기</h3>
              </div>
              <span>{summary.review_queues.length}개 큐</span>
            </div>
            {!summary.review_queues.length ? (
              <div className="empty-state empty-state--info">
                <strong>검토 대기 항목이 없습니다.</strong>
                <p>승인이나 검토가 필요한 항목이 생기면 여기에 표시됩니다.</p>
              </div>
            ) : (
              <div className="metric-grid">
                {summary.review_queues.map((queue) => (
                  <article key={queue.queue_type}>
                    <span>{queue.label}</span>
                    <strong>{queue.count}</strong>
                    <Link className="comparison-chip" to={queue.detail_url}>
                      열기
                    </Link>
                  </article>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
