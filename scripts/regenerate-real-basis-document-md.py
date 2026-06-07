from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_SAMPLE_DIR = BACKEND_DIR / "tests" / "real-basis-document-samples"
DEFAULT_MANIFEST = DEFAULT_SAMPLE_DIR / "manifest.json"
DEFAULT_OUTPUT = DEFAULT_SAMPLE_DIR / "regenerated-basis-document.md"
DEFAULT_REPORT = DEFAULT_SAMPLE_DIR / "md-regeneration-comparison-report.json"
COMPARE_SCRIPT = ROOT_DIR / "scripts" / "compare-real-basis-document-txt.py"


def load_compare_module():
    spec = importlib.util.spec_from_file_location("real_basis_reference_compare", COMPARE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load compare script: {COMPARE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_pdf_from_manifest(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        pdfs = sorted(DEFAULT_SAMPLE_DIR.glob("*.pdf"))
        if pdfs:
            return pdfs[0]
        raise FileNotFoundError(f"Manifest not found and no PDF sample exists: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample = manifest.get("sample") if isinstance(manifest.get("sample"), dict) else manifest
    saved_path = Path(sample.get("saved_path", ""))
    pdf_path = saved_path if saved_path.is_absolute() else ROOT_DIR / saved_path
    if pdf_path.exists():
        return pdf_path
    pdfs = sorted(DEFAULT_SAMPLE_DIR.glob("*.pdf"))
    if pdfs:
        return pdfs[0]
    raise FileNotFoundError(f"PDF sample not found from manifest: {pdf_path}")


def normalize_text(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2024", ".")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def normalize_block_text(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def logical_page_regions(page: fitz.Page, physical_page_number: int) -> list[dict[str, Any]]:
    rect = page.rect
    if physical_page_number == 1:
        return [{"area": "전체", "clip": fitz.Rect(rect), "column_index": 0}]

    midpoint = (rect.x0 + rect.x1) / 2
    return [
        {"area": "좌측", "clip": fitz.Rect(rect.x0, rect.y0, midpoint, rect.y1), "column_index": 0},
        {"area": "우측", "clip": fitz.Rect(midpoint, rect.y0, rect.x1, rect.y1), "column_index": 1},
    ]


def block_sort_key(block: tuple) -> tuple[int, float, float]:
    return (0, float(block[1]), float(block[0]))


def extract_text_for_clip(page: fitz.Page, clip: fitz.Rect) -> str:
    blocks = page.get_text("blocks", clip=clip, sort=False)
    text_parts = [
        normalize_block_text(block[4])
        for block in sorted(blocks, key=block_sort_key)
        if len(block) > 4 and block[4]
    ]
    return normalize_text("\n".join(part for part in text_parts if part))


def clean_cell(value: Any) -> str:
    text = normalize_text("" if value is None else str(value))
    text = text.replace("|", "\\|")
    text = text.replace("\n", "<br>")
    return text.strip()


def normalize_table_rows(rows: list[list[Any]]) -> list[list[str]]:
    cleaned_rows: list[list[str]] = []
    max_cols = max((len(row) for row in rows if row), default=0)
    if max_cols <= 0:
        return []
    for row in rows:
        normalized = [clean_cell(value) for value in row]
        normalized.extend([""] * (max_cols - len(normalized)))
        if any(cell for cell in normalized):
            cleaned_rows.append(normalized)
    return cleaned_rows


def table_to_markdown(rows: list[list[Any]]) -> str:
    cleaned_rows = normalize_table_rows(rows)
    if not cleaned_rows:
        return ""
    max_cols = max(len(row) for row in cleaned_rows)
    header = cleaned_rows[0]
    if not any(header):
        header = [f"열 {index + 1}" for index in range(max_cols)]
    body = cleaned_rows[1:] if len(cleaned_rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(max_cols)) + " |",
    ]
    for row in body:
        row = row + [""] * (max_cols - len(row))
        lines.append("| " + " | ".join(row[:max_cols]) + " |")
    if not body:
        lines.append("| " + " | ".join("" for _ in range(max_cols)) + " |")
    return "\n".join(lines)


def extract_tables_for_clip(page: fitz.Page, clip: fitz.Rect) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    try:
        found = page.find_tables(clip=clip).tables
    except Exception as exc:
        return [{"error": str(exc), "rows": [], "markdown": ""}]

    for table in found:
        rows = table.extract()
        cleaned_rows = normalize_table_rows(rows)
        markdown = table_to_markdown(rows)
        if not cleaned_rows or not markdown:
            continue
        bbox = getattr(table, "bbox", None)
        tables.append(
            {
                "bbox": list(bbox) if bbox else [],
                "row_count": len(cleaned_rows),
                "column_count": max((len(row) for row in cleaned_rows), default=0),
                "rows": cleaned_rows,
                "markdown": markdown,
            }
        )
    return tables


def markdown_table_rows(text: str) -> list[str]:
    rows: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "|" not in line[1:]:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(line)
    return rows


def markdown_table_count(text: str) -> int:
    count = 0
    lines = (text or "").splitlines()
    for previous, current in zip(lines, lines[1:]):
        if previous.strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", current):
            count += 1
    return count


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def row_coverage(base_rows: list[str], target_text: str, *, limit: int = 20000) -> tuple[float, list[str]]:
    if not base_rows:
        return 1.0, []
    target_compact = compact_text(target_text)
    selected = base_rows[:limit]
    misses: list[str] = []
    hits = 0
    for row in selected:
        row_compact = compact_text(row)
        if row_compact and row_compact in target_compact:
            hits += 1
        elif len(misses) < 10:
            misses.append(row)
    return hits / len(selected), misses


def render_pdf_to_markdown(pdf_path: Path) -> tuple[str, dict[str, Any]]:
    lines: list[str] = [
        "# 서비스 재생성 기준문서 Markdown",
        "",
        f"- 원본 PDF: `{pdf_path.name}`",
        "- 추출 방식: PyMuPDF 텍스트 블록 + 좌/우 논리페이지 분리 + `find_tables()` 표 감지",
        "- 주의: 이 파일은 RAG 추출 로직 보강을 위한 비교 산출물입니다.",
        "",
    ]
    logical_page_number = 0
    table_count = 0
    table_row_count = 0
    text_char_count = 0
    per_page: list[dict[str, Any]] = []

    with fitz.open(pdf_path) as doc:
        physical_page_count = len(doc)
        for page_index, page in enumerate(doc, start=1):
            for region in logical_page_regions(page, page_index):
                logical_page_number += 1
                clip = region["clip"]
                area = region["area"]
                text = extract_text_for_clip(page, clip)
                tables = extract_tables_for_clip(page, clip)
                text_char_count += len(text)
                table_count += len([table for table in tables if table.get("markdown")])
                table_row_count += sum(int(table.get("row_count") or 0) for table in tables)
                per_page.append(
                    {
                        "physical_page": page_index,
                        "logical_page": logical_page_number,
                        "area": area,
                        "text_char_count": len(text),
                        "table_count": len([table for table in tables if table.get("markdown")]),
                        "table_row_count": sum(int(table.get("row_count") or 0) for table in tables),
                    }
                )

                lines.extend(
                    [
                        f"## 원문 페이지 {logical_page_number}",
                        "",
                        f"- PDF쪽: {page_index}",
                        f"- 영역: {area}",
                        "",
                        "### 원문 텍스트",
                        "",
                        text or "_추출 텍스트 없음_",
                        "",
                    ]
                )
                if tables:
                    lines.extend(["### 감지 표", ""])
                    rendered_table_index = 0
                    for table in tables:
                        markdown = table.get("markdown", "")
                        if not markdown:
                            continue
                        rendered_table_index += 1
                        lines.extend(
                            [
                                f"#### 표 {logical_page_number}-{rendered_table_index}",
                                "",
                                markdown,
                                "",
                            ]
                        )
                lines.append("")

    markdown = "\n".join(lines).strip() + "\n"
    stats = {
        "physical_page_count": physical_page_count,
        "logical_page_count": logical_page_number,
        "text_char_count": text_char_count,
        "table_count": table_count,
        "table_row_count": table_row_count,
        "markdown_char_count": len(markdown),
        "markdown_table_count": markdown_table_count(markdown),
        "markdown_table_row_count": len(markdown_table_rows(markdown)),
        "per_page": per_page,
    }
    return markdown, stats


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    compare = load_compare_module()
    pdf_path = Path(args.pdf) if args.pdf else load_pdf_from_manifest(Path(args.manifest))
    reference_path = Path(args.reference_md)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not reference_path.exists():
        raise FileNotFoundError(f"Reference MD not found: {reference_path}")

    regenerated_md, generation_stats = render_pdf_to_markdown(pdf_path)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(regenerated_md, encoding="utf-8")

    reference_md, reference_metadata = compare.read_reference_file(reference_path)
    metrics = compare.compare_texts(regenerated_md, reference_md, ngram_size=args.ngram_size)
    regenerated_rows = markdown_table_rows(regenerated_md)
    reference_rows = markdown_table_rows(reference_md)
    regenerated_row_coverage, regenerated_missing_rows = row_coverage(regenerated_rows, reference_md)
    reference_row_coverage, reference_missing_rows = row_coverage(reference_rows, regenerated_md)
    qa_errors: list[str] = []
    if generation_stats["logical_page_count"] < args.min_logical_pages:
        qa_errors.append("Logical page count is below threshold.")
    if generation_stats["table_count"] < args.min_tables:
        qa_errors.append("Detected table count is below threshold.")
    if metrics["service_token_multiset_recall_in_reference"] < args.min_service_token_recall:
        qa_errors.append("Regenerated MD token recall in reference MD is below threshold.")

    return {
        "schema_version": "real_basis_md_regeneration_comparison_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "pdf_path": pdf_path.resolve().as_posix(),
            "reference_md_path": reference_path.resolve().as_posix(),
            "output_md_path": output_path.resolve().as_posix(),
            "ngram_size": args.ngram_size,
        },
        "reference_metadata": reference_metadata,
        "generation": generation_stats,
        "reference_markdown": {
            "char_count": len(reference_md),
            "markdown_table_count": markdown_table_count(reference_md),
            "markdown_table_row_count": len(reference_rows),
        },
        "metrics": metrics,
        "table_metrics": {
            "regenerated_table_row_coverage_in_reference": round(regenerated_row_coverage, 4),
            "reference_table_row_coverage_in_regenerated": round(reference_row_coverage, 4),
            "regenerated_missing_row_examples": regenerated_missing_rows,
            "reference_missing_row_examples": reference_missing_rows,
        },
        "qa": {
            "passed": not qa_errors,
            "errors": qa_errors,
            "thresholds": {
                "min_logical_pages": args.min_logical_pages,
                "min_tables": args.min_tables,
                "min_service_token_recall": args.min_service_token_recall,
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate Markdown from a real basis PDF and compare it with a reference MD.")
    parser.add_argument("--reference-md", required=True, help="Reference Markdown path.")
    parser.add_argument("--pdf", default="", help="PDF path. Defaults to the real-basis manifest PDF.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Real-basis sample manifest path.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Regenerated Markdown output path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Comparison report output path.")
    parser.add_argument("--ngram-size", type=int, default=5)
    parser.add_argument("--min-logical-pages", type=int, default=900)
    parser.add_argument("--min-tables", type=int, default=100)
    parser.add_argument("--min-service-token-recall", type=float, default=0.70)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when QA thresholds fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics = report["metrics"]
    print(
        json.dumps(
            {
                "status": "passed" if report["qa"]["passed"] else "failed",
                "output": report["inputs"]["output_md_path"],
                "report": report_path.as_posix(),
                "logical_page_count": report["generation"]["logical_page_count"],
                "table_count": report["generation"]["table_count"],
                "table_row_count": report["generation"]["table_row_count"],
                "regenerated_char_count": report["generation"]["markdown_char_count"],
                "reference_char_count": report["reference_markdown"]["char_count"],
                "regenerated_token_recall_in_reference": metrics["service_token_multiset_recall_in_reference"],
                "reference_token_recall_in_regenerated": metrics["reference_token_multiset_recall_in_service"],
                "regenerated_table_row_coverage_in_reference": report["table_metrics"]["regenerated_table_row_coverage_in_reference"],
                "reference_table_row_coverage_in_regenerated": report["table_metrics"]["reference_table_row_coverage_in_regenerated"],
                "errors": report["qa"]["errors"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if args.strict and not report["qa"]["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

