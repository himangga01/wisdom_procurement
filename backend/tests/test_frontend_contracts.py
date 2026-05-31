import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_TSX = REPO_ROOT / "frontend" / "src" / "app" / "App.tsx"
API_TS = REPO_ROOT / "frontend" / "src" / "app" / "api.ts"
RETRIEVAL_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisRetrievalEvaluationsPage.tsx"


def app_source() -> str:
    return APP_TSX.read_text(encoding="utf-8")


def api_source() -> str:
    return API_TS.read_text(encoding="utf-8")


def retrieval_page_source() -> str:
    return RETRIEVAL_PAGE_TSX.read_text(encoding="utf-8")


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


if __name__ == "__main__":
    unittest.main()
