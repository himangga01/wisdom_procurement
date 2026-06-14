import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../app/api";
import {
  defaultSelection,
  loadStoredSelection,
  optionsFromSettings,
  keyToSelection,
  saveStoredSelection,
  selectionToKey,
} from "../app/aiModel";
import type { AiModelSelection, AiModelSettings, AnalysisRecord } from "../app/types";
import { useWorkOverlay } from "../app/workOverlay";

type ParsedAnalysis = {
  document_summary?: string;
  key_dates?: string[];
  requirements?: string[];
  required_documents?: string[];
  risks?: string[];
  questions_to_check?: string[];
  confidence_note?: string;
};

function parseJsonSafely(raw: string): ParsedAnalysis {
  try {
    return JSON.parse(raw) as ParsedAnalysis;
  } catch {
    return {};
  }
}

function parseUsage(raw: string) {
  try {
    return JSON.parse(raw) as { provider?: string; model?: string; input_chars?: number };
  } catch {
    return {};
  }
}

export function AnalysisPage() {
  const { documentId } = useParams();
  const { runWithOverlay } = useWorkOverlay();
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null);
  const [aiSettings, setAiSettings] = useState<AiModelSettings | null>(null);
  const [aiSelection, setAiSelection] = useState<AiModelSelection>(defaultSelection());
  const [error, setError] = useState("");
  const [reloading, setReloading] = useState(false);

  const loadAnalysis = async () => {
    if (!documentId) return;
    try {
      const data = await api.getLatestAnalysisByDocument(Number(documentId));
      setAnalysis(data);
      setError("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "분석 결과를 불러오지 못했습니다.";
      setError(message);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, [documentId]);

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
    if (!documentId) return;
    setReloading(true);
    try {
      await runWithOverlay(
        {
          title: "문서 재분석 중",
          description: "선택한 AI 모델로 요약 결과를 다시 생성합니다.",
          steps: ["재분석 요청", "AI 요약 생성", "분석 캐시 갱신", "결과 다시 불러오기"],
          successMessage: "문서 재분석이 완료되었습니다.",
          failureMessage: "문서 재분석을 완료하지 못했습니다.",
          minVisibleMs: 650,
        },
        async () => {
          await api.reanalyzeDocument(Number(documentId), aiSelection);
          await loadAnalysis();
          setError("");
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "재분석에 실패했습니다.");
    } finally {
      setReloading(false);
    }
  };

  const parsed = analysis ? parseJsonSafely(analysis.output_json) : {};
  const usage = analysis ? parseUsage(analysis.token_usage_json) : {};
  const aiOptions = optionsFromSettings(aiSettings);

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">분석 결과</p>
          <h3>한눈에 보는 문서 요약 결과</h3>
          <p className="section-copy">
            기존에는 마크다운 원문만 보여서 다시 읽는 부담이 컸습니다. 지금은 핵심 요약, 요구사항, 확인 포인트를 카드 단위로 나눠 빠르게 검토할 수 있게 바꿨습니다.
          </p>
        </div>
        <div className="toolbar">
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
          <span className="status-badge status-badge--active">{analysis?.status ?? "not-ready"}</span>
          <button type="button" onClick={onReanalyze} disabled={reloading || !documentId}>
            {reloading ? "재분석 중..." : "재분석"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="empty-state">
          <strong>분석 결과를 찾지 못했습니다.</strong>
          <p>{error}</p>
        </div>
      ) : null}

      {analysis ? (
        <>
          <div className="stats-grid">
            <article className="metric-card">
              <span className="metric-label">모델</span>
              <strong className="metric-value metric-value--small">{analysis.model_name}</strong>
              <p className="metric-copy">현재 결과를 생성한 분석 모델입니다.</p>
            </article>
            <article className="metric-card metric-card--petal">
              <span className="metric-label">입력 문자 수</span>
              <strong className="metric-value metric-value--small">{usage.input_chars ?? "-"}</strong>
              <p className="metric-copy">정규화 후 분석에 사용된 텍스트 길이입니다.</p>
            </article>
            <article className="metric-card metric-card--leaf">
              <span className="metric-label">신뢰도 메모</span>
              <strong className="metric-value metric-value--small">
                {parsed.confidence_note ? "확인 가능" : "미기록"}
              </strong>
              <p className="metric-copy">{parsed.confidence_note || "신뢰도 메모가 아직 없습니다."}</p>
            </article>
          </div>

          <div className="analysis-grid">
            <article className="surface-card">
              <p className="eyebrow">요약</p>
              <h3>핵심 요약</h3>
              <p className="analysis-copy">{parsed.document_summary || "요약 텍스트가 없습니다."}</p>
            </article>

            <article className="surface-card">
              <p className="eyebrow">요구사항</p>
              <h3>주요 요구사항</h3>
              {parsed.requirements?.length ? (
                <ul className="feature-list">
                  {parsed.requirements.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">추출된 요구사항이 없습니다.</p>
              )}
            </article>

            <article className="surface-card">
              <p className="eyebrow">확인 포인트</p>
              <h3>추가 확인 포인트</h3>
              {parsed.questions_to_check?.length ? (
                <ul className="feature-list">
                  {parsed.questions_to_check.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">추가 확인 포인트가 없습니다.</p>
              )}
            </article>
          </div>

          <article className="surface-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">원본 출력</p>
                <h3>원본 분석 출력</h3>
              </div>
            </div>
            <pre className="analysis-pre">{analysis.output_markdown}</pre>
          </article>
        </>
      ) : (
        <div className="empty-state">
          <strong>아직 분석 결과가 없습니다.</strong>
          <p>문서 이력 화면에서 먼저 분석을 실행하면 결과가 여기에 표시됩니다.</p>
        </div>
      )}
    </section>
  );
}
