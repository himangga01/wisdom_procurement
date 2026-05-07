import { useEffect, useState } from "react";

import { api } from "../app/api";
import type { NaraIntegrationStatus, NaraIntegrationTestResult } from "../app/types";

export function SettingsPage() {
  const [status, setStatus] = useState<NaraIntegrationStatus | null>(null);
  const [testResult, setTestResult] = useState<NaraIntegrationTestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState("");

  const loadStatus = async () => {
    setLoading(true);
    try {
      const data = await api.getNaraIntegrationStatus();
      setStatus(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "설정 상태를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const onTest = async () => {
    setTesting(true);
    try {
      const data = await api.testNaraIntegration();
      setTestResult(data);
      await loadStatus();
      setError("");
    } catch (err) {
      setTestResult(null);
      setError(err instanceof Error ? err.message : "나라장터 연결 테스트에 실패했습니다.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">API Integrations</p>
          <h3>나라장터 API 연결 상태</h3>
          <p className="section-copy">
            API 키 전체 값은 화면에 표시하지 않고, 설정 여부와 연결 테스트 결과만 확인합니다.
          </p>
        </div>
        <div className="toolbar">
          <button type="button" onClick={loadStatus} disabled={loading}>
            설정 다시 불러오기
          </button>
          <button type="button" onClick={onTest} disabled={testing || !status?.configured}>
            {testing ? "테스트 중..." : "연결 테스트"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>확인이 필요합니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="stats-grid">
        <article className="metric-card">
          <span className="metric-label">키 설정 상태</span>
          <strong className="metric-value metric-value--small">
            {loading ? "확인 중" : status?.configured ? "설정됨" : "미설정"}
          </strong>
          <p className="metric-copy">
            {status?.configured ? `마스킹 키: ${status.masked_key}` : "backend/.env에 NARA_API_SERVICE_KEY를 설정하세요."}
          </p>
        </article>
        <article className="metric-card metric-card--petal">
          <span className="metric-label">응답 형식</span>
          <strong className="metric-value metric-value--small">{status?.response_type ?? "-"}</strong>
          <p className="metric-copy">현재 설계는 JSON 응답을 기준으로 처리합니다.</p>
        </article>
        <article className="metric-card metric-card--leaf">
          <span className="metric-label">최근 테스트</span>
          <strong className="metric-value metric-value--small">{testResult?.status ?? status?.last_test_status ?? "-"}</strong>
          <p className="metric-copy">
            {testResult?.tested_at || status?.last_tested_at
              ? new Date(testResult?.tested_at ?? status?.last_tested_at ?? "").toLocaleString("ko-KR")
              : "아직 연결 테스트를 실행하지 않았습니다."}
          </p>
        </article>
      </div>

      <article className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Nara API</p>
            <h3>연동 엔드포인트</h3>
          </div>
        </div>
        <dl className="detail-list">
          <div>
            <dt>입찰공고정보서비스</dt>
            <dd>{status?.bid_public_base_url ?? "-"}</dd>
          </div>
          <div>
            <dt>공공데이터개방표준서비스</dt>
            <dd>{status?.pubdata_base_url ?? "-"}</dd>
          </div>
        </dl>
      </article>

      {testResult ? (
        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Connection Test</p>
              <h3>최근 연결 테스트 결과</h3>
            </div>
            <span className={`status-badge status-badge--${testResult.status === "ok" ? "active" : "muted"}`}>
              {testResult.status}
            </span>
          </div>
          <dl className="detail-list">
            <div>
              <dt>HTTP 상태</dt>
              <dd>{testResult.http_status ?? "-"}</dd>
            </div>
            <div>
              <dt>API 결과 코드</dt>
              <dd>{testResult.result_code || "-"}</dd>
            </div>
            <div>
              <dt>API 메시지</dt>
              <dd>{testResult.result_msg || testResult.detail || "-"}</dd>
            </div>
            <div>
              <dt>조회 건수</dt>
              <dd>{testResult.total_count}</dd>
            </div>
          </dl>
        </article>
      ) : status?.last_tested_at ? (
        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Connection Test</p>
              <h3>저장된 최근 연결 테스트 결과</h3>
            </div>
            <span className={`status-badge status-badge--${status.last_test_status === "ok" ? "active" : "muted"}`}>
              {status.last_test_status}
            </span>
          </div>
          <dl className="detail-list">
            <div>
              <dt>HTTP 상태</dt>
              <dd>{status.last_test_http_status ?? "-"}</dd>
            </div>
            <div>
              <dt>API 결과 코드</dt>
              <dd>{status.last_test_result_code || "-"}</dd>
            </div>
            <div>
              <dt>API 메시지</dt>
              <dd>{status.last_test_result_msg || status.last_test_detail || "-"}</dd>
            </div>
            <div>
              <dt>조회 건수</dt>
              <dd>{status.last_test_total_count}</dd>
            </div>
          </dl>
        </article>
      ) : null}
    </section>
  );
}
