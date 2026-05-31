import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { Corporation, JudgmentRun, SavedNaraNotice } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

function statusTone(status: string) {
  if (status === "matched" || status === "reviewed" || status === "completed") return "active";
  if (["missing", "needs_review", "needs_followup", "pending"].includes(status)) return "pending";
  return "muted";
}

function joinList(values: string[]) {
  return values.length ? values.join(", ") : "-";
}

export function JudgmentRunsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [notices, setNotices] = useState<SavedNaraNotice[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [runs, setRuns] = useState<JudgmentRun[]>([]);
  const [selectedNoticeId, setSelectedNoticeId] = useState("");
  const [selectedCorporationId, setSelectedCorporationId] = useState("");
  const [activeRunId, setActiveRunId] = useState<number | null>(null);
  const [reviewStatus, setReviewStatus] = useState("pending");
  const [reviewerNote, setReviewerNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeRun = useMemo(
    () => runs.find((item) => item.id === activeRunId) ?? runs[0] ?? null,
    [activeRunId, runs],
  );

  const refresh = async () => {
    const [noticeList, corporationList, runList] = await Promise.all([
      api.listSavedNaraNotices(),
      api.listCorporations(),
      api.listJudgmentRuns(),
    ]);
    setNotices(noticeList);
    setCorporations(corporationList);
    setRuns(runList);
    if (!selectedNoticeId && noticeList.length) setSelectedNoticeId(String(noticeList[0].id));
    if (!selectedCorporationId && corporationList.length) setSelectedCorporationId(String(corporationList[0].id));
    if (!activeRunId && runList.length) setActiveRunId(runList[0].id);
  };

  useEffect(() => {
    refresh()
      .catch((err) => setError(err instanceof Error ? err.message : "판단 실행 데이터를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeRun) return;
    setReviewStatus(activeRun.review_status);
    setReviewerNote(activeRun.reviewer_note || "");
  }, [activeRun?.id]);

  const onCreateRun = async () => {
    if (!selectedNoticeId || !selectedCorporationId) return;
    await runWithOverlay(
      {
        title: "판단 검토 실행 중",
        description: "공고 요구조건, 법인 준비 상태, 기준문서 citation 후보를 묶어 부족조건 중심 결과를 생성합니다.",
        steps: ["공고 요구조건 스냅샷", "법인 프로필 스냅샷", "기준문서 citation 검색", "검토 결과 저장"],
        successMessage: "판단 검토 결과를 생성했습니다.",
        failureMessage: "판단 검토 실행에 실패했습니다.",
      },
      async () => {
        const created = await api.createJudgmentRun(Number(selectedNoticeId), Number(selectedCorporationId), 3);
        await refresh();
        setActiveRunId(created.id);
      },
    );
  };

  const onSaveReview = async () => {
    if (!activeRun) return;
    await runWithOverlay(
      {
        title: "검토 상태 저장 중",
        steps: ["상태 확인", "검토 메모 저장", "목록 갱신"],
        successMessage: "검토 상태를 저장했습니다.",
        failureMessage: "검토 상태 저장에 실패했습니다.",
      },
      async () => {
        const updated = await api.updateJudgmentRunReview(activeRun.id, {
          review_status: reviewStatus,
          reviewer_note: reviewerNote,
        });
        await refresh();
        setActiveRunId(updated.id);
      },
    );
  };

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">Phase 3 Review</p>
          <h3>부족조건 판단 검토</h3>
          <p className="analysis-copy">
            공고 요구조건과 법인 준비 상태를 기준문서 citation 후보와 함께 검토합니다. 결과는 준비 상태 확인용이며
            확정 판정으로 표시하지 않습니다.
          </p>
        </div>
        <button type="button" onClick={onCreateRun} disabled={!selectedNoticeId || !selectedCorporationId}>
          판단 검토 실행
        </button>
      </div>

      <div className="empty-state empty-state--info">
        <strong>citation 후보가 없는 항목은 확인 필요로 남깁니다.</strong>
        <p>기준문서 근거가 부족한 조건은 검토 메모로 남기고, 기준문서 검색 품질 평가에서 다시 확인하세요.</p>
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
              <p className="eyebrow">Run Input</p>
              <h3>실행 대상</h3>
              <p className="section-copy">저장 공고와 법인을 선택해 새 판단 검토를 실행합니다.</p>
            </div>
            <Link to="/basis-documents" className="link-button link-button--soft">
              기준문서 관리
            </Link>
          </div>
          <label>
            저장 공고
            <select value={selectedNoticeId} onChange={(event) => setSelectedNoticeId(event.target.value)}>
              <option value="">공고 선택</option>
              {notices.map((notice) => (
                <option key={notice.id} value={notice.id}>
                  {notice.bid_ntce_nm || "제목 없음"} / {notice.bid_ntce_no}
                </option>
              ))}
            </select>
          </label>
          <label>
            법인
            <select value={selectedCorporationId} onChange={(event) => setSelectedCorporationId(event.target.value)}>
              <option value="">법인 선택</option>
              {corporations.map((corporation) => (
                <option key={corporation.id} value={corporation.id}>
                  {corporation.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Run History</p>
              <h3>실행 이력</h3>
            </div>
          </div>
          {loading ? <p className="section-copy">불러오는 중입니다.</p> : null}
          {runs.length ? (
            <div className="comparison-item-list">
              {runs.slice(0, 12).map((run) => (
                <button
                  type="button"
                  className="quick-action"
                  key={run.id}
                  onClick={() => setActiveRunId(run.id)}
                >
                  <strong>{run.notice?.bid_ntce_nm || "저장 공고"}</strong>
                  <span>
                    {run.corporation?.name || "법인"} · 부족 {run.missing_count} · 확인 {run.needs_review_count}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="section-copy">아직 실행 이력이 없습니다.</p>
          )}
        </div>
      </div>

      {activeRun ? (
        <div className="surface-card comparison-result-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Selected Run</p>
              <h3>{activeRun.notice?.bid_ntce_nm || "판단 검토 결과"}</h3>
              <p className="section-copy">
                {activeRun.corporation?.name || "-"} · citation coverage{" "}
                {Math.round((activeRun.summary.citation_coverage || 0) * 100)}%
              </p>
            </div>
            <span className={`status-badge status-badge--${statusTone(activeRun.review_status)}`}>
              {activeRun.review_status}
            </span>
          </div>

          <div className="comparison-metrics">
            <span>준비 {activeRun.summary.matched_count}</span>
            <span>부족 {activeRun.summary.missing_count}</span>
            <span>확인 {activeRun.summary.needs_review_count}</span>
            <span>근거 {Math.round((activeRun.summary.citation_coverage || 0) * 100)}%</span>
          </div>

          <div className="comparison-layout">
            <label>
              검토 상태
              <select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>
                <option value="pending">대기</option>
                <option value="reviewed">검토 완료</option>
                <option value="needs_followup">추가 확인</option>
                <option value="archived">보관</option>
              </select>
            </label>
            <label>
              검토 메모
              <textarea value={reviewerNote} onChange={(event) => setReviewerNote(event.target.value)} rows={3} />
            </label>
          </div>
          <button type="button" onClick={onSaveReview}>
            검토 상태 저장
          </button>

          {activeRun.result.preparation_guide.required_documents.length ? (
            <div className="empty-state empty-state--warning">
              <strong>필요 서류 후보</strong>
              <p>{joinList(activeRun.result.preparation_guide.required_documents)}</p>
            </div>
          ) : null}

          <div className="comparison-status-grid">
            {activeRun.result.items.slice(0, 16).map((item) => (
              <article className={`comparison-status-panel comparison-status-panel--${item.match_status}`} key={item.requirement_input_id}>
                <div className="comparison-status-heading">
                  <strong>{item.status_label}</strong>
                  <span>{item.label}</span>
                </div>
                <p>{item.required_value}</p>
                <small>{item.recommended_action}</small>
                <div className="comparison-chip-list">
                  <span className="comparison-chip">citation {item.citation_status}</span>
                  {item.citation_candidates.slice(0, 2).map((citation) => (
                    <span className="comparison-chip" key={citation.citation_candidate_id}>
                      {citation.basis_document_title || citation.citation_candidate_id}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
