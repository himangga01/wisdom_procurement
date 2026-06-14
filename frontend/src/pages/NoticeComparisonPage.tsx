import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type {
  BasisChunkDetail,
  Corporation,
  CorporationComparisonProfile,
  CorporationEvidenceDocument,
  NoticeComparisonItem,
  NoticeCorporationComparison,
  NoticeRequirementDetail,
  NoticeRequirementPayload,
  ResultEvidenceLink,
  SavedNaraNotice,
  UserSummary,
  UserSummaryAction,
} from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

const comparisonStatusOrder = ["possibly_missing", "needs_review", "not_found", "prepared"];

type ComparisonModal = "history" | "detail" | "requirements" | "profile" | null;
type DetailBackTarget = "history" | null;
type EvidenceDetail = CorporationEvidenceDocument | BasisChunkDetail | NoticeRequirementDetail;

type EvidenceModalState = {
  title: string;
  loading: boolean;
  error: string;
  detail: EvidenceDetail | null;
};

function statusTone(status: string) {
  if (status === "prepared") return "active";
  if (status === "possibly_missing" || status === "needs_review") return "pending";
  return "muted";
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    prepared: "준비 확인",
    possibly_missing: "준비 필요",
    needs_review: "사람 확인 필요",
    not_found: "법인 정보 없음",
  };
  return labels[status] ?? "확인 필요";
}

function comparisonDisplayCopy(value: string) {
  const legacyReinforce = "\ubcf4\uac15";
  return value
    .split(`${legacyReinforce} 필요`)
    .join("준비 필요")
    .split(`${legacyReinforce}할`)
    .join("준비할")
    .split(`${legacyReinforce}하세요`)
    .join("자료를 보완하세요")
    .split(legacyReinforce)
    .join("보완")
    .split("citation")
    .join("근거");
}

function normalizeUserSummaryAction(action: Partial<UserSummaryAction> | null | undefined): UserSummaryAction {
  const title = typeof action?.title === "string" ? comparisonDisplayCopy(action.title) : "";
  const reason = typeof action?.reason === "string" ? comparisonDisplayCopy(action.reason) : "";
  const nextStep = typeof action?.next_step === "string" ? comparisonDisplayCopy(action.next_step) : "";
  return {
    title,
    reason,
    next_step: nextStep,
    related_requirement_ids: Array.isArray(action?.related_requirement_ids)
      ? action.related_requirement_ids.filter((value): value is string => typeof value === "string" && Boolean(value.trim()))
      : [],
    documents: Array.isArray(action?.documents)
      ? action.documents.filter((value): value is string => typeof value === "string" && Boolean(value.trim())).map(comparisonDisplayCopy)
      : [],
  };
}

function normalizeUserSummary(summary: UserSummary): UserSummary {
  return {
    ...summary,
    headline_status: comparisonDisplayCopy(summary.headline_status || ""),
    plain_summary: comparisonDisplayCopy(summary.plain_summary || ""),
    top_priority_actions: (summary.top_priority_actions ?? [])
      .map((action) => normalizeUserSummaryAction(action))
      .filter((action) => action.title || action.reason || action.next_step),
    missing_groups: (summary.missing_groups ?? []).map((group) => ({
      ...group,
      group: comparisonDisplayCopy(group.group || ""),
      summary: comparisonDisplayCopy(group.summary || ""),
    })),
    item_explanations: Object.fromEntries(
      Object.entries(summary.item_explanations ?? {}).map(([key, value]) => [
        key,
        {
          ...value,
          user_gap_summary: comparisonDisplayCopy(value.user_gap_summary || ""),
          next_action: comparisonDisplayCopy(value.next_action || ""),
          evidence_hint: comparisonDisplayCopy(value.evidence_hint || ""),
          basis_summary: comparisonDisplayCopy(value.basis_summary || ""),
        },
      ]),
    ),
    risk_notes: (summary.risk_notes ?? []).map((note) => comparisonDisplayCopy(note)),
  };
}

function formatRequirementValue(value?: string) {
  const text = value || "";
  const match = text.match(/^(추정가격|예산금액|기초금액):\s*([0-9,]+)(?:원)?$/);
  if (!match) return text;
  const amount = Number(match[2].replace(/,/g, ""));
  if (!Number.isFinite(amount)) return text;
  return `${match[1]}: ${amount.toLocaleString("ko-KR")}원`;
}

function statusDescription(status: string) {
  const descriptions: Record<string, string> = {
    possibly_missing: "현재 법인 정보와 승인 증빙에서 바로 확인되지 않은 조건입니다.",
    needs_review: "자동 비교만으로 결론을 내리기 어려워 원문 확인이 필요합니다.",
    not_found: "비교할 법인 프로필 또는 승인 증빙이 아직 부족합니다.",
    prepared: "법인 프로필 또는 승인 증빙에서 확인된 준비 항목입니다.",
  };
  return descriptions[status] ?? "";
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

function groupComparisonItems(items: NoticeComparisonItem[]) {
  return {
    possibly_missing: items.filter((item) => item.status === "possibly_missing"),
    needs_review: items.filter((item) => item.status === "needs_review"),
    not_found: items.filter((item) => item.status === "not_found"),
    prepared: items.filter((item) => item.status === "prepared"),
  };
}

function comparisonFallbackSummary(comparison: NoticeCorporationComparison | null): UserSummary {
  const prepared = comparison?.prepared_count ?? 0;
  const gaps = (comparison?.possibly_missing_count ?? 0) + (comparison?.not_found_count ?? 0);
  const review = comparison?.needs_review_count ?? 0;
  const headline = gaps ? "준비 필요" : review ? "사람 확인 필요" : prepared ? "대체로 준비됨" : "검토 필요";
  return {
    generated_by: "fallback",
    headline_status: headline,
    plain_summary: comparison
      ? `준비 확인 ${prepared}개, 준비 필요 ${gaps}개, 사람 확인 필요 ${review}개가 있습니다. 상세 모달에서 조건별 부족 사유와 필요한 근거를 확인하세요.`
      : "공고와 법인을 선택한 뒤 부족조건 미리보기를 실행하면 요약이 표시됩니다.",
    top_priority_actions: [],
    missing_groups: [],
    item_explanations: {},
    risk_notes: ["이 화면은 최종 자격 판정이 아니라 사전 점검 결과입니다."],
    evidence_links: [],
  };
}

function usableUserSummary(summary: UserSummary | undefined, fallback: UserSummary): UserSummary {
  if (!summary?.plain_summary || !summary.headline_status) {
    return normalizeUserSummary(fallback);
  }
  return normalizeUserSummary({
    ...fallback,
    ...summary,
    top_priority_actions: summary.top_priority_actions ?? fallback.top_priority_actions,
    missing_groups: summary.missing_groups ?? fallback.missing_groups,
    item_explanations: summary.item_explanations ?? fallback.item_explanations,
    risk_notes: summary.risk_notes ?? fallback.risk_notes,
    evidence_links: summary.evidence_links ?? fallback.evidence_links,
  });
}

function comparisonEvidenceLinks(comparison: NoticeCorporationComparison | null, summary: UserSummary): ResultEvidenceLink[] {
  if (summary.evidence_links?.length || !comparison) {
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

  comparison.profile?.approved_evidence_documents?.forEach((item) => {
    append({
      type: "corporation_evidence",
      ref_id: String(item.id),
      evidence_document_id: item.id,
      label: item.document_label,
      description: item.original_file_name,
    });
  });
  comparison.items.forEach((item) => {
    if (!item.requirement_candidate_id) return;
    append({
      type: "notice_requirement",
      ref_id: String(item.requirement_candidate_id),
      requirement_candidate_id: item.requirement_candidate_id,
      label: item.label || "공고 요구조건",
      description: formatRequirementValue(item.required_value) || item.source_text,
    });
  });
  return links;
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

function SummaryPanel({ summary, onOpenDetail }: { summary: UserSummary; onOpenDetail?: () => void }) {
  return (
    <div className="result-summary-panel">
      <span className="status-badge status-badge--pending">{summary.headline_status}</span>
      <h3>요약</h3>
      <p>{summary.plain_summary}</p>
      {summary.generated_by ? <small>정리 방식: {summary.generated_by === "fallback" ? "기본 요약" : "AI 요약"}</small> : null}
      {onOpenDetail ? (
        <div className="modal-action-row">
          <button type="button" onClick={onOpenDetail}>
            결과 자세히 보기
          </button>
        </div>
      ) : null}
    </div>
  );
}

function EvidenceLinkList({
  links,
  onOpen,
}: {
  links: ResultEvidenceLink[];
  onOpen: (link: ResultEvidenceLink) => void;
}) {
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
  if (state.loading) {
    return <p className="section-copy">근거 내용을 불러오는 중입니다.</p>;
  }
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
            {detail.label}: {formatRequirementValue(detail.required_value)}
          </strong>
          <p>신뢰도 {Math.round((detail.confidence || 0) * 100)}%</p>
        </article>
        <article className="detail-card detail-card--wide">
          <span>공고 원문</span>
          <pre className="analysis-pre">{detail.source_text || formatRequirementValue(detail.required_value)}</pre>
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
  const [modal, setModal] = useState<ComparisonModal>(null);
  const [detailBackTarget, setDetailBackTarget] = useState<DetailBackTarget>(null);
  const [evidenceModal, setEvidenceModal] = useState<EvidenceModalState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedNotice = notices.find((item) => item.id === Number(selectedNoticeId));
  const selectedCorporation = corporations.find((item) => item.id === Number(selectedCorporationId));
  const groupedItems = groupComparisonItems(comparison?.items ?? []);
  const userSummary = usableUserSummary(comparison?.user_summary, comparisonFallbackSummary(comparison));
  const evidenceLinks = comparisonEvidenceLinks(comparison, userSummary);

  const refreshBaseData = async () => {
    const [noticeList, corporationList, comparisonList] = await Promise.all([
      api.listSavedNaraNotices(),
      api.listCorporations(),
      api.listNoticeComparisons(),
    ]);
    setNotices(noticeList);
    setCorporations(corporationList);
    setHistory(comparisonList);
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

  const refreshHistory = async () => setHistory(await api.listNoticeComparisons());

  const resetComparisonResultForSelectionChange = () => {
    setComparison(null);
    setModal(null);
    setDetailBackTarget(null);
    setEvidenceModal(null);
  };

  const onNoticeSelectionChange = (value: string) => {
    setSelectedNoticeId(value);
    resetComparisonResultForSelectionChange();
  };

  const onCorporationSelectionChange = (value: string) => {
    setSelectedCorporationId(value);
    resetComparisonResultForSelectionChange();
  };

  const closeComparisonModal = () => {
    setModal(null);
    setDetailBackTarget(null);
  };

  const onExtractRequirements = async () => {
    if (!selectedNoticeId) return;
    await runWithOverlay(
      {
        title: "공고 요구조건을 다시 추출하는 중",
        description: "저장 공고 분석 결과를 기준으로 비교 후보를 재생성합니다.",
        steps: ["저장 공고 확인", "요구조건 후보 재생성", "비교 이력 갱신"],
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
        description: "부족 가능성이 있는 조건과 필요한 증빙을 사용자용 요약으로 정리합니다.",
        steps: ["공고 요구조건 확인", "법인 프로필 확인", "부족조건 요약 저장"],
        successMessage: "부족조건 미리보기를 생성했습니다.",
        failureMessage: "부족조건 미리보기 생성에 실패했습니다.",
      },
      async () => {
        const payload = await api.createNoticeComparison(Number(selectedNoticeId), Number(selectedCorporationId));
        setComparison(payload);
        setDetailBackTarget(null);
        await refreshHistory();
      },
    );
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

  const openHistoryComparison = async (item: NoticeCorporationComparison) => {
    setComparison(item);
    setSelectedNoticeId(String(item.nara_notice_id));
    setSelectedCorporationId(String(item.corporation_id));
    setDetailBackTarget("history");
    setModal("detail");
    try {
      const detail = await api.getNoticeComparison(item.id);
      setComparison(detail);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "비교 상세 결과를 불러오지 못했습니다.");
    }
  };

  return (
    <section className="content-stack" data-demo-id="demo-notice-comparison-page">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">부족조건</p>
          <h3>부족조건 미리보기</h3>
          <p className="analysis-copy">
            저장 공고와 법인 정보를 비교해 준비할 조건, 확인이 필요한 원문, 활용한 증빙을 요약합니다.
          </p>
        </div>
        <div className="row">
          <button type="button" onClick={onCompare} disabled={!selectedNoticeId || !selectedCorporationId} data-demo-id="demo-notice-comparison-run">
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
              <p className="eyebrow">실행 대상</p>
              <h3>공고 선택</h3>
              <p className="section-copy">저장한 공고 중 비교할 공고를 선택합니다.</p>
            </div>
            <Link to="/nara-board" className="link-button link-button--soft">
              공고 검색
            </Link>
          </div>
          <select value={selectedNoticeId} onChange={(event) => onNoticeSelectionChange(event.target.value)} data-demo-id="demo-comparison-notice-select">
            <option value="">공고를 선택하세요</option>
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
              <small>마감 {selectedNotice.bid_clse_dt || "-"} / 분석 {selectedNotice.analysis_status}</small>
            </div>
          ) : null}
        </div>

        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">실행 대상</p>
              <h3>법인 선택</h3>
              <p className="section-copy">승인된 증빙자료와 법인 프로필을 비교합니다.</p>
            </div>
            <Link to="/corporations" className="link-button link-button--soft">
              법인 관리
            </Link>
          </div>
          <select
            value={selectedCorporationId}
            onChange={(event) => onCorporationSelectionChange(event.target.value)}
            data-demo-id="demo-comparison-corporation-select"
          >
            <option value="">법인을 선택하세요</option>
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
              <small>지역 {selectedCorporation.region || "-"} / 규모 {selectedCorporation.company_size_classification || "-"}</small>
            </div>
          ) : null}
        </div>
      </div>

      {comparison ? (
        <SummaryPanel summary={userSummary} onOpenDetail={() => setModal("detail")} />
      ) : (
        <div className="empty-state empty-state--info">
          <strong>아직 비교 결과가 없습니다.</strong>
          <p>공고와 법인을 선택한 뒤 실행하면 이곳에 요약만 표시됩니다. 전체 상세는 모달에서 확인합니다.</p>
        </div>
      )}

      <div className="quick-action-grid">
        <button
          type="button"
          className="quick-action"
          onClick={() => setModal("history")}
          data-demo-id="demo-comparison-history-open"
          data-help-ignore="true"
        >
          <strong>비교 이력 보기</strong>
          <span>최근 비교 결과를 모달에서 확인합니다.</span>
        </button>
        <button type="button" className="quick-action" onClick={() => setModal("requirements")} disabled={!selectedNoticeId} data-help-ignore="true">
          <strong>요구조건 보기</strong>
          <span>공고에서 추출한 요구조건 후보를 확인합니다.</span>
        </button>
        <button type="button" className="quick-action" onClick={() => setModal("profile")} disabled={!selectedCorporationId} data-help-ignore="true">
          <strong>법인 프로필 보기</strong>
          <span>비교에 사용된 법인 정보와 승인 증빙을 확인합니다.</span>
        </button>
      </div>

      <AppModal title="최근 비교 이력" open={modal === "history"} onClose={closeComparisonModal} wide demoId="demo-comparison-history-modal">
        {loading ? <p className="section-copy">비교 이력을 불러오는 중입니다.</p> : null}
        {!loading && history.length === 0 ? (
          <div className="empty-state">
            <strong>저장된 비교 이력이 없습니다.</strong>
            <p>첫 비교를 실행하면 이 모달에서 다시 볼 수 있습니다.</p>
          </div>
        ) : (
          <div className="history-list">
            {history.slice(0, 20).map((item) => (
              <button
                type="button"
                className={`history-item${comparison?.id === item.id ? " history-item--active" : ""}`}
                key={item.id}
                onClick={() => openHistoryComparison(item)}
                data-help-ignore="true"
              >
                <strong>{item.notice?.bid_ntce_nm || "저장 공고"}</strong>
                <span>{item.corporation?.name || "법인"} · 준비 {item.possibly_missing_count + item.not_found_count}개 · 확인 {item.needs_review_count}개</span>
                <small>{compactDate(item.created_at)}</small>
              </button>
            ))}
          </div>
        )}
      </AppModal>

      <AppModal title="비교 결과 상세" open={modal === "detail"} onClose={closeComparisonModal} wide demoId="demo-comparison-detail-modal">
        {detailBackTarget === "history" ? (
          <div className="modal-action-row modal-action-row--leading">
            <button type="button" className="button-secondary" onClick={() => setModal("history")} data-help-ignore="true">
              최근 비교 이력으로 돌아가기
            </button>
          </div>
        ) : null}
        <SummaryPanel summary={userSummary} />
        {userSummary.top_priority_actions.length ? (
          <div className="priority-action-list">
            {userSummary.top_priority_actions.map((action) => (
              <article className="priority-action-card" key={action.title}>
                <strong>{action.title}</strong>
                <p>{action.reason}</p>
                <small>{action.next_step}</small>
              </article>
            ))}
          </div>
        ) : null}
        <div className="comparison-status-grid">
          {comparisonStatusOrder.map((status) => {
            const items = groupedItems[status as keyof typeof groupedItems];
            return (
              <article key={status} className={`comparison-status-panel comparison-status-panel--${status}`}>
                <div className="comparison-status-heading">
                  <span className={`status-badge status-badge--${statusTone(status)}`}>{statusLabel(status)}</span>
                  <strong>{items.length}개</strong>
                </div>
                <p className="section-copy">{statusDescription(status)}</p>
                {items.length ? (
                  <ul className="comparison-item-list">
                    {items.map((item, index) => (
                      <li key={`${item.requirement_candidate_id}-${index}`}>
                        <strong>{item.label}: {formatRequirementValue(item.required_value)}</strong>
                        <span>{item.reason}</span>
                        {item.matched_value ? <small>확인값: {item.matched_value}</small> : null}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="section-copy">해당 항목이 없습니다.</p>
                )}
              </article>
            );
          })}
        </div>
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">근거 링크</p>
            <h3>활용한 증빙과 원문</h3>
          </div>
        </div>
        <EvidenceLinkList links={evidenceLinks} onOpen={openEvidenceLink} />
      </AppModal>

      <AppModal title="공고 요구조건 후보" open={modal === "requirements"} onClose={closeComparisonModal} wide demoId="demo-comparison-requirements-modal">
        <div className="modal-action-row">
          <button type="button" className="button-secondary" onClick={onExtractRequirements} disabled={!selectedNoticeId}>
            요구조건 다시 추출
          </button>
        </div>
        {requirements?.requirements.length ? (
          <div className="detail-card-list">
            {requirements.requirements.map((item) => (
              <article className="detail-card detail-card--wide" key={item.id}>
                <div className="comparison-status-heading">
                  <span className="status-badge status-badge--pending">{item.requirement_type || "요구조건"}</span>
                  <strong>{item.label}</strong>
                </div>
                <dl className="detail-list">
                  <div>
                    <dt>요구값</dt>
                    <dd>{formatRequirementValue(item.required_value) || "-"}</dd>
                  </div>
                  <div>
                    <dt>정규화 값</dt>
                    <dd>{item.normalized_value || "-"}</dd>
                  </div>
                  <div>
                    <dt>신뢰도</dt>
                    <dd>{Math.round((item.confidence || 0) * 100)}%</dd>
                  </div>
                  <div>
                    <dt>추출 방식</dt>
                    <dd>{item.extraction_method || "-"}</dd>
                  </div>
                </dl>
                <pre className="analysis-pre">{item.source_text || formatRequirementValue(item.required_value) || "원문 정보 없음"}</pre>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <strong>아직 요구조건 후보가 없습니다.</strong>
            <p>공고 분석이 끝난 뒤 다시 추출을 실행해 보세요.</p>
          </div>
        )}
      </AppModal>

      <AppModal title="법인 비교 프로필" open={modal === "profile"} onClose={() => setModal(null)} wide demoId="demo-comparison-profile-modal">
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
        <div className="section-heading section-heading--compact">
          <div>
            <p className="eyebrow">승인 증빙</p>
            <h3>비교에 활용한 증빙서류</h3>
          </div>
        </div>
        <EvidenceLinkList
          links={(profile?.approved_evidence_documents ?? []).map((item) => ({
            type: "corporation_evidence",
            ref_id: String(item.id),
            evidence_document_id: item.id,
            label: item.document_label,
            description: item.original_file_name,
          }))}
          onOpen={openEvidenceLink}
        />
      </AppModal>

      <AppModal
        title={evidenceModal?.title || "근거 보기"}
        open={Boolean(evidenceModal)}
        onClose={() => setEvidenceModal(null)}
        wide
        demoId="demo-comparison-evidence-modal"
      >
        {evidenceModal ? <EvidenceDetailContent state={evidenceModal} /> : null}
      </AppModal>
    </section>
  );
}
