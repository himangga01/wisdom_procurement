import { useEffect, useState } from "react";

import { api } from "../app/api";
import type { ExternalAccessStatus } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(enabled: boolean) {
  return enabled ? "active" : "muted";
}

async function copyText(value: string) {
  if (!value) return;
  await navigator.clipboard.writeText(value);
}

export function ExternalAccessPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [status, setStatus] = useState<ExternalAccessStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.getExternalAccessStatus();
      setStatus({
        ...data,
        warnings: Array.isArray(data.warnings) ? data.warnings : [],
      });
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "외부 접속 상태를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const onRefresh = async () => {
    await runWithOverlay(
      {
        title: "외부 접속 상태 확인 중",
        steps: ["status 파일 확인", "공개 URL 읽기", "화면 상태 갱신"],
        successMessage: "외부 접속 상태를 갱신했습니다.",
        failureMessage: "외부 접속 상태를 갱신하지 못했습니다.",
      },
      refresh,
    );
  };

  const frontendUrl = status?.frontend_public_url || "";
  const backendUrl = status?.backend_public_url || "";

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">외부 접속</p>
          <h3>ngrok 외부 접속</h3>
          <p className="section-copy">로컬 PC에서 실행 중인 서비스의 외부 접속 URL 상태를 확인합니다.</p>
        </div>
        <button type="button" onClick={onRefresh} disabled={loading}>
          상태 새로고침
        </button>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>확인이 필요합니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="stats-grid">
        <article className="metric-card">
          <span className="metric-label">터널 상태</span>
          <strong className="metric-value metric-value--small">
            {loading ? "확인 중" : status?.enabled ? "실행 중" : "중지됨"}
          </strong>
          <p className="metric-copy">{status?.updated_at || "아직 실행 이력이 없습니다."}</p>
        </article>
        <article className="metric-card metric-card--petal">
          <span className="metric-label">Provider</span>
          <strong className="metric-value metric-value--small">{status?.provider || "ngrok"}</strong>
          <p className="metric-copy">개발/시연용 외부 접속 터널입니다.</p>
        </article>
        <article className="metric-card metric-card--leaf">
          <span className="metric-label">공개 상태</span>
          <strong className={`status-badge status-badge--${statusTone(Boolean(status?.enabled))}`}>
            {status?.enabled ? "외부 URL 활성" : "외부 URL 없음"}
          </strong>
          <p className="metric-copy">프론트에서 start/stop을 직접 실행하지 않습니다.</p>
        </article>
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">접속 URL</p>
            <h3>접속 URL</h3>
          </div>
        </div>
        {status?.enabled ? (
          <div className="table-wrap">
            <table>
              <tbody>
                <tr>
                  <th>프론트엔드 공개 URL</th>
                  <td>{frontendUrl || "-"}</td>
                  <td>
                    <button type="button" className="button-secondary" onClick={() => copyText(frontendUrl)} disabled={!frontendUrl}>
                      복사
                    </button>
                  </td>
                </tr>
                <tr>
                  <th>백엔드 공개 URL</th>
                  <td>{backendUrl || "-"}</td>
                  <td>
                    <button type="button" className="button-secondary" onClick={() => copyText(backendUrl)} disabled={!backendUrl}>
                      복사
                    </button>
                  </td>
                </tr>
                <tr>
                  <th>로컬 URL</th>
                  <td>
                    {status.backend_local_url || "-"} / {status.frontend_local_url || "-"}
                  </td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <strong>외부 접속 터널이 실행 중이 아닙니다.</strong>
            <p>로컬 PowerShell에서 start 명령을 실행한 뒤 상태를 새로고침하세요.</p>
          </div>
        )}
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">로컬 명령</p>
            <h3>PowerShell 명령</h3>
          </div>
        </div>
        <pre>{`powershell -ExecutionPolicy Bypass -File scripts\\manage-ngrok.ps1 start
powershell -ExecutionPolicy Bypass -File scripts\\manage-ngrok.ps1 status
powershell -ExecutionPolicy Bypass -File scripts\\manage-ngrok.ps1 stop`}</pre>
      </div>

      <div className="empty-state empty-state--warning">
        <strong>외부 URL이 켜져 있는 동안 로컬 서비스가 외부에 노출됩니다.</strong>
        <p>{status?.warnings?.join(" / ") || "민감 문서 업로드와 URL 공유 범위를 신중하게 관리하세요."}</p>
      </div>
    </section>
  );
}
