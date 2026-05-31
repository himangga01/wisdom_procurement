import argparse
import hashlib
import json
import os
import random
import re
import shutil
import sys
import tempfile
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
BACKEND_ENV = BACKEND_DIR / ".env"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "tests" / "nara-notice-pdf-samples"
DEFAULT_OPERATION = "getBidPblancListInfoCnstwkPPSSrch"
FORBIDDEN_DECISION_TERMS = ["eligible", "not eligible", "지원 가능", "지원 불가능"]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d")


def format_date(value: datetime) -> str:
    return value.strftime("%Y%m%d")


def date_windows(date_from: str, date_to: str, window_days: int) -> list[tuple[str, str]]:
    start = parse_date(date_from)
    end = parse_date(date_to)
    if start > end:
        raise ValueError("date_from must be before or equal to date_to")

    windows: list[tuple[str, str]] = []
    cursor_end = end
    while cursor_end >= start:
        cursor_start = max(start, cursor_end - timedelta(days=window_days - 1))
        windows.append((format_date(cursor_start), format_date(cursor_end)))
        cursor_end = cursor_start - timedelta(days=1)
    return windows


def safe_file_stem(value: str) -> str:
    ascii_value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    return ascii_value[:90] or "notice"


def redact_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_query = [(key, "***" if key.lower() == "servicekey" else value) for key, value in query]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(redacted_query, doseq=True)))


def compact_attachment_key(notice: dict[str, Any], attachment: dict[str, Any]) -> str:
    return "|".join(
        [
            str(notice.get("bidNtceNo") or ""),
            str(notice.get("bidNtceOrd") or ""),
            str(attachment.get("file_name") or ""),
            str(attachment.get("source_url") or ""),
        ]
    )


def import_runtime():
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["GEMINI_API_KEY"] = ""
    sys.path.insert(0, str(BACKEND_DIR))
    from app import main as runtime  # noqa: PLC0415
    from app.pipelines.parser import extract_document  # noqa: PLC0415

    return runtime, extract_document


def make_search_params(
    service_key: str,
    begin_date: str,
    end_date: str,
    page_no: int,
    rows: int,
    response_type: str,
) -> dict[str, str]:
    return {
        "ServiceKey": service_key,
        "numOfRows": str(rows),
        "pageNo": str(page_no),
        "type": response_type,
        "inqryDiv": "1",
        "inqryBgnDt": f"{begin_date}0000",
        "inqryEndDt": f"{end_date}2359",
    }


def validate_notice_pdf_sample(
    runtime,
    extract_document,
    pdf_path: Path,
    notice: dict[str, Any],
    min_text_chars: int,
    min_candidates: int,
) -> tuple[bool, dict[str, Any]]:
    parsed = extract_document(pdf_path)
    text = parsed.text or ""
    notice_text = runtime.build_nara_summary_text(notice, [text])
    requirements = runtime.extract_notice_requirements(notice, notice_text)
    candidates = runtime.build_notice_requirement_candidates(requirements)
    candidate_types: dict[str, int] = {}
    for candidate in candidates:
        requirement_type = candidate.get("requirement_type", "unknown")
        candidate_types[requirement_type] = candidate_types.get(requirement_type, 0) + 1

    semantic_types = {"region", "license", "company_type", "required_document", "requirement_line"}
    semantic_count = sum(count for key, count in candidate_types.items() if key in semantic_types)
    serialized = json.dumps({"requirements": requirements, "candidates": candidates}, ensure_ascii=False).lower()
    forbidden_found = [term for term in FORBIDDEN_DECISION_TERMS if term in serialized]
    passed = (
        pdf_path.read_bytes().startswith(b"%PDF")
        and len(text.strip()) >= min_text_chars
        and len(candidates) >= min_candidates
        and semantic_count >= 1
        and not forbidden_found
    )

    return passed, {
        "passed": passed,
        "text_char_count": len(text.strip()),
        "parser_kind": parsed.kind,
        "parser_metadata": parsed.metadata,
        "candidate_count": len(candidates),
        "semantic_candidate_count": semantic_count,
        "candidate_types": candidate_types,
        "forbidden_terms_found": forbidden_found,
    }


def remove_existing_samples(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for child in output_dir.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download reusable random Nara notice PDF samples for local PDF-related tests."
    )
    today = datetime.now().strftime("%Y%m%d")
    default_from = (datetime.now() - timedelta(days=45)).strftime("%Y%m%d")
    parser.add_argument("--date-from", default=default_from, help="YYYYMMDD")
    parser.add_argument("--date-to", default=today, help="YYYYMMDD")
    parser.add_argument("--target-count", type=int, default=30)
    parser.add_argument("--num-of-rows", type=int, default=100)
    parser.add_argument("--max-pages-per-window", type=int, default=8)
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--min-text-chars", type=int, default=300)
    parser.add_argument("--min-candidates", type=int, default=3)
    parser.add_argument("--operation", default=DEFAULT_OPERATION)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--keep-existing", action="store_true")
    parser.add_argument("--allow-duplicate-notices", action="store_true")
    parser.add_argument("--random-seed", type=int, default=None)
    args = parser.parse_args()

    load_env_file(BACKEND_ENV)
    service_key = os.getenv("NARA_API_SERVICE_KEY", "").strip()
    if not service_key:
        print("ERROR: NARA_API_SERVICE_KEY is missing. Set it in backend/.env or the environment.", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.keep_existing:
        remove_existing_samples(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    random_seed = args.random_seed if args.random_seed is not None else int(datetime.now().strftime("%Y%m%d%H%M%S"))
    rng = random.Random(random_seed)
    runtime, extract_document = import_runtime()
    runtime.NARA_API_SERVICE_KEY = service_key

    samples: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen_attachments: set[str] = set()
    seen_notices: set[tuple[str, str]] = set()
    windows = date_windows(args.date_from, args.date_to, args.window_days)
    rng.shuffle(windows)

    for begin_date, end_date in windows:
        if len(samples) >= args.target_count:
            break
        pages = list(range(1, args.max_pages_per_window + 1))
        rng.shuffle(pages)
        for page_no in pages:
            if len(samples) >= args.target_count:
                break
            params = make_search_params(
                service_key,
                begin_date,
                end_date,
                page_no,
                args.num_of_rows,
                runtime.NARA_API_RESPONSE_TYPE,
            )
            parsed = runtime.request_nara_operation(args.operation, params)
            header = parsed.get("header") or {}
            if parsed.get("http_status") != 200 or str(header.get("resultCode", "")) not in {"", "00"}:
                skipped.append(
                    {
                        "reason": "search_failed",
                        "window": [begin_date, end_date],
                        "page_no": page_no,
                        "http_status": parsed.get("http_status"),
                        "result_code": header.get("resultCode", ""),
                        "result_msg": header.get("resultMsg", ""),
                    }
                )
                continue

            items = list(parsed.get("items") or [])
            rng.shuffle(items)
            for item in items:
                if len(samples) >= args.target_count:
                    break

                bid_no = str(item.get("bidNtceNo") or "")
                bid_ord = str(item.get("bidNtceOrd") or "000")
                notice_key = (bid_no, bid_ord)
                if not args.allow_duplicate_notices and notice_key in seen_notices:
                    continue

                detail_bundle = runtime.fetch_nara_detail_bundle(bid_no, bid_ord)
                detail_items = detail_bundle.get("items") or []
                merged_item = runtime.merge_notice_items(item, detail_items)
                attachments = runtime.collect_nara_attachments([merged_item, *detail_items])
                rng.shuffle(attachments)
                normalized = runtime.normalize_nara_notice(merged_item, attachments)
                accepted_current_notice = False

                for attachment in attachments:
                    if len(samples) >= args.target_count:
                        break
                    if accepted_current_notice and not args.allow_duplicate_notices:
                        break
                    if attachment.get("support_status") != "supported":
                        continue
                    if str(attachment.get("file_extension") or "").lower() != ".pdf":
                        continue
                    source_url = str(attachment.get("source_url") or "")
                    if not source_url or not runtime.is_safe_external_url(source_url):
                        continue

                    attachment_key = compact_attachment_key(merged_item, attachment)
                    if attachment_key in seen_attachments:
                        continue
                    seen_attachments.add(attachment_key)

                    tmp_path: Path | None = None
                    try:
                        http_status, headers, body = runtime.request_binary(source_url)
                        if http_status != 200 or not body.startswith(b"%PDF"):
                            skipped.append(
                                {
                                    "reason": "download_not_pdf",
                                    "bid_ntce_no": bid_no,
                                    "file_name": attachment.get("file_name", ""),
                                    "http_status": http_status,
                                    "content_type": headers.get("content-type", ""),
                                    "downloaded_bytes": len(body),
                                }
                            )
                            continue

                        sample_index = len(samples) + 1
                        stem = safe_file_stem(f"{sample_index:02d}-{bid_no}-{bid_ord}")
                        target_path = output_dir / f"{stem}.pdf"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=output_dir) as tmp:
                            tmp.write(body)
                            tmp_path = Path(tmp.name)

                        qa_passed, qa = validate_notice_pdf_sample(
                            runtime,
                            extract_document,
                            tmp_path,
                            normalized,
                            args.min_text_chars,
                            args.min_candidates,
                        )
                        if not qa_passed:
                            skipped.append(
                                {
                                    "reason": "qa_failed",
                                    "bid_ntce_no": bid_no,
                                    "file_name": attachment.get("file_name", ""),
                                    "qa": {
                                        "text_char_count": qa["text_char_count"],
                                        "candidate_count": qa["candidate_count"],
                                        "semantic_candidate_count": qa["semantic_candidate_count"],
                                        "forbidden_terms_found": qa["forbidden_terms_found"],
                                    },
                                }
                            )
                            tmp_path.unlink(missing_ok=True)
                            tmp_path = None
                            continue

                        tmp_path.replace(target_path)
                        tmp_path = None
                        sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
                        sample = {
                            "sample_no": sample_index,
                            "bid_ntce_no": normalized.get("bid_ntce_no"),
                            "bid_ntce_ord": normalized.get("bid_ntce_ord"),
                            "bid_ntce_nm": normalized.get("bid_ntce_nm"),
                            "ntce_instt_nm": normalized.get("ntce_instt_nm"),
                            "dminstt_nm": normalized.get("dminstt_nm"),
                            "bid_ntce_dt": normalized.get("bid_ntce_dt"),
                            "bid_clse_dt": normalized.get("bid_clse_dt"),
                            "source_url": redact_url(source_url),
                            "source_field": attachment.get("source_field", ""),
                            "original_file_name": attachment.get("file_name", ""),
                            "saved_path": str(target_path.relative_to(ROOT_DIR)).replace("\\", "/"),
                            "file_size": target_path.stat().st_size,
                            "sha256": sha256,
                            "qa": qa,
                        }
                        samples.append(sample)
                        seen_notices.add(notice_key)
                        accepted_current_notice = True
                        print(
                            "NOTICE_PDF_SAMPLE_OK "
                            f"{sample_index}/{args.target_count} "
                            f"bid={sample['bid_ntce_no']}-{sample['bid_ntce_ord']} "
                            f"chars={qa['text_char_count']} "
                            f"candidates={qa['candidate_count']} "
                            f"file={sample['saved_path']}"
                        )
                    except Exception as exc:
                        skipped.append(
                            {
                                "reason": "exception",
                                "bid_ntce_no": bid_no,
                                "file_name": attachment.get("file_name", ""),
                                "error": str(exc),
                            }
                        )
                    finally:
                        if tmp_path is not None:
                            tmp_path.unlink(missing_ok=True)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "purpose": "Reusable local Nara notice PDF samples for PDF-related tests",
        "date_from": args.date_from,
        "date_to": args.date_to,
        "target_count": args.target_count,
        "sample_count": len(samples),
        "random_seed": random_seed,
        "min_text_chars": args.min_text_chars,
        "min_candidates": args.min_candidates,
        "samples": samples,
        "skipped_count": len(skipped),
        "skipped": skipped[:80],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_lines = [
        "# Reusable Nara Notice PDF Test Samples",
        "",
        f"- generated_at: `{manifest['generated_at']}`",
        f"- date_range: `{args.date_from}` ~ `{args.date_to}`",
        f"- random_seed: `{random_seed}`",
        f"- sample_count: `{len(samples)}` / `{args.target_count}`",
        f"- skipped_count: `{len(skipped)}`",
        "",
        "## Samples",
    ]
    for sample in samples:
        qa = sample["qa"]
        summary_lines.append(
            f"- {sample['sample_no']}. `{sample['bid_ntce_no']}-{sample['bid_ntce_ord']}` "
            f"{sample['bid_ntce_nm']} / chars `{qa['text_char_count']}` / candidates `{qa['candidate_count']}`"
        )
    (output_dir / "qa-summary.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"MANIFEST {manifest_path}")
    if len(samples) < args.target_count:
        print(
            f"ERROR: only {len(samples)} PDF samples were collected. See {manifest_path} for skipped reasons.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
