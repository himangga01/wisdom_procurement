import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import {
  defaultSelection,
  loadStoredSelection,
  optionsFromSettings,
  keyToSelection,
  saveStoredSelection,
  selectionToKey,
} from "../app/aiModel";
import type { AiModelSelection, AiModelSettings, NaraNoticeSearchItem, NaraNoticeSearchResponse } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

type SortKey = "postedAt" | "deadline" | "amount";
type SortDirection = "asc" | "desc";
type SortRule = {
  key: SortKey;
  direction: SortDirection;
};

type NaraBusinessType = "all" | "construction" | "service" | "goods" | "etc";

const naraBusinessTypeOptions: Array<{ value: NaraBusinessType; label: string }> = [
  { value: "all", label: "전체" },
  { value: "construction", label: "공사" },
  { value: "service", label: "용역" },
  { value: "goods", label: "물품" },
  { value: "etc", label: "기타" },
];

function businessTypeLabel(value?: string, label?: string) {
  if (label) return label;
  return naraBusinessTypeOptions.find((option) => option.value === value)?.label ?? value ?? "전체";
}

function toDateInput(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function defaultRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 3);
  return { start: toDateInput(start), end: toDateInput(end) };
}

function money(value: string) {
  const numeric = Number(String(value || "").replace(/[^0-9.-]/g, ""));
  if (!Number.isFinite(numeric) || numeric === 0) return value || "-";
  return numeric.toLocaleString("ko-KR") + "원";
}

function amountValue(item: NaraNoticeSearchItem) {
  return item.presmpt_prce || item.bdgt_amt || item.bssamt || "";
}

function toNumber(value: string) {
  const numeric = Number(String(value || "").replace(/[^0-9.-]/g, ""));
  return Number.isFinite(numeric) ? numeric : Number.NaN;
}

function toTime(value: string) {
  const raw = String(value || "").trim();
  if (!raw) return Number.NaN;
  const compact = raw.replace(/[^0-9]/g, "");
  if (compact.length >= 12) {
    const year = Number(compact.slice(0, 4));
    const month = Number(compact.slice(4, 6)) - 1;
    const day = Number(compact.slice(6, 8));
    const hour = Number(compact.slice(8, 10));
    const minute = Number(compact.slice(10, 12));
    const timestamp = new Date(year, month, day, hour, minute).getTime();
    return Number.isFinite(timestamp) ? timestamp : Number.NaN;
  }
  const timestamp = new Date(raw).getTime();
  return Number.isFinite(timestamp) ? timestamp : Number.NaN;
}

function formatDateTime(value: string) {
  const raw = String(value || "").trim();
  if (!raw) return "-";
  const compact = raw.replace(/[^0-9]/g, "");
  if (compact.length >= 12) {
    return `${compact.slice(0, 4)}-${compact.slice(4, 6)}-${compact.slice(6, 8)} ${compact.slice(8, 10)}:${compact.slice(10, 12)}`;
  }
  return raw;
}

function compareNullableNumber(a: number, b: number, direction: SortDirection) {
  const aMissing = Number.isNaN(a);
  const bMissing = Number.isNaN(b);
  if (aMissing && bMissing) return 0;
  if (aMissing) return 1;
  if (bMissing) return -1;
  return direction === "asc" ? a - b : b - a;
}

function statusTone(status: string) {
  if (status === "supported" || status === "completed") return "active";
  if (status === "pending" || status === "partial_failed") return "pending";
  return "muted";
}

function canPreviewInline(fileExtension: string) {
  return fileExtension.toLowerCase() === ".pdf";
}

function rawValue(item: NaraNoticeSearchItem, keys: string[]) {
  for (const key of keys) {
    const value = item.raw[key];
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value);
    }
  }
  return "";
}

function previewRows(item: NaraNoticeSearchItem) {
  return [
    { label: "공고명", value: item.bid_ntce_nm },
    { label: "공고번호/차수", value: `${item.bid_ntce_no || "-"}-${item.bid_ntce_ord || "-"}` },
    { label: "업무유형", value: businessTypeLabel(item.business_type, item.business_type_label) },
    { label: "공고기관", value: item.ntce_instt_nm },
    { label: "수요기관", value: item.dminstt_nm },
    { label: "등록 날짜", value: formatDateTime(item.bid_ntce_dt) },
    { label: "입찰 시작", value: formatDateTime(item.bid_begin_dt) },
    { label: "입찰 마감", value: formatDateTime(item.bid_clse_dt) },
    { label: "개찰 일시", value: formatDateTime(item.openg_dt) },
    { label: "추정가격", value: money(item.presmpt_prce) },
    { label: "예산금액", value: money(item.bdgt_amt) },
    { label: "기초금액", value: money(item.bssamt) },
    { label: "지역", value: item.region_text || rawValue(item, ["cnstrtsiteRgnNm", "prtcptPsblRgnNm"]) },
    { label: "면허/업종", value: item.license_text || rawValue(item, ["lcnsLmtNm", "indstrytyNm", "indstrytyLmtYn"]) },
    { label: "입찰방식", value: rawValue(item, ["bidMethdNm", "cntrctCnclsMthdNm", "bidQlfctRgstDt"]) },
    { label: "계약방법", value: rawValue(item, ["cntrctCnclsMthdNm", "sucsfbidMthdNm"]) },
    { label: "공동수급", value: rawValue(item, ["cmmnSpldmdMethdCd", "cmmnSpldmdMethdNm", "jointSupplyDemandYn"]) },
    { label: "원문 링크", value: item.source_url },
  ].filter((row) => row.value && row.value !== "-");
}

export function NaraBoardPage() {
  const { runWithOverlay } = useWorkOverlay();
  const range = defaultRange();
  const [keyword, setKeyword] = useState("");
  const [businessType, setBusinessType] = useState<NaraBusinessType>("all");
  const [startDate, setStartDate] = useState(range.start);
  const [endDate, setEndDate] = useState(range.end);
  const [pageSize, setPageSize] = useState(20);
  const [pageNo, setPageNo] = useState(1);
  const [result, setResult] = useState<NaraNoticeSearchResponse | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [aiSettings, setAiSettings] = useState<AiModelSettings | null>(null);
  const [aiSelection, setAiSelection] = useState<AiModelSelection>(defaultSelection());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [savedNoticeId, setSavedNoticeId] = useState<number | null>(null);
  const [sortRules, setSortRules] = useState<SortRule[]>([]);

  const search = async (nextPageNo = pageNo, showOverlay = false) => {
    const executeSearch = async () => {
    setLoading(true);
    setSavedNoticeId(null);
    try {
      const data = await api.searchNaraNotices({
        keyword,
        start_date: startDate,
        end_date: endDate,
        business_type: businessType,
        page_size: pageSize,
        page_no: nextPageNo,
      });
      setResult(data);
      setPageNo(nextPageNo);
      setSelectedKey(data.items[0] ? `${data.items[0].bid_ntce_no}:${data.items[0].bid_ntce_ord}` : "");
      setError("");
    } catch (err) {
      setResult(null);
      setSelectedKey("");
      setError(err instanceof Error ? err.message : "나라장터 공고 조회에 실패했습니다.");
    } finally {
      setLoading(false);
    }
    };

    if (showOverlay) {
      await runWithOverlay(
        {
          title: "나라장터 공고 조회 중",
          description: "공공데이터 API에서 공고 목록을 가져와 표와 미리보기를 갱신합니다.",
          steps: ["조회 조건 확인", "나라장터 API 호출", "응답 데이터 정리", "공고 목록 갱신"],
          successMessage: "나라장터 공고 조회가 완료되었습니다.",
          failureMessage: "나라장터 공고 조회를 완료하지 못했습니다.",
        },
        executeSearch,
      );
      return;
    }

    await executeSearch();
  };

  useEffect(() => {
    search();
  }, []);

  useEffect(() => {
    api
      .getAiModelSettings()
      .then((settings) => {
        setAiSettings(settings);
        setAiSelection(loadStoredSelection(settings));
      })
      .catch(() => {
        setAiSelection(loadStoredSelection(null));
      });
  }, []);

  const onAiModelChange = (value: string) => {
    const next = keyToSelection(value);
    setAiSelection(next);
    saveStoredSelection(next);
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void search(1, true);
  };

  const onPageSizeChange = (nextPageSize: number) => {
    setPageSize(nextPageSize);
    setPageNo(1);
  };

  const selectedNotice = result?.items.find((item) => `${item.bid_ntce_no}:${item.bid_ntce_ord}` === selectedKey);

  const sortedItems = result
    ? [...result.items].sort((a, b) => {
        for (const rule of sortRules) {
          let result = 0;
          if (rule.key === "postedAt") {
            result = compareNullableNumber(toTime(a.bid_ntce_dt), toTime(b.bid_ntce_dt), rule.direction);
          } else if (rule.key === "deadline") {
            result = compareNullableNumber(toTime(a.bid_clse_dt), toTime(b.bid_clse_dt), rule.direction);
          } else {
            result = compareNullableNumber(toNumber(amountValue(a)), toNumber(amountValue(b)), rule.direction);
          }
          if (result !== 0) return result;
        }
        return 0;
      })
    : [];

  const toggleSort = (nextKey: SortKey) => {
    setSortRules((prev) => {
      const existing = prev.find((rule) => rule.key === nextKey);
      if (!existing) {
        return [...prev, { key: nextKey, direction: "asc" }];
      }
      if (existing.direction === "asc") {
        return prev.map((rule) => (rule.key === nextKey ? { ...rule, direction: "desc" } : rule));
      }
      return prev.filter((rule) => rule.key !== nextKey);
    });
  };

  const sortRule = (key: SortKey) => sortRules.find((rule) => rule.key === key);

  const sortIcon = (key: SortKey) => {
    const rule = sortRule(key);
    if (!rule) return "↕";
    return rule.direction === "asc" ? "↑" : "↓";
  };

  const sortPriority = (key: SortKey) => {
    const index = sortRules.findIndex((rule) => rule.key === key);
    return index >= 0 && sortRules.length > 1 ? String(index + 1) : "";
  };

  const totalPages = result ? Math.max(1, Math.ceil(result.total_count / result.page_size)) : 1;
  const isMergedAllPagination = result?.pagination_mode === "merged_all";
  const canGoNext = result ? (isMergedAllPagination ? Boolean(result.has_next_page) : pageNo < totalPages) : false;
  const showPagination = result
    ? isMergedAllPagination
      ? pageNo > 1 || Boolean(result.has_next_page)
      : result.total_count > result.page_size
    : false;
  const resultCountText = result
    ? isMergedAllPagination
      ? `총 ${result.total_count.toLocaleString("ko-KR")}건 추정 중 ${sortedItems.length}건 표시 · ${pageNo}페이지`
      : `총 ${result.total_count.toLocaleString("ko-KR")}건 중 ${sortedItems.length}건 표시 · ${pageNo}/${totalPages}페이지`
    : "조회 결과가 여기에 표시됩니다.";
  const pageWindowStart = Math.max(1, Math.min(pageNo - 2, Math.max(1, totalPages - 4)));
  const pageNumbers = Array.from({ length: Math.min(5, totalPages) }, (_, index) => pageWindowStart + index).filter(
    (page) => page <= totalPages,
  );
  const aiOptions = optionsFromSettings(aiSettings);

  const onSave = async () => {
    if (!selectedNotice) return;
    const ok = window.confirm(
      "선택한 공고를 저장하고 백그라운드에서 첨부 PDF/DOCX 다운로드와 분석을 진행합니다. HWP/HWPX/XLSX는 메타데이터만 저장합니다.",
    );
    if (!ok) return;

    setSaving(true);
    try {
      await runWithOverlay(
        {
          title: "공고 저장 작업 등록 중",
          description: "선택한 공고를 저장하고 첨부파일 다운로드/분석 백그라운드 작업을 시작합니다.",
          steps: ["공고 상세 저장", "첨부파일 처리 작업 등록", "분석 파이프라인 시작", "상태 화면 준비"],
          successMessage: "공고 저장/분석 작업이 시작되었습니다.",
          failureMessage: "공고 저장 작업을 시작하지 못했습니다.",
        },
        async () => {
          const response = await api.saveAndAnalyzeNaraNotice(selectedNotice, aiSelection);
          setSavedNoticeId(response.notice.id);
          setError("");
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "공고 상세 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="content-stack" data-demo-id="demo-nara-board-page">
      <form className="surface-card form-card" onSubmit={onSubmit}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">나라장터 공고 검색</p>
            <h3>나라장터 공고 검색</h3>
            <p className="section-copy">
              기본 조회 기간은 오늘 기준 최근 3일입니다. 공고 1개를 선택한 뒤 저장하면 첨부 다운로드와 요약 파이프라인이 이어집니다.
            </p>
          </div>
          <Link to="/settings/integrations/nara" className="link-button link-button--soft">
            API 설정 확인
          </Link>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>검색어</span>
            <input
              value={keyword}
              data-demo-id="demo-nara-search-keyword"
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="공고명 기준 검색"
            />
          </label>
          <label className="field">
            <span>페이지 크기</span>
            <select value={pageSize} onChange={(e) => onPageSizeChange(Number(e.target.value))}>
              <option value={10}>10건</option>
              <option value={20}>20건</option>
              <option value={50}>50건</option>
              <option value={100}>100건</option>
            </select>
          </label>
          <label className="field">
            <span>업무유형</span>
            <select
              value={businessType}
              data-demo-id="demo-nara-business-type"
              onChange={(e) => setBusinessType(e.target.value as NaraBusinessType)}
            >
              {naraBusinessTypeOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>조회 시작일</span>
            <input
              type="date"
              value={startDate}
              data-demo-id="demo-nara-search-start-date"
              onChange={(e) => setStartDate(e.target.value)}
            />
          </label>
          <label className="field">
            <span>조회 종료일</span>
            <input
              type="date"
              value={endDate}
              data-demo-id="demo-nara-search-end-date"
              onChange={(e) => setEndDate(e.target.value)}
            />
          </label>
          <label className="field">
            <span>AI 분석 모델</span>
            <select value={selectionToKey(aiSelection)} onChange={(e) => onAiModelChange(e.target.value)}>
              {aiOptions.map((option) => (
                <option key={`${option.provider}:${option.model}`} value={`${option.provider}:${option.model}`}>
                  {option.label}
                  {option.recommended ? " 추천" : ""}
                  {option.configured ? "" : " · 키 미설정"}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" disabled={loading} data-demo-id="demo-nara-search-submit">
            {loading ? "조회 중..." : "공고 조회"}
          </button>
        </div>
      </form>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>나라장터 조회/저장을 완료하지 못했습니다.</strong>
          <p>{error}</p>
          <Link to="/settings/integrations/nara" className="link-button link-button--soft">
            나라장터 API 설정으로 이동
          </Link>
        </div>
      ) : null}

      {savedNoticeId ? (
        <div className="empty-state">
          <strong>공고 저장/분석 작업을 백그라운드로 시작했습니다.</strong>
          <p>다른 페이지로 이동해도 작업은 계속 진행됩니다. 저장한 공고 상세에서 처리 상태가 자동 갱신됩니다.</p>
          <Link to={`/nara-saved-notices/${savedNoticeId}`} className="link-button">
            처리 상태 보기
          </Link>
        </div>
      ) : null}

      {result?.partial_errors?.length ? (
        <div className="empty-state empty-state--warning nara-partial-warning" data-demo-id="demo-nara-partial-error">
          <strong>일부 업무유형 조회에 실패했습니다.</strong>
          <p>
            조회 가능한 공고는 표시했습니다. 실패 업무유형:{" "}
            {result.partial_errors.map((item) => businessTypeLabel(item.business_type)).join(", ")}
          </p>
        </div>
      ) : null}

      <div className="two-column-grid two-column-grid--wide-left">
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">검색 결과</p>
              <h3>공고 목록</h3>
              <p className="section-copy">{resultCountText}</p>
            </div>
          </div>

          {loading ? (
            <div className="empty-state">
              <strong>나라장터 API를 조회하는 중입니다.</strong>
              <p>공공데이터 API 응답 상태에 따라 몇 초 정도 걸릴 수 있습니다.</p>
            </div>
          ) : !result || result.items.length === 0 ? (
            <div className="empty-state">
              <strong>조회된 공고가 없습니다.</strong>
              <p>검색어 또는 조회 기간을 조정해보세요.</p>
            </div>
          ) : (
            <div className="nara-table-shell" data-demo-id="demo-nara-result-list">
              <div className="sticky-action-bar">
                <div>
                  <strong>{selectedNotice ? selectedNotice.bid_ntce_nm || "선택한 공고" : "공고를 1개 선택하세요"}</strong>
                  <span>
                    {selectedNotice
                      ? `${selectedNotice.bid_ntce_no}-${selectedNotice.bid_ntce_ord} · 첨부 ${selectedNotice.supported_attachment_count}/${selectedNotice.attachment_count}`
                      : "라디오 버튼으로 선택한 공고만 저장/분석됩니다."}
                  </span>
                </div>
                <button type="button" disabled={!selectedNotice || saving} onClick={onSave} data-demo-id="demo-nara-save-analyze">
                  {saving ? "작업 등록 중..." : "공고 상세 저장"}
                </button>
              </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>No.</th>
                    <th>선택</th>
                    <th>공고명</th>
                    <th>업무유형</th>
                    <th>기관</th>
                    <th>
                      <button type="button" className="table-sort-button" onClick={() => toggleSort("postedAt")}>
                        <span>등록 날짜</span>
                        <span className={`sort-icon ${sortRule("postedAt") ? "sort-icon--active" : ""}`}>
                          {sortIcon("postedAt")}
                        </span>
                        {sortPriority("postedAt") ? <span className="sort-priority">{sortPriority("postedAt")}</span> : null}
                      </button>
                    </th>
                    <th>
                      <button type="button" className="table-sort-button" onClick={() => toggleSort("deadline")}>
                        <span>마감</span>
                        <span className={`sort-icon ${sortRule("deadline") ? "sort-icon--active" : ""}`}>
                          {sortIcon("deadline")}
                        </span>
                        {sortPriority("deadline") ? <span className="sort-priority">{sortPriority("deadline")}</span> : null}
                      </button>
                    </th>
                    <th>
                      <button type="button" className="table-sort-button" onClick={() => toggleSort("amount")}>
                        <span>금액</span>
                        <span className={`sort-icon ${sortRule("amount") ? "sort-icon--active" : ""}`}>
                          {sortIcon("amount")}
                        </span>
                        {sortPriority("amount") ? <span className="sort-priority">{sortPriority("amount")}</span> : null}
                      </button>
                    </th>
                    <th>첨부</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedItems.map((item, index) => {
                    const key = `${item.bid_ntce_no}:${item.bid_ntce_ord}`;
                    return (
                      <tr key={key} onClick={() => setSelectedKey(key)} data-demo-id="demo-nara-result-row" data-demo-row-id={key}>
                        <td>{index + 1}</td>
                        <td>
                          <input
                            type="radio"
                            name="nara-notice"
                            checked={selectedKey === key}
                            onChange={() => setSelectedKey(key)}
                          />
                        </td>
                        <td>
                          <strong>{item.bid_ntce_nm || "-"}</strong>
                          <div className="table-subcopy">
                            {item.bid_ntce_no}-{item.bid_ntce_ord}
                          </div>
                        </td>
                        <td>
                          <span className="status-badge status-badge--muted">
                            {businessTypeLabel(item.business_type, item.business_type_label)}
                          </span>
                        </td>
                        <td>
                          {item.ntce_instt_nm || "-"}
                          <div className="table-subcopy">{item.dminstt_nm || "-"}</div>
                        </td>
                        <td>{formatDateTime(item.bid_ntce_dt)}</td>
                        <td>{formatDateTime(item.bid_clse_dt)}</td>
                        <td>{money(amountValue(item))}</td>
                        <td>
                          <span className="status-badge status-badge--active">
                            {item.supported_attachment_count}/{item.attachment_count}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            </div>
          )}

          {showPagination ? (
            <div className="pagination-bar">
              <button type="button" className="button-secondary" disabled={loading || pageNo <= 1} onClick={() => search(1, true)}>
                처음
              </button>
              <button
                type="button"
                className="button-secondary"
                disabled={loading || pageNo <= 1}
                onClick={() => search(pageNo - 1, true)}
              >
                이전
              </button>
              {isMergedAllPagination ? (
                <span className="pagination-current">{pageNo}페이지</span>
              ) : (
                <div className="pagination-pages" aria-label="공고 목록 페이지">
                  {pageNumbers.map((page) => (
                    <button
                      type="button"
                      key={page}
                      className={`pagination-page ${page === pageNo ? "pagination-page--active" : ""}`}
                      disabled={loading || page === pageNo}
                      onClick={() => search(page, true)}
                    >
                      {page}
                    </button>
                  ))}
                </div>
              )}
              <button
                type="button"
                className="button-secondary"
                disabled={loading || !canGoNext}
                onClick={() => search(pageNo + 1, true)}
              >
                다음
              </button>
              {!isMergedAllPagination ? (
                <button
                  type="button"
                  className="button-secondary"
                  disabled={loading || pageNo >= totalPages}
                  onClick={() => search(totalPages, true)}
                >
                  마지막
                </button>
              ) : null}
            </div>
          ) : null}
        </div>

        <aside className="surface-card accent-card--petal notice-preview-panel">
          <div className="notice-preview-panel__header">
            <p className="eyebrow">선택한 공고</p>
            <h3>상세 미리보기</h3>
          </div>
          {selectedNotice ? <div key={`${selectedKey}:loader`} className="notice-preview-loader" aria-hidden="true" /> : null}
          <div className="notice-preview-panel__body">
            {selectedNotice ? (
              <div key={selectedKey} className="notice-preview">
                <dl className="detail-list">
                  {previewRows(selectedNotice).map((row) => (
                    <div key={row.label}>
                      <dt>{row.label}</dt>
                      <dd>
                        {row.label === "원문 링크" ? (
                          <a href={row.value} target="_blank" rel="noreferrer" className="attachment-link">
                            나라장터 원문 열기
                          </a>
                        ) : (
                          row.value
                        )}
                      </dd>
                    </div>
                  ))}
                </dl>

                <details className="preview-details">
                  <summary>API 원본 주요값 보기</summary>
                  <pre className="analysis-pre">{JSON.stringify(selectedNotice.raw, null, 2)}</pre>
                </details>

                <h4>첨부파일</h4>
                {selectedNotice.attachments.length === 0 ? (
                  <p className="section-copy">첨부파일 메타데이터가 없습니다.</p>
                ) : (
                  <ul className="attachment-list">
                    {selectedNotice.attachments.map((attachment) => {
                      const previewUrl =
                        attachment.source_url && canPreviewInline(attachment.file_extension)
                          ? api.getNaraAttachmentPreviewUrl(attachment.source_url, attachment.file_name)
                          : attachment.source_url;
                      const actionLabel = canPreviewInline(attachment.file_extension) ? "브라우저 열기" : "다운로드";

                      return (
                        <li key={`${attachment.source_field}:${attachment.file_name}:${attachment.source_url}`}>
                          <span>
                            {previewUrl ? (
                              <a href={previewUrl} target="_blank" rel="noreferrer" className="attachment-link">
                                {attachment.file_name}
                              </a>
                            ) : (
                              attachment.file_name
                            )}
                          </span>
                          <span className="row">
                            <span className={`status-badge status-badge--${statusTone(attachment.support_status)}`}>
                              {attachment.support_status}
                            </span>
                            {previewUrl ? (
                              <a href={previewUrl} target="_blank" rel="noreferrer" className="link-button link-button--soft link-button--compact">
                                {actionLabel}
                              </a>
                            ) : (
                              <span className="status-badge status-badge--muted">URL 없음</span>
                            )}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            ) : (
              <p className="section-copy">목록에서 공고를 선택하면 상세 정보가 표시됩니다.</p>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
