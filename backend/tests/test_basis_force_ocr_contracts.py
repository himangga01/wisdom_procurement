import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PY = REPO_ROOT / "backend" / "app" / "main.py"
BASIS_DOCUMENT_PY = REPO_ROOT / "backend" / "app" / "pipelines" / "basis_document.py"
OCR_PY = REPO_ROOT / "backend" / "app" / "pipelines" / "ocr.py"
BASIS_PAGE_TSX = REPO_ROOT / "frontend" / "src" / "pages" / "BasisDocumentsPage.tsx"
API_TS = REPO_ROOT / "frontend" / "src" / "app" / "api.ts"
STYLES_CSS = REPO_ROOT / "frontend" / "src" / "styles.css"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class BasisForceOcrContractTests(unittest.TestCase):
    def test_backend_upload_and_reprocess_accept_force_ocr(self) -> None:
        main = read(MAIN_PY)

        self.assertIn("force_ocr = parse_bool_value(request.form.get(\"force_ocr\"))", main)
        self.assertIn("json.dumps({\"options\": processing_options}", main)
        self.assertIn("process_basis_document(conn, basis_document_id, processing_options)", main)
        self.assertIn("request_payload = get_json_payload()", main)
        self.assertIn("option_overrides[\"force_ocr\"] = parse_bool_value", main)
        self.assertIn("ocr_status='processing'", main)
        self.assertIn("conn.commit()", main)
        self.assertIn("process_basis_document(conn, basis_document_id, option_overrides or None)", main)
        self.assertIn("effective_options = metadata.get(\"options\")", main)

    def test_basis_pipeline_persists_and_uses_force_ocr_option(self) -> None:
        basis = read(BASIS_DOCUMENT_PY)
        ocr = read(OCR_PY)

        self.assertIn("def basis_processing_options", basis)
        self.assertIn("def bool_option(value: Any) -> bool:", basis)
        self.assertIn("force_ocr=processing_options[\"force_ocr\"]", basis)
        self.assertIn("\"options\": processing_options", basis)
        self.assertIn("force: bool = False", ocr)
        self.assertIn("if not force and not should_run_ocr(extracted_text):", ocr)
        self.assertIn("\"ocr.force_required\" if force else \"ocr.required\"", ocr)

    def test_frontend_exposes_upload_and_reprocess_force_ocr_controls(self) -> None:
        page = read(BASIS_PAGE_TSX)
        api = read(API_TS)
        styles = read(STYLES_CSS)

        self.assertIn("uploadForceOcr", page)
        self.assertIn("reprocessForceOcr", page)
        self.assertIn("reprocessProgress", page)
        self.assertIn("basis-processing-panel", page)
        self.assertIn("OCR 강제 실행 처리 중", page)
        self.assertIn("OCR 강제 실행은 PDF 전체 페이지를 다시 판독하므로", page)
        self.assertIn("기준문서 재처리 진행 중", page)
        self.assertIn("disabled={Boolean(selectedReprocessProgress)}", page)
        self.assertIn("formData.append(\"force_ocr\", uploadForceOcr ? \"true\" : \"false\")", page)
        self.assertIn("api.reprocessBasisDocument(documentId, { force_ocr: forceOcr })", page)
        self.assertIn("OCR 강제 실행", page)
        self.assertIn("reprocessBasisDocument: (id: number, body: Record<string, unknown> = {})", api)
        self.assertIn("body: JSON.stringify(body)", api)
        self.assertIn(".toggle-field", styles)
        self.assertIn(".inline-warning", styles)
        self.assertIn(".basis-reprocess-control", styles)
        self.assertIn(".basis-reprocess-actions", styles)
        self.assertIn(".basis-processing-panel", styles)
        self.assertIn(".work-overlay-progress", styles)
        self.assertIn(".inline-toggle", styles)


if __name__ == "__main__":
    unittest.main()
