from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
SAMPLE_DIR = TESTS_DIR / "real-basis-document-samples"
MANIFEST_PATH = Path(os.getenv("REAL_BASIS_SAMPLE_MANIFEST", SAMPLE_DIR / "manifest.json"))
REPORT_PATH = Path(os.getenv("REAL_BASIS_EXTRACTION_REPORT", SAMPLE_DIR / "extraction-report.json"))
BASELINE_PATH = Path(os.getenv("REAL_BASIS_EXTRACTION_BASELINE", SAMPLE_DIR / "extraction-baseline.json"))
RUN_REAL_BASIS_RAG_TESTS = os.getenv("RUN_REAL_BASIS_RAG_TESTS") == "1"
TMP_DIR: Path | None = None
SQLITE_PATH: Path | None = None
STORAGE_ROOT: Path | None = None
runtime = None
basis_pipeline = None

if RUN_REAL_BASIS_RAG_TESTS:
    TMP_DIR = Path(tempfile.mkdtemp(prefix="wisdom_real_basis_rag_"))
    SQLITE_PATH = TMP_DIR / "test.db"
    STORAGE_ROOT = TMP_DIR / "storage"

    os.environ["SQLITE_PATH"] = str(SQLITE_PATH)
    os.environ["STORAGE_ROOT"] = str(STORAGE_ROOT)
    os.environ.setdefault("OCR_ENGINE", "noop")
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["GEMINI_API_KEY"] = ""

    sys.path.insert(0, str(BACKEND_DIR))

    from app import main as runtime  # noqa: E402
    from app.pipelines import basis_document as basis_pipeline  # noqa: E402

    runtime.SQLITE_PATH = SQLITE_PATH
    runtime.STORAGE_ROOT = STORAGE_ROOT
    basis_pipeline.STORAGE_ROOT = STORAGE_ROOT
    basis_pipeline.BASIS_INDEX_DIR = STORAGE_ROOT / "basis-index"
    basis_pipeline.BASIS_INDEX_PATH = basis_pipeline.BASIS_INDEX_DIR / "basis-index.json"


def tearDownModule() -> None:
    if TMP_DIR is not None:
        shutil.rmtree(TMP_DIR, ignore_errors=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@unittest.skipUnless(
    RUN_REAL_BASIS_RAG_TESTS,
    "Set RUN_REAL_BASIS_RAG_TESTS=1 after registering the real basis-document PDF sample.",
)
class RealBasisDocumentRagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest(f"Real basis sample manifest not found: {MANIFEST_PATH}")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        sample = manifest.get("sample") if isinstance(manifest.get("sample"), dict) else manifest
        pdf_path = Path(sample.get("saved_path", ""))
        if not pdf_path.is_absolute():
            pdf_path = ROOT_DIR / pdf_path
        if not pdf_path.exists():
            raise unittest.SkipTest(f"Real basis sample PDF not found: {pdf_path}")

        expected_sha = sample.get("sha256", "")
        if expected_sha:
            actual_sha = file_sha256(pdf_path)
            if actual_sha != expected_sha:
                raise unittest.SkipTest(f"Real basis sample sha256 mismatch: {pdf_path}")

        cls.manifest = manifest
        cls.sample = sample
        cls.pdf_path = pdf_path
        cls.report = load_json_if_exists(REPORT_PATH)
        cls.baseline = load_json_if_exists(BASELINE_PATH)

    def setUp(self) -> None:
        assert runtime is not None
        assert SQLITE_PATH is not None
        assert STORAGE_ROOT is not None
        runtime.app.config["TESTING"] = True
        self.client = runtime.app.test_client()
        if SQLITE_PATH.exists():
            SQLITE_PATH.unlink()
        if STORAGE_ROOT.exists():
            shutil.rmtree(STORAGE_ROOT)
        runtime.init_db()

    def upload_real_basis_document(self) -> dict[str, Any]:
        response = self.client.post(
            "/api/basis-documents",
            data={
                "title": self.sample.get("title") or "중소기업자간 경쟁제품 직접생산 확인기준",
                "category": self.sample.get("category") or "direct_production_basis",
                "document_version": self.sample.get("document_version") or "2025-116_2025-11-19",
                "issuing_agency": self.sample.get("issuing_agency") or "중소벤처기업부",
                "memo": "실제 기준문서 RAG opt-in QA 샘플",
                "file": (io.BytesIO(self.pdf_path.read_bytes()), self.pdf_path.name),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        return response.get_json()

    def search_basis(self, query: str, top_k: int = 5) -> dict[str, Any]:
        response = self.client.post(
            "/api/basis-search",
            json={
                "query": query,
                "category": self.sample.get("category") or "direct_production_basis",
                "top_k": top_k,
            },
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.get_json()

    def real_basis_queries(self) -> list[str]:
        baseline_queries = self.baseline.get("rag_queries") if isinstance(self.baseline, dict) else None
        if isinstance(baseline_queries, list) and baseline_queries:
            return [str(query) for query in baseline_queries if str(query).strip()]
        return [
            "직접생산 확인기준",
            "중소기업자간 경쟁제품",
            "세부품명 직접생산",
            "생산시설 검사설비",
            "공장등록 직접생산",
        ]

    def table_queries(self) -> list[dict[str, Any]]:
        baseline_queries = self.baseline.get("table_queries") if isinstance(self.baseline, dict) else None
        if isinstance(baseline_queries, list) and baseline_queries:
            return [query for query in baseline_queries if isinstance(query, dict) and query.get("query")]
        report_queries = (
            self.report.get("table_extraction", {}).get("table_queries", [])
            if isinstance(self.report, dict)
            else []
        )
        return [query for query in report_queries if isinstance(query, dict) and query.get("query")]

    def test_real_basis_sample_manifest_points_to_pdf(self) -> None:
        self.assertTrue(self.pdf_path.exists())
        self.assertGreater(self.pdf_path.stat().st_size, 1024 * 1024)
        self.assertTrue(self.pdf_path.read_bytes().startswith(b"%PDF"))
        self.assertEqual(self.sample.get("category"), "direct_production_basis")

    def test_real_basis_document_upload_extracts_chunks_and_indexes(self) -> None:
        payload = self.upload_real_basis_document()

        self.assertEqual(payload["processing_status"], "completed")
        self.assertEqual(payload["parse_status"], "completed")
        self.assertEqual(payload["index_status"], "completed")
        self.assertGreaterEqual(payload["page_count"], 1)
        self.assertGreaterEqual(payload["chunk_count"], 10)
        self.assertEqual(payload["chunk_count"], payload["vector_count"])
        self.assertIn("직접생산", payload["extracted_text_preview"])

        chunks_response = self.client.get(f"/api/basis-documents/{payload['id']}/chunks")
        self.assertEqual(chunks_response.status_code, 200)
        chunks = chunks_response.get_json()
        self.assertEqual(len(chunks), payload["chunk_count"])
        self.assertTrue(any(chunk["page_start"] for chunk in chunks))

        status_response = self.client.get("/api/basis-index/status")
        self.assertEqual(status_response.status_code, 200)
        status = status_response.get_json()
        self.assertTrue(status["valid"])
        self.assertTrue(status["can_search"])
        self.assertEqual(status["db_indexed_chunk_count"], payload["vector_count"])

    def test_real_basis_document_search_returns_direct_production_citations(self) -> None:
        basis = self.upload_real_basis_document()
        hits = 0
        queries = self.real_basis_queries()

        for query in queries:
            with self.subTest(query=query):
                payload = self.search_basis(query)
                self.assertEqual(payload["index_source"], "json_basis_index")
                if payload["result_count"] > 0:
                    hits += 1
                    first = payload["results"][0]
                    self.assertEqual(first["index_source"], "json_basis_index")
                    self.assertTrue(first["citation_candidate_id"].startswith(f"basis:{basis['id']}:chunk:"))
                    self.assertEqual(first["document"]["id"], basis["id"])
                    self.assertGreater(first["score"], 0)

        coverage = hits / len(queries)
        self.assertGreaterEqual(coverage, 0.8)

    def test_real_basis_document_retrieval_evaluation_records_coverage(self) -> None:
        self.upload_real_basis_document()
        queries = self.real_basis_queries()
        response = self.client.post(
            "/api/basis-retrieval-evaluations",
            json={
                "name": "실제 기준문서 RAG 검색 평가",
                "queries": queries,
                "category": self.sample.get("category") or "direct_production_basis",
                "top_k": 5,
            },
        )

        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertEqual(payload["query_count"], len(queries))
        self.assertEqual(payload["result"]["index_source"], "json_basis_index")
        self.assertGreaterEqual(payload["result"]["metrics"]["result_coverage"], 0.8)
        self.assertGreater(payload["average_top_score"], 0)

    def test_real_basis_document_table_like_content_is_searchable(self) -> None:
        table_queries = self.table_queries()
        if not table_queries:
            raise unittest.SkipTest("Run scripts/analyze-real-basis-document-pdf.py to generate table queries.")

        basis = self.upload_real_basis_document()
        hits = 0
        for query_item in table_queries[:5]:
            query = query_item["query"]
            with self.subTest(query=query):
                payload = self.search_basis(query, top_k=8)
                if payload["result_count"] <= 0:
                    continue
                hits += 1
                first = payload["results"][0]
                self.assertEqual(first["document"]["id"], basis["id"])
                self.assertTrue(first["citation_candidate_id"].startswith(f"basis:{basis['id']}:chunk:"))

        coverage = hits / min(len(table_queries), 5)
        self.assertGreaterEqual(coverage, 0.8)


if __name__ == "__main__":
    unittest.main()
