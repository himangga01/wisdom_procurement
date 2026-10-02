import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../app/api";
import type { AnalysisRecord, BasisDocumentBundle } from "../app/types";

const DIRECT_PRODUCTION_CATEGORY = "direct_production_certificate";
const DIRECT_PRODUCTION_KEYWORDS = ["직접생산", "직생", "직접생산확인증명"];

type ParsedAnalysis = {
  document_summary?: string;
  bidder_qualification_summary?: string;
  qualification_requirements?: string[];
  disqualification_or_limitations?: string[];
  required_documents?: string[];
  key_dates?: string[];
  questions_to_check?: string[];
  confidence_note?: string;
  requirements?: string[];
  risks?: string[];
};

type ParsedBasisAnalysis = {
  document_summary?: string;
  qualification_requirements?: string[];
  production_requirements?: string[];
  facility_requirements?: string[];
  personnel_requirements?: string[];
  required_documents?: string[];
  confidence_note?: string;
};

function parseJsonSafely<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function parseUsage(raw: string) {
  try {
    return JSON.parse(raw) as { provider?: string; model?: string; input_chars?: number };
  } catch {
    return {};
  }
}

function mergeLists(...lists: Array<string[] | undefined>): string[] {
  const seen = new Set<string>();
  const merged: string[] = [];

  for (const list of lists) {
    for (const item of list ?? []) {
      const cleaned = item.trim();
      if (!cleaned) continue;

      const key = cleaned.toLowerCase();
      if (seen.has(key)) continue;

      seen.add(key);
      merged.push(cleaned);
    }
  }

  return merged;
}

function includesDirectProduction(items: string[]) {
  return items.some((item) =>
    DIRECT_PRODUCTION_KEYWORDS.some((keyword) => item.toLowerCase().includes(keyword.toLowerCase())),
  );
}

function compact(items: string[], max = 5) {
  return items.slice(0, max);
}

function pickFirst(items: string[]) {
  return items[0] ?? "";
}

export function AnalysisPage() {
  const { documentId } = useParams();
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null);
  const [basisBundle, setBasisBundle] = useState<BasisDocumentBundle | null>(null);
  const [error, setError] = useState("");
  const [basisError, setBasisError] = useState("");
  const [reloading, setReloading] = useState(false);

  const loadBasis = async (shouldLoad: boolean) => {
    if (!shouldLoad) {
      setBasisBundle(null);
      setBasisError("");
      return;
    }

    try {
      const data = await api.getLatestBasisByCategory(DIRECT_PRODUCTION_CATEGORY);
      setBasisBundle(data);
      setBasisError("");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "기준문서 분석 결과를 불러오지 못했습니다.";
      setBasisBundle(null);
      setBasisError(message);
    }
  };

  const loadAnalysis = async () => {
    if (!documentId) return;

    try {
      const data = await api.getLatestAnalysisByDocument(Number(documentId));
      setAnalysis(data);
      setError("");

      const parsed = parseJsonSafely<ParsedAnalysis>(data.output_json) ?? {};
      const qualificationRequirements = mergeLists(
        parsed.qualification_requirements,
        parsed.requirements,
      );
      const requiredDocuments = mergeLists(parsed.required_documents);
      const shouldLoadBasis = includesDirectProduction([
        ...qualificationRequirements,
        ...requiredDocuments,
        parsed.bidder_qualification_summary ?? "",
      ]);

      await loadBasis(shouldLoadBasis);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "분석 결과를 불러오지 못했습니다.";
      setError(message);
    }
  };

  useEffect(() => {
    void loadAnalysis();
  }, [documentId]);

  const onReanalyze = async () => {
    if (!documentId) return;

    setReloading(true);
    try {
      await api.reanalyzeDocument(Number(documentId));
      await loadAnalysis();
    } finally {
      setReloading(false);
    }
  };

  const parsed = analysis ? parseJsonSafely<ParsedAnalysis>(analysis.output_json) ?? {} : {};
  const usage = analysis ? parseUsage(analysis.token_usage_json) : {};
  const parsedBasis =
    basisBundle?.analysis ? parseJsonSafely<ParsedBasisAnalysis>(basisBundle.analysis.output_json) ?? {} : {};

  const qualificationRequirements = mergeLists(
    parsed.qualification_requirements,
    parsed.requirements,
  );
  const limitationItems = mergeLists(
    parsed.disqualification_or_limitations,
    parsed.risks,
  );
  const requiredDocuments = mergeLists(parsed.required_documents);
  const keyDates = mergeLists(parsed.key_dates);
  const questionsToCheck = mergeLists(parsed.questions_to_check);

  const needsDirectProductionBasis = includesDirectProduction([
    ...qualificationRequirements,
    ...requiredDocuments,
    parsed.bidder_qualification_summary ?? "",
  ]);

  const directProductionQualification = pickFirst(
    mergeLists(parsedBasis.qualification_requirements),
  );
  const directProductionProcess = pickFirst(mergeLists(parsedBasis.production_requirements));
  const directProductionFacility = pickFirst(mergeLists(parsedBasis.facility_requirements));
  const directProductionPersonnel = pickFirst(mergeLists(parsedBasis.personnel_requirements));
  const directProductionDocuments = compact(mergeLists(parsedBasis.required_documents), 3);

  const qualificationSummary =
    parsed.bidder_qualification_summary ||
    (qualificationRequirements.length
      ? qualificationRequirements.slice(0, 2).join(" / ")
      : "입찰참가자격 관련 핵심 문구를 다시 확인해 주세요.");

  const analysisSource =
    usage.provider === "fallback"
      ? "Fallback"
      : usage.model || analysis?.model_name || "-";

  return (
    <section className="content-stack">
      <div className="surface-card analysis-hero">
        <div>
          <p className="eyebrow">Bid Qualification Focus</p>
          <h3>자격요건 중심 분석</h3>
          <p className="section-copy">
            공고에서 확인해야 할 자격요건을 먼저 보여주고, 직접생산확인증명서가
            필요한 경우에만 관련 발급 요건을 짧게 덧붙여 보여줍니다.
          </p>
        </div>
        <div className="toolbar">
          <span className="status-badge status-badge--active">
            {analysis?.status ?? "not-ready"}
          </span>
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
              <span className="metric-label">분석 소스</span>
              <strong className="metric-value metric-value--small">{analysisSource}</strong>
              <p className="metric-copy">현재 결과를 생성한 분석 소스입니다.</p>
            </article>
            <article className="metric-card metric-card--petal">
              <span className="metric-label">자격요건 수</span>
              <strong className="metric-value metric-value--small">{qualificationRequirements.length}</strong>
              <p className="metric-copy">공고에서 추출된 자격요건 항목 수입니다.</p>
            </article>
            <article className="metric-card metric-card--leaf">
              <span className="metric-label">신뢰도 메모</span>
              <strong className="metric-value metric-value--small">{analysis.prompt_version}</strong>
              <p className="metric-copy">
                {parsed.confidence_note || "원문 조항을 함께 확인해 주세요."}
              </p>
            </article>
          </div>

          <article className="surface-card accent-card accent-card--petal">
            <p className="eyebrow">Qualification Snapshot</p>
            <h3>핵심 자격요건 요약</h3>
            <p className="analysis-copy">{qualificationSummary}</p>
          </article>

          <div className="analysis-grid">
            <article className="surface-card">
              <p className="eyebrow">Qualification Requirements</p>
              <h3>입찰참가자격</h3>
              {qualificationRequirements.length ? (
                <ul className="feature-list">
                  {qualificationRequirements.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">자격요건이 명확히 추출되지 않았습니다.</p>
              )}
            </article>

            <article className="surface-card">
              <p className="eyebrow">Required Documents</p>
              <h3>제출서류</h3>
              {requiredDocuments.length ? (
                <ul className="feature-list">
                  {requiredDocuments.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">제출서류가 명확히 추출되지 않았습니다.</p>
              )}
            </article>

            <article className="surface-card">
              <p className="eyebrow">Limitations</p>
              <h3>제한 또는 유의 사항</h3>
              {limitationItems.length ? (
                <ul className="feature-list">
                  {limitationItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">제한 사항이 별도로 추출되지 않았습니다.</p>
              )}
            </article>

            <article className="surface-card">
              <p className="eyebrow">Checkpoints</p>
              <h3>추가 확인 포인트</h3>
              {questionsToCheck.length ? (
                <ul className="feature-list">
                  {questionsToCheck.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="analysis-copy">추가 확인 포인트가 없습니다.</p>
              )}
            </article>
          </div>

          {needsDirectProductionBasis ? (
            <article className="surface-card accent-card accent-card--leaf">
              <p className="eyebrow">Direct Production Certificate</p>
              <h3>직접생산확인증명서 발급 요건</h3>
              <p className="section-copy">
                공고 자격요건에 직접생산확인증명서가 보여서, 기준문서에서 지금 바로
                확인할 핵심 요건과 준비서류만 간단히 가져왔습니다.
              </p>

              {basisBundle?.analysis ? (
                <div className="analysis-grid">
                  <article className="surface-card">
                    <p className="eyebrow">Issuance Requirements</p>
                    <h3>핵심 확인 항목</h3>
                    {directProductionProcess ||
                    directProductionFacility ||
                    directProductionPersonnel ||
                    directProductionQualification ? (
                      <ul className="feature-list">
                        {directProductionQualification ? (
                          <li>기본요건: {directProductionQualification}</li>
                        ) : null}
                        {directProductionProcess ? (
                          <li>생산공정: {directProductionProcess}</li>
                        ) : null}
                        {directProductionFacility ? (
                          <li>시설: {directProductionFacility}</li>
                        ) : null}
                        {directProductionPersonnel ? (
                          <li>인력: {directProductionPersonnel}</li>
                        ) : null}
                      </ul>
                    ) : (
                      <p className="analysis-copy">기준문서에서 요건을 명확히 추출하지 못했습니다.</p>
                    )}
                  </article>

                  <article className="surface-card">
                    <p className="eyebrow">Basis Documents</p>
                    <h3>준비서류 3개</h3>
                    {directProductionDocuments.length ? (
                      <ul className="feature-list">
                        {directProductionDocuments.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="analysis-copy">기준문서상 준비서류가 추출되지 않았습니다.</p>
                    )}
                  </article>
                </div>
              ) : (
                <div className="empty-state">
                  <strong>직접생산확인증명 기준문서 요약을 아직 불러오지 못했습니다.</strong>
                  <p>{basisError || "기준문서 분석이 준비되면 이곳에 발급 요건만 표시됩니다."}</p>
                </div>
              )}
            </article>
          ) : null}

          {keyDates.length ? (
            <article className="surface-card">
              <p className="eyebrow">Schedule Notes</p>
              <h3>일정 메모</h3>
              <ul className="feature-list">
                {keyDates.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ) : null}
        </>
      ) : (
        <div className="empty-state">
          <strong>아직 분석 결과가 없습니다.</strong>
          <p>문서 업로드 화면에서 분석을 실행하면 이곳에서 결과를 확인할 수 있습니다.</p>
        </div>
      )}
    </section>
  );
}
