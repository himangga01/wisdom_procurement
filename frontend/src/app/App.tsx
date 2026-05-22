import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AnalysisPage } from "../pages/AnalysisPage";
import { CorporationsPage } from "../pages/CorporationsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { NaraBoardPage } from "../pages/NaraBoardPage";
import { NoticeComparisonPage } from "../pages/NoticeComparisonPage";
import { NaraSavedNoticeDetailPage } from "../pages/NaraSavedNoticeDetailPage";
import { NaraSavedNoticesPage } from "../pages/NaraSavedNoticesPage";
import { ProjectsPage } from "../pages/ProjectsPage";
import { SettingsPage } from "../pages/SettingsPage";
import { WorkOverlayProvider } from "./workOverlay";

type NavItem = {
  to?: string;
  icon: string;
  label: string;
  note: string;
  disabled?: boolean;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    title: "업무 현황",
    items: [{ to: "/", icon: "OV", label: "대시보드", note: "오늘 처리할 일과 시스템 상태" }],
  },
  {
    title: "공고 업무",
    items: [
      { to: "/nara-board", icon: "NB", label: "나라장터 공고 검색", note: "API 조회, 선택 저장, 자동 분석" },
      { to: "/nara-saved-notices", icon: "SN", label: "저장한 공고", note: "저장 공고와 첨부 처리 상태" },
      { to: "/notice-comparison", icon: "PV", label: "부족조건 미리보기", note: "공고 요구조건과 법인 준비상태 비교" },
    ],
  },
  {
    title: "문서 분석",
    items: [{ to: "/documents", icon: "DC", label: "문서 업로드", note: "PDF/DOCX 업로드와 분석 이력" }],
  },
  {
    title: "기준문서 / RAG",
    items: [
      {
        icon: "RG",
        label: "기준문서 관리",
        note: "Phase 2에서 업로드/청킹/인덱싱 예정",
        disabled: true,
      },
    ],
  },
  {
    title: "내부 관리",
    items: [
      { to: "/corporations", icon: "CO", label: "법인 관리", note: "법인 정보와 기본 자격 맥락" },
      { to: "/projects", icon: "PR", label: "프로젝트 관리", note: "프로젝트 단위 업무 흐름" },
    ],
  },
  {
    title: "설정",
    items: [{ to: "/settings/integrations/nara", icon: "ST", label: "API 설정", note: "나라장터 API 키와 연결 상태" }],
  },
];

const pageMeta = [
  {
    match: (pathname: string) => pathname === "/",
    eyebrow: "Operations Overview",
    title: "오늘 처리할 조달 업무를 한눈에",
    description: "공고, 문서, 분석 상태를 운영형 대시보드로 정리해 다음 액션을 빠르게 찾습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/corporations"),
    eyebrow: "Corporation Workspace",
    title: "법인 기본 정보 관리",
    description: "향후 지원 가능성 판단에 필요한 법인 프로필을 안정적으로 관리합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/projects"),
    eyebrow: "Project Workflow",
    title: "프로젝트 중심 문서 이력",
    description: "공고 대응 업무를 프로젝트 단위로 묶어 문서와 분석 결과를 추적합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/documents"),
    eyebrow: "Document Analysis",
    title: "문서 업로드와 분석 관리",
    description: "PDF/DOCX 업로드, 분석 실행, 결과 확인 흐름을 한곳에서 관리합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/settings"),
    eyebrow: "Integration Settings",
    title: "외부 API 연결 상태",
    description: "나라장터 API 키는 전체 값을 노출하지 않고 설정 여부와 테스트 결과만 확인합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/nara-board"),
    eyebrow: "Nara Marketplace",
    title: "나라장터 공고 검색",
    description: "공공데이터 API에서 공고를 조회하고 선택한 공고를 저장해 분석합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/nara-saved-notices"),
    eyebrow: "Saved Notices",
    title: "저장한 공고 관리",
    description: "로컬 DB에 저장한 공고, 첨부 다운로드 상태, 분석 결과를 확인합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/notice-comparison"),
    eyebrow: "Gap Preview",
    title: "공고별 부족조건 미리보기",
    description: "저장 공고의 요구조건 후보와 법인 준비상태를 비교해 부족 가능성이 있는 항목을 먼저 확인합니다.",
  },
];

function getPageMeta(pathname: string) {
  return pageMeta.find((item) => item.match(pathname)) ?? pageMeta[0];
}

export function App() {
  const location = useLocation();
  const currentPage = getPageMeta(location.pathname);

  return (
    <WorkOverlayProvider>
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-card">
          <div className="brand-mark">SC</div>
          <div>
            <p className="eyebrow eyebrow--soft">SMART Procurement</p>
            <h1>SMART 조달청 계산기</h1>
            <p className="brand-copy">문서 분석, 공고 저장, 기준문서 확장을 위한 로컬 운영 포탈</p>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Primary Navigation">
          {navGroups.map((group) => (
            <div className="nav-section" key={group.title}>
              <p className="nav-section-title">{group.title}</p>
              {group.items.map((item) =>
                item.to ? (
                  <NavLink
                    key={item.label}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) => `nav-card${isActive ? " active" : ""}`}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span>
                      <span className="nav-label">{item.label}</span>
                      <span className="nav-note">{item.note}</span>
                    </span>
                  </NavLink>
                ) : (
                  <div key={item.label} className="nav-card nav-card--disabled" aria-disabled="true">
                    <span className="nav-icon">{item.icon}</span>
                    <span>
                      <span className="nav-label">{item.label}</span>
                      <span className="nav-note">{item.note}</span>
                    </span>
                  </div>
                ),
              )}
            </div>
          ))}
        </nav>

        <div className="sidebar-note">
          <p className="eyebrow eyebrow--soft">운영 순서</p>
          <ol className="mini-flow">
            <li>나라장터 공고를 검색합니다.</li>
            <li>필요한 공고를 저장해 분석합니다.</li>
            <li>프로젝트/법인 맥락으로 대응을 정리합니다.</li>
          </ol>
        </div>
      </aside>

      <main className="main">
        <header className="hero-panel">
          <div>
            <p className="eyebrow">{currentPage.eyebrow}</p>
            <h2>{currentPage.title}</h2>
            <p className="hero-description">{currentPage.description}</p>
          </div>
          <div className="hero-chip-group">
            <span className="hero-chip">Local PC</span>
            <span className="hero-chip hero-chip--petal">Phase 1.5</span>
            <span className="hero-chip hero-chip--leaf">RAG Ready Next</span>
          </div>
        </header>

        <section className="page-stage">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/corporations" element={<CorporationsPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/:documentId/analysis" element={<AnalysisPage />} />
            <Route path="/nara-board" element={<NaraBoardPage />} />
            <Route path="/nara-saved-notices" element={<NaraSavedNoticesPage />} />
            <Route path="/nara-saved-notices/:id" element={<NaraSavedNoticeDetailPage />} />
            <Route path="/notice-comparison" element={<NoticeComparisonPage />} />
            <Route path="/settings/integrations/nara" element={<SettingsPage />} />
          </Routes>
        </section>
      </main>
    </div>
    </WorkOverlayProvider>
  );
}
