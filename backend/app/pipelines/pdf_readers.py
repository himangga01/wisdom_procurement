from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from app.core.logging import get_logger, log_event, log_exception


ODL_ENGINE_NAME = "opendataloader-pdf"
PYMUPDF_ENGINE_NAME = "PyMuPDF"
DEFAULT_ODL_VERSION = "2.4.7"
LOGGER = get_logger("pipelines.pdf_readers")


class PdfReaderError(RuntimeError):
    """Raised when a configured PDF reader cannot complete conversion."""


@dataclass(frozen=True)
class PdfReadResult:
    text: str
    metadata: dict[str, Any]


def read_pdf_document(file_path: str | Path) -> PdfReadResult:
    engine = _configured_engine()

    path = Path(file_path)
    log_event(
        LOGGER,
        "pdf_reader.started",
        domain="pdf_reader",
        configured_engine=engine,
        file_name=path.name,
        file_size_bytes=path.stat().st_size if path.exists() else 0,
    )
    if engine == "pymupdf":
        result = PyMuPdfPdfReader().read(path)
        log_event(
            LOGGER,
            "pdf_reader.completed",
            domain="pdf_reader",
            engine=result.metadata.get("engine"),
            file_name=path.name,
            page_count=result.metadata.get("page_count"),
            char_count=len(result.text),
            table_count=result.metadata.get("table_count"),
        )
        return result
    if engine == "opendataloader":
        result = OpenDataLoaderPdfReader().read(path)
        log_event(
            LOGGER,
            "pdf_reader.completed",
            domain="pdf_reader",
            engine=result.metadata.get("engine"),
            file_name=path.name,
            page_count=result.metadata.get("page_count"),
            char_count=len(result.text),
            table_count=result.metadata.get("table_count"),
        )
        return result
    result = AutoPdfReader().read(path)
    log_event(
        LOGGER,
        "pdf_reader.completed",
        domain="pdf_reader",
        engine=result.metadata.get("engine"),
        fallback_from=result.metadata.get("fallback_from", ""),
        file_name=path.name,
        page_count=result.metadata.get("page_count"),
        char_count=len(result.text),
        table_count=result.metadata.get("table_count"),
    )
    return result


def pdf_reader_status() -> dict[str, Any]:
    odl = OpenDataLoaderPdfReader()
    return {
        "configured_engine": _configured_engine(),
        "opendataloader": odl.status(),
        "pymupdf": {"available": True, "engine": PYMUPDF_ENGINE_NAME},
        "fallback_enabled": _bool_env("PDF_READER_ALLOW_PYMUPDF_FALLBACK", True),
    }


class PyMuPdfPdfReader:
    def read(self, path: Path) -> PdfReadResult:
        page_texts: list[str] = []
        page_metadata: list[dict[str, Any]] = []

        with fitz.open(path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                blocks = _order_blocks_for_reading(page, page.get_text("blocks", sort=False))
                block_texts = [_normalize_block_text(block[4]) for block in blocks if len(block) > 4 and block[4]]
                page_text = _normalize_procurement_text("\n".join(x for x in block_texts if x))
                page_texts.append(page_text)
                page_metadata.append(
                    {
                        "page_number": page_index,
                        "char_count": len(page_text),
                        "block_count": len(block_texts),
                    }
                )

        text_cursor = 0
        has_rendered_page = False
        for page_text, metadata in zip(page_texts, page_metadata):
            if page_text:
                if has_rendered_page:
                    text_cursor += 2
                metadata["char_start"] = text_cursor
                text_cursor += len(page_text)
                metadata["char_end"] = text_cursor
                has_rendered_page = True
            else:
                metadata["char_start"] = text_cursor
                metadata["char_end"] = text_cursor

        text = _normalize_procurement_text("\n\n".join(x for x in page_texts if x))
        return PdfReadResult(
            text=text,
            metadata={
                "engine": PYMUPDF_ENGINE_NAME,
                "page_count": len(page_metadata),
                "char_count": len(text),
                "pages": page_metadata,
                "table_count": 0,
                "table_row_count": 0,
                "needs_ocr": len(text.strip()) < 80,
            },
        )


class OpenDataLoaderPdfReader:
    def read(self, path: Path) -> PdfReadResult:
        status = self.status()
        if not status["available"]:
            log_event(
                LOGGER,
                "pdf_reader.opendataloader.unavailable",
                level="warning",
                domain="pdf_reader",
                file_name=path.name,
                errors=status["errors"],
            )
            raise PdfReaderError("; ".join(status["errors"]) or "OpenDataLoader PDF is unavailable.")

        timeout_seconds = _int_env("PDF_READER_ODL_TIMEOUT_SECONDS", 180, minimum=1)
        table_method = os.getenv("PDF_READER_ODL_TABLE_METHOD", "cluster").strip() or "cluster"
        reading_order = os.getenv("PDF_READER_ODL_READING_ORDER", "xycut").strip() or "xycut"
        threads = os.getenv("PDF_READER_ODL_THREADS", "1").strip() or "1"
        output_format = _list_env("PDF_READER_ODL_FORMAT", ["markdown", "json"])
        if "json" not in output_format:
            output_format.append("json")

        with tempfile.TemporaryDirectory(prefix="wisdom_odl_pdf_") as temp_dir:
            output_dir = Path(temp_dir)
            args = {
                "input_path": str(path),
                "output_dir": str(output_dir),
                "format": output_format,
                "quiet": True,
                "table_method": table_method,
                "reading_order": reading_order,
                "image_output": "off",
                "threads": threads,
            }
            log_event(
                LOGGER,
                "pdf_reader.opendataloader.started",
                domain="pdf_reader",
                file_name=path.name,
                options={
                    "table_method": table_method,
                    "reading_order": reading_order,
                    "format": output_format,
                    "threads": threads,
                    "timeout_seconds": timeout_seconds,
                },
            )
            self._run_convert(args, timeout_seconds)
            json_path = _first_output(output_dir, ".json")
            md_path = _first_output(output_dir, ".md")
            if not json_path:
                raise PdfReaderError("OpenDataLoader did not produce a JSON output.")

            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise PdfReaderError(f"Unable to read OpenDataLoader JSON output: {exc}") from exc

            markdown = md_path.read_text(encoding="utf-8", errors="replace") if md_path else ""
            rendered_text, pages, tables = render_opendataloader_payload(payload)
            text = _normalize_odl_text(rendered_text or markdown)
            if not text and markdown:
                text = _normalize_odl_text(markdown)
            if not text:
                text = _normalize_odl_text(_extract_all_content(payload))

            table_count = len(tables)
            table_row_count = sum(int(table.get("row_count") or 0) for table in tables)
            page_count = _int_value(payload.get("number of pages"), len(pages))
            log_event(
                LOGGER,
                "pdf_reader.opendataloader.completed",
                domain="pdf_reader",
                file_name=path.name,
                page_count=page_count,
                char_count=len(text),
                table_count=table_count,
                table_row_count=table_row_count,
            )

            return PdfReadResult(
                text=text,
                metadata={
                    "engine": ODL_ENGINE_NAME,
                    "engine_version": os.getenv("PDF_READER_ODL_VERSION", DEFAULT_ODL_VERSION),
                    "page_count": page_count,
                    "char_count": len(text),
                    "markdown_char_count": len(markdown),
                    "table_count": table_count,
                    "table_row_count": table_row_count,
                    "pages": pages,
                    "tables": tables,
                    "needs_ocr": len(text.strip()) < 80,
                    "options": {
                        "table_method": table_method,
                        "reading_order": reading_order,
                        "format": output_format,
                        "threads": threads,
                        "timeout_seconds": timeout_seconds,
                    },
                },
            )

    def status(self) -> dict[str, Any]:
        errors: list[str] = []
        if importlib.util.find_spec("opendataloader_pdf") is None:
            errors.append("Python package opendataloader-pdf is not installed.")
        java_probe = _run_java_version_probe()
        if java_probe is None:
            errors.append("Java executable was not found.")
        elif isinstance(java_probe, str):
            errors.append(java_probe)
        elif java_probe.returncode != 0:
            errors.append((java_probe.stderr or java_probe.stdout or "java -version failed").strip())
        java_version = ""
        if java_probe is not None and not isinstance(java_probe, str):
            java_version = (java_probe.stderr or java_probe.stdout or "").splitlines()[0] if (java_probe.stderr or java_probe.stdout) else ""
        return {
            "available": not errors,
            "engine": ODL_ENGINE_NAME,
            "expected_version": os.getenv("PDF_READER_ODL_VERSION", DEFAULT_ODL_VERSION),
            "java_version": java_version,
            "errors": errors,
        }

    def _run_convert(self, args: dict[str, Any], timeout_seconds: int) -> None:
        script = (
            "import json, sys\n"
            "from opendataloader_pdf import convert\n"
            "kwargs = json.loads(sys.argv[1])\n"
            "convert(**kwargs)\n"
        )
        try:
            process = subprocess.run(
                [sys.executable, "-c", script, json.dumps(args, ensure_ascii=False)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            log_exception(
                LOGGER,
                "pdf_reader.opendataloader.timeout",
                exc,
                domain="pdf_reader",
                file_name=Path(args.get("input_path", "")).name,
                timeout_seconds=timeout_seconds,
            )
            raise PdfReaderError(f"OpenDataLoader timed out after {timeout_seconds} seconds.") from exc
        except OSError as exc:
            log_exception(
                LOGGER,
                "pdf_reader.opendataloader.process_failed",
                exc,
                domain="pdf_reader",
                file_name=Path(args.get("input_path", "")).name,
            )
            raise PdfReaderError(f"OpenDataLoader process failed: {exc}") from exc
        if process.returncode != 0:
            output = "\n".join(part.strip() for part in [process.stdout, process.stderr] if part.strip())
            log_event(
                LOGGER,
                "pdf_reader.opendataloader.failed",
                level="error",
                domain="pdf_reader",
                file_name=Path(args.get("input_path", "")).name,
                returncode=process.returncode,
                message=output[:1200] or f"OpenDataLoader exited with code {process.returncode}.",
            )
            raise PdfReaderError(output[:1200] or f"OpenDataLoader exited with code {process.returncode}.")


class AutoPdfReader:
    def read(self, path: Path) -> PdfReadResult:
        fallback_enabled = _bool_env("PDF_READER_ALLOW_PYMUPDF_FALLBACK", True)
        try:
            return OpenDataLoaderPdfReader().read(path)
        except Exception as exc:
            if not fallback_enabled:
                log_exception(
                    LOGGER,
                    "pdf_reader.auto.failed",
                    exc,
                    domain="pdf_reader",
                    file_name=path.name,
                    fallback_enabled=False,
                )
                raise
            log_exception(
                LOGGER,
                "pdf_reader.fallback.pymupdf",
                exc,
                domain="pdf_reader",
                file_name=path.name,
                fallback_enabled=True,
            )
            fallback = PyMuPdfPdfReader().read(path)
            fallback.metadata["engine"] = PYMUPDF_ENGINE_NAME
            fallback.metadata["fallback_from"] = ODL_ENGINE_NAME
            fallback.metadata["fallback_reason"] = str(exc)[:1200]
            fallback.metadata["reader_mode"] = "auto"
            return fallback


def render_opendataloader_payload(payload: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    raw_tables = _collect_tables(payload)
    table_by_object_id = {id(table): _table_to_metadata(table, index + 1) for index, table in enumerate(raw_tables)}
    tables = [table for table in table_by_object_id.values() if is_meaningful_table(table)]

    parts_by_page: dict[int, list[str]] = {}
    table_ids_by_page: dict[int, set[str]] = {}
    _collect_page_parts(payload, parts_by_page, table_by_object_id, {table["table_id"] for table in tables}, table_ids_by_page)

    pages: list[dict[str, Any]] = []
    rendered_pages: list[str] = []
    page_numbers = sorted(parts_by_page) if parts_by_page else sorted({int(table["page_number"]) for table in tables if table.get("page_number")})
    text_cursor = 0
    has_rendered_page = False
    for page_number in page_numbers:
        page_text = _normalize_odl_text("\n\n".join(part for part in parts_by_page.get(page_number, []) if part))
        if page_text:
            if has_rendered_page:
                text_cursor += 2
            char_start = text_cursor
            text_cursor += len(page_text)
            char_end = text_cursor
            rendered_pages.append(page_text)
            has_rendered_page = True
        else:
            char_start = text_cursor
            char_end = text_cursor
        pages.append(
            {
                "page_number": page_number,
                "char_count": len(page_text),
                "char_start": char_start,
                "char_end": char_end,
                "table_count": len(table_ids_by_page.get(page_number, set())),
            }
        )

    return "\n\n".join(rendered_pages), pages, tables


def is_meaningful_table(table: dict[str, Any]) -> bool:
    row_count = _int_value(table.get("row_count"), 0)
    column_count = _int_value(table.get("column_count"), 0)
    if row_count < 2 or column_count < 2:
        return False
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    cell_texts: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            cell_texts.extend(str(cell) for cell in row.get("cells", []))
    non_empty = [cell for cell in cell_texts if str(cell).strip()]
    if len(non_empty) < 3:
        return False
    joined_header = " ".join(str(cell) for cell in (rows[0].get("cells", []) if rows else [])).lower()
    header_terms = [
        "항목",
        "내용",
        "비고",
        "연번",
        "생산시설",
        "생산공정",
        "세부",
        "설명",
        "품명",
        "기준",
        "item",
        "content",
        "note",
    ]
    if any(term in joined_header for term in header_terms):
        return True
    total_text_length = sum(len(str(cell).strip()) for cell in non_empty)
    return row_count >= 3 and column_count >= 3 and total_text_length >= 40


def table_to_markdown(table: dict[str, Any]) -> str:
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    if not rows:
        return ""
    matrix = [row.get("cells", []) for row in rows if isinstance(row, dict)]
    max_cols = max((len(row) for row in matrix), default=0)
    if max_cols <= 0:
        return ""
    header = [_escape_markdown_cell(cell) for cell in (matrix[0] + [""] * max_cols)[:max_cols]]
    if not any(header):
        header = [f"col_{index + 1}" for index in range(max_cols)]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(max_cols)) + " |",
    ]
    for row in matrix[1:]:
        cells = [_escape_markdown_cell(cell) for cell in (row + [""] * max_cols)[:max_cols]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _collect_page_parts(
    node: Any,
    parts_by_page: dict[int, list[str]],
    table_by_object_id: dict[int, dict[str, Any]],
    allowed_table_ids: set[str],
    table_ids_by_page: dict[int, set[str]],
) -> None:
    if isinstance(node, dict):
        node_type = str(node.get("type", "")).lower()
        if node_type == "table":
            table = table_by_object_id.get(id(node))
            if table and table["table_id"] in allowed_table_ids:
                page_number = _int_value(table.get("page_number"), 0)
                if page_number:
                    parts_by_page.setdefault(page_number, []).append(table_to_markdown(table))
                    table_ids_by_page.setdefault(page_number, set()).add(table["table_id"])
            return
        if node_type in {"paragraph", "heading", "caption", "list item"}:
            text = _clean_text(node.get("content"))
            page_number = _int_value(node.get("page number") or node.get("page_number") or node.get("page"), 0)
            if not text:
                text = _clean_text(_extract_all_content(node))
            if text and page_number:
                prefix = "# " if node_type == "heading" else ""
                parts_by_page.setdefault(page_number, []).append(f"{prefix}{text}")
                return
        for value in node.values():
            _collect_page_parts(value, parts_by_page, table_by_object_id, allowed_table_ids, table_ids_by_page)
    elif isinstance(node, list):
        for item in node:
            _collect_page_parts(item, parts_by_page, table_by_object_id, allowed_table_ids, table_ids_by_page)


def _collect_tables(node: Any) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if str(node.get("type", "")).lower() == "table":
            tables.append(node)
            return tables
        for value in node.values():
            tables.extend(_collect_tables(value))
    elif isinstance(node, list):
        for item in node:
            tables.extend(_collect_tables(item))
    return tables


def _table_to_metadata(table: dict[str, Any], sequence: int) -> dict[str, Any]:
    page_number = _int_value(table.get("page number") or table.get("page_number") or table.get("page"), 0)
    rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(table.get("rows", []) if isinstance(table.get("rows"), list) else [], start=1):
        cells = row.get("cells", []) if isinstance(row, dict) else []
        cell_texts = [_cell_text(cell) if isinstance(cell, dict) else _clean_text(cell) for cell in cells]
        if any(cell_texts):
            rows.append(
                {
                    "row_index": _int_value(row.get("row number") if isinstance(row, dict) else None, row_index),
                    "cells": cell_texts,
                    "bbox": _bbox(row.get("bounding box") if isinstance(row, dict) else None),
                }
            )
    headers = rows[0]["cells"] if rows else []
    table_id = f"p{page_number or 0}-t{sequence}"
    return {
        "table_id": table_id,
        "source_engine": ODL_ENGINE_NAME,
        "page_number": page_number,
        "bbox": _bbox(table.get("bounding box") or table.get("bbox")),
        "row_count": _int_value(table.get("number of rows") or table.get("row_count"), len(rows)),
        "column_count": _int_value(table.get("number of columns") or table.get("column_count"), max((len(row["cells"]) for row in rows), default=0)),
        "headers": headers,
        "rows": rows,
    }


def _cell_text(cell: dict[str, Any]) -> str:
    parts: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if "content" in node:
                text = _clean_text(node.get("content"))
                if text:
                    parts.append(text)
                    return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(cell)
    return _clean_text(" ".join(parts))


def _extract_all_content(node: Any) -> str:
    parts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if "content" in value:
                text = _clean_text(value.get("content"))
                if text:
                    parts.append(text)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(node)
    return "\n".join(parts)


def _first_output(output_dir: Path, suffix: str) -> Path | None:
    matches = sorted(output_dir.glob(f"*{suffix}"))
    return matches[0] if matches else None


def _order_blocks_for_reading(page: fitz.Page, blocks: list[tuple]) -> list[tuple]:
    if not blocks:
        return []

    page_width = float(page.rect.width)
    column_boundary = page_width * 0.52
    has_right_column = any(block[0] >= column_boundary for block in blocks)
    has_left_column = any(block[0] < column_boundary for block in blocks)

    if has_left_column and has_right_column:
        return sorted(blocks, key=lambda block: (0 if block[0] < column_boundary else 1, block[1], block[0]))

    return sorted(blocks, key=lambda block: (block[1], block[0]))


def _normalize_block_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_procurement_text(text: str) -> str:
    text = text.replace("\u2024", ".")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Restore common procurement boundaries flattened by PDF text extraction.
    text = re.sub(r"(?<!\n)(?=\d+\.\s*[가-힣A-Za-z])", "\n", text)
    text = re.sub(r"(?<!\n)(?=[가-힣]\.\s*[가-힣A-Za-z])", "\n", text)
    text = re.sub(r"(?<=[가-힣)])(?=\d{4}\.\s*\d{1,2}\.\s*\d{1,2})", "\n", text)
    text = re.sub(r"(?<=다)(?=\s*[-가-힣])", "\n", text)

    return _normalize_lines_preserving_paragraphs(text)


def _normalize_odl_text(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2024", ".")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return _normalize_lines_preserving_paragraphs(text)


def _normalize_lines_preserving_paragraphs(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    normalized: list[str] = []
    blank_seen = False
    for line in lines:
        if line:
            normalized.append(line)
            blank_seen = False
        elif normalized and not blank_seen:
            normalized.append("")
            blank_seen = True
    return "\n".join(normalized).strip()


def _clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return " ".join(part.strip() for part in text.splitlines() if part.strip()).strip()


def _escape_markdown_cell(value: Any) -> str:
    return _clean_text(value).replace("|", "\\|").replace("\n", "<br>")


def _bbox(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    bbox: list[float] = []
    for item in value[:4]:
        try:
            bbox.append(round(float(item), 3))
        except (TypeError, ValueError):
            return []
    return bbox


def _int_env(name: str, default: int, *, minimum: int = 0) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(value, minimum)


def _run_java_version_probe() -> subprocess.CompletedProcess[str] | str | None:
    if not shutil.which("java"):
        return None
    try:
        return subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "java -version timed out."
    except OSError as exc:
        return f"java -version failed: {exc}"


def _configured_engine() -> str:
    engine = os.getenv("PDF_READER_ENGINE", "auto").strip().lower() or "auto"
    if engine not in {"auto", "opendataloader", "pymupdf"}:
        return "auto"
    return engine


def _list_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return list(default)
    values = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return values or list(default)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
