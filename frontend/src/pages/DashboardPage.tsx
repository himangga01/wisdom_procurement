import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type {
  CorporationEvidenceDocument,
  CorporationReadiness,
  DashboardSummary,
  DocumentRecord,
  NaraIntegrationStatus,
  SavedNaraNotice,
} from "../app/types";

function getNextAction(summary: DashboardSummary, documents: DocumentRecord[], savedNotices: SavedNaraNotice[]) {
  if (summary.corporation_count === 0) {
    return {
      title: "법인 프로필을 먼저 등록하세요",
      description: "향후 판단 엔진의 기준 데이터가 되므로 법인 정보가 가장 먼저 필요합니다.",
      action: "/corporations",
      actionLabel: "법인 등록",
    };
  }

  if (summary.project_count === 0) {
    return {
      title: "프로젝트를 만들어 문서 이력을 묶으세요",
      description: "프로젝트 단위로 업로드와 분석 결과를 관리하면 이후 재검토가 쉬워집니다.",
      action: "/projects",
      actionLabel: "프로젝트 생성",
    };
  }

  if (summary.document_count === 0 && savedNotices.length === 0) {
    return {
      title: "공고 검색 또는 문서 업로드를 시작하세요",
      description: "나라장터 공고를 저장하거나 PDF/DOCX를 직접 업로드해 첫 분석을 실행할 수 있습니다.",
      action: "/nara-board",
      actionLabel: "공고 검색",
    };
  }

  const failed = documents.filter((item) => ["failed", "partial_failed"].includes(item.analysis_status)).length;
  if (failed) {
    return {
      title: "분석 실패 문서를 먼저 확인하세요",
      description: "파일 품질, OCR 필요 여부, API 연결 상태를 확인하면 다음 처리 흐름이 안정됩니다.",
      action: "/documents",
      actionLabel: "문서 이력 확인",
    };
  }

  return {
    title: "저장한 공고와 최근 분석 결과를 검토하세요",
    description: "분석된 공고와 문서에서 제출 조건, 일정, 첨부 상태를 확인하면 다음 대응이 빨라집니다.",
    action: savedNotices.length ? "/nara-saved-notices" : "/documents",
    actionLabel: savedNotices.length ? "저장한 공고 보기" : "문서 이력 보기",
  };
}

function statusTone(status: string) {
  if (status === "completed" || status === "cached" || status === "ok") return "active";
  if (status === "pending" || status === "partial_failed" || status === "not_run") return "pending";
  return "muted";
}

function recentDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function hasRequirementValue(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => hasRequirementValue(item));
  }
  if (value && typeof value === "object") {
    return Object.values(value as Record<string, unknown>).some((item) => hasRequirementValue(item));
  }
  if (typeof value === "string") {
    return value.trim().length > 0;
  }
  return value !== null && value !== undefined && value !== "";
}

function hasExtractedNoticeRequirements(notice: SavedNaraNotice) {
  if (!notice.analysis_summary_json) return false;
  try {
    const parsed = JSON.parse(notice.analysis_summary_json) as { notice_requirements?: unknown };
    const requirements = parsed.notice_requirements;
    if (Array.isArray(requirements)) {
      return requirements.some((item) => hasRequirementValue(item));
    }
    if (!requirements || typeof requirements !== "object") {
      return false;
    }
    return ["regions", "licenses", "company_types", "required_documents", "requirement_lines", "money", "dates"].some(
      (key) => hasRequirementValue((requirements as Record<string, unknown>)[key]),
    );
  } catch {
    return false;
  }
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>({
    corporation_count: 0,
    project_count: 0,
    document_count: 0,
  });
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [savedNotices, setSavedNotices] = useState<SavedNaraNotice[]>([]);
  const [evidenceDocuments, setEvidenceDocuments] = useState<CorporationEvidenceDocument[]>([]);
  const [readinessList, setReadinessList] = useState<CorporationReadiness[]>([]);
  const [naraStatus, setNaraStatus] = useState<NaraIntegrationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.getDashboard(),
      api.listDocuments(),
      api.listSavedNaraNotices(),
      api.getNaraIntegrationStatus(),
      api.listAllCorporationEvidenceDocuments(),
      api.listCorporationReadiness(),
    ])
      .then(([dashboard, documentList, noticeList, integration, evidenceList, readiness]) => {
        setSummary(dashboard);
        setDocuments(documentList);
        setSavedNotices(noticeList);
        setNaraStatus(integration);
        setEvidenceDocuments(evidenceList);
        setReadinessList(readiness);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "대시보드를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  const nextAction = getNextAction(summary, documents, savedNotices);
  const pendingDocuments = documents.filter((item) => item.analysis_status === "pending").length;
  const failedDocuments = documents.filter((item) => ["failed", "partial_failed"].includes(item.analysis_status)).length;
  const pendingNotices = savedNotices.filter((item) => ["pending", "saving"].includes(item.analysis_status)).length;
  const failedNotices = savedNotices.filter((item) => ["failed", "partial_failed"].includes(item.analysis_status)).length;
  const pendingEvidenceReviews = evidenceDocuments.filter((item) => (item.pending_candidate_count ?? 0) > 0).length;
  const evidenceNeedsCorrection = evidenceDocuments.filter(
    (item) =>
      item.extraction_status === "failed" ||
      item.ocr_status === "failed" ||
      item.ocr_status === "needs_ocr_setup" ||
      item.ocr_status === "unavailable",
  ).length;
  const lowReadinessCorporations = readinessList.filter((item) => item.score < 50).length;
  const requirementReadyNotices = savedNotices.filter(hasExtractedNoticeRequirements).length;
  const recentDocuments = documents.slice(0, 5);
  const recentNotices = savedNotices.slice(0, 5);

  return (
    <section className="content-stack">
      <div className="workboard-grid">
        <article className="surface-card work-card work-card--primary">
          <p className="eyebrow">다음 작업</p>
          <h3>{nextAction.title}</h3>
          <p className="section-copy">{nextAction.description}</p>
          <div className="form-actions">
            <Link to={nextAction.action} className="link-button">
              {nextAction.actionLabel}
            </Link>
          </div>
        </article>

        <article className="surface-card work-card">
          <p className="eyebrow">처리 현황</p>
          <h3>처리 대기/주의</h3>
          <div className="task-list">
            <div className="task-item">
              <span>문서 분석 대기</span>
              <strong>{loading ? "-" : pendingDocuments}</strong>
            </div>
            <div className="task-item">
              <span>문서 분석 실패</span>
              <strong>{loading ? "-" : failedDocuments}</strong>
            </div>
            <div className="task-item">
              <span>공고 처리 대기</span>
              <strong>{loading ? "-" : pendingNotices}</strong>
            </div>
            <div className="task-item">
              <span>공고 부분 실패</span>
              <strong>{loading ? "-" : failedNotices}</strong>
            </div>
          </div>
        </article>

        <article className="surface-card work-card">
          <p className="eyebrow">연동 상태</p>
          <h3>연동 상태</h3>
          <div className="status-stack">
            <span className={`status-badge status-badge--${naraStatus?.configured ? "active" : "pending"}`}>
              나라장터 API {naraStatus?.configured ? "설정됨" : "미설정"}
            </span>
            <span className={`status-badge status-badge--${statusTone(naraStatus?.last_test_status || "not_run")}`}>
              테스트 {naraStatus?.last_test_status || "not_run"}
            </span>
          </div>
          <p className="metric-copy">API 키 전체값은 포탈에 표시하지 않습니다.</p>
        </article>
      </div>

      <section className="surface-card today-queue-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">우선 확인</p>
            <h3>우선 확인할 항목</h3>
            <p className="section-copy">
              검토 대기, 보정 필요, 준비도 낮은 법인, 요구조건 추출 공고를 한곳에서 확인합니다.
            </p>
          </div>
        </div>
        <div className="queue-grid">
          <Link to="/corporations" className="queue-card queue-card--primary">
            <span>증빙 추출값 검토</span>
            <strong>{loading ? "-" : pendingEvidenceReviews}</strong>
            <small>승인 대기 후보가 있는 증빙자료</small>
          </Link>
          <Link to="/corporations" className="queue-card">
            <span>OCR/추출 보정 필요</span>
            <strong>{loading ? "-" : evidenceNeedsCorrection}</strong>
            <small>재처리 또는 텍스트 보정이 필요한 증빙</small>
          </Link>
          <Link to="/corporations" className="queue-card">
            <span>준비도 낮은 법인</span>
            <strong>{loading ? "-" : lowReadinessCorporations}</strong>
            <small>필수 프로필 정보가 부족한 법인</small>
          </Link>
          <Link to="/nara-saved-notices" className="queue-card">
            <span>요구조건 추출 완료 공고</span>
            <strong>{loading ? "-" : requirementReadyNotices}</strong>
            <small>향후 법인 비교에 사용할 조건 후보</small>
          </Link>
        </div>
      </section>

      <div className="stats-grid stats-grid--compact">
        <article className="metric-card">
          <span className="metric-label">법인</span>
          <strong className="metric-value">{loading ? "-" : summary.corporation_count}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">프로젝트</span>
          <strong className="metric-value">{loading ? "-" : summary.project_count}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">업로드 문서</span>
          <strong className="metric-value">{loading ? "-" : summary.document_count}</strong>
        </article>
        <article className="metric-card">
          <span className="metric-label">저장 공고</span>
          <strong className="metric-value">{loading ? "-" : savedNotices.length}</strong>
        </article>
      </div>

      <div className="quick-action-grid">
        <Link to="/nara-board" className="quick-action">
          <strong>공고 검색</strong>
          <span>최근 1개월 나라장터 공고 조회</span>
        </Link>
        <Link to="/documents" className="quick-action">
          <strong>문서 업로드</strong>
          <span>PDF/DOCX 직접 업로드 분석</span>
        </Link>
        <Link to="/settings/integrations/nara" className="quick-action">
          <strong>API 설정</strong>
          <span>나라장터 연결 상태 확인</span>
        </Link>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>대시보드 연결을 확인해주세요.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="two-column-grid">
        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">최근 공고</p>
              <h3>최근 저장한 공고</h3>
            </div>
            <Link to="/nara-saved-notices" className="link-button link-button--soft">
              전체 보기
            </Link>
          </div>
          {recentNotices.length === 0 ? (
            <div className="empty-state">
              <strong>아직 저장한 공고가 없습니다.</strong>
              <p>나라장터 공고 검색에서 1개 공고를 선택해 저장하면 여기에 표시됩니다.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>공고명</th>
                    <th>분석</th>
                    <th>저장</th>
                  </tr>
                </thead>
                <tbody>
                  {recentNotices.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link to={`/nara-saved-notices/${item.id}`}>
                          <strong>{item.bid_ntce_nm || "-"}</strong>
                        </Link>
                        <div className="table-subcopy">
                          {item.bid_ntce_no}-{item.bid_ntce_ord}
                        </div>
                      </td>
                      <td>
                        <span className={`status-badge status-badge--${statusTone(item.analysis_status)}`}>
                          {item.analysis_status}
                        </span>
                      </td>
                      <td>{recentDate(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">최근 문서</p>
              <h3>최근 업로드 문서</h3>
            </div>
            <Link to="/documents" className="link-button link-button--soft">
              문서 이력
            </Link>
          </div>
          {recentDocuments.length === 0 ? (
            <div className="empty-state">
              <strong>아직 업로드한 문서가 없습니다.</strong>
              <p>프로젝트를 만든 뒤 PDF/DOCX 문서를 업로드해 분석을 시작하세요.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>파일명</th>
                    <th>상태</th>
                    <th>업로드</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDocuments.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.original_file_name}</strong>
                        <div className="table-subcopy">{item.document_type}</div>
                      </td>
                      <td>
                        <span className={`status-badge status-badge--${statusTone(item.analysis_status)}`}>
                          {item.analysis_status}
                        </span>
                      </td>
                      <td>{recentDate(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}
