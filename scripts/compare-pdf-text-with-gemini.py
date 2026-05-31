import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DEFAULT_MANIFEST = BACKEND_DIR / "tests" / "nara-notice-pdf-samples" / "manifest.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "temp" / "pdf-text-compare-gemini"
DEFAULT_MODEL = "gemini-2.5-flash"


def import_parser():
    sys.path.insert(0, str(BACKEND_DIR))
    from app.pipelines.parser import extract_document  # noqa: PLC0415

    return extract_document


def normalize_text(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("text"):
            text = text[4:].strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[0-9A-Za-z가-힣]+", text or "") if len(token) >= 2]


def numeric_tokens(text: str) -> list[str]:
    return re.findall(r"\d[\d.,:-]*", text or "")


def character_ngrams(text: str, n: int = 3) -> list[str]:
    compacted = compact_text(text)
    if len(compacted) < n:
        return [compacted] if compacted else []
    return [compacted[index : index + n] for index in range(len(compacted) - n + 1)]


def line_items(text: str) -> list[str]:
    lines = []
    for raw_line in (text or "").splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if len(line) >= 12:
            lines.append(line)
    return lines


def coverage(base_items: list[str], target_text: str) -> tuple[float, list[str]]:
    if not base_items:
        return 1.0, []
    target_compact = compact_text(target_text)
    missing = [item for item in base_items if compact_text(item) not in target_compact]
    return (len(base_items) - len(missing)) / len(base_items), missing[:8]


def token_recall(base: list[str], target: list[str]) -> float:
    base_set = set(base)
    if not base_set:
        return 1.0
    target_set = set(target)
    return len(base_set & target_set) / len(base_set)


def load_samples(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest.get("samples") or []


def wait_for_file(client: genai.Client, uploaded_file: types.File, timeout_seconds: int = 90) -> types.File:
    deadline = time.monotonic() + timeout_seconds
    current = uploaded_file
    while time.monotonic() < deadline:
        state = getattr(current, "state", None)
        state_name = getattr(state, "name", str(state))
        if state_name == "ACTIVE":
            return current
        if state_name == "FAILED":
            raise RuntimeError(f"Gemini file upload failed: {uploaded_file.name}")
        time.sleep(3)
        current = client.files.get(name=uploaded_file.name)
    raise TimeoutError(f"Gemini file upload did not become ACTIVE: {uploaded_file.name}")


def build_extraction_prompt() -> str:
    return "\n".join(
        [
            "당신은 PDF 원문 텍스트 추출기입니다.",
            "첨부된 PDF에서 눈으로 읽을 수 있는 텍스트를 가능한 빠짐없이 원문 순서대로 추출하세요.",
            "요약, 번역, 해설, 평가, 마크다운, 코드블록은 쓰지 마세요.",
            "표는 보이는 행/열 순서를 최대한 유지하되 일반 텍스트 줄로 반환하세요.",
            "문서에 보이지 않는 내용은 추정하거나 보완하지 마세요.",
            "반환값은 추출 텍스트만이어야 합니다.",
        ]
    )


def extract_with_gemini(
    client: genai.Client,
    model: str,
    pdf_path: Path,
    max_output_tokens: int,
    retries: int,
    retry_delay_seconds: int,
) -> str:
    uploaded = client.files.upload(
        file=pdf_path,
        config=types.UploadFileConfig(mime_type="application/pdf", display_name=pdf_path.name),
    )
    try:
        active_file = wait_for_file(client, uploaded)
        pdf_part = types.Part.from_uri(
            file_uri=active_file.uri,
            mime_type=active_file.mime_type or "application/pdf",
        )
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[build_extraction_prompt(), pdf_part],
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_output_tokens,
                        temperature=0,
                    ),
                )
                return response.text or ""
            except errors.APIError as exc:
                last_error = exc
                if attempt >= retries:
                    raise
                time.sleep(retry_delay_seconds * attempt)
        if last_error:
            raise last_error
        return ""
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass


def compare_texts(service_text: str, gemini_text: str) -> dict[str, Any]:
    service_norm = normalize_text(service_text)
    gemini_norm = normalize_text(gemini_text)
    service_compact = compact_text(service_norm)
    gemini_compact = compact_text(gemini_norm)
    service_tokens = tokens(service_norm)
    gemini_tokens = tokens(gemini_norm)
    service_numbers = numeric_tokens(service_norm)
    gemini_numbers = numeric_tokens(gemini_norm)
    service_line_coverage, service_missing_lines = coverage(line_items(service_norm), gemini_norm)
    gemini_line_coverage, gemini_extra_lines = coverage(line_items(gemini_norm), service_norm)

    return {
        "service_char_count": len(service_norm),
        "gemini_char_count": len(gemini_norm),
        "service_compact_char_count": len(service_compact),
        "gemini_compact_char_count": len(gemini_compact),
        "compact_sequence_similarity": round(SequenceMatcher(None, service_compact, gemini_compact).ratio(), 4),
        "service_token_recall_in_gemini": round(token_recall(service_tokens, gemini_tokens), 4),
        "gemini_token_recall_in_service": round(token_recall(gemini_tokens, service_tokens), 4),
        "service_numeric_recall_in_gemini": round(token_recall(service_numbers, gemini_numbers), 4),
        "gemini_numeric_recall_in_service": round(token_recall(gemini_numbers, service_numbers), 4),
        "service_char_3gram_recall_in_gemini": round(
            token_recall(character_ngrams(service_norm), character_ngrams(gemini_norm)), 4
        ),
        "gemini_char_3gram_recall_in_service": round(
            token_recall(character_ngrams(gemini_norm), character_ngrams(service_norm)), 4
        ),
        "service_line_coverage_in_gemini": round(service_line_coverage, 4),
        "gemini_line_coverage_in_service": round(gemini_line_coverage, 4),
        "service_missing_line_examples": service_missing_lines,
        "gemini_extra_line_examples": gemini_extra_lines,
    }


def sample_stem(sample: dict[str, Any]) -> str:
    sample_no = int(sample.get("sample_no") or 0)
    bid_ntce_no = sample.get("bid_ntce_no") or "sample"
    return f"{sample_no:02d}-{bid_ntce_no}"


def write_result_texts(output_dir: Path, sample: dict[str, Any], service_text: str, gemini_text: str) -> None:
    stem = sample_stem(sample)
    (output_dir / f"{stem}.service.txt").write_text(normalize_text(service_text), encoding="utf-8")
    (output_dir / f"{stem}.gemini.txt").write_text(normalize_text(gemini_text), encoding="utf-8")


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    metric_keys = [
        "compact_sequence_similarity",
        "service_token_recall_in_gemini",
        "gemini_token_recall_in_service",
        "service_numeric_recall_in_gemini",
        "gemini_numeric_recall_in_service",
        "service_char_3gram_recall_in_gemini",
        "gemini_char_3gram_recall_in_service",
        "service_line_coverage_in_gemini",
        "gemini_line_coverage_in_service",
    ]
    metric_results = [result for result in results if result.get("metrics")]
    aggregate: dict[str, Any] = {"count": len(metric_results), "metrics": {}}
    for key in metric_keys:
        values = [result["metrics"][key] for result in metric_results]
        if not values:
            continue
        aggregate["metrics"][key] = {
            "avg": round(sum(values) / len(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local service PDF text extraction with Gemini PDF extraction.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--sample-nos", nargs="+", type=int, default=[1, 2, 8])
    parser.add_argument("--model", default="")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-output-tokens", type=int, default=32000)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--retry-delay-seconds", type=int, default=20)
    parser.add_argument(
        "--reuse-existing-output",
        action="store_true",
        help="Reuse already saved service/gemini text files in the output directory instead of calling Gemini again.",
    )
    args = parser.parse_args()

    load_dotenv(BACKEND_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not configured.", file=sys.stderr)
        return 2

    model = args.model.strip() or os.getenv("GEMINI_MODEL_PRIMARY", "").strip() or DEFAULT_MODEL
    manifest_path = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    extract_document = import_parser()
    client = genai.Client(api_key=api_key)
    samples = {sample.get("sample_no"): sample for sample in load_samples(manifest_path)}

    results: list[dict[str, Any]] = []
    for sample_no in args.sample_nos:
        sample = samples.get(sample_no)
        if not sample:
            print(f"SKIP missing sample_no={sample_no}")
            continue

        pdf_path = ROOT_DIR / sample["saved_path"]
        print(
            "COMPARE "
            f"sample_no={sample_no} "
            f"bid={sample.get('bid_ntce_no')}-{sample.get('bid_ntce_ord')} "
            f"file={sample.get('original_file_name')}"
        )
        if args.reuse_existing_output:
            stem = sample_stem(sample)
            service_path = output_dir / f"{stem}.service.txt"
            gemini_path = output_dir / f"{stem}.gemini.txt"
            if not service_path.exists() or not gemini_path.exists():
                print(f"SKIP missing saved output sample_no={sample_no}")
                continue
            service_text = service_path.read_text(encoding="utf-8")
            gemini_text = gemini_path.read_text(encoding="utf-8")
        else:
            service_parsed = extract_document(pdf_path)
            service_text = service_parsed.text
            try:
                gemini_text = extract_with_gemini(
                    client=client,
                    model=model,
                    pdf_path=pdf_path,
                    max_output_tokens=args.max_output_tokens,
                    retries=args.retries,
                    retry_delay_seconds=args.retry_delay_seconds,
                )
            except Exception as exc:
                result = {
                    "sample_no": sample_no,
                    "bid_ntce_no": sample.get("bid_ntce_no", ""),
                    "bid_ntce_ord": sample.get("bid_ntce_ord", ""),
                    "bid_ntce_nm": sample.get("bid_ntce_nm", ""),
                    "original_file_name": sample.get("original_file_name", ""),
                    "saved_path": sample.get("saved_path", ""),
                    "model": model,
                    "service_char_count": len(normalize_text(service_text)),
                    "gemini_error": {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                }
                results.append(result)
                print(f"GEMINI_ERROR sample_no={sample_no} type={type(exc).__name__} message={str(exc)[:240]}")
                continue

        metrics = compare_texts(service_text, gemini_text)
        result = {
            "sample_no": sample_no,
            "bid_ntce_no": sample.get("bid_ntce_no", ""),
            "bid_ntce_ord": sample.get("bid_ntce_ord", ""),
            "bid_ntce_nm": sample.get("bid_ntce_nm", ""),
            "original_file_name": sample.get("original_file_name", ""),
            "saved_path": sample.get("saved_path", ""),
            "model": model,
            "metrics": metrics,
        }
        results.append(result)
        write_result_texts(output_dir, sample, service_text, gemini_text)
        print(
            "RESULT "
            f"sample_no={sample_no} "
            f"seq={metrics['compact_sequence_similarity']} "
            f"service_token_recall={metrics['service_token_recall_in_gemini']} "
            f"gemini_token_recall={metrics['gemini_token_recall_in_service']} "
            f"service_numbers={metrics['service_numeric_recall_in_gemini']} "
            f"gemini_numbers={metrics['gemini_numeric_recall_in_service']} "
            f"service_3gram={metrics['service_char_3gram_recall_in_gemini']} "
            f"gemini_3gram={metrics['gemini_char_3gram_recall_in_service']} "
            f"service_lines={metrics['service_line_coverage_in_gemini']} "
            f"gemini_lines={metrics['gemini_line_coverage_in_service']}"
        )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "manifest": str(manifest_path),
        "model": model,
        "sample_nos": args.sample_nos,
        "aggregate": aggregate_results(results),
        "results": results,
    }
    summary_path = output_dir / "comparison-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUMMARY {summary_path}")
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
