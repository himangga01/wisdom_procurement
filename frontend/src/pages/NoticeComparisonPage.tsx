import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type {
  Corporation,
  CorporationComparisonProfile,
  NoticeCorporationComparison,
  NoticeRequirementPayload,
  SavedNaraNotice,
} from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "prepared") return "active";
  if (status === "possibly_missing" || status === "needs_review") return "pending";
  return "muted";
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    prepared: "준비된 항목",
    possibly_missing: "부족 가능성",
    needs_review: "확인 필요",
    not_found: "법인 정보 없음",
  };
  return labels[status] ?? status;
}

function compactDate(value: string) {
  if (!value) return "-";
  return new Date(value).toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function joinValues(values?: string[]) {
  return values?.length ? values.join(", ") : "아직 확인된 값 없음";
}

export function NoticeComparisonPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [notices, setNotices] = useState<SavedNaraNotice[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [history, setHistory] = useState<NoticeCorporationComparison[]>([]);
  const [selectedNoticeId, setSelectedNoticeId] = useState("");
  const [selectedCorporationId, setSelectedCorporationId] = useState("");
  const [requirements, setRequirements] = useState<NoticeRequirementPayload | null>(null);
  const [profile, setProfile] = useState<CorporationComparisonProfile | null>(null);
  const [comparison, setComparison] = useState<NoticeCorporationComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedNotice = notices.find((item) => item.id === Number(selectedNoticeId));
  const selectedCorporation = corporations.find((item) => item.id === Number(selectedCorporationId));

  const refreshBaseData = async () => {
    const [noticeList, corporationList, comparisonList] = await Promise.all([
      api.listSavedNaraNotices(),
      api.listCorporations(),
      api.listNoticeComparisons(),
    ]);
    setNotices(noticeList);
    setCorporations(corporationList);
    setHistory(comparisonList);
    if (!selectedNoticeId && noticeList.length) {
      setSelectedNoticeId(String(noticeList[0].id));
    }
    if (!selectedCorporationId && corporationList.length) {
      setSelectedCorporationId(String(corporationList[0].id));
    }
  };

  useEffect(() => {
    refreshBaseData()
      .catch((err) => setError(err instanceof Error ? err.message : "비교 준비 데이터를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedNoticeId) {
      setRequirements(null);
      return;
    }
    api
      .getSavedNaraNoticeRequirements(Number(selectedNoticeId))
      .then((payload) => {
        setRequirements(payload);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "공고 요구조건 후보를 불러오지 못했습니다."));
  }, [selectedNoticeId]);

  useEffect(() => {
    if (!selectedCorporationId) {
      setProfile(null);
      return;
    }
    api
      .getCorporationComparisonProfile(Number(selectedCorporationId))
      .then((payload) => {
        setProfile(payload);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "법인 비교 프로필을 불러오지 못했습니다."));
  }, [selectedCorporationId]);

  const refreshHistory = async () => {
    const comparisonList = await api.listNoticeComparisons();
    setHistory(comparisonList);
  };

  const onExtractRequirements = async () => {
    if (!selectedNoticeId) return;
    await runWithOverlay(
      {
        title: "공고 요구조건을 다시 추출하는 중",
        description: "저장된 공고 분석 결과를 기준으로 비교 후보를 재생성합니다.",
        steps: ["저장 공고 확인", "요구조건 후보 재생성", "기존 비교 결과 무효화"],
        successMessage: "공고 요구조건 후보를 다시 추출했습니다.",
        failureMessage: "공고 요구조건 재추출에 실패했습니다.",
      },
      async () => {
        const payload = await api.extractSavedNaraNoticeRequirements(Number(selectedNoticeId));
        setRequirements(payload);
        setComparison(null);
        await refreshHistory();
      },
    );
  };

  const onCompare = async () => {
    if (!selectedNoticeId || !selectedCorporationId) return;
    await runWithOverlay(
      {
        title: "공고와 법인 준비상태를 비교하는 중",
        description: "최종 판정이 아니라 부족 가능성이 있는 조건을 먼저 정리합니다.",
        steps: ["공고 요구조건 후보 확인", "법인 프로필 정규화", "부족 가능성 미리보기 저장"],
        successMessage: "부족조건 미리보기를 생성했습니다.",
        failureMessage: "부족조건 미리보기 생성에 실패했습니다.",
      },
      async () => {
        const payload = await api.createNoticeComparison(Number(selectedNoticeId), Number(selectedCorporationId));
        setComparison(payload);
        await refreshHistory();
      },
    );
  };

  const groupedItems = {
    prepared: comparison?.items.filter((item) => item.status === "prepared") ?? [],
    possibly_missing: comparison?.items.filter((item) => item.status === "possibly_missing") ?? [],
    needs_review: comparison?.items.filter((item) => item.status === "needs_review") ?? [],
    not_found: comparison?.items.filter((item) => item.status === "not_found") ?? [],
  };

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">Phase 1.7 Preview</p>
          <h3>부족조건 미리보기</h3>
          <p className="analysis-copy">
            저장한 나라장터 공고의 요구조건 후보와 법인 프로필을 비교해, 지금 무엇이 준비되어 있고 무엇을 더 확인해야 하는지 보여줍니다.
          </p>
        </div>
        <div className="row">
          <button type="button" onClick={onCompare} disabled={!selectedNoticeId || !selectedCorporationId}>
            부족조건 미리보기 실행
          </button>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="comparison-layout">
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Select Notice</p>
              <h3>1. 공고 선택</h3>
              <p className="section-copy">저장한 공고만 비교할 수 있습니다. 공고 검색 화면에서 먼저 공고 상세 저장을 실행하세요.</p>
            </div>
            <Link to="/nara-board" className="link-button link-button--soft">
              공고 검색
            </Link>
          </div>
          <select value={selectedNoticeId} onChange={(event) => setSelectedNoticeId(event.target.value)}>
            <option value="">저장 공고 선택</option>
            {notices.map((notice) => (
              <option key={notice.id} value={notice.id}>
                {notice.bid_ntce_nm || "제목 없음"} / {notice.bid_ntce_no}
              </option>
            ))}
          </select>
          {selectedNotice ? (
            <div className="comparison-summary-card">
              <span>선택 공고</span>
              <strong>{selectedNotice.bid_ntce_nm || "-"}</strong>
              <small>
                마감 {selectedNotice.bid_clse_dt || "-"} / 분석 {selectedNotice.analysis_status}
              </small>
            </div>
          ) : null}
        </div>

        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Select Corporation</p>
              <h3>2. 법인 선택</h3>
              <p className="section-copy">승인된 증빙자료와 법인 프로필 입력값을 비교용 프로필로 정규화합니다.</p>
            </div>
            <Link to="/corporations" className="link-button link-button--soft">
              법인 관리
            </Link>
          </div>
          <select value={selectedCorporationId} onChange={(event) => setSelectedCorporationId(event.target.value)}>
            <option value="">법인 선택</option>
            {corporations.map((corporation) => (
              <option key={corporation.id} value={corporation.id}>
                {corporation.name} / {corporation.management_group_name}
              </option>
            ))}
          </select>
          {selectedCorporation ? (
            <div className="comparison-summary-card">
              <span>선택 법인</span>
              <strong>{selectedCorporation.name}</strong>
              <small>
                지역 {selectedCorporation.region || "-"} / 규모 {selectedCorporation.company_size_classification || "-"}
              </small>
            </div>
          ) : null}
        </div>
      </div>

      <div className="comparison-layout">
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Requirement Candidates</p>
              <h3>공고 요구조건 후보</h3>
              <p className="section-copy">후보 수 {requirements?.summary.total_count ?? 0}개. 최종 판정이 아니라 비교 재료입니다.</p>
            </div>
            <button type="button" className="button-secondary" onClick={onExtractRequirements} disabled={!selectedNoticeId}>
              다시 추출
            </button>
          </div>
          {requirements?.requirements.length ? (
            <div className="comparison-chip-list">
              {requirements.requirements.slice(0, 18).map((item) => (
                <span key={item.id} className="comparison-chip">
                  {item.label}: {item.required_value}
                </span>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <strong>아직 요구조건 후보가 없습니다.</strong>
              <p>공고 분석이 끝난 뒤 다시 추출을 실행해 보세요.</p>
            </div>
          )}
        </div>

        <div className="surface-card">
          <p className="eyebrow">Corporation Profile</p>
          <h3>법인 비교 프로필</h3>
          <div className="comparison-profile-grid">
            <article>
              <span>지역</span>
              <strong>{joinValues(profile?.regions)}</strong>
            </article>
            <article>
              <span>면허/업종</span>
              <strong>{joinValues(profile?.licenses)}</strong>
            </article>
            <article>
              <span>기업유형/우대</span>
              <strong>{joinValues(profile?.company_types)}</strong>
            </article>
            <article>
              <span>증빙서류</span>
              <strong>{joinValues(profile?.required_documents)}</strong>
            </article>
          </div>
        </div>
      </div>

      {comparison ? (
        <div className="surface-card comparison-result-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Comparison Result</p>
              <h3>비교 결과</h3>
              <p className="section-copy">{comparison.summary.note}</p>
            </div>
            <div className="comparison-metrics">
              <span>준비 {comparison.prepared_count}</span>
              <span>부족 가능성 {comparison.possibly_missing_count}</span>
              <span>확인 필요 {comparison.needs_review_count}</span>
            </div>
          </div>

          <div className="comparison-status-grid">
            {Object.entries(groupedItems).map(([status, items]) => (
              <article key={status} className={`comparison-status-panel comparison-status-panel--${status}`}>
                <div className="comparison-status-heading">
                  <span className={`status-badge status-badge--${statusTone(status)}`}>{statusLabel(status)}</span>
                  <strong>{items.length}개</strong>
                </div>
                {items.length ? (
                  <ul className="comparison-item-list">
                    {items.map((item, index) => (
                      <li key={`${item.requirement_candidate_id}-${index}`}>
                        <strong>{item.label}: {item.required_value}</strong>
                        <span>{item.reason}</span>
                        {item.matched_value ? <small>확인값: {item.matched_value}</small> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="section-copy">해당 항목이 없습니다.</p>
                )}
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="empty-state empty-state--info">
          <strong>아직 비교 결과가 없습니다.</strong>
          <p>공고와 법인을 선택한 뒤 부족조건 미리보기를 실행하면 결과가 저장됩니다.</p>
        </div>
      )}

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">History</p>
            <h3>최근 비교 이력</h3>
            <p className="section-copy">같은 공고/법인도 다시 실행하면 새 비교 이력으로 저장됩니다.</p>
          </div>
        </div>
        {loading ? (
          <div className="empty-state">
            <strong>비교 이력을 불러오는 중입니다.</strong>
          </div>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <strong>저장된 비교 이력이 없습니다.</strong>
            <p>첫 비교를 실행하면 이곳에 결과가 쌓입니다.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>공고</th>
                  <th>법인</th>
                  <th>부족 가능성</th>
                  <th>확인 필요</th>
                  <th>생성</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 10).map((item) => (
                  <tr key={item.id}>
                    <td>{item.notice?.bid_ntce_nm || "-"}</td>
                    <td>{item.corporation?.name || "-"}</td>
                    <td>{item.possibly_missing_count}</td>
                    <td>{item.needs_review_count}</td>
                    <td>{compactDate(item.created_at)}</td>
                    <td>
                      <button
                        type="button"
                        className="button-secondary"
                        onClick={() => {
                          setComparison(item);
                          setSelectedNoticeId(String(item.nara_notice_id));
                          setSelectedCorporationId(String(item.corporation_id));
                        }}
                      >
                        다시 보기
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
