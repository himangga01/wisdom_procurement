import { FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import { api } from "../app/api";
import type { BasisDocument, BasisRuleCandidate } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

const statusOptions = [
  { value: "", label: "전체" },
  { value: "needs_review", label: "검토 필요" },
  { value: "approved", label: "승인" },
  { value: "rejected", label: "반려" },
  { value: "archived", label: "보관" },
];

const ruleTypeOptions = [
  { value: "", label: "전체 유형" },
  { value: "region", label: "지역" },
  { value: "license", label: "면허/업종" },
  { value: "company_type", label: "기업유형" },
  { value: "required_document", label: "제출서류" },
  { value: "basis_rule", label: "기준 규칙" },
];

const ruleTypeLabels = Object.fromEntries(ruleTypeOptions.map((option) => [option.value, option.label]));
const statusLabels = Object.fromEntries(statusOptions.map((option) => [option.value, option.label]));
const TEXT_PREVIEW_LIMIT = 360;
const MODAL_PREVIEW_LIMIT = 4200;
const CANDIDATE_LIST_LIMIT = 200;

function statusTone(status: string) {
  if (status === "approved") return "active";
  if (status === "needs_review") return "pending";
  return "muted";
}

function statusLabel(status: string) {
  return statusLabels[status] || status || "상태 없음";
}

function ruleTypeLabel(ruleType: string) {
  return ruleTypeLabels[ruleType] || ruleType || "유형 없음";
}

function truncateText(value = "", limit = TEXT_PREVIEW_LIMIT) {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) return "";
  return normalized.length > limit ? `${normalized.slice(0, limit).trim()}...` : normalized;
}

function formatCount(value: number) {
  return value.toLocaleString("ko-KR");
}

function splitList(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(values?: string[]) {
  return values?.length ? values.join(", ") : "";
}

function AppModal({
  title,
  children,
  wide = false,
  onClose,
  demoId,
}: {
  title: string;
  children: ReactNode;
  wide?: boolean;
  onClose: () => void;
  demoId: string;
}) {
  return (
    <div className="app-modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className={`app-modal-dialog${wide ? " app-modal-dialog--wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        data-demo-id={demoId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="app-modal-header">
          <h3>{title}</h3>
          <button type="button" className="button-secondary" onClick={onClose}>
            닫기
          </button>
        </div>
        <div className="app-modal-body">{children}</div>
      </div>
    </div>
  );
}

export function BasisRuleCandidatesPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [items, setItems] = useState<BasisRuleCandidate[]>([]);
  const [basisDocuments, setBasisDocuments] = useState<BasisDocument[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [active, setActive] = useState<BasisRuleCandidate | null>(null);
  const [status, setStatus] = useState("needs_review");
  const [ruleType, setRuleType] = useState("");
  const [keyword, setKeyword] = useState("");
  const [basisDocumentId, setBasisDocumentId] = useState("");
  const [candidateTotalCount, setCandidateTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sourceModalOpen, setSourceModalOpen] = useState(false);
  const [showFullSource, setShowFullSource] = useState(false);
  const [form, setForm] = useState({
    rule_type: "",
    condition_text: "",
    target_scope: "",
    required_evidence_types: "",
    related_profile_fields: "",
    citation_candidate_id: "",
    review_note: "",
    reviewer_name: "local_admin",
  });

  const selected = useMemo(() => items.find((item) => item.id === activeId) ?? items[0] ?? null, [items, activeId]);
  const summaryCounts = useMemo(
    () =>
      items.reduce(
        (acc, item) => {
          acc.total += 1;
          acc[item.status as keyof typeof acc] = (acc[item.status as keyof typeof acc] ?? 0) + 1;
          return acc;
        },
        { total: 0, needs_review: 0, approved: 0, rejected: 0, archived: 0 } as Record<string, number>,
      ),
    [items],
  );
  const activeChunkText = active?.chunk?.chunk_text || "";
  const activeSourceText = activeChunkText || active?.source_condition_text || active?.condition_text || "";
  const activeSourcePreview = truncateText(activeSourceText, TEXT_PREVIEW_LIMIT);
  const activeSourceModalText = showFullSource ? activeSourceText : truncateText(activeSourceText, MODAL_PREVIEW_LIMIT);
  const citationMatchesExpected =
    !active?.expected_citation_candidate_id || form.citation_candidate_id === active.expected_citation_candidate_id;
  const closeSourceModal = () => {
    setSourceModalOpen(false);
    setShowFullSource(false);
  };

  const fillForm = (candidate: BasisRuleCandidate | null) => {
    setForm({
      rule_type: candidate?.rule_type ?? "",
      condition_text: candidate?.condition_text ?? "",
      target_scope: candidate?.target_scope ?? "",
      required_evidence_types: joinList(candidate?.required_evidence_types),
      related_profile_fields: joinList(candidate?.related_profile_fields),
      citation_candidate_id: candidate?.citation_candidate_id || candidate?.expected_citation_candidate_id || "",
      review_note: candidate?.review_note ?? "",
      reviewer_name: candidate?.reviewer_name || "local_admin",
    });
  };

  const refresh = async (nextActiveId?: number | null) => {
    setLoading(true);
    try {
      const data = await api.listBasisRuleCandidates({ status, rule_type: ruleType, keyword, limit: CANDIDATE_LIST_LIMIT });
      setItems(data.candidates);
      setCandidateTotalCount(data.candidate_count ?? data.candidates.length);
      const targetId = nextActiveId === null ? data.candidates[0]?.id ?? null : nextActiveId ?? activeId ?? data.candidates[0]?.id ?? null;
      setActiveId(targetId);
      if (targetId) {
        const detail = await api.getBasisRuleCandidate(targetId);
        setActive(detail);
        fillForm(detail);
      } else {
        setActive(null);
        fillForm(null);
      }
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "규칙 후보 목록을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    api
      .listBasisDocuments()
      .then((data) => setBasisDocuments(data))
      .catch(() => setBasisDocuments([]));
  }, []);

  useEffect(() => {
    if (!selected) return;
    api
      .getBasisRuleCandidate(selected.id)
      .then((detail) => {
        setActive(detail);
        fillForm(detail);
        setShowFullSource(false);
        setSourceModalOpen(false);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "규칙 후보 상세를 불러오지 못했습니다."));
  }, [selected?.id]);

  const candidatePayload = () => ({
    rule_type: form.rule_type,
    condition_text: form.condition_text,
    target_scope: form.target_scope,
    required_evidence_types: splitList(form.required_evidence_types),
    related_profile_fields: splitList(form.related_profile_fields),
    citation_candidate_id: form.citation_candidate_id,
    review_note: form.review_note,
    reviewer_name: form.reviewer_name,
  });

  const onFilter = (event: FormEvent) => {
    event.preventDefault();
    refresh(null);
  };

  const onExtract = async () => {
    const id = Number(basisDocumentId);
    if (!id) return;
    await runWithOverlay(
      {
        title: "규칙 후보 추출 중",
        description: "기준문서 청크에서 판단에 쓸 수 있는 조건 후보를 다시 생성합니다.",
        steps: ["기준문서 확인", "청크 분석", "후보 저장"],
        successMessage: "규칙 후보를 추출했습니다.",
        failureMessage: "규칙 후보 추출에 실패했습니다.",
      },
      async () => {
        const result = await api.extractBasisRuleCandidates(id);
        await refresh(result.candidates[0]?.id ?? null);
      },
    );
  };

  const onSave = async (event: FormEvent) => {
    event.preventDefault();
    if (!active) return;
    const updated = await api.updateBasisRuleCandidate(active.id, candidatePayload());
    await refresh(updated.id);
  };

  const onApprove = async () => {
    if (!active) return;
    const updated = await api.approveBasisRuleCandidate(active.id, candidatePayload());
    await refresh(updated.id);
  };

  const onReject = async () => {
    if (!active) return;
    const updated = await api.rejectBasisRuleCandidate(active.id, candidatePayload());
    await refresh(updated.id);
  };

  return (
    <section className="page-grid">
      <div className="page-title">
        <p className="eyebrow">규칙 후보 관리</p>
        <h1>기준문서 규칙 후보 관리</h1>
        <p>기준문서에서 자동 추출된 조건 후보를 검토해, 판단 검토에서 신뢰할 근거 규칙으로 사용할 항목만 승인합니다.</p>
      </div>

      <div className="rule-candidate-guide" data-demo-id="demo-rule-candidate-guide">
        <article>
          <span>1</span>
          <strong>후보 추출</strong>
          <p>완료/인덱싱된 기준문서를 선택해 조건 후보를 생성합니다.</p>
        </article>
        <article>
          <span>2</span>
          <strong>문구 검토</strong>
          <p>후보 문구, 필요한 증빙자료, 연결 프로필 필드를 사람이 읽기 좋게 보정합니다.</p>
        </article>
        <article>
          <span>3</span>
          <strong>근거 확인 후 승인</strong>
          <p>기준문서 청크와 연결된 근거 후보를 확인한 뒤 승인해야 판단 검토에 우선 사용됩니다.</p>
        </article>
      </div>

      {error ? (
        <div className="notice notice--error">
          <strong>확인 필요</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <form className="surface-card" onSubmit={onFilter}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">조회 조건</p>
            <h3>후보 조회</h3>
          </div>
          <div className="toolbar">
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statusOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <select value={ruleType} onChange={(event) => setRuleType(event.target.value)}>
              {ruleTypeOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <input className="search-input" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="조건 문구 검색" />
            <button type="submit">조회</button>
          </div>
        </div>
        <div className="rule-candidate-summary" aria-label="규칙 후보 상태 요약">
          <span>
            검색 결과 {formatCount(candidateTotalCount || summaryCounts.total || 0)}건 중 {formatCount(summaryCounts.total || 0)}건 표시
          </span>
          <span>검토 필요 {formatCount(summaryCounts.needs_review || 0)}건</span>
          <span>승인 {formatCount(summaryCounts.approved || 0)}건</span>
          <span>반려 {formatCount(summaryCounts.rejected || 0)}건</span>
        </div>
      </form>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">후보 추출</p>
            <h3>기준문서에서 후보 추출</h3>
          </div>
          <div className="toolbar">
            <select value={basisDocumentId} onChange={(event) => setBasisDocumentId(event.target.value)}>
              <option value="">기준문서 선택</option>
              {basisDocuments.map((document) => (
                <option value={document.id} key={document.id}>
                  #{document.id} {document.title} / {document.document_version || document.category}
                </option>
              ))}
            </select>
            <button type="button" onClick={onExtract} disabled={!basisDocumentId}>
              후보 추출
            </button>
          </div>
        </div>
      </div>

      <div className="content-split">
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">후보 목록</p>
              <h3>후보 목록</h3>
            </div>
            <span className="status-badge status-badge--muted">
              {loading ? "-" : `${formatCount(items.length)} / ${formatCount(candidateTotalCount || items.length)}`}건
            </span>
          </div>

          {candidateTotalCount > items.length ? (
            <div className="notice notice--info">
              <strong>최근 {formatCount(CANDIDATE_LIST_LIMIT)}건만 표시합니다.</strong>
              <span>브라우저 멈춤을 막기 위해 전체 {formatCount(candidateTotalCount)}건 중 최신 후보만 먼저 보여줍니다. 필요한 후보는 상태, 유형, 검색어로 좁혀서 확인하세요.</span>
            </div>
          ) : null}

          {!items.length ? (
            <div className="empty-state">
              <strong>표시할 후보가 없습니다.</strong>
              <p>필터를 바꾸거나 기준문서 ID로 후보 추출을 실행하세요.</p>
            </div>
          ) : (
            <div className="comparison-item-list">
              {items.map((item) => (
                <button
                  type="button"
                  className={`rule-candidate-row${selected?.id === item.id ? " active" : ""}`}
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                  data-demo-id="demo-rule-candidate-row"
                >
                  <span className={`status-badge status-badge--${statusTone(item.status)}`}>{statusLabel(item.status)}</span>
                  <strong>{ruleTypeLabel(item.rule_type)}</strong>
                  <small>{truncateText(item.condition_text, 180) || "조건 문구 없음"}</small>
                  <em>
                    문서 #{item.basis_document_id} · 청크 #{item.basis_chunk_id} · 신뢰도 {Math.round((item.confidence || 0) * 100)}%
                  </em>
                </button>
              ))}
            </div>
          )}
        </div>

        {active ? (
          <form className="surface-card" onSubmit={onSave}>
            <div className="section-heading">
              <div>
                <p className="eyebrow">후보 검토</p>
                <h3>후보 검토</h3>
              </div>
              <div className="modal-action-row">
                <button type="button" className="button-secondary" onClick={() => setSourceModalOpen(true)} data-demo-id="demo-rule-candidate-source-open">
                  원문 보기
                </button>
                <span className={`status-badge status-badge--${statusTone(active.status)}`}>{statusLabel(active.status)}</span>
              </div>
            </div>

            <div className="rule-candidate-context">
              <div>
                <span>기준문서</span>
                <strong>{active.basis_document?.title || `기준문서 #${active.basis_document_id}`}</strong>
              </div>
              <div>
                <span>근거 위치</span>
                <strong>청크 #{active.basis_chunk_id}</strong>
                <small>
                  {active.chunk?.page_start || active.chunk?.page_end
                    ? `페이지 ${active.chunk?.page_start ?? "-"}-${active.chunk?.page_end ?? "-"}`
                    : "페이지 정보 없음"}
                </small>
              </div>
              <div>
                <span>검토 기준</span>
                <strong>{citationMatchesExpected ? "승인 가능" : "근거 후보 확인 필요"}</strong>
              </div>
            </div>

            <div className="form-grid">
              <label className="field">
                <span>규칙 유형</span>
                <select value={form.rule_type} onChange={(event) => setForm((prev) => ({ ...prev, rule_type: event.target.value }))}>
                  {ruleTypeOptions
                    .filter((option) => option.value)
                    .map((option) => (
                      <option value={option.value} key={option.value}>
                        {option.label}
                      </option>
                    ))}
                </select>
              </label>
              <label className="field">
                <span>대상 범위</span>
                <input value={form.target_scope} onChange={(event) => setForm((prev) => ({ ...prev, target_scope: event.target.value }))} />
              </label>
              <label className="field field--full">
                <span>조건 문구</span>
                <textarea
                  rows={5}
                  value={form.condition_text}
                  onChange={(event) => setForm((prev) => ({ ...prev, condition_text: event.target.value }))}
                  required
                />
              </label>
              <label className="field field--full">
                <span>필요 증빙자료</span>
                <input
                  value={form.required_evidence_types}
                  onChange={(event) => setForm((prev) => ({ ...prev, required_evidence_types: event.target.value }))}
                  placeholder="쉼표로 구분"
                />
              </label>
              <label className="field field--full">
                <span>연결 프로필 필드</span>
                <input
                  value={form.related_profile_fields}
                  onChange={(event) => setForm((prev) => ({ ...prev, related_profile_fields: event.target.value }))}
                  placeholder="쉼표로 구분"
                />
              </label>
              <label className="field field--full">
                <span>근거 후보 ID</span>
                <select
                  value={form.citation_candidate_id}
                  onChange={(event) => setForm((prev) => ({ ...prev, citation_candidate_id: event.target.value }))}
                >
                  <option value="">근거 후보 선택</option>
                  {(active.citation_options ?? []).map((option) => (
                    <option value={option.citation_candidate_id} key={option.citation_candidate_id}>
                      {option.citation_candidate_id}
                    </option>
                  ))}
                </select>
                <small>
                  {active.citation_candidate_valid ? "현재 근거 후보는 기준문서 청크와 연결되어 있습니다." : "승인 전 근거 후보를 선택해야 합니다."}
                </small>
              </label>
              <label className="field">
                <span>검토자</span>
                <input value={form.reviewer_name} onChange={(event) => setForm((prev) => ({ ...prev, reviewer_name: event.target.value }))} />
              </label>
              <label className="field field--full">
                <span>검토 메모</span>
                <textarea rows={3} value={form.review_note} onChange={(event) => setForm((prev) => ({ ...prev, review_note: event.target.value }))} />
              </label>
            </div>

            <div className="form-actions">
              <button type="submit">수정 저장</button>
              <button type="button" className="button-secondary" onClick={onApprove} disabled={!citationMatchesExpected}>
                승인
              </button>
              <button type="button" className="button-danger" onClick={onReject}>
                반려
              </button>
            </div>

            <div className="basis-preview">
              <div className="basis-preview__header">
                <strong>기준문서 원문 미리보기</strong>
                <button type="button" className="button-secondary" onClick={() => setSourceModalOpen(true)}>
                  원문 보기
                </button>
              </div>
              <p>{activeSourcePreview || "연결된 원문이 없습니다."}</p>
              <small>
                청크 #{active.basis_chunk_id} · 신뢰도 {Math.round((active.confidence || 0) * 100)}%
                {activeSourceText.length > TEXT_PREVIEW_LIMIT ? ` · ${formatCount(activeSourceText.length)}자 중 일부만 표시` : ""}
              </small>
            </div>
          </form>
        ) : null}
      </div>

      {sourceModalOpen && active ? (
        <AppModal title="기준문서 원문 확인" wide demoId="demo-rule-candidate-source-modal" onClose={closeSourceModal}>
          <div className="detail-card-list">
            <article className="detail-card">
              <span>기준문서</span>
              <strong>{active.basis_document?.title || `기준문서 #${active.basis_document_id}`}</strong>
              <p>{active.basis_document?.document_version || active.basis_document?.category || "버전 정보 없음"}</p>
            </article>
            <article className="detail-card">
              <span>근거 위치</span>
              <strong>청크 #{active.basis_chunk_id}</strong>
              <p>
                {active.chunk?.page_start || active.chunk?.page_end
                  ? `페이지 ${active.chunk?.page_start ?? "-"}-${active.chunk?.page_end ?? "-"}`
                  : "페이지 정보 없음"}
              </p>
            </article>
            <article className="detail-card detail-card--wide">
              <span>원문</span>
              <pre className="rule-candidate-source-text">{activeSourceModalText || "표시할 원문이 없습니다."}</pre>
              {activeSourceText.length > MODAL_PREVIEW_LIMIT && !showFullSource ? (
                <button type="button" className="button-secondary" onClick={() => setShowFullSource(true)}>
                  전체 원문 표시
                </button>
              ) : null}
            </article>
          </div>
        </AppModal>
      ) : null}
    </section>
  );
}
