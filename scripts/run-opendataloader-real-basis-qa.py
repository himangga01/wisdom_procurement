from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_SAMPLE_DIR = BACKEND_DIR / "tests" / "real-basis-document-samples"
DEFAULT_MANIFEST = DEFAULT_SAMPLE_DIR / "manifest.json"
DEFAULT_OUTPUT = DEFAULT_SAMPLE_DIR / "opendataloader-basis-qa-report.json"
DEFAULT_OUTPUT_MD = DEFAULT_SAMPLE_DIR / "opendataloader-regenerated-basis-document.md"
DEFAULT_USER_PDF = Path(
    "C:/Users/HOONJAE/Documents/카카오톡 받은 파일/"
    "전체합본_(제2025-116호)중소기업자간_경쟁제품_직접생산_확인기준(2025.11.19.).pdf"
)
DEFAULT_REFERENCE_MD = Path(
    "C:/Users/HOONJAE/Documents/카카오톡 받은 파일/"
    "중소기업자간_경쟁제품_직접생산_확인기준_전체추출.md"
)
COMPARE_SCRIPT = ROOT_DIR / "scripts" / "compare-real-basis-document-txt.py"


def load_compare_module():
    spec = importlib.util.spec_from_file_location("real_basis_reference_compare", COMPARE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load compare script: {COMPARE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_pdf_path(raw_pdf: str = "") -> Path:
    if raw_pdf:
        path = Path(raw_pdf)
        if path.exists():
            return path
    if DEFAULT_USER_PDF.exists():
        return DEFAULT_USER_PDF
    if DEFAULT_MANIFEST.exists():
        manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        sample = manifest.get("sample") if isinstance(manifest.get("sample"), dict) else manifest
        saved_path = Path(sample.get("saved_path", ""))
        pdf_path = saved_path if saved_path.is_absolute() else ROOT_DIR / saved_path
        if pdf_path.exists():
            return pdf_path
    pdfs = sorted(DEFAULT_SAMPLE_DIR.glob("*.pdf"))
    if pdfs:
        return pdfs[0]
    raise FileNotFoundError("Real basis PDF was not found.")


def markdown_table_rows(text: str) -> list[str]:
    rows: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "|" not in line[1:]:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(cell.replace(":", "").replace("-", "") == "" and "---" in cell for cell in cells):
            continue
        rows.append(line)
    return rows


def compact_text(text: str) -> str:
    return "".join((text or "").split())


def row_coverage(base_rows: list[str], target_text: str, *, limit: int = 30000) -> tuple[float, list[str]]:
    if not base_rows:
        return 1.0, []
    target = compact_text(target_text)
    selected = base_rows[:limit]
    hits = 0
    misses: list[str] = []
    for row in selected:
        if compact_text(row) in target:
            hits += 1
        elif len(misses) < 10:
            misses.append(row)
    return hits / len(selected), misses


def row_token_coverage(
    base_rows: list[str],
    target_text: str,
    token_fn,
    *,
    limit: int = 30000,
    min_row_recall: float = 0.65,
) -> tuple[float, list[str]]:
    if not base_rows:
        return 1.0, []
    target_tokens = set(token_fn(target_text))
    selected = base_rows[:limit]
    hits = 0
    misses: list[str] = []
    for row in selected:
        row_tokens = set(token_fn(row))
        if not row_tokens:
            hits += 1
            continue
        recall = len(row_tokens & target_tokens) / len(row_tokens)
        if recall >= min_row_recall:
            hits += 1
        elif len(misses) < 10:
            misses.append(row)
    return hits / len(selected), misses


def counter_recall(base: Counter[str], target: Counter[str]) -> float:
    total = sum(base.values())
    if total <= 0:
        return 1.0
    matched = sum(min(count, target.get(item, 0)) for item, count in base.items())
    return matched / total


def run(args: argparse.Namespace) -> dict[str, Any]:
    sys.path.insert(0, str(BACKEND_DIR))
    os.environ["PDF_READER_ENGINE"] = args.engine
    os.environ["PDF_READER_ODL_TIMEOUT_SECONDS"] = str(args.timeout_seconds)
    os.environ["PDF_READER_ODL_THREADS"] = str(args.threads)
    os.environ["PDF_READER_ODL_TABLE_METHOD"] = args.table_method

    from app.pipelines.basis_document import (  # noqa: PLC0415
        normalize_basis_text,
        split_basis_tables_into_row_chunks,
        split_basis_text_into_chunks,
    )
    from app.pipelines.parser import extract_document  # noqa: PLC0415

    compare = load_compare_module()
    pdf_path = resolve_pdf_path(args.pdf)
    started_at = datetime.now(timezone.utc)
    parsed = extract_document(pdf_path)
    elapsed_seconds = (datetime.now(timezone.utc) - started_at).total_seconds()
    normalized_text = normalize_basis_text(parsed.text)
    paragraph_chunks = split_basis_text_into_chunks(normalized_text, parsed.metadata) if normalized_text else []
    table_chunks = split_basis_tables_into_row_chunks(parsed.metadata, start_index=len(paragraph_chunks))

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pdf_path": str(pdf_path),
        "engine": parsed.metadata.get("engine"),
        "fallback_from": parsed.metadata.get("fallback_from", ""),
        "fallback_reason": parsed.metadata.get("fallback_reason", ""),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "page_count": parsed.metadata.get("page_count", 0),
        "char_count": len(parsed.text),
        "normalized_char_count": len(normalized_text),
        "table_count": parsed.metadata.get("table_count", 0),
        "table_row_count": parsed.metadata.get("table_row_count", 0),
        "paragraph_chunk_count": len(paragraph_chunks),
        "table_row_chunk_count": len(table_chunks),
        "parser_options": parsed.metadata.get("options", {}),
        "regenerated_markdown_path": str(Path(args.output_md)),
        "comparison": {},
        "qa": {
            "errors": [],
            "warnings": [],
            "thresholds": {
                "min_page_count": args.min_page_count,
                "min_table_count": args.min_table_count,
                "min_table_row_chunks": args.min_table_row_chunks,
                "min_reference_table_row_coverage": args.min_reference_table_row_coverage,
                "min_reference_table_row_token_coverage": args.min_reference_table_row_token_coverage,
                "min_row_token_recall": args.min_row_token_recall,
            },
        },
    }

    output_md_path = Path(args.output_md)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(parsed.text, encoding="utf-8")

    reference_path = Path(args.reference_md) if args.reference_md else DEFAULT_REFERENCE_MD
    if reference_path.exists():
        reference_text, reference_metadata = compare.read_reference_file(reference_path)
        service_text = compare.normalize_reference_text(parsed.text)
        reference_normalized = compare.normalize_reference_text(reference_text)
        service_tokens = Counter(compare.tokens(service_text))
        reference_tokens = Counter(compare.tokens(reference_normalized))
        service_rows = markdown_table_rows(parsed.text)
        reference_rows = markdown_table_rows(reference_text)
        service_row_coverage, service_missing = row_coverage(service_rows, reference_text)
        reference_row_coverage, reference_missing = row_coverage(reference_rows, parsed.text)
        service_row_token_coverage, service_token_missing = row_token_coverage(
            service_rows,
            reference_text,
            compare.tokens,
            min_row_recall=args.min_row_token_recall,
        )
        reference_row_token_coverage, reference_token_missing = row_token_coverage(
            reference_rows,
            parsed.text,
            compare.tokens,
            min_row_recall=args.min_row_token_recall,
        )
        report["comparison"] = {
            "reference_path": str(reference_path),
            "reference_metadata": reference_metadata,
            "reference_char_count": len(reference_normalized),
            "service_token_recall_in_reference": round(counter_recall(service_tokens, reference_tokens), 4),
            "reference_token_recall_in_service": round(counter_recall(reference_tokens, service_tokens), 4),
            "service_markdown_table_row_count": len(service_rows),
            "reference_markdown_table_row_count": len(reference_rows),
            "service_table_row_coverage_in_reference": round(service_row_coverage, 4),
            "reference_table_row_coverage_in_service": round(reference_row_coverage, 4),
            "service_table_row_token_coverage_in_reference": round(service_row_token_coverage, 4),
            "reference_table_row_token_coverage_in_service": round(reference_row_token_coverage, 4),
            "row_token_min_recall": args.min_row_token_recall,
            "missing_service_table_rows": service_missing,
            "missing_reference_table_rows": reference_missing,
            "missing_service_table_rows_by_token": service_token_missing,
            "missing_reference_table_rows_by_token": reference_token_missing,
        }

    qa_errors: list[str] = []
    if int(report["page_count"] or 0) < args.min_page_count:
        qa_errors.append("page_count is below threshold.")
    if int(report["table_count"] or 0) < args.min_table_count:
        qa_errors.append("table_count is below threshold.")
    if int(report["table_row_chunk_count"] or 0) < args.min_table_row_chunks:
        qa_errors.append("table_row_chunk_count is below threshold.")
    reference_coverage = float(report.get("comparison", {}).get("reference_table_row_coverage_in_service") or 0)
    reference_token_coverage = float(
        report.get("comparison", {}).get("reference_table_row_token_coverage_in_service") or 0
    )
    if report.get("comparison") and reference_coverage < args.min_reference_table_row_coverage:
        report["qa"]["warnings"].append("reference exact table row coverage is below target.")
    if report.get("comparison") and reference_token_coverage < args.min_reference_table_row_token_coverage:
        qa_errors.append("reference table row token coverage is below threshold.")
    report["qa"]["errors"] = qa_errors
    report["qa"]["status"] = "failed" if qa_errors else "passed"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenDataLoader QA against the fixed real basis PDF.")
    parser.add_argument("--pdf", default="")
    parser.add_argument("--reference-md", default=str(DEFAULT_REFERENCE_MD))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--engine", choices=["opendataloader", "auto", "pymupdf"], default="opendataloader")
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--table-method", default="cluster")
    parser.add_argument("--min-page-count", type=int, default=400)
    parser.add_argument("--min-table-count", type=int, default=100)
    parser.add_argument("--min-table-row-chunks", type=int, default=1000)
    parser.add_argument("--min-reference-table-row-coverage", type=float, default=0.70)
    parser.add_argument("--min-reference-table-row-token-coverage", type=float, default=0.80)
    parser.add_argument("--min-row-token-recall", type=float, default=0.65)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run(args)
    print(
        json.dumps(
            {
                "status": report["qa"]["status"],
                "output": args.output,
                "engine": report["engine"],
                "fallback_from": report["fallback_from"],
                "elapsed_seconds": report["elapsed_seconds"],
                "page_count": report["page_count"],
                "table_count": report["table_count"],
                "table_row_count": report["table_row_count"],
                "table_row_chunk_count": report["table_row_chunk_count"],
                "regenerated_markdown_path": report["regenerated_markdown_path"],
                "comparison": report.get("comparison", {}),
                "errors": report["qa"]["errors"],
                "warnings": report["qa"].get("warnings", []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.strict and report["qa"]["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
