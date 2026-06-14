import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_TSX = REPO_ROOT / "frontend" / "src" / "app" / "App.tsx"
API_TS = REPO_ROOT / "frontend" / "src" / "app" / "api.ts"
HELP_GUIDES_TSX = REPO_ROOT / "frontend" / "src" / "app" / "helpGuides.tsx"
DASHBOARD_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "DashboardPage.tsx"
BASIS_DOCUMENTS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisDocumentsPage.tsx"
BASIS_RULE_CANDIDATES_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisRuleCandidatesPage.tsx"
RETRIEVAL_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisRetrievalEvaluationsPage.tsx"
NARA_BOARD_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "NaraBoardPage.tsx"
NARA_COLLECTION_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "NaraCollectionRunsPage.tsx"
NARA_SAVED_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "NaraSavedNoticesPage.tsx"
NARA_SAVED_DETAIL_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "NaraSavedNoticeDetailPage.tsx"
CORPORATIONS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "CorporationsPage.tsx"
NOTICE_COMPARISON_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "NoticeComparisonPage.tsx"
JUDGMENT_RUNS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "JudgmentRunsPage.tsx"
CONTRACTS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "ContractsPage.tsx"
OPERATIONS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "OperationsPage.tsx"
OPERATION_RUNS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "OperationRunsPage.tsx"
TYPES_TS = REPO_ROOT / "frontend" / "src" / "app" / "types.ts"
STYLES_CSS = REPO_ROOT / "frontend" / "src" / "styles.css"
VITE_CONFIG_TS = REPO_ROOT / "frontend" / "vite.config.ts"
DEMO_VIDEO_SCRIPT = REPO_ROOT / "scripts" / "create-service-demo-video.mjs"


def app_source() -> str:
    return APP_TSX.read_text(encoding="utf-8")


def api_source() -> str:
    return API_TS.read_text(encoding="utf-8")


def help_guides_source() -> str:
    return HELP_GUIDES_TSX.read_text(encoding="utf-8")


def dashboard_source() -> str:
    return DASHBOARD_TSX.read_text(encoding="utf-8")


def basis_documents_page_source() -> str:
    return BASIS_DOCUMENTS_PAGE_TSX.read_text(encoding="utf-8")


def basis_rule_candidates_page_source() -> str:
    return BASIS_RULE_CANDIDATES_PAGE_TSX.read_text(encoding="utf-8")


def retrieval_page_source() -> str:
    return RETRIEVAL_PAGE_TSX.read_text(encoding="utf-8")


def nara_board_page_source() -> str:
    return NARA_BOARD_PAGE_TSX.read_text(encoding="utf-8")


def nara_collection_page_source() -> str:
    return NARA_COLLECTION_PAGE_TSX.read_text(encoding="utf-8")


def nara_saved_page_source() -> str:
    return NARA_SAVED_PAGE_TSX.read_text(encoding="utf-8")


def nara_saved_detail_page_source() -> str:
    return NARA_SAVED_DETAIL_PAGE_TSX.read_text(encoding="utf-8")


def corporations_page_source() -> str:
    return CORPORATIONS_PAGE_TSX.read_text(encoding="utf-8")


def notice_comparison_page_source() -> str:
    return NOTICE_COMPARISON_PAGE_TSX.read_text(encoding="utf-8")


def judgment_runs_page_source() -> str:
    return JUDGMENT_RUNS_PAGE_TSX.read_text(encoding="utf-8")


def contracts_page_source() -> str:
    return CONTRACTS_PAGE_TSX.read_text(encoding="utf-8")


def operations_page_source() -> str:
    return OPERATIONS_PAGE_TSX.read_text(encoding="utf-8")


def operation_runs_page_source() -> str:
    return OPERATION_RUNS_PAGE_TSX.read_text(encoding="utf-8")


def types_source() -> str:
    return TYPES_TS.read_text(encoding="utf-8")


def styles_source() -> str:
    return STYLES_CSS.read_text(encoding="utf-8")


def vite_config_source() -> str:
    return VITE_CONFIG_TS.read_text(encoding="utf-8")


def demo_video_script_source() -> str:
    return DEMO_VIDEO_SCRIPT.read_text(encoding="utf-8")


def nav_routes(source: str) -> set[str]:
    return set(re.findall(r'to:\s*"([^"]+)"', source))


def registered_routes(source: str) -> set[str]:
    return set(re.findall(r'<Route\s+path="([^"]+)"', source))


def page_meta_matchers(source: str) -> tuple[set[str], set[str]]:
    exact = set(re.findall(r'pathname\s*===\s*"([^"]+)"', source))
    prefixes = set(re.findall(r'pathname\.startsWith\("([^"]+)"\)', source))
    return exact, prefixes


def route_has_page_meta(route: str, exact: set[str], prefixes: set[str]) -> bool:
    if route in exact:
        return True
    return any(route == prefix or route.startswith(f"{prefix}/") for prefix in prefixes)


class FrontendContractTests(unittest.TestCase):
    def test_primary_navigation_routes_are_registered(self) -> None:
        source = app_source()
        missing = sorted(nav_routes(source) - registered_routes(source))

        self.assertEqual(missing, [])

    def test_primary_navigation_routes_have_page_metadata(self) -> None:
        source = app_source()
        exact, prefixes = page_meta_matchers(source)
        missing = sorted(route for route in nav_routes(source) if not route_has_page_meta(route, exact, prefixes))

        self.assertEqual(missing, [])

    def test_sidebar_navigation_sections_have_distinct_tones(self) -> None:
        app = app_source()
        styles = styles_source()
        expected_tones = ["overview", "notice", "document", "rag", "admin", "settings"]

        self.assertIn("type NavGroupTone", app)
        self.assertIn("tone: NavGroupTone", app)
        self.assertIn("nav-section nav-section--${group.tone}", app)
        nav_groups_block = app[app.index("const navGroups"): app.index("const pageMeta")]
        group_titles = re.findall(r'title: "([^"]+)"', nav_groups_block)
        self.assertEqual(
            group_titles,
            ["업무 현황", "내부 관리", "공고 업무", "기준문서 / RAG", "문서 분석", "설정"],
        )
        group_blocks = {
            match.group("title"): match.group("body")
            for match in re.finditer(
                r'title: "(?P<title>[^"]+)",\s*tone: "[^"]+",\s*items: \[(?P<body>.*?)\],\s*},',
                nav_groups_block,
                re.S,
            )
        }
        for moved_label in ["운영 대시보드", "작업 이력", "자동 수집 관리", "백업/복원"]:
            self.assertIn(moved_label, group_blocks["설정"])
            self.assertNotIn(moved_label, group_blocks["업무 현황"])
            self.assertNotIn(moved_label, group_blocks["공고 업무"])
        for tone in expected_tones:
            self.assertIn(f'tone: "{tone}"', app)
            self.assertIn(f".nav-section--{tone}", styles)

        self.assertIn("--nav-section-bg", styles)
        self.assertIn("--nav-section-accent", styles)
        self.assertIn("background: var(--nav-section-bg);", styles)
        self.assertIn("border-left: 4px solid var(--nav-section-accent);", styles)
        self.assertIn("color: var(--nav-section-accent);", styles)
        icon_style = re.search(r"\.nav-icon\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(icon_style)
        self.assertIn("background: var(--nav-section-bg);", icon_style.group("body"))
        self.assertNotIn("box-shadow", icon_style.group("body"))
        active_icon_style = re.search(r"\.nav-card\.active \.nav-icon\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(active_icon_style)
        self.assertIn("background: var(--nav-section-bg);", active_icon_style.group("body"))
        self.assertIn("color: var(--nav-section-accent);", active_icon_style.group("body"))
        self.assertNotIn("box-shadow", active_icon_style.group("body"))

    def test_basis_retrieval_evaluation_can_be_created_from_frontend(self) -> None:
        api = api_source()
        page = retrieval_page_source()

        self.assertIn("createBasisRetrievalEvaluation", api)
        self.assertIn("/api/basis-retrieval-evaluations", api)
        self.assertIn("method: \"POST\"", api)
        self.assertIn("api.createBasisRetrievalEvaluation", page)
        self.assertIn("평가 실행", page)

    def test_basis_document_chunks_are_collapsed_by_default(self) -> None:
        api = api_source()
        page = basis_documents_page_source()
        styles = styles_source()

        self.assertIn("listBasisDocumentChunks", api)
        self.assertIn("/chunks", api)
        self.assertIn("CHUNK_PREVIEW_LIMIT", page)
        self.assertIn("chunkDisplayText(chunk, expanded)", page)
        self.assertIn("expandedChunkIds", page)
        self.assertIn("chunksVisible", page)
        self.assertIn("api.listBasisDocumentChunks", page)
        self.assertIn("청크 본문은 숨겨져 있습니다.", page)
        self.assertIn("aria-expanded={expanded}", page)
        self.assertIn("더보기", page)
        self.assertIn("접기", page)
        self.assertNotIn("<p>{chunk.chunk_text}</p>", page)
        self.assertNotIn("selectedDoc.chunks.map", page)
        self.assertNotIn("?? data[0]?.id", page)
        self.assertIn(".chunk-row__body", styles)
        self.assertIn(".chunk-row__toggle", styles)

    def test_basis_rule_candidates_page_keeps_long_sources_collapsed(self) -> None:
        page = basis_rule_candidates_page_source()
        styles = styles_source()

        for token in [
            "demo-rule-candidate-guide",
            "demo-rule-candidate-row",
            "demo-rule-candidate-source-open",
            "demo-rule-candidate-source-modal",
            "원문 보기",
            "전체 원문 표시",
            "기준문서 원문 미리보기",
            "CANDIDATE_LIST_LIMIT",
            "limit: CANDIDATE_LIST_LIMIT",
            "최근 {formatCount(CANDIDATE_LIST_LIMIT)}건만 표시합니다.",
            "truncateText(item.condition_text, 180)",
            "truncateText(activeSourceText, TEXT_PREVIEW_LIMIT)",
            "truncateText(activeSourceText, MODAL_PREVIEW_LIMIT)",
        ]:
            self.assertIn(token, page)

        self.assertNotIn("active.chunk?.chunk_text || active.condition_text", page)
        self.assertIn(".rule-candidate-guide", styles)
        self.assertIn(".rule-candidate-row", styles)
        self.assertIn(".rule-candidate-context", styles)
        self.assertIn(".rule-candidate-source-text", styles)
        self.assertIn("max-height: min(58vh, 520px);", styles)

    def test_basis_document_loading_state_has_progress_bar(self) -> None:
        page = basis_documents_page_source()
        styles = styles_source()

        self.assertIn("loading-state", page)
        self.assertIn("loading-bar", page)
        self.assertIn('role="progressbar"', page)
        self.assertIn('aria-label="기준문서 로딩 진행 상태"', page)
        self.assertIn(".loading-bar", styles)
        self.assertIn("@keyframes loadingBarSweep", styles)


    def test_ngrok_api_requests_skip_browser_warning(self) -> None:
        api = api_source()

        self.assertIn("NEEDS_NGROK_SKIP_HEADER", api)
        self.assertIn(".ngrok-free.app", api)
        self.assertIn("ngrok-skip-browser-warning", api)
        self.assertIn("withRuntimeHeaders(init)", api)

    def test_vite_dev_server_allows_ngrok_free_hosts(self) -> None:
        config = vite_config_source()

        self.assertIn("allowedHosts", config)
        self.assertIn(".ngrok-free.app", config)
        self.assertIn("localhost", config)
        self.assertIn("127.0.0.1", config)
        self.assertIn("VITE_ALLOW_NGROK_HOSTS", config)

    def test_navigation_and_dashboard_copy_do_not_use_stale_phase_badges(self) -> None:
        app = app_source()
        dashboard = dashboard_source()

        self.assertNotRegex(app, r'icon:\s*"[A-Z]{2}"')
        self.assertNotIn("Local PC", app)
        self.assertNotIn("Phase 1.5", app)
        self.assertNotIn("RAG Ready Next", app)
        self.assertNotIn("Operations Overview", app)
        self.assertNotIn("오늘 처리할 조달 업무를 한눈에", app)
        self.assertNotIn("운영형 대시보드로 정리", app)
        self.assertNotIn("오늘 처리할 큐", dashboard)
        self.assertNotIn("Phase 1.6 이후", dashboard)
        self.assertIn("hero-panel--mark", app)
        self.assertIn("hero-logo__core", app)
        self.assertIn("hero-logo__wordmark", app)
        self.assertIn("SMART Procurement", app)
        self.assertIn("SMART 조달청 계산기", app)
        self.assertNotIn("brand-card", app)
        self.assertNotIn("brand-mark", app)
        self.assertNotIn('className="brand-copy"', app)

    def test_portal_copy_does_not_expose_internal_phase_or_ux_rationale(self) -> None:
        banned_phrases = [
            "Phase",
            "Project First",
            "Why It Matters",
            "Manual Fallback",
            "Evidence First",
            "Profile Readiness",
            "Usability Upgrade",
            "바꾼 이유",
            "바꾼 점",
            "업로드 자체보다",
            "훨씬 읽기",
            "UX로",
            "UX를",
        ]

        for path in (REPO_ROOT / "frontend" / "src").rglob("*.tsx"):
            source = path.read_text(encoding="utf-8")
            for phrase in banned_phrases:
                self.assertNotIn(phrase, source, f"{phrase} should not be exposed in {path.relative_to(REPO_ROOT)}")

    def test_menu_and_action_help_guides_are_available(self) -> None:
        app = app_source()
        help_guides = help_guides_source()
        styles = styles_source()
        final_help_button_style = styles[styles.rfind(".help-guide-trigger,\n.action-help-trigger") :]

        self.assertIn("ActionHelpProvider", app)
        self.assertIn("HelpGuideButton", app)
        self.assertIn("getMenuHelpGuide", app)
        self.assertIn("nav-card-row", app)
        self.assertIn("decorateActionButtons", help_guides)
        self.assertIn("button:not(.help-guide-trigger):not(.action-help-trigger)", help_guides)
        self.assertIn("a.link-button:not(.help-guide-trigger):not(.action-help-trigger)", help_guides)
        self.assertIn("help-guide-backdrop", help_guides)
        self.assertIn('role="dialog"', help_guides)
        self.assertIn(".nav-card-row", styles)
        self.assertIn(".action-help-trigger", styles)
        self.assertIn("width: 16px;", final_help_button_style)
        self.assertIn("height: 16px;", final_help_button_style)
        section_heading_style = re.search(r"\.section-heading\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(section_heading_style)
        self.assertIn("justify-content: flex-start;", section_heading_style.group("body"))
        self.assertIn("column-gap: 6px;", section_heading_style.group("body"))
        self.assertIn(".section-heading > :first-child", styles)
        self.assertIn(".section-heading > .action-help-trigger", styles)
        self.assertIn(".analysis-hero > :first-child", styles)
        self.assertIn(".analysis-hero > .action-help-trigger", styles)
        self.assertIn(".sticky-action-bar > :first-child", styles)
        self.assertIn(".sticky-action-bar > .action-help-trigger", styles)
        self.assertIn("margin-left: -2px;", styles)
        self.assertIn(".toolbar > .action-help-trigger", styles)
        self.assertIn("margin-left: -6px;", styles)
        analysis_hero_style = re.search(r"\.analysis-hero\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(analysis_hero_style)
        self.assertIn("justify-content: flex-start;", analysis_hero_style.group("body"))
        self.assertIn("column-gap: 6px;", analysis_hero_style.group("body"))
        self.assertNotIn("justify-content: space-between;", analysis_hero_style.group("body"))
        sticky_action_style = re.search(r"\.sticky-action-bar\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(sticky_action_style)
        self.assertIn("justify-content: flex-start;", sticky_action_style.group("body"))
        self.assertIn("column-gap: 6px;", sticky_action_style.group("body"))
        self.assertNotIn("justify-content: space-between;", sticky_action_style.group("body"))

    def test_corporation_evidence_review_empty_candidates_are_explained(self) -> None:
        page = corporations_page_source()
        styles = styles_source()

        self.assertIn("function evidenceReviewLabel", page)
        self.assertIn("evidencePendingCandidateCount", page)
        self.assertIn("evidenceApprovedCandidateCount", page)
        self.assertIn("후보 없음", page)
        self.assertIn("승인 대기 후보 전체 선택", page)
        self.assertIn("선택한 후보 반영", page)
        self.assertIn("승인할 자동 추출 후보가 없습니다.", page)
        self.assertIn("승인 대기 후보가 없습니다.", page)
        self.assertIn("aria-label={`${candidate.field_label} 승인 후보 선택`}", page)
        self.assertIn("evidenceReviewLabel(item)", page)
        self.assertIn("원본 검토값", page)
        self.assertIn(".evidence-candidate-notice", styles)
        self.assertIn(".evidence-review-actions", styles)

    def test_corporation_readiness_cards_open_edit_form(self) -> None:
        page = corporations_page_source()
        styles = styles_source()

        self.assertIn("useRef", page)
        self.assertIn("editSectionRef", page)
        self.assertIn("directorySectionRef", page)
        self.assertIn("scrollToEditForm", page)
        self.assertIn("openCorporationFromReadiness", page)
        self.assertIn("readiness-card readiness-card--button", page)
        self.assertIn('data-help-ignore="true"', page)
        self.assertIn("클릭해서 법인 정보 편집", page)
        self.assertIn("scrollIntoView({ behavior: \"smooth\", block: \"start\" })", page)
        self.assertIn("ref={editSectionRef}", page)
        self.assertIn("ref={directorySectionRef}", page)
        self.assertIn(".readiness-card--button", styles)
        self.assertIn(".readiness-card__hint", styles)
        readiness_grid_style = re.search(r"\.readiness-grid\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(readiness_grid_style)
        self.assertIn("align-items: stretch;", readiness_grid_style.group("body"))
        readiness_card_style = re.search(r"\.readiness-card\s*\{(?P<body>[^}]+)\}", styles)
        self.assertIsNotNone(readiness_card_style)
        self.assertIn("min-height: 212px;", readiness_card_style.group("body"))

    def test_demo_video_selectors_and_interactive_modes_are_available(self) -> None:
        sources = {
            "app": app_source(),
            "corporations": corporations_page_source(),
            "nara_board": nara_board_page_source(),
            "nara_saved": nara_saved_page_source(),
            "nara_saved_detail": nara_saved_detail_page_source(),
            "basis": basis_documents_page_source(),
            "comparison": notice_comparison_page_source(),
            "judgment": judgment_runs_page_source(),
            "contracts": contracts_page_source(),
            "operations": operations_page_source(),
            "operation_runs": operation_runs_page_source(),
            "nara_collection": nara_collection_page_source(),
        }
        expected_by_source = {
            "app": [
                "sidebar-dashboard",
                "sidebar-nara-board",
                "sidebar-nara-saved-notices",
                "sidebar-notice-comparison",
                "sidebar-judgment-runs",
                "sidebar-contracts",
                "sidebar-basis-documents",
                "sidebar-corporations",
                "sidebar-operation-runs",
            ],
            "corporations": [
                "demo-corporations-page",
                "demo-corporation-upload-tab",
                "demo-corporation-review-tab",
                "demo-corporation-library-tab",
                "demo-corporation-directory-tab",
                "demo-evidence-file-input",
                "demo-evidence-upload-submit",
                "demo-latest-evidence-result",
                "demo-evidence-document-list",
                "demo-corporation-list",
            ],
            "nara_board": [
                "demo-nara-board-page",
                "demo-nara-business-type",
                "demo-nara-search-keyword",
                "demo-nara-search-start-date",
                "demo-nara-search-end-date",
                "demo-nara-search-submit",
                "demo-nara-result-list",
                "demo-nara-result-row",
                "demo-nara-save-analyze",
                "demo-nara-partial-error",
            ],
            "nara_saved": [
                "demo-saved-notices-page",
                "demo-saved-notice-list",
                "demo-saved-notice-row",
                "demo-saved-notice-detail-link",
            ],
            "nara_saved_detail": [
                "demo-saved-notice-detail-page",
                "demo-notice-requirements",
                "demo-notice-attachment-status",
            ],
            "basis": [
                "demo-basis-documents-page",
                "demo-basis-file-input",
                "demo-basis-force-ocr-toggle",
                "demo-basis-upload-submit",
                "demo-basis-document-list",
                "demo-basis-document-row",
                "demo-basis-document-detail",
                "demo-basis-reprocess-force-ocr-toggle",
                "demo-basis-reprocess-submit",
                "demo-basis-processing-status",
                "demo-basis-chunk-list",
                "demo-basis-chunk-list-toggle",
                "demo-basis-chunk-expand",
            ],
            "comparison": [
                "demo-notice-comparison-page",
                "demo-comparison-notice-select",
                "demo-comparison-corporation-select",
                "demo-notice-comparison-run",
                "demo-comparison-history-open",
                "demo-comparison-history-modal",
                "demo-comparison-detail-modal",
                "demo-comparison-evidence-modal",
                "demo-comparison-requirements-modal",
                "demo-comparison-profile-modal",
            ],
            "judgment": [
                "demo-judgment-runs-page",
                "demo-judgment-run-create",
                "demo-judgment-history-open",
                "demo-judgment-detail-open",
                "demo-judgment-history-modal",
                "demo-judgment-detail-modal",
                "demo-judgment-evidence-modal",
                "demo-judgment-run-list",
                "demo-judgment-run-row",
            ],
            "contracts": [
                "demo-contracts-page",
                "demo-contract-notice-select",
                "demo-contract-corporation-select",
                "demo-contract-judgment-select",
                "demo-contract-preview",
                "demo-contract-create",
                "demo-contract-list",
                "demo-contract-download",
            ],
            "operations": [
                "demo-operations-page",
                "demo-operations-summary",
                "demo-operation-error-detail",
            ],
            "operation_runs": [
                "demo-operation-runs-page",
                "demo-operation-run-list",
                "demo-operation-run-row",
                "demo-operation-error-detail",
            ],
            "nara_collection": [
                "demo-nara-collection-runs-page",
                "demo-nara-collection-business-type",
                "demo-nara-collection-run-create",
                "demo-nara-collection-run-list",
                "demo-nara-collection-run-row",
            ],
        }

        for source_name, selectors in expected_by_source.items():
            source = sources[source_name]
            for selector in selectors:
                self.assertIn(selector, source, f"{selector} missing in {source_name}")

        script = demo_video_script_source()
        for token in [
            "interactive-demo",
            "real-pdf-demo",
            "live-nara-demo",
            "installDemoCursor",
            "clickWithCursor",
            "typeWithCursor",
            "setInputFilesWithCursor",
            "navigateBySidebar",
            "runRealPdfEvidenceScene",
            "runLiveNaraSearchScene",
            "data-demo-id",
            "source",
            "test_doc",
        ]:
            self.assertIn(token, script)

    def test_comparison_and_judgment_pages_use_modal_summary_ux(self) -> None:
        comparison = notice_comparison_page_source()
        judgment = judgment_runs_page_source()
        api = api_source()

        for token in [
            "비교 이력 보기",
            "결과 자세히 보기",
            "증빙서류 보기",
            "기준문서 근거 보기",
            "공고 요구조건 보기",
            "공고를 선택하세요",
            "법인을 선택하세요",
            "최근 비교 이력으로 돌아가기",
            "추출 방식",
            "demo-comparison-history-modal",
            "demo-comparison-detail-modal",
            "demo-comparison-evidence-modal",
        ]:
            self.assertIn(token, comparison)

        for token in [
            "판단 검토 실행 이력 보기",
            "결과 자세히 보기",
            "증빙서류 보기",
            "기준문서 근거 보기",
            "공고 요구조건 보기",
            "공고를 선택하세요",
            "법인을 선택하세요",
            "판단 결과",
            "판단 요약",
            "Gemini 판단 정리",
            "판단 검토 실행 이력으로 돌아가기",
            "priority-related-list",
            "normalizeJudgmentSummaryCopy",
            "준비 필요",
            "추가 확인",
            "demo-judgment-history-modal",
            "demo-judgment-detail-modal",
            "demo-judgment-evidence-modal",
        ]:
            self.assertIn(token, judgment)
        for removed_visible_copy in [
            '<option value="needs_followup">보강 필요</option>',
            "보강 {run.missing_count}",
            "<span>보강 필요",
            "조건별 보강 사유",
            "계약서 초안 생성",
            "setActiveRunId(runList[0].id)",
        ]:
            self.assertNotIn(removed_visible_copy, judgment)
        for removed_auto_select in [
            "setSelectedNoticeId(String(noticeList[0].id))",
            "setSelectedCorporationId(String(corporationList[0].id))",
        ]:
            self.assertNotIn(removed_auto_select, comparison)
            self.assertNotIn(removed_auto_select, judgment)
        self.assertNotIn("계약서 초안 생성", comparison)
        requirements_modal = comparison.split('title="공고 요구조건 후보"', 1)[1].split('title="법인 비교 프로필"', 1)[0]
        self.assertNotIn("공고 요구조건 보기", requirements_modal)

        self.assertIn("getBasisDocumentChunk", api)
        self.assertIn("getNoticeRequirement", api)

        raw_user_statuses = ["candidate_found", "weak_candidate"]
        visible_sources = comparison + judgment
        for raw_status in raw_user_statuses:
            self.assertNotIn(raw_status, visible_sources)

    def test_portal_theme_uses_procurement_slate_and_korean_font_stack(self) -> None:
        styles = styles_source()

        self.assertIn("--bg: #f6f8fb;", styles)
        self.assertIn("--ink: #172033;", styles)
        self.assertIn("--brand: #1d4ed8;", styles)
        self.assertIn("--brand-deep: #1e3a8a;", styles)
        self.assertIn("--leaf: #0f766e;", styles)
        self.assertIn('"Pretendard Variable", Pretendard, "Noto Sans KR"', styles)
        self.assertIn("min-height: 82px;", styles)
        self.assertIn(".hero-logo__wordmark", styles)
        self.assertNotIn(".brand-card", styles)
        self.assertNotIn(".brand-mark", styles)

        stale_theme_tokens = [
            "#fff8fb",
            "#fff1f4",
            "#f7f4ef",
            "#d95a8a",
            "#c64678",
            "#c75f78",
            "#9f415b",
            "#ffd9e8",
            "#f8b3cb",
            "rgba(217, 90, 138",
            "rgba(255, 224, 235",
            "rgba(232, 202, 211",
        ]
        for stale in stale_theme_tokens:
            self.assertNotIn(stale, styles)

        self.assertNotIn("Dotum", styles)
        self.assertNotIn("돋움", styles)
        self.assertNotIn("맑은 고딕", styles)

    def test_nara_business_type_controls_are_wired_to_search_and_collection(self) -> None:
        board = nara_board_page_source()
        collection = nara_collection_page_source()
        detail = nara_saved_detail_page_source()
        types = types_source()

        for source in (board, collection):
            self.assertIn('type NaraBusinessType = "all" | "construction" | "service" | "goods" | "etc"', source)
            for value in ["all", "construction", "service", "goods", "etc"]:
                self.assertIn(f'value: "{value}"', source)
            self.assertIn('useState<NaraBusinessType>("all")', source)
            self.assertIn("business_type: businessType", source)

        self.assertIn("businessTypeLabel(item.business_type, item.business_type_label)", board)
        self.assertIn("businessTypeLabel(activeRun.criteria.business_type, activeRun.result.business_type_label)", collection)
        self.assertIn("businessTypeLabel(notice)", detail)
        self.assertIn("business_type?: string;", types)
        self.assertIn("business_type_label?: string;", types)
        self.assertIn("queried_business_types?: string[];", types)

    def test_nara_board_supports_merged_all_pagination_and_partial_error_warning(self) -> None:
        board = nara_board_page_source()
        types = types_source()

        self.assertIn('pagination_mode?: "single" | "merged_all";', types)
        self.assertIn("has_next_page?: boolean;", types)
        self.assertIn("total_count_is_estimated?: boolean;", types)
        self.assertIn("partial_errors?: Array<", types)
        self.assertIn('result?.pagination_mode === "merged_all"', board)
        self.assertIn("isMergedAllPagination", board)
        self.assertIn("총 ${result.total_count.toLocaleString(\"ko-KR\")}건 추정", board)
        self.assertIn("일부 업무유형 조회에 실패했습니다.", board)
        self.assertIn("result.partial_errors.map", board)
        self.assertIn("pagination-current", board)
        self.assertIn("!isMergedAllPagination ? (", board)
        self.assertIn("onClick={() => search(totalPages, true)}", board)

    def test_corporation_evidence_options_include_all_separated_demo_pdf_types(self) -> None:
        page = corporations_page_source()
        help_guides = help_guides_source()
        expected_types = [
            "gpass_company_certificate",
            "iso_quality_certificate",
            "venture_business_confirmation",
            "innobiz_confirmation",
            "factory_registration_certificate",
            "research_institute_certificate",
            "software_business_certificate",
            "software_quality_certificate",
            "green_technology_certificate",
            "green_product_confirmation",
            "excellent_product_certificate",
            "patent_certificate",
            "copyright_registration_certificate",
            "outdoor_advertising_business_registration",
            "online_sales_business_registration",
            "industry_association_membership",
            "investment_share_certificate",
            "employment_support_approval",
            "insurance_policy_certificate",
            "special_business_license",
            "technology_grade_confirmation",
            "technology_evaluation_excellent_certificate",
        ]

        for document_type in expected_types:
            self.assertIn(f'value: "{document_type}"', page)

        self.assertIn("법인 증빙자료 업로드", page)
        self.assertIn("기존 법인에 연결", page)
        self.assertIn("새로운 법인 생성 및 추가", page)
        self.assertNotIn("새 법인으로 생성 예정", page)
        self.assertIn("사업자등록증명, 사업자등록증, 인증서, 면허, 확인서, 특허/저작권 문서", page)
        self.assertIn("여러 파일을 한 번에 선택하면", page)
        self.assertIn("const [evidenceFiles, setEvidenceFiles] = useState<File[]>([])", page)
        self.assertIn("multiple", page)
        self.assertIn("Array.from(e.target.files ?? [])", page)
        self.assertIn("for (const file of filesToUpload)", page)
        self.assertIn("증빙자료 관리에서 각 문서의 검토 버튼", page)
        self.assertIn("selected-file-list", page)
        self.assertIn("여러 증빙자료 OCR 분석 중", page)
        self.assertNotIn("사업자등록증명 또는 사업자등록증 업로드", page)
        self.assertIn("여러 파일을 한 번에 선택하면 순서대로 분석하고", help_guides)


if __name__ == "__main__":
    unittest.main()
