import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AnalysisPage } from "../pages/AnalysisPage";
import { BasisDocumentsPage } from "../pages/BasisDocumentsPage";
import { CorporationsPage } from "../pages/CorporationsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { ProjectsPage } from "../pages/ProjectsPage";

const navItems = [
  { to: "/", label: "대시보드", note: "현재 단계와 다음 작업 흐름 확인" },
  { to: "/corporations", label: "법인 관리", note: "법인 기본 정보와 인증 현황 정리" },
  { to: "/projects", label: "프로젝트 관리", note: "프로젝트 단위로 문서와 검토 흐름 관리" },
  { to: "/documents", label: "문서 업로드", note: "공고문과 첨부 문서를 업로드하고 분석" },
  { to: "/basis-documents", label: "기준문서", note: "직접생산확인증명 등 기준 PDF 별도 관리" },
];

const pageMeta = [
  {
    match: (pathname: string) => pathname === "/",
    eyebrow: "Phase 1 MVP",
    title: "조달 검토 흐름을 한 번에 정리하는 로컬 포털",
    description:
      "법인 등록부터 프로젝트 생성, 공고 문서 분석, 기준문서 참고까지 한 흐름에서 볼 수 있도록 구성했습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/corporations"),
    eyebrow: "Corporation Workspace",
    title: "법인 현황을 먼저 정리해 두는 화면",
    description:
      "입찰참가자격 검토에 자주 쓰이는 법인 기본 정보와 인증 현황을 먼저 정리할 수 있습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/projects"),
    eyebrow: "Project Workflow",
    title: "프로젝트 기준으로 문서와 검토 이력을 관리",
    description:
      "파일 단위가 아니라 프로젝트 단위로 흐름을 묶어야 공고, 첨부, 분석 결과를 다시 찾기 쉽습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/documents"),
    eyebrow: "Upload + Analysis",
    title: "공고 문서를 올리고 입찰참가자격 중심으로 분석",
    description:
      "문서 업로드 이후 바로 자격 요건, 제출서류, 기준문서 참고 정보까지 이어서 확인할 수 있습니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/basis-documents"),
    eyebrow: "Basis Library",
    title: "직접생산확인증명 기준문서를 별도로 관리",
    description:
      "공고 문서와 분리된 기준문서를 업로드하고 분석해 두면 여러 프로젝트에서 재사용할 수 있습니다.",
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
              공고 문서와 기준문서를 분리해 관리하면서, 입찰참가자격 검토를 빠르게
              이어갈 수 있도록 만든 로컬형 조달 분석 포털입니다.
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
          <p className="eyebrow eyebrow--soft">권장 순서</p>
          <ol className="mini-flow">
            <li>법인 정보를 먼저 등록합니다.</li>
            <li>프로젝트를 만들고 공고 문서를 업로드합니다.</li>
            <li>기준문서 메뉴에서 직접생산확인증명 기준 PDF를 관리합니다.</li>
            <li>분석 화면에서 공고 요구사항과 기준문서를 함께 검토합니다.</li>
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
            <span className="hero-chip">Single PC</span>
            <span className="hero-chip hero-chip--petal">Project Documents</span>
            <span className="hero-chip hero-chip--leaf">Basis Documents</span>
          </div>
        </header>

        <section className="page-stage">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/corporations" element={<CorporationsPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/basis-documents" element={<BasisDocumentsPage />} />
            <Route path="/documents/:documentId/analysis" element={<AnalysisPage />} />
          </Routes>
        </section>
      </main>
    </div>
  );
}
