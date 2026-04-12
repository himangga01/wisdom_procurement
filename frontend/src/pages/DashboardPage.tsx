import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../app/api";
import type { DashboardSummary } from "../app/types";

function getNextAction(summary: DashboardSummary) {
  if (summary.corporation_count === 0) {
    return {
      title: "법인 등록부터 시작해보세요",
      description: "판단 엔진의 기준이 되는 기본 정보가 아직 없어서, 먼저 법인 프로필을 만드는 흐름이 가장 자연스럽습니다.",
      action: "/corporations",
      actionLabel: "법인 등록하러 가기",
    };
  }

  if (summary.project_count === 0) {
    return {
      title: "이제 프로젝트를 만들어야 문서 이력이 쌓입니다",
      description: "프로젝트를 먼저 만들면 같은 공고 관련 파일과 결과를 하나의 업무 단위로 정리할 수 있습니다.",
      action: "/projects",
      actionLabel: "프로젝트 만들기",
    };
  }

  if (summary.document_count === 0) {
    return {
      title: "프로젝트에 문서를 업로드해 분석을 시작하세요",
      description: "문서 유형과 메모를 함께 남기면 나중에 다시 봐도 문맥이 유지됩니다.",
      action: "/documents",
      actionLabel: "문서 업로드하기",
    };
  }

  return {
    title: "분석 결과를 확인하며 다음 액션을 정리해보세요",
    description: "현재 Phase 1 포탈은 업로드 이력과 요약 결과를 빠르게 훑어보는 데 가장 잘 맞춰져 있습니다.",
    action: "/documents",
    actionLabel: "문서 이력 보러 가기",
  };
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>({
    corporation_count: 0,
    project_count: 0,
    document_count: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getDashboard()
      .then((data) => setSummary(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const nextAction = getNextAction(summary);

  return (
    <section className="content-stack">
      <div className="spotlight-card">
        <div>
          <p className="eyebrow">Today&apos;s Flow</p>
          <h3>지금 무엇을 해야 하는지 먼저 보이게</h3>
          <p className="section-copy">
            현재 포탈은 문서 검토를 더 빠르게 이어가기 위한 1단계 MVP입니다. 오늘 필요한 작업부터 바로 이어질 수 있도록 대시보드 문맥을 강화했습니다.
          </p>
        </div>
        <div className="callout-card">
          <strong>{nextAction.title}</strong>
          <p>{nextAction.description}</p>
          <Link to={nextAction.action} className="link-button">
            {nextAction.actionLabel}
          </Link>
        </div>
      </div>

      <div className="stats-grid">
        <article className="metric-card">
          <span className="metric-label">등록된 법인</span>
          <strong className="metric-value">{loading ? "-" : summary.corporation_count}</strong>
          <p className="metric-copy">판단과 프로젝트의 기준이 되는 기본 주체입니다.</p>
        </article>
        <article className="metric-card metric-card--petal">
          <span className="metric-label">운영 중 프로젝트</span>
          <strong className="metric-value">{loading ? "-" : summary.project_count}</strong>
          <p className="metric-copy">파일보다 위에 있는 업무 단위로 이력이 정리됩니다.</p>
        </article>
        <article className="metric-card metric-card--leaf">
          <span className="metric-label">누적 문서</span>
          <strong className="metric-value">{loading ? "-" : summary.document_count}</strong>
          <p className="metric-copy">업로드 문서가 많아질수록 검색과 문맥 구분이 중요해집니다.</p>
        </article>
      </div>

      <div className="two-column-grid">
        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Phase 1 Scope</p>
              <h3>현재 가능한 작업</h3>
            </div>
          </div>
          <ul className="feature-list">
            <li>법인 등록과 기본 정보 관리</li>
            <li>프로젝트 생성 및 연결 관계 유지</li>
            <li>PDF/DOCX 문서 업로드</li>
            <li>AI 요약 결과 확인과 재분석</li>
          </ul>
        </article>

        <article className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Workflow Guide</p>
              <h3>추천 운영 순서</h3>
            </div>
          </div>
          <ol className="step-list">
            <li>법인 페이지에서 기본 프로필을 먼저 만듭니다.</li>
            <li>프로젝트 페이지에서 문서를 묶을 업무 단위를 생성합니다.</li>
            <li>문서 업로드 화면에서 파일과 메모를 함께 남깁니다.</li>
            <li>분석 결과 화면에서 핵심 요구사항을 빠르게 검토합니다.</li>
          </ol>
        </article>
      </div>
    </section>
  );
}
