import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { api } from "../app/api";
import type { ContractCustomFields, ContractDocument, ContractPreview, Corporation, JudgmentRun, SavedNaraNotice } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

const reviewStatusOptions = [
  ["", "전체"],
  ["draft", "초안"],
  ["needs_review", "검토 필요"],
  ["approved", "승인"],
  ["rejected", "반려"],
  ["archived", "보관"],
];

function statusTone(status: string) {
  if (status === "generated" || status === "approved") return "active";
  if (status === "failed" || status === "needs_review" || status === "rejected") return "pending";
  return "muted";
}

function normalizePreview(value: ContractPreview | null): ContractPreview | null {
  if (!value) return null;
  return {
    ...value,
    errors: Array.isArray(value.errors) ? value.errors : [],
    warnings: Array.isArray(value.warnings) ? value.warnings : [],
    snapshot: {
      ...value.snapshot,
      generated_fields: value.snapshot?.generated_fields ?? {},
      validation: {
        valid: Boolean(value.snapshot?.validation?.valid),
        errors: Array.isArray(value.snapshot?.validation?.errors) ? value.snapshot.validation.errors : [],
        warnings: Array.isArray(value.snapshot?.validation?.warnings) ? value.snapshot.validation.warnings : [],
      },
    },
  };
}

function fieldValue(fields: Record<string, string>, key: string) {
  return fields[key] || "-";
}

export function ContractsPage() {
  const { runWithOverlay } = useWorkOverlay();
  const [searchParams] = useSearchParams();
  const [notices, setNotices] = useState<SavedNaraNotice[]>([]);
  const [corporations, setCorporations] = useState<Corporation[]>([]);
  const [judgmentRuns, setJudgmentRuns] = useState<JudgmentRun[]>([]);
  const [contracts, setContracts] = useState<ContractDocument[]>([]);
  const [selectedNoticeId, setSelectedNoticeId] = useState(searchParams.get("notice_id") ?? "");
  const [selectedCorporationId, setSelectedCorporationId] = useState(searchParams.get("corporation_id") ?? "");
  const [selectedJudgmentRunId, setSelectedJudgmentRunId] = useState(searchParams.get("judgment_run_id") ?? "");
  const [title, setTitle] = useState("");
  const [customFields, setCustomFields] = useState<ContractCustomFields>({});
  const [preview, setPreview] = useState<ContractPreview | null>(null);
  const [keyword, setKeyword] = useState("");
  const [reviewStatusFilter, setReviewStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const selectedNotice = useMemo(
    () => notices.find((item) => String(item.id) === selectedNoticeId) ?? null,
    [notices, selectedNoticeId],
  );
  const selectedCorporation = useMemo(
    () => corporations.find((item) => String(item.id) === selectedCorporationId) ?? null,
    [corporations, selectedCorporationId],
  );
  const compatibleJudgmentRuns = useMemo(
    () =>
      judgmentRuns.filter(
        (run) =>
          (!selectedNoticeId || String(run.nara_notice_id) === selectedNoticeId) &&
          (!selectedCorporationId || String(run.corporation_id) === selectedCorporationId),
      ),
    [judgmentRuns, selectedNoticeId, selectedCorporationId],
  );

  const refreshContracts = async () => {
    const data = await api.listContracts({
      keyword,
      review_status: reviewStatusFilter,
      notice_id: selectedNoticeId ? Number(selectedNoticeId) : undefined,
      corporation_id: selectedCorporationId ? Number(selectedCorporationId) : undefined,
    });
    setContracts(data);
  };

  const refreshInitialData = async () => {
    const [noticeList, corporationList, runList] = await Promise.all([
      api.listSavedNaraNotices(),
      api.listCorporations(),
      api.listJudgmentRuns(),
    ]);
    setNotices(noticeList);
    setCorporations(corporationList);
    setJudgmentRuns(runList);
    if (!selectedNoticeId && noticeList.length) setSelectedNoticeId(String(noticeList[0].id));
    if (!selectedCorporationId && corporationList.length) setSelectedCorporationId(String(corporationList[0].id));
  };

  useEffect(() => {
    Promise.all([refreshInitialData(), refreshContracts()])
      .catch((err) => setError(err instanceof Error ? err.message : "계약서 데이터를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setPreview(null);
  }, [selectedNoticeId, selectedCorporationId]);

  const updateCustomField = (key: keyof ContractCustomFields, value: string) => {
    setCustomFields((current) => ({ ...current, [key]: value }));
  };

  const requestBody = () => ({
    nara_notice_id: Number(selectedNoticeId),
    corporation_id: Number(selectedCorporationId),
    judgment_run_id: selectedJudgmentRunId ? Number(selectedJudgmentRunId) : null,
    custom_fields: customFields,
  });

  const onPreview = async () => {
    if (!selectedNoticeId || !selectedCorporationId) return;
    await runWithOverlay(
      {
        title: "계약서 미리보기 생성 중",
        steps: ["입력값 확인", "공고/법인 스냅샷 구성", "표준계약서 필드 매핑"],
        successMessage: "계약서 미리보기를 생성했습니다.",
        failureMessage: "계약서 미리보기를 생성하지 못했습니다.",
      },
      async () => {
        const data = await api.previewContract(requestBody());
        setPreview(normalizePreview(data));
        setError("");
      },
    );
  };

  const onCreate = async () => {
    if (!selectedNoticeId || !selectedCorporationId) return;
    await runWithOverlay(
      {
        title: "계약서 초안 생성 중",
        steps: ["입력 snapshot 저장", "DOCX 표준양식 렌더링", "생성 이력 갱신"],
        successMessage: "계약서 초안 생성을 완료했습니다.",
        failureMessage: "계약서 초안 생성에 실패했습니다.",
      },
      async () => {
        const created = await api.createContract({ ...requestBody(), title });
        setPreview(null);
        await refreshContracts();
        if (created.status === "failed") {
          setError(created.error_message || "계약서 초안 생성 실패 이력이 저장되었습니다.");
        } else {
          setError("");
        }
      },
    );
  };

  const onSearch = async () => {
    await runWithOverlay(
      {
        title: "계약서 이력 검색 중",
        steps: ["필터 확인", "계약서 이력 조회", "목록 갱신"],
        successMessage: "계약서 이력 검색을 완료했습니다.",
        failureMessage: "계약서 이력을 검색하지 못했습니다.",
      },
      refreshContracts,
    );
  };

  const onDelete = async (contract: ContractDocument) => {
    if (!window.confirm(`${contract.title || contract.file_name} 계약서 초안을 삭제할까요? DOCX 파일도 함께 정리됩니다.`)) return;
    await runWithOverlay(
      {
        title: "계약서 초안 삭제 중",
        steps: ["삭제 요청 전송", "DOCX 파일 정리", "이력 목록 갱신"],
        successMessage: "계약서 초안을 삭제했습니다.",
        failureMessage: "계약서 초안 삭제에 실패했습니다.",
      },
      async () => {
        await api.deleteContract(contract.id);
        await refreshContracts();
      },
    );
  };

  const generatedFields = preview?.snapshot.generated_fields ?? {};

  return (
    <section className="content-stack" data-demo-id="demo-contracts-page">
      <div className="surface-card form-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">계약서 생성</p>
            <h3>계약서 생성</h3>
            <p className="section-copy">저장 공고와 법인 정보를 기준으로 검토용 용역표준계약서 DOCX 초안을 생성합니다.</p>
          </div>
          <button
            type="button"
            onClick={onCreate}
            disabled={!selectedNoticeId || !selectedCorporationId}
            data-demo-id="demo-contract-create"
          >
            계약서 초안 생성
          </button>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>확인이 필요합니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="comparison-layout">
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">생성 입력</p>
              <h3>생성 입력</h3>
            </div>
          </div>
          <div className="form-grid">
            <label className="field">
              <span>저장 공고</span>
              <select
                value={selectedNoticeId}
                data-demo-id="demo-contract-notice-select"
                onChange={(event) => setSelectedNoticeId(event.target.value)}
              >
                <option value="">공고 선택</option>
                {notices.map((notice) => (
                  <option key={notice.id} value={notice.id}>
                    {notice.bid_ntce_nm || "제목 없음"} / {notice.bid_ntce_no}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>법인</span>
              <select
                value={selectedCorporationId}
                data-demo-id="demo-contract-corporation-select"
                onChange={(event) => setSelectedCorporationId(event.target.value)}
              >
                <option value="">법인 선택</option>
                {corporations.map((corporation) => (
                  <option key={corporation.id} value={corporation.id}>
                    {corporation.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>판단 run</span>
              <select
                value={selectedJudgmentRunId}
                data-demo-id="demo-contract-judgment-select"
                onChange={(event) => setSelectedJudgmentRunId(event.target.value)}
              >
                <option value="">선택 안 함</option>
                {compatibleJudgmentRuns.map((run) => (
                  <option key={run.id} value={run.id}>
                    #{run.id} / 부족 {run.missing_count} / 확인 {run.needs_review_count}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>문서 제목</span>
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="비우면 공고명 기준 자동 생성" />
            </label>
            <label className="field">
              <span>계약번호</span>
              <input value={customFields.contract_number ?? ""} onChange={(event) => updateCustomField("contract_number", event.target.value)} />
            </label>
            <label className="field">
              <span>계약금액</span>
              <input value={customFields.contract_amount ?? ""} onChange={(event) => updateCustomField("contract_amount", event.target.value)} />
            </label>
            <label className="field">
              <span>계약기간</span>
              <input value={customFields.contract_period ?? ""} onChange={(event) => updateCustomField("contract_period", event.target.value)} />
            </label>
            <label className="field">
              <span>위치</span>
              <input value={customFields.delivery_location ?? ""} onChange={(event) => updateCustomField("delivery_location", event.target.value)} />
            </label>
            <label className="field">
              <span>전화번호</span>
              <input value={customFields.corporation_phone ?? ""} onChange={(event) => updateCustomField("corporation_phone", event.target.value)} />
            </label>
            <label className="field">
              <span>지연배상금률</span>
              <input value={customFields.delay_penalty_rate ?? ""} onChange={(event) => updateCustomField("delay_penalty_rate", event.target.value)} />
            </label>
            <label className="field field--full">
              <span>그 밖의 사항</span>
              <textarea value={customFields.other_terms ?? ""} onChange={(event) => updateCustomField("other_terms", event.target.value)} />
            </label>
            <label className="field field--full">
              <span>붙임서류</span>
              <textarea value={customFields.attachment_notes ?? ""} onChange={(event) => updateCustomField("attachment_notes", event.target.value)} />
            </label>
          </div>
          <button
            type="button"
            className="button-secondary"
            onClick={onPreview}
            disabled={!selectedNoticeId || !selectedCorporationId}
            data-demo-id="demo-contract-preview"
          >
            미리보기
          </button>
        </div>

        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">미리보기</p>
              <h3>표준계약서 매핑</h3>
            </div>
          </div>
          {preview ? (
            <div className="content-stack">
              <div className={`empty-state ${preview.valid ? "empty-state--info" : "empty-state--warning"}`}>
                <strong>{preview.valid ? "생성 가능" : "생성 전 보완 필요"}</strong>
                <p>{[...preview.errors, ...preview.warnings].join(" / ") || "필수 입력을 확인했습니다."}</p>
              </div>
              <div className="table-wrap">
                <table>
                  <tbody>
                    <tr>
                      <th>발주처</th>
                      <td>{fieldValue(generatedFields, "buyer_name")}</td>
                    </tr>
                    <tr>
                      <th>계약상대자</th>
                      <td>{fieldValue(generatedFields, "corporation_name")}</td>
                    </tr>
                    <tr>
                      <th>용역명</th>
                      <td>{fieldValue(generatedFields, "service_name")}</td>
                    </tr>
                    <tr>
                      <th>계약금액</th>
                      <td>{fieldValue(generatedFields, "contract_amount")}</td>
                    </tr>
                    <tr>
                      <th>공고번호</th>
                      <td>{fieldValue(generatedFields, "notice_number")}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <strong>미리보기를 실행하세요.</strong>
              <p>{selectedNotice && selectedCorporation ? `${selectedNotice.bid_ntce_nm} / ${selectedCorporation.name}` : "공고와 법인을 선택하면 매핑을 확인할 수 있습니다."}</p>
            </div>
          )}
        </div>
      </div>

      <div className="surface-card" data-demo-id="demo-contract-list">
        <div className="section-heading">
          <div>
            <p className="eyebrow">생성 이력</p>
            <h3>생성 이력</h3>
          </div>
        </div>
        <div className="toolbar">
          <input className="search-input" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="계약서 제목, 공고명, 법인명 검색" />
          <select value={reviewStatusFilter} onChange={(event) => setReviewStatusFilter(event.target.value)}>
            {reviewStatusOptions.map(([value, label]) => (
              <option key={value || "all"} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button type="button" className="button-secondary" onClick={onSearch}>
            검색
          </button>
        </div>
        {loading ? (
          <div className="empty-state">
            <strong>계약서 이력을 불러오는 중입니다.</strong>
          </div>
        ) : contracts.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>계약서</th>
                  <th>공고/법인</th>
                  <th>상태</th>
                  <th>검토</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((contract) => (
                  <tr key={contract.id} data-demo-id="demo-contract-row" data-demo-row-id={contract.id}>
                    <td>
                      <strong>{contract.title || contract.file_name || `contract #${contract.id}`}</strong>
                      <div className="table-subcopy">{contract.created_at}</div>
                    </td>
                    <td>
                      {contract.notice?.bid_ntce_nm || "-"}
                      <div className="table-subcopy">{contract.corporation?.name || "-"}</div>
                    </td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(contract.status)}`}>{contract.status}</span>
                    </td>
                    <td>
                      <span className={`status-badge status-badge--${statusTone(contract.review_status)}`}>{contract.review_status}</span>
                    </td>
                    <td>
                      <div className="row">
                        {contract.download_url ? (
                          <a
                            className="link-button link-button--soft"
                            href={api.getContractDownloadUrl(contract.id)}
                            data-demo-id="demo-contract-download"
                          >
                            다운로드
                          </a>
                        ) : null}
                        <button type="button" className="button-danger" onClick={() => onDelete(contract)}>
                          삭제
                        </button>
                      </div>
                      {contract.error_message ? <div className="table-subcopy">{contract.error_message}</div> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <strong>생성 이력이 없습니다.</strong>
            <p>공고와 법인을 선택한 뒤 계약서 초안을 생성하세요.</p>
          </div>
        )}
      </div>
    </section>
  );
}
