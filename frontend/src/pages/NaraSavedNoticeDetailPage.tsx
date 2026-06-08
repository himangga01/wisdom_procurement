import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../app/api";
import {
  defaultSelection,
  loadStoredSelection,
  optionsFromSettings,
  keyToSelection,
  saveStoredSelection,
  selectionToKey,
} from "../app/aiModel";
import type { AiModelSelection, AiModelSettings, SavedNaraNotice } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

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

function parseJsonObject(value: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function isPipelineRunning(notice: SavedNaraNotice | null) {
  if (!notice) return false;
  return [notice.save_status, notice.download_status, notice.analysis_status].some((status) =>
    ["saving", "pending", "queued"].includes(status),
  );
}

export function NaraSavedNoticeDetailPage() {
  const { id } = useParams();
  const noticeId = Number(id);
  const { runWithOverlay } = useWorkOverlay();
  const [notice, setNotice] = useState<SavedNaraNotice | null>(null);
  const [aiSettings, setAiSettings] = useState<AiModelSettings | null>(null);
  const [aiSelection, setAiSelection] = useState<AiModelSelection>(defaultSelection());
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const refresh = async (showLoading = true) => {
    if (!noticeId) return;
    if (showLoading) {
      setLoading(true);
    }
    try {
      const data = await api.getSavedNaraNotice(noticeId);
      setNotice(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "저장 공고 상세를 불러오지 못했습니다.");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    refresh();
  }, [noticeId]);

  useEffect(() => {
    if (!isPipelineRunning(notice)) return;
    const timer = window.setInterval(() => {
      refresh(false);
    }, 2000);
    return () => window.clearInterval(timer);
  }, [noticeId, notice?.save_status, notice?.download_status, notice?.analysis_status]);

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

  const onReanalyze = async () => {
    if (!noticeId) return;
    setProcessing(true);
    try {
      await runWithOverlay(
        {
          title: "저장 공고 재분석 시작 중",
          description: "저장된 첨부 텍스트를 기준으로 AI 분석 작업을 다시 등록합니다.",
          steps: ["저장 공고 확인", "재분석 작업 등록", "상태 갱신"],
          successMessage: "저장 공고 재분석 작업이 시작되었습니다.",
          failureMessage: "저장 공고 재분석을 시작하지 못했습니다.",
        },
        async () => {
          const response = await api.reanalyzeSavedNaraNotice(noticeId, aiSelection);
          setNotice(response.notice);
          setError("");
        },
      );
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

  const aiOptions = optionsFromSettings(aiSettings);
  const summaryPayload = parseJsonObject(notice.analysis_summary_json);
  const noticeRequirements = objectValue(summaryPayload.notice_requirements);
  const requirementMoney = objectValue(noticeRequirements.money);
  const requirementDates = objectValue(noticeRequirements.dates);
  const hasRequirementCandidates = Object.keys(noticeRequirements).length > 0;
  const pipelineRunning = isPipelineRunning(notice);

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
          <select
            className="ai-model-select"
            value={selectionToKey(aiSelection)}
            onChange={(e) => onAiModelChange(e.target.value)}
            title="재분석에 사용할 AI 모델"
          >
            {aiOptions.map((option) => (
              <option key={`${option.provider}:${option.model}`} value={`${option.provider}:${option.model}`}>
                {option.label}
                {option.recommended ? " 추천" : ""}
                {option.configured ? "" : " · 키 미설정"}
              </option>
            ))}
          </select>
          <button type="button" onClick={onReanalyze} disabled={processing || pipelineRunning}>
            {processing || pipelineRunning ? "처리 중..." : "재분석"}
          </button>
          <Link to="/nara-saved-notices" className="link-button link-button--soft">
            목록
          </Link>
          <Link to={`/contracts?notice_id=${notice.id}`} className="link-button link-button--soft">
            계약서 초안 생성
          </Link>
        </div>
      </div>

      {error ? (
        <div className="empty-state empty-state--warning">
          <strong>작업을 완료하지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      {pipelineRunning ? (
        <div className="empty-state empty-state--info">
          <strong>백그라운드에서 저장/분석 작업이 진행 중입니다.</strong>
          <p>다른 페이지로 이동해도 서버 작업은 계속 진행됩니다. 이 화면은 2초마다 상태를 자동 갱신합니다.</p>
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

      {hasRequirementCandidates ? (
        <div className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Requirement Candidates</p>
              <h3>요구조건 구조화 후보</h3>
              <p className="section-copy">
                최종 자격 판단이 아니라 향후 비교에 필요한 요구조건 후보만 정리합니다.
              </p>
            </div>
          </div>
          <div className="requirement-candidate-grid">
            <article>
              <span>지역</span>
              <strong>{stringList(noticeRequirements.regions).join(", ") || "원문 확인 필요"}</strong>
            </article>
            <article>
              <span>면허/업종</span>
              <strong>{stringList(noticeRequirements.licenses).join(", ") || "원문 확인 필요"}</strong>
            </article>
            <article>
              <span>기업유형</span>
              <strong>{stringList(noticeRequirements.company_types).join(", ") || "원문 확인 필요"}</strong>
            </article>
            <article>
              <span>제출/증빙서류</span>
              <strong>{stringList(noticeRequirements.required_documents).join(", ") || "원문 확인 필요"}</strong>
            </article>
            <article>
              <span>추정가격</span>
              <strong>{String(requirementMoney.presmpt_prce || notice.presmpt_prce || "-")}</strong>
            </article>
            <article>
              <span>입찰마감</span>
              <strong>{String(requirementDates.bid_clse_dt || notice.bid_clse_dt || "-")}</strong>
            </article>
          </div>
          {stringList(noticeRequirements.requirement_lines).length ? (
            <ul className="requirement-lines">
              {stringList(noticeRequirements.requirement_lines).slice(0, 6).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <details className="surface-card">
        <summary>API 원본 JSON 보기</summary>
        <pre className="analysis-pre">{parseJson(notice.raw_json)}</pre>
      </details>
    </section>
  );
}
