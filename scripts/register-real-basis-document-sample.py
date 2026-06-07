from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "backend" / "tests" / "real-basis-document-samples"
DEFAULT_TITLE = "중소기업자간 경쟁제품 직접생산 확인기준"
DEFAULT_CATEGORY = "direct_production_basis"
DEFAULT_DOCUMENT_VERSION = "2025-116_2025-11-19"
DEFAULT_ISSUING_AGENCY = "중소벤처기업부"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_to_root(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return resolved.as_posix()


def safe_pdf_file_name(source: Path) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", source.stem).strip(" ._")
    stem = re.sub(r"\s+", "_", stem)
    return f"{stem[:160] or 'real-basis-document'}{source.suffix.lower()}"


def build_manifest(args: argparse.Namespace, source: Path, saved_path: Path) -> dict[str, Any]:
    sample = {
        "title": args.title,
        "category": args.category,
        "document_version": args.document_version,
        "issuing_agency": args.issuing_agency,
        "source_path": source.resolve().as_posix(),
        "saved_path": relative_to_root(saved_path),
        "file_name": saved_path.name,
        "file_size_bytes": saved_path.stat().st_size,
        "sha256": file_sha256(saved_path),
        "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return {
        "schema_version": "real_basis_document_sample_v1",
        "sample": sample,
        "usage": {
            "purpose": "real basis-document RAG and table extraction QA",
            "analyze_command": "py -3.13 scripts/analyze-real-basis-document-pdf.py",
            "test_command": "$env:RUN_REAL_BASIS_RAG_TESTS=\"1\"; py -3.13 -m pytest backend/tests/test_real_basis_document_rag.py -q",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a local real basis-document PDF sample for opt-in RAG QA.")
    parser.add_argument("--source", required=True, help="Source PDF path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Sample output directory.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Basis document title.")
    parser.add_argument("--category", default=DEFAULT_CATEGORY, help="Basis document category used in tests.")
    parser.add_argument("--document-version", default=DEFAULT_DOCUMENT_VERSION, help="Basis document version.")
    parser.add_argument("--issuing-agency", default=DEFAULT_ISSUING_AGENCY, help="Issuing agency metadata.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing copied PDF.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Source PDF not found: {source}", file=sys.stderr)
        return 1
    if source.suffix.lower() != ".pdf":
        print("Only PDF samples are supported.", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_path = output_dir / safe_pdf_file_name(source)
    if saved_path.exists() and not args.overwrite:
        print(f"Sample already exists. Use --overwrite to replace it: {saved_path}", file=sys.stderr)
        return 1

    shutil.copy2(source, saved_path)
    manifest = build_manifest(args, source, saved_path)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "registered",
                "manifest_path": relative_to_root(manifest_path),
                "saved_path": relative_to_root(saved_path),
                "sha256": manifest["sample"]["sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

