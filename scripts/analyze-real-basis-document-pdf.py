from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_SAMPLE_DIR = BACKEND_DIR / "tests" / "real-basis-document-samples"
DEFAULT_MANIFEST = DEFAULT_SAMPLE_DIR / "manifest.json"
DEFAULT_REPORT = DEFAULT_SAMPLE_DIR / "extraction-report.json"
DEFAULT_BASELINE = DEFAULT_SAMPLE_DIR / "extraction-baseline.json"

REQUIRED_TERMS = [
    "직접생산",
    "확인기준",
    "중소기업자간",
    "경쟁제품",
    "세부품명",
    "생산시설",
    "검사설비",
]
TABLE_TERMS = ["세부품명", "품명", "제품명", "생산시설", "생산설비", "검사설비", "검사시설", "기준"]
DEFAULT_RAG_QUERIES = [
    "직접생산 확인기준",
    "중소기업자간 경쟁제품",
    "세부품명 직접생산",
    "생산시설 검사설비",
    "공장등록 직접생산",
]


def import_pipeline_helpers():
    sys.path.insert(0, str(BACKEND_DIR))
    from app.pipelines.basis_document import normalize_basis_text, split_basis_text_into_chunks  # noqa: PLC0415
    from app.pipelines.parser import extract_document  # noqa: PLC0415

    return extract_document, normalize_basis_text, split_basis_text_into_chunks


def load_sample(manifest_path: Path) -> tuple[dict[str, Any], Path]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Sample manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample = manifest.get("sample") if isinstance(manifest.get("sample"), dict) else manifest
    saved_path = Path(sample.get("saved_path", ""))
    pdf_path = saved_path if saved_path.is_absolute() else ROOT_DIR / saved_path
    if not pdf_path.exists():
        raise FileNotFoundError(f"Sample PDF not found: {pdf_path}")
    return sample, pdf_path


def extract_raw_page_lines(pdf_path: Path) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            for raw_line in (page.get_text("text") or "").splitlines():
                line = re.sub(r"[ \t]+", " ", raw_line).strip()
                if line:
                    lines.append({"page_number": page_index, "text": line, "raw_text": raw_line})
    return lines


def token_list(text: str) -> list[str]:
    return re.findall(r"[0-9A-Za-z가-힣]{2,}", text or "")


def table_line_score(item: dict[str, Any]) -> int:
    line = item["text"]
    raw_line = item.get("raw_text", line)
    score = 0
    if any(term in line for term in TABLE_TERMS):
        score += 2
    if re.search(r"\d{2,}|[A-Za-z]{2,}", line):
        score += 1
    if len(token_list(line)) >= 4:
        score += 1
    if re.search(r"\t|\||\s{2,}", raw_line):
        score += 1
    if 8 <= len(line) <= 160:
        score += 1
    return score


def table_like_lines(page_lines: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    scored = [
        {
            "page_number": item["page_number"],
            "text": item["text"],
            "score": table_line_score(item),
        }
        for item in page_lines
    ]
    selected = [item for item in scored if item["score"] >= 3]
    selected.sort(key=lambda item: (-item["score"], item["page_number"], item["text"]))
    return selected[:limit]


def query_from_line(line: str) -> str:
    tokens = [token for token in token_list(line) if not token.isdigit()]
    return " ".join(tokens[:6])


def build_table_queries(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    queries: list[dict[str, Any]] = []
    for item in lines:
        query = query_from_line(item["text"])
        if len(query) < 4 or query in seen:
            continue
        seen.add(query)
        queries.append(
            {
                "query": query,
                "source_page": item["page_number"],
                "source_text": item["text"],
            }
        )
        if len(queries) >= 5:
            break
    if len(queries) < 5:
        for query in DEFAULT_RAG_QUERIES:
            if query not in seen:
                queries.append({"query": query, "source_page": None, "source_text": ""})
            if len(queries) >= 5:
                break
    return queries


def coverage_map(text: str, terms: list[str]) -> dict[str, bool]:
    return {term: term in text for term in terms}


def top_terms(text: str, limit: int = 20) -> list[dict[str, Any]]:
    stopwords = {"기준", "확인", "한다", "있는", "없는", "따른", "경우", "제조", "제품"}
    counts = Counter(token for token in token_list(text) if token not in stopwords and not token.isdigit())
    return [{"term": term, "count": count} for term, count in counts.most_common(limit)]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    extract_document, normalize_basis_text, split_basis_text_into_chunks = import_pipeline_helpers()
    sample, pdf_path = load_sample(Path(args.manifest))
    parsed = extract_document(pdf_path)
    normalized_text = normalize_basis_text(parsed.text)
    chunks = split_basis_text_into_chunks(normalized_text, parsed.metadata) if normalized_text else []
    page_lines = extract_raw_page_lines(pdf_path)
    table_lines = table_like_lines(page_lines)
    table_queries = build_table_queries(table_lines)
    required_coverage = coverage_map(normalized_text, REQUIRED_TERMS)
    non_empty_pages = {
        item["page_number"]
        for item in parsed.metadata.get("pages", [])
        if isinstance(item, dict) and int(item.get("char_count") or 0) > 0
    }
    page_count = int(parsed.metadata.get("page_count") or 0)
    page_coverage = round(len(non_empty_pages) / page_count, 4) if page_count else 0

    errors: list[str] = []
    warnings: list[str] = []
    if len(normalized_text) < args.min_text_chars:
        errors.append(f"Extracted text is shorter than {args.min_text_chars} characters.")
    if page_coverage < args.min_page_coverage:
        errors.append(f"Page text coverage is below {args.min_page_coverage}.")
    if len(chunks) < args.min_chunks:
        errors.append(f"Chunk count is below {args.min_chunks}.")
    if sum(1 for passed in required_coverage.values() if passed) < args.min_required_terms:
        errors.append(f"Required-term coverage is below {args.min_required_terms} terms.")
    if len(table_lines) < args.min_table_lines:
        warnings.append(f"Table-like line count is below {args.min_table_lines}.")

    return {
        "schema_version": "real_basis_extraction_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sample": sample,
        "pdf": {
            "path": pdf_path.as_posix(),
            "page_count": page_count,
            "file_size_bytes": pdf_path.stat().st_size,
        },
        "text_extraction": {
            "engine": parsed.metadata.get("engine", ""),
            "char_count": len(normalized_text),
            "page_coverage": page_coverage,
            "non_empty_page_count": len(non_empty_pages),
            "needs_ocr": bool(parsed.metadata.get("needs_ocr")),
            "required_terms": required_coverage,
            "top_terms": top_terms(normalized_text),
        },
        "chunking": {
            "chunk_count": len(chunks),
            "sample_chunks": [
                {
                    "chunk_index": chunk["chunk_index"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "token_count": chunk["token_count"],
                    "text_preview": chunk["chunk_text"][:240],
                }
                for chunk in chunks[:5]
            ],
        },
        "table_extraction": {
            "table_like_line_count": len(table_lines),
            "sample_lines": table_lines[:20],
            "table_queries": table_queries,
        },
        "rag_queries": DEFAULT_RAG_QUERIES,
        "qa": {
            "passed": not errors,
            "errors": errors,
            "warnings": warnings,
            "thresholds": {
                "min_text_chars": args.min_text_chars,
                "min_page_coverage": args.min_page_coverage,
                "min_chunks": args.min_chunks,
                "min_required_terms": args.min_required_terms,
                "min_table_lines": args.min_table_lines,
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze real basis-document PDF extraction and table-like content.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Sample manifest path.")
    parser.add_argument("--output", default=str(DEFAULT_REPORT), help="Extraction report output path.")
    parser.add_argument("--baseline-output", default=str(DEFAULT_BASELINE), help="Extraction baseline output path.")
    parser.add_argument("--min-text-chars", type=int, default=10000)
    parser.add_argument("--min-page-coverage", type=float, default=0.6)
    parser.add_argument("--min-chunks", type=int, default=10)
    parser.add_argument("--min-required-terms", type=int, default=4)
    parser.add_argument("--min-table-lines", type=int, default=5)
    parser.add_argument("--strict", action="store_true", help="Exit with failure when report qa.passed is false.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    baseline = {
        "schema_version": "real_basis_extraction_baseline_v1",
        "generated_from_report": output_path.resolve().as_posix(),
        "table_queries": report["table_extraction"]["table_queries"],
        "rag_queries": report["rag_queries"],
        "expected_minimums": report["qa"]["thresholds"],
    }
    baseline_path = Path(args.baseline_output)
    baseline_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "passed" if report["qa"]["passed"] else "failed",
                "output": output_path.as_posix(),
                "baseline_output": baseline_path.as_posix(),
                "char_count": report["text_extraction"]["char_count"],
                "chunk_count": report["chunking"]["chunk_count"],
                "table_like_line_count": report["table_extraction"]["table_like_line_count"],
                "errors": report["qa"]["errors"],
                "warnings": report["qa"]["warnings"],
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

