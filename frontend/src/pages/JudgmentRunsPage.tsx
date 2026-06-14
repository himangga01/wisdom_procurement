import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type {
  BasisChunkDetail,
  Corporation,
  CorporationEvidenceDocument,
  JudgmentItem,
  JudgmentRun,
  NoticeRequirementDetail,
  ResultEvidenceLink,
  SavedNaraNotice,
  UserSummary,
  UserSummaryAction,
} from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

type JudgmentModal = "history" | "detail" | null;
type DetailBackTarget = "history" | null;
type EvidenceDetail = CorporationEvidenceDocument | BasisChunkDetail | NoticeRequirementDetail;

type EvidenceModalState = {
  title: string;
  loading: boolean;
  error: string;
  detail: EvidenceDetail | null;
};

function statusTone(status: string) {
  if (status === "matched" || status === "reviewed" || status === "completed") return "active";
  if (["missing", "needs_review", "needs_followup", "pending", "uncertain"].includes(status)) return "pending";
  return "muted";
}

function judgmentStatusLabel(status: string) {
  const labels: Record<string, string> = {
    matched: "준비 확인",
    missing: "준비 필요",
    uncertain: "사람 확인 필요",
    needs_review: "사람 확인 필요",
    not_applicable: "적용 제외",
  };
  return labels[status] ?? "확인 필요";
}

function reviewStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: "검토 전",
    reviewed: "검토 완료",
    needs_followup: "추가 확인",
    archived: "보관",
  };
  return labels[status] ?? "검토 전";
}

function judgmentDisplayCopy(value: string) {
  return [
    ["보강 필요", "준비 필요"],
    ["보강할", "준비할"],
    ["보강 사유", "준비 사유"],
    ["보강이 필요", "준비가 필요"],
    ["보강하세요", "보완하세요"],
  ].reduce((text, [from, to]) => text.split(from).join(to), value);
}

function normalizeJudgmentSummaryCopy(summary: UserSummary): UserSummary {
  return {
    ...summary,
    headline_status: judgmentDisplayCopy(summary.headline_status || ""),
    plain_summary: judgmentDisplayCopy(summary.plain_summary || ""),
    top_priority_actions: (summary.top_priority_actions ?? []).map((action) => ({
      ...action,
      title: judgmentDisplayCopy(action.title || ""),
      reason: judgmentDisplayCopy(action.reason || ""),
      next_step: judgmentDisplayCopy(action.next_step || ""),
    })),
    missing_groups: (summary.missing_groups ?? []).map((group) => ({
      ...group,
      group: judgmentDisplayCopy(group.group || ""),
      summary: judgmentDisplayCopy(group.summary || ""),
    })),
    item_explanations: Object.fromEntries(
      Object.entries(summary.item_explanations ?? {}).map(([key, value]) => [
        key,
        {
          ...value,
          user_gap_summary: judgmentDisplayCopy(value.user_gap_summary || ""),
          next_action: judgmentDisplayCopy(value.next_action || ""),
          evidence_hint: judgmentDisplayCopy(value.evidence_hint || ""),
          citation_summary: judgmentDisplayCopy(value.citation_summary || ""),
        },
      ]),
    ),
    risk_notes: (summary.risk_notes ?? []).map((note) => judgmentDisplayCopy(note)),
  };
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

function judgmentFallbackSummary(run: JudgmentRun | null): UserSummary {
  const prepared = run?.summary.matched_count ?? 0;
  const gaps = run?.summary.missing_count ?? 0;
  const review = (run?.summary.needs_review_count ?? 0) + (run?.summary.uncertain_count ?? 0);
  const headline = gaps ? "준비 필요" : review ? "사람 확인 필요" : prepared ? "대체로 준비됨" : "검토 필요";
  return {
    generated_by: "fallback",
    headline_status: headline,
    plain_summary: run
      ? `준비 확인 ${prepared}개, 준비 필요 ${gaps}개, 사람 확인 필요 ${review}개가 있습니다. 우선 준비 항목과 근거 링크를 확인하세요.`
      : "공고와 법인을 선택한 뒤 판단 검토를 실행하면 요약이 표시됩니다.",
    top_priority_actions: [],
    missing_groups: [],
    item_explanations: {},
    risk_notes: ["이 결과는 확정 판정이 아니라 준비 상태 검토용입니다."],
    evidence_links: [],
  };
}

function usableUserSummary(summary: UserSummary | undefined, fallback: UserSummary): UserSummary {
  if (!summary?.plain_summary || !summary.headline_status) {
    return fallback;
  }
  return {
    ...fallback,
    ...summary,
    top_priority_actions: summary.top_priority_actions ?? fallback.top_priority_actions,
    missing_groups: summary.missing_groups ?? fallback.missing_groups,
    item_explanations: summary.item_explanations ?? fallback.item_explanations,
    risk_notes: summary.risk_notes ?? fallback.risk_notes,
    evidence_links: summary.evidence_links ?? fallback.evidence_links,
  };
}

function judgmentEvidenceLinks(run: JudgmentRun | null, summary: UserSummary): ResultEvidenceLink[] {
  if (summary.evidence_links?.length || !run) {
    return summary.evidence_links ?? [];
  }
  const links: ResultEvidenceLink[] = [];
  const seen = new Set<string>();
  const append = (link: ResultEvidenceLink) => {
    const key = `${link.type}:${link.ref_id}`;
    if (seen.has(key)) return;
    seen.add(key);
    links.push(link);
  };

  run.result.items.forEach((item) => {
    const requirementId = item.requirement_input_id?.startsWith("notice_requirement:")
      ? Number(item.requirement_input_id.replace("notice_requirement:", ""))
      : 0;
    if (requirementId) {
      append({
        type: "notice_requirement",
        ref_id: String(requirementId),
        requirement_candidate_id: requirementId,
        label: item.label || "공고 요구조건",
        description: item.required_value || item.source_text,
      });
    }
    (item.review_ready_citation_candidates?.length ? item.review_ready_citation_candidates : item.citation_candidates).forEach((citation) => {
      if (!citation.basis_document_id || !citation.chunk_id) return;
      append({
        type: "basis_chunk",
        ref_id: `${citation.basis_document_id}:${citation.chunk_id}`,
        basis_document_id: citation.basis_document_id,
        chunk_id: citation.chunk_id,
        label: citation.basis_document_title || "기준문서 근거",
        description: citation.section_title || citation.text_preview,
      });
    });
  });
  return links;
}

function noticeRequirementIdFromJudgmentItem(item: JudgmentItem) {
  if (item.requirement_candidate_id) return item.requirement_candidate_id;
  if (item.requirement_input_id?.startsWith("notice_requirement:")) {
    return Number(item.requirement_input_id.replace("notice_requirement:", ""));
  }
  return 0;
}

function noticeRequirementLinkFromJudgmentItem(item: JudgmentItem): ResultEvidenceLink | null {
  const requirementId = noticeRequirementIdFromJudgmentItem(item);
  if (!requirementId) return null;
  return {
    type: "notice_requirement",
    ref_id: String(requirementId),
    requirement_candidate_id: requirementId,
    label: item.label || "공고 요구조건",
    description: item.required_value || item.source_text,
  };
}

function judgmentItemsForAction(run: JudgmentRun | null, action: UserSummaryAction): JudgmentItem[] {
  if (!run) return [];
  const relatedIds = new Set(action.related_requirement_ids ?? []);
  if (relatedIds.size) {
    return run.result.items.filter((item) => {
      const requirementId = noticeRequirementIdFromJudgmentItem(item);
      return (
        relatedIds.has(item.requirement_input_id) ||
        relatedIds.has(String(item.requirement_candidate_id ?? "")) ||
        (requirementId ? relatedIds.has(`notice_requirement:${requirementId}`) : false)
      );
    });
  }

  const actionText = `${action.title} ${action.reason} ${action.next_step}`;
  if (/자동|수동|검토|판단|사람|금액|일정/.test(actionText)) {
    return run.result.items.filter((item) => ["needs_review", "uncertain"].includes(item.match_status));
  }
  if (/준비|부족|보강|필요|증빙|서류/.test(actionText)) {
    return run.result.items.filter((item) => item.match_status === "missing");
  }
  return [];
}

function AppModal({
  title,
  open,
  wide = false,
  onClose,
  children,
  demoId,
}: {
  title: string;
  open: boolean;
  wide?: boolean;
  onClose: () => void;
  children: ReactNode;
  demoId?: string;
}) {
  if (!open) return null;
  return (
    <div className="app-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className={`app-modal-dialog${wide ? " app-modal-dialog--wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-demo-id={demoId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="app-modal-header">
          <h3>{title}</h3>
          <button type="button" className="button-secondary" onClick={onClose} data-help-ignore="true">
            닫기
          </button>
        </div>
        <div className="app-modal-body">{children}</div>
      </section>
    </div>
  );
}

function SummaryPanel({ summary }: { summary: UserSummary }) {
  return (
    <div className="result-summary-panel">
      <span className="status-badge status-badge--pending">{summary.headline_status}</span>
      <h3>판단 결과</h3>
      <span className="summary-section-label">판단 요약</span>
      <p>{summary.plain_summary}</p>
      {summary.generated_by ? (
        <small>정리 방식: {summary.generated_by === "fallback" ? "기본 요약" : summary.generated_by === "gemini" ? "Gemini 판단 정리" : "AI 판단 정리"}</small>
      ) : null}
    </div>
  );
}

function EvidenceLinkList({ links, onOpen }: { links: ResultEvidenceLink[]; onOpen: (link: ResultEvidenceLink) => void }) {
  if (!links.length) {
    return <p className="section-copy">연결된 근거 링크가 없습니다.</p>;
  }
  return (
    <div className="evidence-link-list">
      {links.map((link) => (
        <button type="button" className="evidence-link-button" key={`${link.type}-${link.ref_id}`} onClick={() => onOpen(link)} data-help-ignore="true">
          <strong>
            {link.type === "corporation_evidence"
              ? "증빙서류 보기"
              : link.type === "basis_chunk"
                ? "기준문서 근거 보기"
                : "공고 요구조건 보기"}
          </strong>
          <span>{link.label}</span>
          <small>{link.description || "내용 확인"}</small>
        </button>
      ))}
    </div>
  );
}

function EvidenceDetailContent({ state }: { state: EvidenceModalState }) {
  if (state.loading) return <p className="section-copy">근거 내용을 불러오는 중입니다.</p>;
  if (state.error) {
    return (
      <div className="empty-state empty-state--warning">
        <strong>근거를 불러오지 못했습니다.</strong>
        <p>{state.error}</p>
      </div>
    );
  }
  if (!state.detail) return null;

  if ("detail_type" in state.detail && state.detail.detail_type === "basis_chunk") {
    const detail = state.detail;
    return (
      <div className="detail-card-list">
        <article className="detail-card">
          <span>기준문서</span>
          <strong>{detail.basis_document?.title || "-"}</strong>
          <p>
            {detail.basis_document?.document_version || "-"} · {detail.page_start || "-"}쪽
            {detail.page_end && detail.page_end !== detail.page_start ? `-${detail.page_end}쪽` : ""}
          </p>
        </article>
        <article className="detail-card detail-card--wide">
          <span>원문 청크</span>
          <pre className="analysis-pre">{detail.chunk_text_normalized || detail.chunk_text}</pre>
        </article>
      </div>
    );
  }

  if ("detail_type" in state.detail && state.detail.detail_type === "notice_requirement") {
    const detail = state.detail;
    return (
      <div className="detail-card-list">
        <article className="detail-card">
          <span>공고</span>
          <strong>{detail.notice?.bid_ntce_nm || "-"}</strong>
          <p>{detail.notice?.bid_ntce_no || "-"}</p>
        </article>
        <article className="detail-card">
          <span>추출 조건</span>
          <strong>
            {detail.label}: {detail.required_value}
          </strong>
          <p>신뢰도 {Math.round((detail.confidence || 0) * 100)}%</p>
        </article>
        <article className="detail-card detail-card--wide">
          <span>공고 원문</span>
          <pre className="analysis-pre">{detail.source_text || detail.required_value}</pre>
        </article>
      </div>
    );
  }

  const evidence = state.detail as CorporationEvidenceDocument;
  return (
    <div className="detail-card-list">
      <article className="detail-card">
        <span>증빙서류</span>
        <strong>{evidence.original_file_name}</strong>
        <p>
          {evidence.document_type} · {evidence.review_status}
        </p>
      </article>
      <article className="detail-card detail-card--wide">
        <span>추출 텍스트</span>
        <pre className="analysis-pre">{evidence.extracted_text || evidence.extracted_text_preview || "추출 텍스트가 없습니다."}</pre>
      </article>
      {evidence.candidates?.length ? (
        <article className="detail-card detail-card--wide">
          <span>승인 후보</span>
          <div className="comparison-chip-list">
            {evidence.candidates.map((candidate) => (
              <span className="comparison-chip" key={candidate.id}>
                {candidate.field_label}: {candidate.extracted_value}
              </span>
            ))}
          </div>
        </article>
      ) : null}
    </div>
  );
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
  const [modal, setModal] = useState<JudgmentModal>(null);
  const [detailBackTarget, setDetailBackTarget] = useState<DetailBackTarget>(null);
  const [evidenceModal, setEvidenceModal] = useState<EvidenceModalState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeRun = useMemo(
    () => runs.find((item) => item.id === activeRunId) ?? null,
    [activeRunId, runs],
  );
  const userSummary = normalizeJudgmentSummaryCopy(usableUserSummary(activeRun?.result.user_summary, judgmentFallbackSummary(activeRun)));
  const evidenceLinks = judgmentEvidenceLinks(activeRun, userSummary);

  const refresh = async () => {
    const [noticeList, corporationList, runList] = await Promise.all([
      api.listSavedNaraNotices(),
      api.listCorporations(),
      api.listJudgmentRuns(),
    ]);
    setNotices(noticeList);
    setCorporations(corporationList);
    setRuns(runList);
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
        description: "공고 요구조건, 법인 준비 상태, 기준문서 근거를 사용자용 요약으로 정리합니다.",
        steps: ["공고 요구조건 확인", "법인 프로필 확인", "기준문서 근거 검색", "판단 요약 저장"],
        successMessage: "판단 검토 결과를 생성했습니다.",
        failureMessage: "판단 검토 실행에 실패했습니다.",
      },
      async () => {
        const created = await api.createJudgmentRun(Number(selectedNoticeId), Number(selectedCorporationId), 3);
        await refresh();
        setActiveRunId(created.id);
        setDetailBackTarget(null);
        setModal(null);
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

  const resetJudgmentResultForSelectionChange = () => {
    setActiveRunId(null);
    setReviewStatus("pending");
    setReviewerNote("");
    setModal(null);
    setDetailBackTarget(null);
    setEvidenceModal(null);
  };

  const onNoticeSelectionChange = (value: string) => {
    setSelectedNoticeId(value);
    resetJudgmentResultForSelectionChange();
  };

  const onCorporationSelectionChange = (value: string) => {
    setSelectedCorporationId(value);
    resetJudgmentResultForSelectionChange();
  };

  const closeJudgmentModal = () => {
    setModal(null);
    setDetailBackTarget(null);
  };

  const openEvidenceLink = async (link: ResultEvidenceLink) => {
    setEvidenceModal({ title: link.label, loading: true, error: "", detail: null });
    try {
      let detail: EvidenceDetail;
      if (link.type === "corporation_evidence" && link.evidence_document_id) {
        detail = await api.getCorporationEvidenceDocument(link.evidence_document_id);
      } else if (link.type === "basis_chunk" && link.basis_document_id && link.chunk_id) {
        detail = await api.getBasisDocumentChunk(link.basis_document_id, link.chunk_id);
      } else if (link.type === "notice_requirement" && link.requirement_candidate_id) {
        detail = await api.getNoticeRequirement(link.requirement_candidate_id);
      } else {
        throw new Error("근거 링크 정보가 부족합니다.");
      }
      setEvidenceModal({ title: link.label, loading: false, error: "", detail });
    } catch (err) {
      setEvidenceModal({
        title: link.label,
        loading: false,
        error: err instanceof Error ? err.message : "근거를 불러오지 못했습니다.",
        detail: null,
      });
    }
  };

  const openRunFromHistory = async (run: JudgmentRun) => {
    setActiveRunId(run.id);
    setSelectedNoticeId(String(run.nara_notice_id));
    setSelectedCorporationId(String(run.corporation_id));
    setDetailBackTarget("history");
    setModal("detail");
    try {
      const detail = await api.getJudgmentRun(run.id);
      setRuns((current) => current.map((item) => (item.id === detail.id ? detail : item)));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "판단 상세 결과를 불러오지 못했습니다.");
    }
  };

  return (
    <section className="content-stack" data-demo-id="demo-judgment-runs-page">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">판단 검토</p>
          <h3>부족조건 판단 검토</h3>
          <p className="analysis-copy">
            공고 요구조건, 법인 준비 상태, 기준문서 근거를 묶어 준비할 항목과 다음 행동을 정리합니다.
          </p>
        </div>
        <button type="button" onClick={onCreateRun} disabled={!selectedNoticeId || !selectedCorporationId} data-demo-id="demo-judgment-run-create">
          판단 검토 실행
        </button>
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
              <p className="eyebrow">실행 대상</p>
              <h3>공고 선택</h3>
              <p className="section-copy">저장 공고를 선택합니다.</p>
            </div>
            <Link to="/basis-documents" className="link-button link-button--soft">
              기준문서 관리
            </Link>
          </div>
          <select value={selectedNoticeId} onChange={(event) => onNoticeSelectionChange(event.target.value)} data-demo-id="demo-judgment-notice-select">
            <option value="">공고를 선택하세요</option>
            {notices.map((notice) => (
              <option key={notice.id} value={notice.id}>
                {notice.bid_ntce_nm || "제목 없음"} / {notice.bid_ntce_no}
              </option>
            ))}
          </select>
        </div>

        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">실행 대상</p>
              <h3>법인 선택</h3>
              <p className="section-copy">비교할 법인 프로필과 승인 증빙을 선택합니다.</p>
            </div>
            <Link to="/corporations" className="link-button link-button--soft">
              법인 관리
            </Link>
          </div>
          <select
            value={selectedCorporationId}
            onChange={(event) => onCorporationSelectionChange(event.target.value)}
            data-demo-id="demo-judgment-corporation-select"
          >
            <option value="">법인을 선택하세요</option>
            {corporations.map((corporation) => (
              <option key={corporation.id} value={corporation.id}>
                {corporation.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {activeRun ? (
        <SummaryPanel summary={userSummary} />
      ) : (
        <div className="empty-state empty-state--info">
          <strong>아직 판단 검토 결과가 없습니다.</strong>
          <p>공고와 법인을 선택한 뒤 실행하면 요약만 먼저 표시하고, 상세는 모달에서 확인합니다.</p>
        </div>
      )}

      {activeRun && userSummary.top_priority_actions.length ? (
        <div className="priority-action-list">
          {userSummary.top_priority_actions.slice(0, 3).map((action, index) => {
            const relatedItems = judgmentItemsForAction(activeRun, action);
            return (
            <article className="priority-action-card" key={`${action.title}-${index}`}>
              <strong>{action.title}</strong>
              <p>{action.reason}</p>
              <small>{action.next_step}</small>
              {relatedItems.length ? (
                <div className="priority-related-list">
                  <span>관련 조건 {relatedItems.length}개</span>
                  {relatedItems.map((item) => {
                    const requirementLink = noticeRequirementLinkFromJudgmentItem(item);
                    return (
                      <div className="priority-related-item" key={item.requirement_input_id}>
                        <strong>{item.label}</strong>
                        <p>{item.required_value || item.source_text}</p>
                        {requirementLink ? (
                          <button type="button" className="link-button link-button--soft" onClick={() => void openEvidenceLink(requirementLink)} data-help-ignore="true">
                            공고 원문 보기
                          </button>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </article>
            );
          })}
        </div>
      ) : null}

      <div className="quick-action-grid">
        <button
          type="button"
          className="quick-action"
          onClick={() => {
            setDetailBackTarget(null);
            setModal("history");
          }}
          data-demo-id="demo-judgment-history-open"
          data-help-ignore="true"
        >
          <strong>판단 검토 실행 이력 보기</strong>
          <span>최근 판단 검토 결과를 모달에서 확인합니다.</span>
        </button>
        <button
          type="button"
          className="quick-action"
          onClick={() => {
            setDetailBackTarget(null);
            setModal("detail");
          }}
          disabled={!activeRun}
          data-demo-id="demo-judgment-detail-open"
          data-help-ignore="true"
        >
          <strong>결과 자세히 보기</strong>
          <span>조건별 준비 사유, 다음 행동, 근거 링크를 확인합니다.</span>
        </button>
      </div>

      <AppModal title="판단 실행 이력" open={modal === "history"} onClose={closeJudgmentModal} wide demoId="demo-judgment-history-modal">
        {loading ? <p className="section-copy">실행 이력을 불러오는 중입니다.</p> : null}
        {!loading && runs.length === 0 ? (
          <div className="empty-state">
            <strong>저장된 실행 이력이 없습니다.</strong>
            <p>판단 검토를 실행하면 이 모달에서 다시 볼 수 있습니다.</p>
          </div>
        ) : (
          <div className="history-list" data-demo-id="demo-judgment-run-list">
            {runs.slice(0, 20).map((run) => (
              <button
                type="button"
                className={`history-item${activeRun?.id === run.id ? " history-item--active" : ""}`}
                key={run.id}
                onClick={() => openRunFromHistory(run)}
                data-demo-id="demo-judgment-run-row"
                data-demo-row-id={run.id}
                data-help-ignore="true"
              >
                <strong>{run.notice?.bid_ntce_nm || "저장 공고"}</strong>
                <span>{run.corporation?.name || "법인"} · 준비 {run.missing_count}개 · 확인 {run.needs_review_count + run.uncertain_count}개</span>
                <small>{compactDate(run.created_at)} · {reviewStatusLabel(run.review_status)}</small>
              </button>
            ))}
          </div>
        )}
      </AppModal>

      <AppModal title="판단 상세" open={modal === "detail"} onClose={closeJudgmentModal} wide demoId="demo-judgment-detail-modal">
        {detailBackTarget === "history" ? (
          <div className="modal-action-row modal-action-row--leading">
            <button type="button" className="button-secondary" onClick={() => setModal("history")} data-help-ignore="true">
              판단 검토 실행 이력으로 돌아가기
            </button>
          </div>
        ) : null}
        <SummaryPanel summary={userSummary} />
        <div className="comparison-metrics">
          <span>준비 확인 {activeRun?.summary.matched_count ?? 0}</span>
          <span>준비 필요 {activeRun?.summary.missing_count ?? 0}</span>
          <span>사람 확인 {(activeRun?.summary.needs_review_count ?? 0) + (activeRun?.summary.uncertain_count ?? 0)}</span>
          <span>근거 확인률 {Math.round(((activeRun?.summary.citation_coverage ?? 0) || 0) * 100)}%</span>
        </div>

        {activeRun?.result.items.length ? (
          <div className="detail-card-list">
            {activeRun.result.items.map((item) => {
              const explanation = userSummary.item_explanations?.[item.requirement_input_id];
              return (
                <article className="detail-card detail-card--wide" key={item.requirement_input_id}>
                  <div className="comparison-status-heading">
                    <span className={`status-badge status-badge--${statusTone(item.match_status)}`}>{judgmentStatusLabel(item.match_status)}</span>
                    <strong>{item.label}</strong>
                  </div>
                  <p>{item.required_value || item.source_text}</p>
                  <dl className="detail-list">
                    <div>
                      <dt>현재 확인값</dt>
                      <dd>{item.matched_value || "승인된 법인 정보에서 바로 확인되지 않았습니다."}</dd>
                    </div>
                    <div>
                      <dt>부족 사유</dt>
                      <dd>{explanation?.user_gap_summary || item.gap_reason || "추가 확인이 필요합니다."}</dd>
                    </div>
                    <div>
                      <dt>다음 행동</dt>
                      <dd>{explanation?.next_action || item.recommended_action}</dd>
                    </div>
                  </dl>
                </article>
              );
            })}
          </div>
        ) : (
          <p className="section-copy">조건별 상세가 없습니다.</p>
        )}

        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">근거 링크</p>
            <h3>활용한 증빙과 원문</h3>
          </div>
        </div>
        <EvidenceLinkList links={evidenceLinks} onOpen={openEvidenceLink} />

        <div className="review-save-panel">
          <label>
            검토 상태
            <select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)}>
              <option value="pending">검토 전</option>
              <option value="reviewed">검토 완료</option>
              <option value="needs_followup">추가 확인</option>
              <option value="archived">보관</option>
            </select>
          </label>
          <label>
            검토 메모
            <textarea
              value={reviewerNote}
              onChange={(event) => setReviewerNote(event.target.value)}
              rows={3}
              placeholder="예: 면허증 업로드 후 다시 판단 검토 실행 필요"
            />
          </label>
          <button type="button" onClick={onSaveReview} disabled={!activeRun}>
            검토 결과 저장
          </button>
        </div>
      </AppModal>

      <AppModal
        title={evidenceModal?.title || "근거 보기"}
        open={Boolean(evidenceModal)}
        onClose={() => setEvidenceModal(null)}
        wide
        demoId="demo-judgment-evidence-modal"
      >
        {evidenceModal ? <EvidenceDetailContent state={evidenceModal} /> : null}
      </AppModal>
    </section>
  );
}
