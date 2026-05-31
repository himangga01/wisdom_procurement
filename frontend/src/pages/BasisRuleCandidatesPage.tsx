import { FormEvent, useEffect, useMemo, useState } from "react";

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

function statusTone(status: string) {
  if (status === "approved") return "active";
  if (status === "needs_review") return "pending";
  return "muted";
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
  const citationMatchesExpected =
    !active?.expected_citation_candidate_id || form.citation_candidate_id === active.expected_citation_candidate_id;

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
      const data = await api.listBasisRuleCandidates({ status, rule_type: ruleType, keyword });
      setItems(data.candidates);
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
        <p className="eyebrow">Basis Rule Candidates</p>
        <h1>기준문서 규칙 후보 관리</h1>
        <p>자동 추출된 기준문서 조건을 검토하고, 승인된 후보만 향후 판단 근거로 사용할 수 있게 관리합니다.</p>
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
            <p className="eyebrow">Filters</p>
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
      </form>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Extraction</p>
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
              <p className="eyebrow">Candidates</p>
              <h3>후보 목록</h3>
            </div>
            <span className="status-badge status-badge--muted">{loading ? "-" : items.length}건</span>
          </div>

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
                  className={`quick-action${selected?.id === item.id ? " active" : ""}`}
                  key={item.id}
                  onClick={() => setActiveId(item.id)}
                >
                  <span className={`status-badge status-badge--${statusTone(item.status)}`}>{item.status}</span>
                  <strong>{item.rule_type}</strong>
                  <small>{item.condition_text}</small>
                </button>
              ))}
            </div>
          )}
        </div>

        {active ? (
          <form className="surface-card" onSubmit={onSave}>
            <div className="section-heading">
              <div>
                <p className="eyebrow">Review</p>
                <h3>후보 검토</h3>
              </div>
              <span className={`status-badge status-badge--${statusTone(active.status)}`}>{active.status}</span>
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
                <span>Citation 후보 ID</span>
                <select
                  value={form.citation_candidate_id}
                  onChange={(event) => setForm((prev) => ({ ...prev, citation_candidate_id: event.target.value }))}
                >
                  <option value="">Citation 후보 선택</option>
                  {(active.citation_options ?? []).map((option) => (
                    <option value={option.citation_candidate_id} key={option.citation_candidate_id}>
                      {option.citation_candidate_id}
                    </option>
                  ))}
                </select>
                <small>
                  {active.citation_candidate_valid ? "현재 citation은 기준문서 청크와 연결되어 있습니다." : "승인 전 citation 후보를 선택해야 합니다."}
                </small>
              </label>
              <label className="field">
                <span>검토자</span>
                <input value={form.reviewer_name} onChange={(event) => setForm((prev) => ({ ...prev, reviewer_name: event.target.value }))} />
              </label>
              <label className="field field--full">
                <span>검토 메모</span>
                <textarea value={form.review_note} onChange={(event) => setForm((prev) => ({ ...prev, review_note: event.target.value }))} />
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
              <strong>{active.basis_document?.title || `기준문서 #${active.basis_document_id}`}</strong>
              <p>{active.chunk?.chunk_text || active.condition_text}</p>
              <small>
                chunk #{active.basis_chunk_id} · confidence {active.confidence}
              </small>
            </div>
          </form>
        ) : null}
      </div>
    </section>
  );
}
