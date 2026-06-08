import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

from app.pipelines.pdf_readers import (
    AutoPdfReader,
    OpenDataLoaderPdfReader,
    PdfReaderError,
    PyMuPdfPdfReader,
    is_meaningful_table,
    pdf_reader_status,
    render_opendataloader_payload,
)


class PdfReaderEnv:
    def __init__(self, **values: str) -> None:
        self.values = values
        self.previous: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self.values.items():
            self.previous[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, *_args: object) -> None:
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def paragraph(text: str, page_number: int = 1) -> dict:
    return {
        "type": "paragraph",
        "page number": page_number,
        "content": text,
    }


def cell(text: str, row_number: int, column_number: int, page_number: int = 1) -> dict:
    return {
        "type": "table cell",
        "page number": page_number,
        "row number": row_number,
        "column number": column_number,
        "kids": [paragraph(text, page_number)],
    }


def table(rows: list[list[str]], page_number: int = 1) -> dict:
    return {
        "type": "table",
        "page number": page_number,
        "bounding box": [10, 10, 200, 120],
        "number of rows": len(rows),
        "number of columns": max(len(row) for row in rows),
        "rows": [
            {
                "type": "table row",
                "row number": row_index,
                "cells": [
                    cell(value, row_index, column_index, page_number)
                    for column_index, value in enumerate(row, start=1)
                ],
            }
            for row_index, row in enumerate(rows, start=1)
        ],
    }


class PdfReaderTests(unittest.TestCase):
    def test_opendataloader_payload_keeps_meaningful_tables_and_filters_title_boxes(self) -> None:
        payload = {
            "number of pages": 1,
            "kids": [
                paragraph("직접생산 확인기준"),
                table([["45", "경쟁제품 도로및철도건설자재"]]),
                table(
                    [
                        ["항목", "내용", "비고"],
                        ["생산시설", "절단기 천공기 용접기", "임차보유 인정하지 않음"],
                        ["생산인력", "상시근로자 2명 이상", "4대보험 가입증명"],
                    ]
                ),
            ],
        }

        text, pages, tables = render_opendataloader_payload(payload)

        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["headers"], ["항목", "내용", "비고"])
        self.assertIn("| 항목 | 내용 | 비고 |", text)
        self.assertIn("생산시설", text)
        self.assertEqual(pages[0]["table_count"], 1)

    def test_table_filter_rejects_single_row_title_table(self) -> None:
        text, _pages, tables = render_opendataloader_payload({"kids": [table([["45", "제목"]])]})

        self.assertEqual(text, "")
        self.assertEqual(tables, [])

    def test_opendataloader_payload_page_offsets_match_joined_text(self) -> None:
        text, pages, _tables = render_opendataloader_payload(
            {
                "number of pages": 3,
                "kids": [
                    paragraph("page one", 1),
                    paragraph("page two", 2),
                    paragraph("page three", 3),
                ],
            }
        )

        self.assertEqual(text, "page one\n\npage two\n\npage three")
        self.assertEqual(pages[0]["char_start"], text.index("page one"))
        self.assertEqual(pages[1]["char_start"], text.index("page two"))
        self.assertEqual(pages[2]["char_start"], text.index("page three"))
        self.assertEqual(pages[2]["char_end"], len(text))

    def test_opendataloader_payload_reads_nested_blank_content_nodes(self) -> None:
        payload = {
            "number of pages": 1,
            "kids": [
                {
                    "type": "paragraph",
                    "page number": 1,
                    "content": "",
                    "kids": [paragraph("nested paragraph text", 1)],
                },
                {
                    "type": "table",
                    "page number": 1,
                    "number of rows": 2,
                    "number of columns": 2,
                    "rows": [
                        {
                            "type": "table row",
                            "row number": 1,
                            "cells": ["item", "content"],
                        },
                        {
                            "type": "table row",
                            "row number": 2,
                            "cells": [
                                {
                                    "type": "table cell",
                                    "page number": 1,
                                    "content": "",
                                    "kids": [paragraph("nested cell", 1)],
                                },
                                "string cell",
                            ],
                        },
                    ],
                },
            ],
        }

        text, _pages, tables = render_opendataloader_payload(payload)

        self.assertIn("nested paragraph text", text)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["rows"][1]["cells"], ["nested cell", "string cell"])
        self.assertIn("| nested cell | string cell |", text)

    def test_status_normalizes_unknown_configured_engine_to_auto(self) -> None:
        with PdfReaderEnv(PDF_READER_ENGINE="unknown-engine"):
            status = pdf_reader_status()

        self.assertEqual(status["configured_engine"], "auto")

    def test_status_reports_java_timeout_without_raising(self) -> None:
        with patch("app.pipelines.pdf_readers.shutil.which", return_value="java"):
            with patch(
                "app.pipelines.pdf_readers.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["java", "-version"], 10),
            ):
                status = OpenDataLoaderPdfReader().status()

        self.assertFalse(status["available"])
        self.assertIn("java -version timed out.", status["errors"])

    def test_opendataloader_timeout_is_normalized_to_reader_error(self) -> None:
        with self.assertRaisesRegex(PdfReaderError, "timed out"):
            with patch(
                "app.pipelines.pdf_readers.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["python"], 1),
            ):
                OpenDataLoaderPdfReader()._run_convert({}, 1)

    def test_opendataloader_format_setting_always_preserves_json_output(self) -> None:
        captured: dict[str, object] = {}

        def fake_run_convert(_reader: OpenDataLoaderPdfReader, args: dict, _timeout_seconds: int) -> None:
            captured["format"] = args["format"]
            output_dir = Path(args["output_dir"])
            (output_dir / "fixture.json").write_text(
                '{"number of pages": 1, "kids": [{"type": "paragraph", "page number": 1, "content": "format smoke"}]}',
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "notice.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with PdfReaderEnv(PDF_READER_ODL_FORMAT="text"):
                with patch.object(OpenDataLoaderPdfReader, "status", return_value={"available": True, "errors": []}):
                    with patch.object(OpenDataLoaderPdfReader, "_run_convert", fake_run_convert):
                        result = OpenDataLoaderPdfReader().read(pdf_path)

        self.assertEqual(captured["format"], ["text", "json"])
        self.assertIn("format smoke", result.text)

    def test_auto_reader_falls_back_to_pymupdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "notice.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            page.insert_text((30, 50), "Procurement fallback smoke test")
            doc.save(pdf_path)
            doc.close()

            with patch.object(OpenDataLoaderPdfReader, "read", side_effect=PdfReaderError("forced failure")):
                result = AutoPdfReader().read(pdf_path)

        self.assertEqual(result.metadata["engine"], "PyMuPDF")
        self.assertEqual(result.metadata["fallback_from"], "opendataloader-pdf")
        self.assertIn("forced failure", result.metadata["fallback_reason"])
        self.assertIn("fallback smoke test", result.text)

    def test_forced_pymupdf_reader_still_extracts_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "notice.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            page.insert_text((30, 50), "PyMuPDF forced smoke test")
            doc.save(pdf_path)
            doc.close()

            result = PyMuPdfPdfReader().read(pdf_path)

        self.assertEqual(result.metadata["engine"], "PyMuPDF")
        self.assertIn("forced smoke test", result.text)

    def test_pymupdf_reader_records_page_offsets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "multi-page.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            page.insert_text((30, 50), "first page text")
            page = doc.new_page(width=300, height=200)
            page.insert_text((30, 50), "second page text")
            doc.save(pdf_path)
            doc.close()

            result = PyMuPdfPdfReader().read(pdf_path)

        pages = result.metadata["pages"]
        self.assertEqual(result.text, "first page text\n\nsecond page text")
        self.assertEqual(pages[0]["char_start"], result.text.index("first page"))
        self.assertEqual(pages[1]["char_start"], result.text.index("second page"))
        self.assertEqual(pages[1]["char_end"], len(result.text))

    def test_real_opendataloader_reader_extracts_pdf_when_available(self) -> None:
        status = OpenDataLoaderPdfReader().status()
        if not status["available"]:
            self.skipTest("; ".join(status["errors"]))
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "notice.pdf"
            doc = fitz.open()
            page = doc.new_page(width=300, height=200)
            page.insert_text((30, 50), "OpenDataLoader smoke test")
            doc.save(pdf_path)
            doc.close()

            with PdfReaderEnv(PDF_READER_ODL_TIMEOUT_SECONDS="60"):
                result = OpenDataLoaderPdfReader().read(pdf_path)

        self.assertEqual(result.metadata["engine"], "opendataloader-pdf")
        self.assertEqual(result.metadata["page_count"], 1)
        self.assertIn("OpenDataLoader", result.text)


if __name__ == "__main__":
    unittest.main()
