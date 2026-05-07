import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../app/api";
import type { SavedNaraNotice } from "../app/types";

function statusTone(status: string) {
  if (status === "completed" || status === "saved") return "active";
  if (status === "pending" || status === "partial_failed" || status === "saving") return "pending";
  return "muted";
}

function parseJson(value: string) {
  try {
    return JSON.stringify(JSON.parse(value || "{}"), null, 2);
  } catch {
    return value || "{}";
  }
}

export function NaraSavedNoticeDetailPage() {
  const { id } = useParams();
  const noticeId = Number(id);
  const [notice, setNotice] = useState<SavedNaraNotice | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    if (!noticeId) return;
    setLoading(true);
    try {
      const data = await api.getSavedNaraNotice(noticeId);
      setNotice(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장 공고 상세를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [noticeId]);

  const onReanalyze = async () => {
    if (!noticeId) return;
    setProcessing(true);
    try {
      const response = await api.reanalyzeSavedNaraNotice(noticeId);
      setNotice(response.notice);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "공고 재분석에 실패했습니다.");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <section className="content-stack">
        <div className="empty-state">
          <strong>저장 공고 상세를 불러오는 중입니다.</strong>
          <p>첨부 상태와 분석 결과를 정리하고 있습니다.</p>
        </div>
      </section>
    );
  }

  if (!notice) {
    return (
      <section className="content-stack">
        <div className="empty-state empty-state--warning">
          <strong>저장 공고를 찾지 못했습니다.</strong>
          <p>{error || "삭제되었거나 존재하지 않는 공고입니다."}</p>
          <Link to="/nara-saved-notices" className="link-button link-button--soft">
            저장한 공고로 이동
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">Saved Notice Detail</p>
          <h3>{notice.bid_ntce_nm || "저장 공고"}</h3>
          <p className="analysis-copy">
            {notice.bid_ntce_no}-{notice.bid_ntce_ord} / {notice.ntce_instt_nm || "-"} / {notice.dminstt_nm || "-"}
          </p>
        </div>
        <div className="row">
          <button type="button" onClick={onReanalyze} disabled={processing}>
            {processing ? "재분석 중..." : "재분석"}
          </button>
          <Link to="/nara-saved-notices" className="link-button link-button--soft">
            목록
          </Link>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      <div className="analysis-grid">
        <div className="surface-card">
          <p className="eyebrow">Metadata</p>
          <h3>공고 기본정보</h3>
          <dl className="detail-list">
            <div>
              <dt>공고일시</dt>
              <dd>{notice.bid_ntce_dt || "-"}</dd>
            </div>
            <div>
              <dt>입찰마감</dt>
              <dd>{notice.bid_clse_dt || "-"}</dd>
            </div>
            <div>
              <dt>개찰일시</dt>
              <dd>{notice.openg_dt || "-"}</dd>
            </div>
            <div>
              <dt>추정가격</dt>
              <dd>{notice.presmpt_prce || notice.bdgt_amt || "-"}</dd>
            </div>
            <div>
              <dt>지역/면허</dt>
              <dd>{[notice.region_text, notice.license_text].filter(Boolean).join(" / ") || "-"}</dd>
            </div>
          </dl>
        </div>

        <div className="surface-card">
          <p className="eyebrow">Pipeline</p>
          <h3>처리 상태</h3>
          <div className="status-stack">
            <span className={`status-badge status-badge--${statusTone(notice.save_status)}`}>
              저장: {notice.save_status}
            </span>
            <span className={`status-badge status-badge--${statusTone(notice.download_status)}`}>
              다운로드: {notice.download_status}
            </span>
            <span className={`status-badge status-badge--${statusTone(notice.analysis_status)}`}>
              분석: {notice.analysis_status}
            </span>
          </div>
        </div>
      </div>

      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Attachments</p>
            <h3>첨부파일 처리 결과</h3>
          </div>
        </div>
        {!notice.attachments || notice.attachments.length === 0 ? (
          <div className="empty-state">
            <strong>저장된 첨부파일 메타데이터가 없습니다.</strong>
            <p>API 응답에 첨부 URL이 없거나 아직 처리되지 않았습니다.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>파일명</th>
                  <th>확장자</th>
                  <th>지원</th>
                  <th>다운로드</th>
                  <th>파싱</th>
                  <th>메모</th>
                </tr>
              </thead>
              <tbody>
                {notice.attachments.map((attachment) => (
                  <tr key={attachment.id}>
                    <td>
                      <strong>{attachment.file_name || "-"}</strong>
                      <div className="table-subcopy">{attachment.source_field}</div>
                    </td>
                    <td>{attachment.file_extension || "-"}</td>
                    <td>{attachment.support_status}</td>
                    <td>{attachment.download_status}</td>
                    <td>{attachment.parse_status}</td>
                    <td>{attachment.error_message || attachment.extracted_text_preview || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="surface-card">
        <p className="eyebrow">AI Summary</p>
        <h3>공고 분석 요약</h3>
        <pre className="analysis-pre">{notice.analysis_summary_markdown || "아직 분석 결과가 없습니다."}</pre>
      </div>

      <details className="surface-card">
        <summary>API 원본 JSON 보기</summary>
        <pre className="analysis-pre">{parseJson(notice.raw_json)}</pre>
      </details>
    </section>
  );
}
