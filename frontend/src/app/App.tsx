import { NavLink, Route, Routes } from "react-router-dom";
import {
  Activity,
  BookmarkCheck,
  Building2,
  ClipboardCheck,
  DatabaseBackup,
  ExternalLink,
  FilePenLine,
  FileText,
  FolderKanban,
  History,
  LayoutDashboard,
  Library,
  ListChecks,
  Plug,
  RefreshCw,
  Scale,
  Search,
  SearchCheck,
  type LucideIcon,
} from "lucide-react";

import { AnalysisPage } from "../pages/AnalysisPage";
import { BackupsPage } from "../pages/BackupsPage";
import { BasisDocumentsPage } from "../pages/BasisDocumentsPage";
import { BasisRetrievalEvaluationsPage } from "../pages/BasisRetrievalEvaluationsPage";
import { BasisRuleCandidatesPage } from "../pages/BasisRuleCandidatesPage";
import { ContractsPage } from "../pages/ContractsPage";
import { CorporationsPage } from "../pages/CorporationsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DocumentsPage } from "../pages/DocumentsPage";
import { ExternalAccessPage } from "../pages/ExternalAccessPage";
import { JudgmentRunsPage } from "../pages/JudgmentRunsPage";
import { NaraCollectionRunsPage } from "../pages/NaraCollectionRunsPage";
import { NaraBoardPage } from "../pages/NaraBoardPage";
import { NoticeComparisonPage } from "../pages/NoticeComparisonPage";
import { NaraSavedNoticeDetailPage } from "../pages/NaraSavedNoticeDetailPage";
import { NaraSavedNoticesPage } from "../pages/NaraSavedNoticesPage";
import { OperationRunsPage } from "../pages/OperationRunsPage";
import { OperationsPage } from "../pages/OperationsPage";
import { ProjectsPage } from "../pages/ProjectsPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ActionHelpProvider, getMenuHelpGuide, HelpGuideButton } from "./helpGuides";
import { WorkOverlayProvider } from "./workOverlay";

type NavItem = {
  to?: string;
  icon: LucideIcon;
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
    items: [
      { to: "/", icon: LayoutDashboard, label: "대시보드", note: "오늘 처리할 일과 시스템 상태" },
      { to: "/operations", icon: Activity, label: "운영 대시보드", note: "실패, 검토대기, 연동 상태" },
      { to: "/operation-runs", icon: History, label: "작업 이력", note: "실행, 실패 사유, 재시도" },
      { to: "/backups", icon: DatabaseBackup, label: "백업/복원", note: "백업 생성, 검증, dry-run" },
    ],
  },
  {
    title: "공고 업무",
    items: [
      { to: "/nara-board", icon: Search, label: "나라장터 공고 검색", note: "API 조회, 선택 저장, 자동 분석" },
      { to: "/nara-saved-notices", icon: BookmarkCheck, label: "저장한 공고", note: "저장 공고와 첨부 처리 상태" },
      { to: "/notice-comparison", icon: Scale, label: "부족조건 미리보기", note: "공고 요구조건과 법인 준비상태 비교" },
      { to: "/judgment-runs", icon: ClipboardCheck, label: "판단 검토", note: "부족조건, citation 후보, 검토 상태 관리" },
      { to: "/contracts", icon: FilePenLine, label: "계약서 생성", note: "공고와 법인 기반 DOCX 초안" },
      { to: "/nara-collection-runs", icon: RefreshCw, label: "자동 수집 관리", note: "나라장터 API 수집 실행과 이력 확인" },
    ],
  },
  {
    title: "문서 분석",
    items: [{ to: "/documents", icon: FileText, label: "문서 업로드", note: "PDF/DOCX 업로드와 분석 이력" }],
  },
  {
    title: "기준문서 / RAG",
    items: [
      {
        to: "/basis-documents",
        icon: Library,
        label: "기준문서 관리",
        note: "PDF 업로드, 청킹, 로컬 검색 인덱스",
      },
      {
        to: "/basis-rule-candidates",
        icon: ListChecks,
        label: "규칙 후보 관리",
        note: "기준문서 조건 후보 승인, 반려, 수정",
      },
      {
        to: "/basis-retrieval-evaluations",
        icon: SearchCheck,
        label: "검색 평가",
        note: "검색 coverage와 citation 누락 확인",
      },
    ],
  },
  {
    title: "내부 관리",
    items: [
      { to: "/corporations", icon: Building2, label: "법인 관리", note: "법인 정보와 기본 자격 맥락" },
      { to: "/projects", icon: FolderKanban, label: "프로젝트 관리", note: "프로젝트 단위 업무 흐름" },
    ],
  },
  {
    title: "설정",
    items: [
      { to: "/settings/integrations/nara", icon: Plug, label: "API 설정", note: "나라장터 API 키와 연결 상태" },
      { to: "/settings/external-access", icon: ExternalLink, label: "외부 접속", note: "ngrok 공개 URL과 로컬 명령" },
    ],
  },
];

const pageMeta = [
  {
    match: (pathname: string) => pathname === "/",
    eyebrow: "",
    title: "",
    description: "",
  },
  {
    match: (pathname: string) => pathname.startsWith("/backups"),
    eyebrow: "Backup & Restore",
    title: "로컬 데이터 백업과 복원 검증",
    description: "SQLite DB와 storage 파일을 백업하고, 복원 전 dry-run으로 검증합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/operation-runs"),
    eyebrow: "Operation Runs",
    title: "작업 실행과 실패 사유 관리",
    description: "운영 작업의 실행 이력, 요청/결과, 실패 사유와 재시도 흐름을 확인합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/operations"),
    eyebrow: "Operations Control",
    title: "운영 상태와 실패 작업 관리",
    description: "Phase 4 운영 제품화를 위한 상태 요약, 실패 목록, 검토 대기 큐를 확인합니다.",
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
    match: (pathname: string) => pathname.startsWith("/basis-documents"),
    eyebrow: "Basis Library",
    title: "기준문서 청킹과 검색 인덱스",
    description: "재사용 기준문서를 일반 업로드 문서와 분리해 관리합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/basis-rule-candidates"),
    eyebrow: "Rule Candidate Review",
    title: "기준 규칙 후보 검토",
    description: "기준문서에서 추출한 조건 후보를 승인, 반려, 수정하며 citation 품질을 관리합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/settings/external-access"),
    eyebrow: "External Access",
    title: "ngrok 외부 접속 상태",
    description: "로컬 PC에서 실행 중인 서비스를 외부에서 확인할 수 있는 공개 URL 상태를 표시합니다.",
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
    match: (pathname: string) => pathname.startsWith("/nara-collection-runs"),
    eyebrow: "Nara Collection Runs",
    title: "나라장터 자동 수집 관리",
    description: "나라장터 API 수집 실행 조건과 결과, 실패 사유, 재시도 대상을 확인합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/notice-comparison"),
    eyebrow: "Gap Preview",
    title: "공고별 부족조건 미리보기",
    description: "저장 공고의 요구조건 후보와 법인 준비상태를 비교해 부족 가능성이 있는 항목을 먼저 확인합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/judgment-runs"),
    eyebrow: "Judgment Review",
    title: "부족조건 판단 검토",
    description: "공고 요구조건, 법인 준비상태, 기준문서 citation 후보를 묶어 검토 가능한 결과로 정리합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/contracts"),
    eyebrow: "Contract Drafts",
    title: "계약서 초안 생성",
    description: "저장 공고와 법인 기본정보를 기준으로 검토용 용역표준계약서 DOCX를 생성합니다.",
  },
  {
    match: (pathname: string) => pathname.startsWith("/basis-retrieval-evaluations"),
    eyebrow: "Retrieval Evaluation",
    title: "기준문서 검색 품질 확인",
    description: "평가 질의셋별 검색 coverage와 누락 citation을 확인합니다.",
  },
];

function getPageMeta(pathname: string) {
  return pageMeta.find((item) => item.match(pathname)) ?? pageMeta[0];
}

export function App() {
  return (
    <WorkOverlayProvider>
    <ActionHelpProvider>
    <div className="app-shell">
      <aside className="sidebar">
        <nav className="nav-stack" aria-label="Primary Navigation">
          {navGroups.map((group) => (
            <div className="nav-section" key={group.title}>
              <p className="nav-section-title">{group.title}</p>
              {group.items.map((item) =>
                item.to ? (
                  <div key={item.label} className="nav-card-row">
                    <NavLink
                      to={item.to}
                      end={item.to === "/"}
                      className={({ isActive }) => `nav-card${isActive ? " active" : ""}`}
                    >
                      <span className="nav-icon">
                        <item.icon size={18} strokeWidth={2.2} aria-hidden="true" />
                      </span>
                      <span>
                        <span className="nav-label">{item.label}</span>
                        <span className="nav-note">{item.note}</span>
                      </span>
                    </NavLink>
                    <HelpGuideButton guide={getMenuHelpGuide(item.to, item.label, item.note)} compact />
                  </div>
                ) : (
                  <div key={item.label} className="nav-card-row">
                    <div className="nav-card nav-card--disabled" aria-disabled="true">
                      <span className="nav-icon">
                        <item.icon size={18} strokeWidth={2.2} aria-hidden="true" />
                      </span>
                      <span>
                        <span className="nav-label">{item.label}</span>
                        <span className="nav-note">{item.note}</span>
                      </span>
                    </div>
                    <HelpGuideButton guide={getMenuHelpGuide(item.to, item.label, item.note)} compact />
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
        <header className="hero-panel hero-panel--mark" aria-label="SMART 조달 업무 대시보드">
          <div className="hero-logo">
            <div className="hero-logo__core" aria-hidden="true">
              <LayoutDashboard size={30} strokeWidth={1.9} />
            </div>
            <div className="hero-logo__wordmark">
              <span>SMART Procurement</span>
              <strong>SMART 조달청 계산기</strong>
            </div>
            <div className="hero-logo__nodes" aria-hidden="true">
              <span className="hero-logo__node">
                <Search size={16} strokeWidth={2} />
              </span>
              <span className="hero-logo__node">
                <FileText size={16} strokeWidth={2} />
              </span>
              <span className="hero-logo__node">
                <Library size={16} strokeWidth={2} />
              </span>
              <span className="hero-logo__node">
                <ClipboardCheck size={16} strokeWidth={2} />
              </span>
            </div>
          </div>
        </header>

        <section className="page-stage">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/operations" element={<OperationsPage />} />
            <Route path="/operation-runs" element={<OperationRunsPage />} />
            <Route path="/backups" element={<BackupsPage />} />
            <Route path="/corporations" element={<CorporationsPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/:documentId/analysis" element={<AnalysisPage />} />
            <Route path="/basis-documents" element={<BasisDocumentsPage />} />
            <Route path="/basis-rule-candidates" element={<BasisRuleCandidatesPage />} />
            <Route path="/basis-retrieval-evaluations" element={<BasisRetrievalEvaluationsPage />} />
            <Route path="/nara-board" element={<NaraBoardPage />} />
            <Route path="/nara-saved-notices" element={<NaraSavedNoticesPage />} />
            <Route path="/nara-saved-notices/:id" element={<NaraSavedNoticeDetailPage />} />
            <Route path="/notice-comparison" element={<NoticeComparisonPage />} />
            <Route path="/judgment-runs" element={<JudgmentRunsPage />} />
            <Route path="/contracts" element={<ContractsPage />} />
            <Route path="/nara-collection-runs" element={<NaraCollectionRunsPage />} />
            <Route path="/settings/integrations/nara" element={<SettingsPage />} />
            <Route path="/settings/external-access" element={<ExternalAccessPage />} />
          </Routes>
        </section>
      </main>
    </div>
    </ActionHelpProvider>
    </WorkOverlayProvider>
  );
}
