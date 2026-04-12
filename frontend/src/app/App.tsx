import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AnalysisPage } from "../pages/AnalysisPage";
import { CorporationsPage } from "../pages/CorporationsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { ProjectsPage } from "../pages/ProjectsPage";

const navItems = [
  { to: "/", label: "대시보드", note: "오늘 해야 할 일과 전체 현황" },
  { to: "/corporations", label: "법인 관리", note: "법인 정보와 기본 자격 맥락" },
  { to: "/projects", label: "프로젝트 관리", note: "프로젝트 단위로 업무 흐름 구성" },
  { to: "/documents", label: "문서 업로드", note: "분석 대상 파일 업로드와 이력 관리" },
];

const pageMeta = [
  {
    match: (pathname: string) => pathname === "/",
    eyebrow: "Phase 1 MVP",
    title: "산뜻하게 정리하는 조달 포탈",
    description: "법인 등록, 프로젝트 생성, 문서 업로드, 분석 확인까지 한 흐름으로 이어집니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/corporations"),
    eyebrow: "Corporation Workspace",
    title: "법인 기본 정보를 먼저 단단하게",
    description: "법인 정보가 이후 판단 엔진의 기준이 되므로, 실무에서 자주 보는 항목을 빠르게 정리할 수 있게 구성했습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/projects"),
    eyebrow: "Project Workflow",
    title: "프로젝트 중심으로 문서 이력 관리",
    description: "파일이 아니라 프로젝트를 기준으로 흐름을 잡아, 나중에 근거와 결과를 다시 찾기 쉽도록 개선했습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/documents"),
    eyebrow: "Upload + Analysis",
    title: "업로드부터 분석까지 한 화면에서",
    description: "파일 선택 전에 프로젝트와 문서 성격을 명확히 고르게 해서, 나중에 이력이 더 읽기 쉬워지도록 다듬었습니다.",
  },
];

function getPageMeta(pathname: string) {
  return pageMeta.find((item) => item.match(pathname)) ?? pageMeta[0];
}

export function App() {
  const location = useLocation();
  const currentPage = getPageMeta(location.pathname);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-card">
          <div className="brand-mark">SC</div>
          <div>
            <p className="eyebrow eyebrow--soft">SMART Procurement</p>
            <h1>SMART 조달청 계산기</h1>
            <p className="brand-copy">
              벚꽃 시즌처럼 산뜻한 흐름으로 문서를 정리하고, 다음 액션을 더 빨리 보이게 만드는 Phase 1 포탈입니다.
            </p>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Primary Navigation">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"} className="nav-card">
              <span className="nav-label">{item.label}</span>
              <span className="nav-note">{item.note}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-note">
          <p className="eyebrow eyebrow--soft">추천 흐름</p>
          <ol className="mini-flow">
            <li>법인을 먼저 등록합니다.</li>
            <li>프로젝트를 만든 뒤 대상 문서를 업로드합니다.</li>
            <li>분석 결과에서 핵심 요구사항과 리스크를 검토합니다.</li>
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
            <span className="hero-chip">Single Admin</span>
            <span className="hero-chip hero-chip--petal">Project First</span>
            <span className="hero-chip hero-chip--leaf">AI Summary Ready</span>
          </div>
        </header>

        <section className="page-stage">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/corporations" element={<CorporationsPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/:documentId/analysis" element={<AnalysisPage />} />
          </Routes>
        </section>
      </main>
    </div>
  );
}
