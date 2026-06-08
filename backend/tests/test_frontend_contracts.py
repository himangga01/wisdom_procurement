import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_TSX = REPO_ROOT / "frontend" / "src" / "app" / "App.tsx"
API_TS = REPO_ROOT / "frontend" / "src" / "app" / "api.ts"
HELP_GUIDES_TSX = REPO_ROOT / "frontend" / "src" / "app" / "helpGuides.tsx"
DASHBOARD_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "DashboardPage.tsx"
BASIS_DOCUMENTS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisDocumentsPage.tsx"
RETRIEVAL_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisRetrievalEvaluationsPage.tsx"
STYLES_CSS = REPO_ROOT / "frontend" / "src" / "styles.css"


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


def retrieval_page_source() -> str:
    return RETRIEVAL_PAGE_TSX.read_text(encoding="utf-8")


def styles_source() -> str:
    return STYLES_CSS.read_text(encoding="utf-8")


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
        self.assertIn("margin-left: -2px;", styles)
        self.assertIn(".toolbar > .action-help-trigger", styles)
        self.assertIn("margin-left: -6px;", styles)

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


if __name__ == "__main__":
    unittest.main()
