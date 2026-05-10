import hashlib
import json
import mimetypes
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from app.pipelines.corporation_evidence import (
    FIELD_LABELS,
    EvidenceExtractionResult,
    EvidenceFieldCandidate,
    allowed_profile_update_fields,
    analyze_corporation_evidence,
    evidence_storage_subdir,
)
from app.pipelines.ocr import run_ocr, run_ocr_if_needed
from app.pipelines.parser import extract_document

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"


def _resolve_local_path(raw_value: str) -> Path:
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


STORAGE_ROOT = _resolve_local_path(os.getenv("STORAGE_ROOT", "./storage"))
SQLITE_PATH = _resolve_local_path(os.getenv("SQLITE_PATH", "./app.db"))
AI_PROVIDER_DEFAULT = os.getenv("AI_PROVIDER_DEFAULT", "gemini").strip().lower()
AI_MODEL_DEFAULT = os.getenv("AI_MODEL_DEFAULT", "gemini-2.5-flash").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_PRIMARY = os.getenv("OPENAI_MODEL_PRIMARY", "gpt-5.4-mini")
OPENAI_MODEL_SECONDARY = os.getenv("OPENAI_MODEL_SECONDARY", "gpt-5.4")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_PRIMARY = os.getenv("GEMINI_MODEL_PRIMARY", "gemini-2.5-flash")
NARA_API_SERVICE_KEY = os.getenv("NARA_API_SERVICE_KEY", "")
NARA_BID_PUBLIC_API_BASE_URL = os.getenv(
    "NARA_BID_PUBLIC_API_BASE_URL",
    "https://apis.data.go.kr/1230000/ad/BidPublicInfoService",
)
NARA_PUBDATA_API_BASE_URL = os.getenv(
    "NARA_PUBDATA_API_BASE_URL",
    "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService",
)
NARA_API_RESPONSE_TYPE = os.getenv("NARA_API_RESPONSE_TYPE", "json")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
EVIDENCE_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
EVIDENCE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
UNSUPPORTED_NARA_EXTENSIONS = {".hwp", ".hwpx", ".xlsx", ".xls", ".zip"}
NARA_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
DEFAULT_MANAGEMENT_GROUP_NAME = "기본 관리그룹"
KST = timezone(timedelta(hours=9))

app = Flask(__name__)
CORS(app)

SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
NARA_NOTICE_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="nara-notice-worker")


@contextmanager
def db_conn():
    conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json_payload() -> dict:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def clean_text(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def normalize_management_group_name(value) -> str:
    return clean_text(value) or DEFAULT_MANAGEMENT_GROUP_NAME


def normalize_business_registration_number(value) -> str:
    cleaned = clean_text(value)
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return cleaned


def business_registration_match_key(value) -> str:
    return "".join(ch for ch in clean_text(value) if ch.isdigit())


def parse_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


AI_PROVIDERS = {"gemini", "openai"}


def normalize_ai_provider(value) -> str:
    candidate = clean_text(value).lower()
    if candidate in AI_PROVIDERS:
        return candidate
    if AI_PROVIDER_DEFAULT in AI_PROVIDERS:
        return AI_PROVIDER_DEFAULT
    return "gemini"


def default_model_for_provider(provider: str) -> str:
    if provider == "openai":
        return OPENAI_MODEL_PRIMARY
    if provider == "gemini":
        return GEMINI_MODEL_PRIMARY
    return AI_MODEL_DEFAULT or GEMINI_MODEL_PRIMARY


def api_key_for_provider(provider: str) -> str:
    if provider == "openai":
        return OPENAI_API_KEY
    if provider == "gemini":
        return GEMINI_API_KEY
    return ""


def resolve_ai_model_selection(provider=None, model=None) -> dict:
    normalized_provider = normalize_ai_provider(provider)
    normalized_model = clean_text(model) or default_model_for_provider(normalized_provider)
    if not normalized_model:
        normalized_model = AI_MODEL_DEFAULT or default_model_for_provider(normalized_provider)
    return {
        "provider": normalized_provider,
        "model": normalized_model,
        "configured": bool(api_key_for_provider(normalized_provider)),
    }


def resolve_ai_model_selection_from_payload(payload: dict | None) -> dict:
    payload = payload or {}
    return resolve_ai_model_selection(
        payload.get("model_provider") or payload.get("ai_provider") or payload.get("provider"),
        payload.get("model_name") or payload.get("ai_model") or payload.get("model"),
    )


def ai_model_options() -> list[dict]:
    options = [
        {
            "provider": "gemini",
            "model": GEMINI_MODEL_PRIMARY,
            "label": f"Gemini 2.5 Flash ({GEMINI_MODEL_PRIMARY})",
            "description": "저비용/고속 요약 기본값입니다.",
            "configured": bool(GEMINI_API_KEY),
            "recommended": True,
        },
        {
            "provider": "openai",
            "model": OPENAI_MODEL_PRIMARY,
            "label": f"OpenAI {OPENAI_MODEL_PRIMARY}",
            "description": "기존 OpenAI 요약 경로입니다.",
            "configured": bool(OPENAI_API_KEY),
            "recommended": False,
        },
    ]
    if OPENAI_MODEL_SECONDARY and OPENAI_MODEL_SECONDARY != OPENAI_MODEL_PRIMARY:
        options.append(
            {
                "provider": "openai",
                "model": OPENAI_MODEL_SECONDARY,
                "label": f"OpenAI {OPENAI_MODEL_SECONDARY}",
                "description": "정밀 재분석용 보조 후보입니다.",
                "configured": bool(OPENAI_API_KEY),
                "recommended": False,
            }
        )
    return options


def normalize_certifications(value) -> str:
    if value in (None, ""):
        return "[]"
    if isinstance(value, list):
        return json.dumps([str(item).strip() for item in value if str(item).strip()], ensure_ascii=False)
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
        items = [item.strip() for item in stripped.split(",") if item.strip()]
        return json.dumps(items, ensure_ascii=False)
    return "[]"


def safe_unlink(path: Path) -> None:
    try:
        resolved = path.resolve()
        storage_root = STORAGE_ROOT.resolve()
        if resolved.exists() and resolved.is_file() and resolved.is_relative_to(storage_root):
            resolved.unlink()
    except OSError:
        return


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return value[:2] + "*" * max(len(value) - 4, 0) + value[-2:]
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def parse_nara_response(payload: dict) -> tuple[str, str, int]:
    response = payload.get("response", payload) if isinstance(payload, dict) else {}
    header = response.get("header", {}) if isinstance(response, dict) else {}
    body = response.get("body", {}) if isinstance(response, dict) else {}
    return (
        str(header.get("resultCode", "")),
        str(header.get("resultMsg", "")),
        parse_int(body.get("totalCount"), 0),
    )


def normalize_json_items(items: Any) -> list[dict]:
    if not items:
        return []
    if isinstance(items, dict):
        item = items.get("item")
        if isinstance(item, list):
            return [row for row in item if isinstance(row, dict)]
        if isinstance(item, dict):
            return [item]
    if isinstance(items, list):
        return [row for row in items if isinstance(row, dict)]
    return []


def xml_children_to_dict(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    return {child.tag: (child.text or "") for child in list(element)}


def parse_public_data_text(raw_text: str) -> dict:
    text = raw_text.strip()
    if not text:
        return {"format": "empty", "header": {}, "body": {}, "items": [], "total_count": 0}

    if text.startswith("{") or text.startswith("["):
        payload = json.loads(text)
        response = payload.get("response", payload) if isinstance(payload, dict) else {}
        header = response.get("header", {}) if isinstance(response, dict) else {}
        body = response.get("body", {}) if isinstance(response, dict) else {}
        items = normalize_json_items(body.get("items")) if isinstance(body, dict) else []
        return {
            "format": "json",
            "header": header,
            "body": body,
            "items": items,
            "total_count": parse_int(body.get("totalCount", len(items))) if isinstance(body, dict) else len(items),
        }

    root = ET.fromstring(text)
    body = xml_children_to_dict(root.find("./body"))
    items = [xml_children_to_dict(item) for item in root.findall("./body/items/item")]
    return {
        "format": "xml",
        "header": xml_children_to_dict(root.find("./header")),
        "body": body,
        "items": items,
        "total_count": parse_int(body.get("totalCount", len(items))),
    }


def build_nara_url(base_url: str, operation: str, params: dict[str, str]) -> str:
    return f"{base_url.rstrip('/')}/{operation}?{urllib.parse.urlencode(params, doseq=True, safe='%')}"


def request_text(url: str, timeout: int = 20) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, application/xml;q=0.9, */*;q=0.8",
            "User-Agent": "SMART-Procurement-Calculator/local-portal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def request_nara_operation(operation: str, params: dict[str, str]) -> dict:
    url = build_nara_url(NARA_BID_PUBLIC_API_BASE_URL, operation, params)
    http_status, body = request_text(url)
    parsed = parse_public_data_text(body)
    parsed["http_status"] = http_status
    parsed["url_without_key"] = build_nara_url(
        NARA_BID_PUBLIC_API_BASE_URL,
        operation,
        {**params, "ServiceKey": "***"},
    )
    return parsed


def date_to_api_datetime(value: str, suffix: str) -> str:
    cleaned = clean_text(value)
    if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
        return cleaned.replace("-", "") + suffix
    if len(cleaned) == 8 and cleaned.isdigit():
        return cleaned + suffix
    return cleaned


def item_first(item: dict, keys: list[str]) -> str:
    for key in keys:
        value = clean_text(item.get(key))
        if value:
            return value
    return ""


def attachment_extension(name: str, url: str, content_type: str = "") -> str:
    candidates = [name, urllib.parse.urlparse(url).path]
    for candidate in candidates:
        suffix = Path(candidate).suffix.lower()
        if suffix:
            return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else ""
    return guessed or ""


def collect_nara_attachments(items: list[dict]) -> list[dict]:
    attachments: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_attachment(name: str, url: str, source_field: str) -> None:
        name = clean_text(name) or Path(urllib.parse.urlparse(url).path).name or source_field
        url = clean_text(url)
        if not url and name == source_field:
            return
        key = (name, url)
        if key in seen or (not name and not url):
            return
        seen.add(key)
        suffix = attachment_extension(name, url)
        support_status = "supported" if url and suffix in NARA_SUPPORTED_EXTENSIONS else "unsupported"
        if not suffix and not url:
            support_status = "unsupported"
        attachments.append(
            {
                "file_name": name,
                "source_url": url,
                "source_field": source_field,
                "file_extension": suffix,
                "support_status": support_status,
            }
        )

    for item in items:
        for index in range(1, 11):
            add_attachment(
                clean_text(item.get(f"ntceSpecFileNm{index}")),
                clean_text(item.get(f"ntceSpecDocUrl{index}")),
                f"ntceSpecDocUrl{index}",
            )

        std_notice_url = clean_text(item.get("stdNtceDocUrl"))
        if std_notice_url:
            add_attachment("표준공고문.pdf", std_notice_url, "stdNtceDocUrl")
        add_attachment(clean_text(item.get("eorderAtchFileNm")), clean_text(item.get("eorderAtchFileUrl")), "eorderAtchFileUrl")

    return attachments


def normalize_nara_notice(item: dict, attachments: list[dict] | None = None) -> dict:
    attachment_rows = attachments if attachments is not None else collect_nara_attachments([item])
    supported_count = len([row for row in attachment_rows if row["support_status"] == "supported"])
    return {
        "bid_ntce_no": item_first(item, ["bidNtceNo"]),
        "bid_ntce_ord": item_first(item, ["bidNtceOrd"]) or "000",
        "bid_ntce_nm": item_first(item, ["bidNtceNm"]),
        "ntce_instt_nm": item_first(item, ["ntceInsttNm"]),
        "dminstt_nm": item_first(item, ["dminsttNm"]),
        "bid_ntce_dt": item_first(item, ["bidNtceDt"]),
        "bid_begin_dt": item_first(item, ["bidBeginDt"]),
        "bid_clse_dt": item_first(item, ["bidClseDt"]),
        "openg_dt": item_first(item, ["opengDt"]),
        "presmpt_prce": item_first(item, ["presmptPrce", "asignBdgtAmt"]),
        "bdgt_amt": item_first(item, ["bdgtAmt", "asignBdgtAmt"]),
        "bssamt": item_first(item, ["bssamt", "bssAmt"]),
        "region_text": item_first(item, ["prtcptPsblRgnNm", "cnstrtsiteRgnNm", "rgstTyNm"]),
        "license_text": item_first(item, ["lcnsLmtNm", "indstrytyNm", "indstrytyLmtYn"]),
        "source_url": item_first(item, ["bidNtceUrl", "bidNtceDtlUrl"]),
        "attachment_count": len(attachment_rows),
        "supported_attachment_count": supported_count,
        "raw": item,
    }


def fetch_nara_detail_bundle(bid_no: str, bid_ord: str) -> dict:
    if not NARA_API_SERVICE_KEY:
        return {"errors": ["NARA_API_SERVICE_KEY is missing"], "items": []}

    params = {
        "ServiceKey": NARA_API_SERVICE_KEY,
        "numOfRows": "20",
        "pageNo": "1",
        "type": NARA_API_RESPONSE_TYPE,
        "inqryDiv": "2",
        "bidNtceNo": bid_no,
        "bidNtceOrd": bid_ord or "000",
    }
    operations = {
        "notice": "getBidPblancListInfoCnstwk",
        "basis_amount": "getBidPblancListInfoCnstwkBsisAmount",
        "license_limit": "getBidPblancListInfoLicenseLimit",
        "eligible_region": "getBidPblancListInfoPrtcptPsblRgn",
        "eorder_attachments": "getBidPblancListInfoEorderAtchFileInfo",
    }
    bundle: dict[str, Any] = {"errors": [], "items": []}
    for key, operation in operations.items():
        try:
            parsed = request_nara_operation(operation, params)
            bundle[key] = {
                "http_status": parsed.get("http_status"),
                "header": parsed.get("header"),
                "total_count": parsed.get("total_count", 0),
                "items": parsed.get("items", []),
            }
            bundle["items"].extend(parsed.get("items", []))
        except Exception as exc:
            bundle["errors"].append(f"{operation}: {exc}")
    return bundle


def merge_notice_items(base_item: dict, detail_items: list[dict]) -> dict:
    merged = dict(base_item)
    for item in detail_items:
        for key, value in item.items():
            if clean_text(value) and not clean_text(merged.get(key)):
                merged[key] = value
    return merged


def request_binary(url: str, timeout: int = 30, max_bytes: int = 50 * 1024 * 1024) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, */*",
            "User-Agent": "SMART-Procurement-Calculator/attachment-download",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("download exceeded 50MB limit")
            chunks.append(chunk)
        return response.status, {key.lower(): value for key, value in response.headers.items()}, b"".join(chunks)


def is_safe_external_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return False
    return True


def inline_content_type(file_name: str, url: str, upstream_content_type: str, body: bytes) -> str:
    suffix = attachment_extension(file_name, url, upstream_content_type)
    if body.startswith(b"%PDF") or suffix == ".pdf":
        return "application/pdf"
    if body.startswith(b"PK\x03\x04") or suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return upstream_content_type.split(";")[0].strip() or "application/octet-stream"


def build_nara_summary_text(notice: dict, attachment_texts: list[str]) -> str:
    lines = [
        f"공고명: {notice.get('bid_ntce_nm', '')}",
        f"공고번호: {notice.get('bid_ntce_no', '')}-{notice.get('bid_ntce_ord', '')}",
        f"공고기관: {notice.get('ntce_instt_nm', '')}",
        f"수요기관: {notice.get('dminstt_nm', '')}",
        f"공고일시: {notice.get('bid_ntce_dt', '')}",
        f"입찰개시: {notice.get('bid_begin_dt', '')}",
        f"입찰마감: {notice.get('bid_clse_dt', '')}",
        f"개찰일시: {notice.get('openg_dt', '')}",
        f"추정가격: {notice.get('presmpt_prce', '')}",
        f"기초금액: {notice.get('bssamt', '')}",
        f"지역: {notice.get('region_text', '')}",
        f"면허/업종 제한: {notice.get('license_text', '')}",
        "",
        "첨부문서 추출 내용:",
    ]
    for index, text in enumerate(attachment_texts, start=1):
        lines.extend([f"[첨부 {index}]", text[:20000], ""])
    return "\n".join(lines).strip()


def _dedupe_text_items(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = clean_text(item)
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _find_notice_tokens(text: str, tokens: list[str]) -> list[str]:
    compact = text.replace(" ", "")
    return [token for token in tokens if token.replace(" ", "") in compact]


def extract_notice_requirements(notice: dict, notice_text: str) -> dict:
    text = notice_text or ""
    region_tokens = [
        "서울",
        "부산",
        "대구",
        "인천",
        "광주",
        "대전",
        "울산",
        "세종",
        "경기도",
        "강원",
        "충북",
        "충남",
        "전북",
        "전남",
        "경북",
        "경남",
        "제주",
    ]
    license_tokens = [
        "건설업",
        "조경식재",
        "조경시설물",
        "산림사업법인",
        "전기공사업",
        "정보통신공사업",
        "소방시설공사업",
        "폐기물처리",
        "엔지니어링사업자",
        "소프트웨어사업자",
        "직접생산확인",
    ]
    company_type_tokens = [
        "중소기업",
        "소기업",
        "소상공인",
        "여성기업",
        "장애인기업",
        "사회적기업",
        "창업기업",
        "벤처기업",
    ]
    document_tokens = [
        "사업자등록증",
        "법인등기부등본",
        "인감증명서",
        "사용인감계",
        "국세 납세증명서",
        "지방세 납세증명서",
        "4대보험 완납증명서",
        "중소기업확인서",
        "직접생산확인증명서",
        "기업신용평가등급확인서",
        "실적증명서",
        "입찰보증서",
        "청렴계약이행서약서",
    ]
    requirement_lines = []
    for line in text.splitlines():
        cleaned = clean_text(line)
        if not cleaned:
            continue
        if any(token in cleaned for token in ["참가자격", "입찰참가", "제출서류", "구비서류", "면허", "업종", "직접생산", "중소기업"]):
            requirement_lines.append(cleaned[:260])
        if len(requirement_lines) >= 12:
            break

    return {
        "extraction_method": "rule_based_phase_1_6",
        "regions": _dedupe_text_items([notice.get("region_text", ""), *_find_notice_tokens(text, region_tokens)]),
        "licenses": _dedupe_text_items([notice.get("license_text", ""), *_find_notice_tokens(text, license_tokens)]),
        "company_types": _dedupe_text_items(_find_notice_tokens(text, company_type_tokens)),
        "required_documents": _dedupe_text_items(_find_notice_tokens(text, document_tokens)),
        "requirement_lines": _dedupe_text_items(requirement_lines),
        "money": {
            "presmpt_prce": clean_text(notice.get("presmpt_prce")),
            "bdgt_amt": clean_text(notice.get("bdgt_amt")),
            "bssamt": clean_text(notice.get("bssamt")),
        },
        "dates": {
            "bid_ntce_dt": clean_text(notice.get("bid_ntce_dt")),
            "bid_begin_dt": clean_text(notice.get("bid_begin_dt")),
            "bid_clse_dt": clean_text(notice.get("bid_clse_dt")),
            "openg_dt": clean_text(notice.get("openg_dt")),
        },
        "uncertainty_notes": [
            "Phase 1.6에서는 요구조건 후보만 추출하며 법인별 지원 가능 여부는 판단하지 않습니다."
        ],
    }


def render_notice_requirements_markdown(requirements: dict) -> str:
    def line(label: str, values: list[str]) -> str:
        return f"- {label}: {', '.join(values) if values else '원문 확인 필요'}"

    return "\n".join(
        [
            "",
            "## 공고 요구조건 구조화 후보",
            line("지역", requirements.get("regions") or []),
            line("면허/업종", requirements.get("licenses") or []),
            line("기업유형", requirements.get("company_types") or []),
            line("제출/증빙서류", requirements.get("required_documents") or []),
            f"- 추정가격: {(requirements.get('money') or {}).get('presmpt_prce') or '원문 확인 필요'}",
            f"- 입찰마감: {(requirements.get('dates') or {}).get('bid_clse_dt') or '원문 확인 필요'}",
            "",
            "※ 위 항목은 자동 추출 후보이며, 최종 지원 가능 여부 판단이 아닙니다.",
        ]
    )


def ensure_table_columns(conn: sqlite3.Connection, table_name: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for column_name, ddl in columns.items():
        if column_name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "uploads").mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "corporation-evidence").mkdir(parents=True, exist_ok=True)

    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS corporations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                management_group_name TEXT DEFAULT '기본 관리그룹',
                business_category TEXT DEFAULT '',
                region TEXT DEFAULT '',
                certifications_json TEXT DEFAULT '[]',
                company_size_classification TEXT DEFAULT '',
                internal_notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                corporation_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS project_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                document_type TEXT DEFAULT 'general',
                original_file_name TEXT NOT NULL,
                stored_file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                memo TEXT DEFAULT '',
                revision_note TEXT DEFAULT '',
                parsing_status TEXT DEFAULT 'pending',
                ocr_status TEXT DEFAULT 'pending',
                analysis_status TEXT DEFAULT 'pending',
                latest_analysis_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_document_id INTEGER NOT NULL,
                analysis_type TEXT DEFAULT 'summary',
                model_provider TEXT DEFAULT 'gemini',
                model_name TEXT DEFAULT 'gemini-2.5-flash',
                prompt_version TEXT DEFAULT 'v1',
                input_hash TEXT NOT NULL,
                output_json TEXT NOT NULL,
                output_markdown TEXT NOT NULL,
                token_usage_json TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_document_id) REFERENCES project_documents(id)
            );

            CREATE TABLE IF NOT EXISTS corporation_evidence_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                corporation_id INTEGER,
                management_group_name TEXT DEFAULT '기본 관리그룹',
                document_type TEXT DEFAULT 'unknown',
                classification_status TEXT DEFAULT 'needs_review',
                classification_confidence REAL DEFAULT 0,
                original_file_name TEXT NOT NULL,
                stored_file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                memo TEXT DEFAULT '',
                extraction_status TEXT DEFAULT 'pending',
                ocr_status TEXT DEFAULT 'pending',
                review_status TEXT DEFAULT 'pending',
                extracted_text TEXT DEFAULT '',
                extracted_text_preview TEXT DEFAULT '',
                extraction_json TEXT DEFAULT '{}',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS corporation_profile_update_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_document_id INTEGER NOT NULL,
                corporation_id INTEGER,
                field_key TEXT NOT NULL,
                field_label TEXT DEFAULT '',
                extracted_value TEXT DEFAULT '',
                confidence REAL DEFAULT 0,
                source_text TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                applied_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(evidence_document_id) REFERENCES corporation_evidence_documents(id),
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS nara_notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bid_ntce_no TEXT NOT NULL,
                bid_ntce_ord TEXT NOT NULL,
                bid_ntce_nm TEXT DEFAULT '',
                ntce_instt_nm TEXT DEFAULT '',
                dminstt_nm TEXT DEFAULT '',
                bid_ntce_dt TEXT DEFAULT '',
                bid_begin_dt TEXT DEFAULT '',
                bid_clse_dt TEXT DEFAULT '',
                openg_dt TEXT DEFAULT '',
                presmpt_prce TEXT DEFAULT '',
                bdgt_amt TEXT DEFAULT '',
                bssamt TEXT DEFAULT '',
                region_text TEXT DEFAULT '',
                license_text TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                raw_json TEXT NOT NULL,
                detail_json TEXT DEFAULT '{}',
                save_status TEXT DEFAULT 'saved',
                download_status TEXT DEFAULT 'pending',
                analysis_status TEXT DEFAULT 'pending',
                analysis_summary_json TEXT DEFAULT '{}',
                analysis_summary_markdown TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(bid_ntce_no, bid_ntce_ord)
            );

            CREATE TABLE IF NOT EXISTS nara_notice_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nara_notice_id INTEGER NOT NULL,
                file_name TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                source_field TEXT DEFAULT '',
                file_extension TEXT DEFAULT '',
                support_status TEXT DEFAULT 'unsupported',
                download_status TEXT DEFAULT 'pending',
                stored_file_path TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                parse_status TEXT DEFAULT 'pending',
                analysis_status TEXT DEFAULT 'pending',
                extracted_text_preview TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(nara_notice_id) REFERENCES nara_notices(id)
            );

            CREATE TABLE IF NOT EXISTS integration_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_name TEXT NOT NULL,
                status TEXT NOT NULL,
                http_status INTEGER,
                result_code TEXT DEFAULT '',
                result_msg TEXT DEFAULT '',
                total_count INTEGER DEFAULT 0,
                detail TEXT DEFAULT '',
                tested_at TEXT NOT NULL
            );
            """
        )
        ensure_table_columns(
            conn,
            "corporations",
            {
                "management_group_name": "TEXT DEFAULT '기본 관리그룹'",
                "business_registration_number": "TEXT DEFAULT ''",
                "representative_name": "TEXT DEFAULT ''",
                "corporate_registration_number": "TEXT DEFAULT ''",
                "business_address": "TEXT DEFAULT ''",
                "headquarters_address": "TEXT DEFAULT ''",
                "opening_date": "TEXT DEFAULT ''",
                "business_type": "TEXT DEFAULT ''",
                "business_item": "TEXT DEFAULT ''",
                "preference_tags_json": "TEXT DEFAULT '[]'",
                "direct_production_items_json": "TEXT DEFAULT '[]'",
                "license_summary": "TEXT DEFAULT ''",
                "procurement_registration_status": "TEXT DEFAULT ''",
                "evidence_expiry_summary": "TEXT DEFAULT ''",
                "evidence_verification_status": "TEXT DEFAULT 'unverified'",
            },
        )
        ensure_table_columns(
            conn,
            "corporation_evidence_documents",
            {
                "management_group_name": "TEXT DEFAULT '기본 관리그룹'",
            },
        )
        conn.commit()


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def one_or_404(conn: sqlite3.Connection, query: str, params: tuple):
    row = conn.execute(query, params).fetchone()
    if not row:
        return None, (jsonify({"detail": "Not found"}), 404)
    return row, None


def extract_text(file_path: Path) -> str:
    return extract_document(file_path).text


def extract_evidence_text(file_path: Path) -> tuple[str, str, dict[str, Any]]:
    suffix = file_path.suffix.lower()
    if suffix in EVIDENCE_IMAGE_EXTENSIONS:
        ocr_result = run_ocr(file_path)
        return ocr_result.text, "image", ocr_result.to_dict()

    parsed = extract_document(file_path)
    ocr_result = run_ocr_if_needed(parsed.text, file_path, parsed.kind, parsed.metadata)
    text = ocr_result.text or parsed.text
    return text, parsed.kind, {"parser": parsed.metadata, "ocr": ocr_result.to_dict()}


LLM_EVIDENCE_DOCUMENT_TYPES = {
    "business_registration_certificate",
    "business_registration_proof",
    "small_business_confirmation",
    "women_owned_business_confirmation",
    "disabled_owned_business_confirmation",
    "direct_production_confirmation",
    "procurement_registration_certificate",
    "license_registration_certificate",
    "tax_payment_certificate",
    "local_tax_payment_certificate",
    "insurance_payment_certificate",
    "credit_rating_certificate",
    "performance_certificate",
    "financial_statement_certificate",
    "employment_certificate",
    "qualification_certificate",
    "social_enterprise_certificate",
    "venture_business_confirmation",
    "startup_business_confirmation",
    "factory_registration_certificate",
    "unknown",
}


def parse_json_object(raw_text: str) -> dict:
    cleaned = clean_text(raw_text)
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("AI response must be a JSON object")
    return payload


def generate_json_with_ai(prompt: str, selection: dict) -> tuple[dict, dict]:
    provider = selection["provider"]
    model = selection["model"]
    if not selection["configured"]:
        raise ValueError(f"{provider.upper()} API key is not configured")

    if provider == "gemini":
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return parse_json_object(response.text), {"provider": provider, "model": model}

    if provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.create(
            model=model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        return parse_json_object(response.output_text), {"provider": provider, "model": model}

    raise ValueError(f"Unsupported AI provider: {provider}")


def classify_unknown_evidence_with_ai(
    text: str,
    file_name: str,
    provider: str | None = None,
    model: str | None = None,
) -> EvidenceExtractionResult | None:
    if not clean_text(text):
        return None

    selection = resolve_ai_model_selection(provider, model)
    if not selection["configured"]:
        return None

    prompt = "\n".join(
        [
            "당신은 대한민국 공공조달 법인 증빙서류 분류 보조자입니다.",
            "아래 문서가 어떤 증빙서류인지 분류하고, 법인 프로필에 반영 가능한 후보 필드만 추출하세요.",
            "결과는 반드시 JSON 객체만 반환하세요.",
            "문서에 없는 값은 만들지 마세요.",
            "자동 확정이 아니라 사용자 검토용 후보이므로 confidence를 보수적으로 부여하세요.",
            "document_type은 다음 중 하나만 사용하세요: " + ", ".join(sorted(LLM_EVIDENCE_DOCUMENT_TYPES)),
            "candidate field_key는 다음 중 하나만 사용하세요: " + ", ".join(sorted(allowed_profile_update_fields())),
            "JSON schema: {\"document_type\":\"...\",\"classification_confidence\":0.0,\"candidates\":[{\"field_key\":\"...\",\"extracted_value\":\"...\",\"confidence\":0.0,\"source_text\":\"...\"}],\"warnings\":[\"...\"]}",
            "",
            f"[file_name]\n{file_name}",
            "",
            "[document_text]",
            text[:12000],
        ]
    )
    payload, usage = generate_json_with_ai(prompt, selection)
    document_type = clean_text(payload.get("document_type")) or "unknown"
    if document_type not in LLM_EVIDENCE_DOCUMENT_TYPES:
        document_type = "unknown"
    try:
        confidence = float(payload.get("classification_confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 0.95))

    candidates: list[EvidenceFieldCandidate] = []
    allowed_fields = allowed_profile_update_fields()
    raw_candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    for item in raw_candidates:
        if not isinstance(item, dict):
            continue
        field_key = clean_text(item.get("field_key"))
        if field_key not in allowed_fields:
            continue
        raw_value = item.get("extracted_value")
        if isinstance(raw_value, list):
            value = normalize_json_list(raw_value) if field_key in JSON_LIST_PROFILE_FIELDS else ", ".join(str(x) for x in raw_value)
        else:
            value = clean_text(raw_value)
        if not value:
            continue
        try:
            candidate_confidence = float(item.get("confidence", confidence))
        except (TypeError, ValueError):
            candidate_confidence = confidence
        candidates.append(
            EvidenceFieldCandidate(
                field_key=field_key,
                field_label=FIELD_LABELS.get(field_key, field_key),
                extracted_value=value,
                confidence=max(0.0, min(candidate_confidence, 0.95)),
                source_text=clean_text(item.get("source_text")) or value,
            )
        )

    warnings = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
    warning_values = [clean_text(value) for value in warnings if clean_text(value)]
    warning_values.append(f"AI 분류 제안: {usage['provider']} / {usage['model']}")
    classification_status = "ai_suggested" if document_type != "unknown" or candidates else "needs_review"
    return EvidenceExtractionResult(
        document_type=document_type,
        classification_confidence=confidence,
        classification_status=classification_status,
        candidates=candidates,
        warnings=warning_values,
    )


def refine_business_registration_kind_with_ai(
    analysis: EvidenceExtractionResult,
    text: str,
    file_name: str,
    provider: str | None = None,
    model: str | None = None,
) -> EvidenceExtractionResult:
    if analysis.document_type not in {"business_registration_certificate", "business_registration_proof"}:
        return analysis
    if not clean_text(text):
        return analysis

    selection = resolve_ai_model_selection(provider, model)
    if not selection["configured"]:
        return analysis

    prompt = "\n".join(
        [
            "당신은 대한민국 사업자등록증 OCR 후처리 보조자입니다.",
            "OCR 텍스트에서 '사업의 종류' 표의 업태와 종목만 정리하세요.",
            "문서에 없는 값은 만들지 마세요.",
            "줄바꿈으로 끊어진 단어는 자연스럽게 붙이세요. 예: '전문기\\n업' -> '전문기업'.",
            "업태는 큰 분류입니다. 예: 건설업, 도소매, 도매 및 소매업.",
            "종목은 세부 영업 내용입니다. 예: 전기공사, 정보통신공사업, 컴퓨터 관련 주변기기.",
            "결과는 반드시 JSON 객체만 반환하세요.",
            "JSON schema: {\"business_type\":[\"...\"],\"business_item\":[\"...\"],\"business_category\":\"업태: ... / 종목: ...\",\"warnings\":[\"...\"]}",
            "",
            f"[file_name]\n{file_name}",
            "",
            "[ocr_text]",
            text[:12000],
        ]
    )
    payload, usage = generate_json_with_ai(prompt, selection)

    business_type = normalize_json_list(payload.get("business_type"))
    business_item = normalize_json_list(payload.get("business_item"))

    def json_list_to_text(value: str) -> str:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return clean_text(value)
        return ", ".join(clean_text(item) for item in parsed if clean_text(item)) if isinstance(parsed, list) else ""

    business_type_text = json_list_to_text(business_type)
    business_item_text = json_list_to_text(business_item)
    business_category = clean_text(payload.get("business_category"))
    if not business_category:
        business_category = " / ".join(
            item
            for item in [
                f"업태: {business_type_text}" if business_type_text else "",
                f"종목: {business_item_text}" if business_item_text else "",
            ]
            if item
        )

    refined_candidates: list[EvidenceFieldCandidate] = []
    if business_type_text:
        refined_candidates.append(
            EvidenceFieldCandidate(
                field_key="business_type",
                field_label=FIELD_LABELS["business_type"],
                extracted_value=business_type_text,
                confidence=0.9,
                source_text="LLM 업태 정규화",
            )
        )
    if business_item_text:
        refined_candidates.append(
            EvidenceFieldCandidate(
                field_key="business_item",
                field_label=FIELD_LABELS["business_item"],
                extracted_value=business_item_text,
                confidence=0.9,
                source_text="LLM 종목 정규화",
            )
        )
    if business_category:
        refined_candidates.append(
            EvidenceFieldCandidate(
                field_key="business_category",
                field_label=FIELD_LABELS["business_category"],
                extracted_value=business_category,
                confidence=0.88,
                source_text="LLM 업태/종목 정규화",
            )
        )

    if not refined_candidates:
        return analysis

    preserved_candidates = [
        candidate
        for candidate in analysis.candidates
        if candidate.field_key not in {"business_type", "business_item", "business_category"}
    ]
    raw_warnings = payload.get("warnings") if isinstance(payload.get("warnings"), list) else []
    warning_values = [clean_text(value) for value in raw_warnings if clean_text(value)]
    warning_values.append(f"AI 업태/종목 정리: {usage['provider']} / {usage['model']}")
    return EvidenceExtractionResult(
        document_type=analysis.document_type,
        classification_confidence=analysis.classification_confidence,
        classification_status=analysis.classification_status,
        candidates=[*preserved_candidates, *refined_candidates],
        warnings=[*analysis.warnings, *warning_values],
    )


def candidate_rows_for_evidence(conn: sqlite3.Connection, evidence_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT * FROM corporation_profile_update_candidates
        WHERE evidence_document_id=?
        ORDER BY id
        """,
        (evidence_id,),
    ).fetchall()
    return rows_to_dict(rows)


def approved_candidate_identity_set(conn: sqlite3.Connection, evidence_id: int) -> set[tuple[str, str]]:
    rows = conn.execute(
        """
        SELECT field_key, extracted_value
        FROM corporation_profile_update_candidates
        WHERE evidence_document_id=? AND status='approved'
        """,
        (evidence_id,),
    ).fetchall()
    return {(row["field_key"], clean_text(row["extracted_value"])) for row in rows}


def evidence_detail(conn: sqlite3.Connection, evidence_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
    if not row:
        return None
    payload = dict(row)
    payload["candidates"] = candidate_rows_for_evidence(conn, evidence_id)
    return payload


def evidence_list_payload(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[dict]:
    payload = rows_to_dict(rows)
    if not payload:
        return []

    evidence_ids = [item["id"] for item in payload]
    placeholders = ",".join("?" for _ in evidence_ids)
    candidate_rows = conn.execute(
        f"""
        SELECT evidence_document_id, status, COUNT(*) AS count
        FROM corporation_profile_update_candidates
        WHERE evidence_document_id IN ({placeholders})
        GROUP BY evidence_document_id, status
        """,
        tuple(evidence_ids),
    ).fetchall()
    counts: dict[int, dict[str, int]] = {}
    for row in candidate_rows:
        evidence_id = row["evidence_document_id"]
        counts.setdefault(evidence_id, {})[row["status"]] = row["count"]

    corporation_ids = sorted({item["corporation_id"] for item in payload if item.get("corporation_id")})
    corporation_names: dict[int, str] = {}
    if corporation_ids:
        corp_placeholders = ",".join("?" for _ in corporation_ids)
        corp_rows = conn.execute(
            f"SELECT id, name FROM corporations WHERE id IN ({corp_placeholders})",
            tuple(corporation_ids),
        ).fetchall()
        corporation_names = {row["id"]: row["name"] for row in corp_rows}

    for item in payload:
        status_counts = counts.get(item["id"], {})
        item["candidate_count"] = sum(status_counts.values())
        item["pending_candidate_count"] = status_counts.get("pending", 0)
        item["approved_candidate_count"] = status_counts.get("approved", 0)
        item["corporation_name"] = corporation_names.get(item.get("corporation_id"), "")
        item["candidates"] = []
    return payload


def process_corporation_evidence_analysis(
    file_path: Path,
    original_file_name: str,
    requested_document_type: str,
) -> dict[str, Any]:
    extraction_status = "completed"
    ocr_status = "skipped"
    extracted_text = ""
    extraction_payload: dict[str, Any] = {}
    error_message = ""

    try:
        extracted_text, _kind, extraction_payload = extract_evidence_text(file_path)
        ocr_status = (extraction_payload.get("ocr") or {}).get("status", "skipped")
    except Exception as exc:
        extraction_status = "failed"
        error_message = str(exc)

    analysis = analyze_corporation_evidence_text(extracted_text, original_file_name, requested_document_type)

    return {
        "analysis": analysis,
        "extraction_status": extraction_status,
        "ocr_status": ocr_status,
        "extracted_text": extracted_text,
        "extraction_payload": extraction_payload,
        "error_message": error_message,
    }


def analyze_corporation_evidence_text(
    extracted_text: str,
    original_file_name: str,
    requested_document_type: str,
) -> EvidenceExtractionResult:
    analysis = analyze_corporation_evidence(extracted_text, original_file_name, requested_document_type)
    if (
        requested_document_type in {"", "auto"}
        and analysis.classification_status == "needs_review"
        and extracted_text.strip()
    ):
        try:
            ai_analysis = classify_unknown_evidence_with_ai(extracted_text, original_file_name)
            if ai_analysis:
                analysis = ai_analysis
        except Exception as exc:
            analysis = EvidenceExtractionResult(
                document_type=analysis.document_type,
                classification_confidence=analysis.classification_confidence,
                classification_status=analysis.classification_status,
                candidates=analysis.candidates,
                warnings=[*analysis.warnings, f"AI 분류 실패: {type(exc).__name__}"],
            )
    if analysis.document_type in {"business_registration_certificate", "business_registration_proof"}:
        try:
            analysis = refine_business_registration_kind_with_ai(
                analysis,
                extracted_text,
                original_file_name,
            )
        except Exception as exc:
            analysis = EvidenceExtractionResult(
                document_type=analysis.document_type,
                classification_confidence=analysis.classification_confidence,
                classification_status=analysis.classification_status,
                candidates=analysis.candidates,
                warnings=[*analysis.warnings, f"AI 업태/종목 정리 실패: {type(exc).__name__}"],
            )
    return analysis


def corporation_allowed_update_fields() -> set[str]:
    return {
        "name",
        "management_group_name",
        "business_category",
        "region",
        "certifications_json",
        "company_size_classification",
        "internal_notes",
        "business_registration_number",
        "representative_name",
        "corporate_registration_number",
        "business_address",
        "headquarters_address",
        "opening_date",
        "business_type",
        "business_item",
        "preference_tags_json",
        "direct_production_items_json",
        "license_summary",
        "procurement_registration_status",
        "evidence_expiry_summary",
        "evidence_verification_status",
    }


JSON_LIST_PROFILE_FIELDS = {"certifications_json", "preference_tags_json", "direct_production_items_json"}


def normalize_profile_update_value(field_key: str, value: Any) -> str:
    if field_key in JSON_LIST_PROFILE_FIELDS:
        return normalize_json_list(value)
    if field_key == "business_registration_number":
        return normalize_business_registration_number(value)
    if field_key == "management_group_name":
        return normalize_management_group_name(value)
    return clean_text(value)


def normalize_json_list(value: Any) -> str:
    if value in (None, ""):
        return "[]"
    if isinstance(value, list):
        items = [clean_text(item) for item in value if clean_text(item)]
        return json.dumps(list(dict.fromkeys(items)), ensure_ascii=False)
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return normalize_json_list(parsed)
        except json.JSONDecodeError:
            pass
        items = [item.strip() for item in stripped.split(",") if item.strip()]
        return json.dumps(list(dict.fromkeys(items)), ensure_ascii=False)
    return "[]"


def merge_json_list_values(existing: Any, incoming: Any) -> str:
    def parse_items(value: Any) -> list[str]:
        try:
            parsed = json.loads(value) if isinstance(value, str) else value
        except json.JSONDecodeError:
            parsed = value
        if isinstance(parsed, list):
            return [clean_text(item) for item in parsed if clean_text(item)]
        if isinstance(parsed, str):
            return [item.strip() for item in parsed.split(",") if item.strip()]
        return []

    merged = list(dict.fromkeys([*parse_items(existing), *parse_items(incoming)]))
    return json.dumps(merged, ensure_ascii=False)


def has_json_list_value(value: Any) -> bool:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        parsed = value
    if isinstance(parsed, list):
        return any(clean_text(item) for item in parsed)
    if isinstance(parsed, str):
        return bool(clean_text(parsed))
    return False


def build_corporation_readiness(conn: sqlite3.Connection, corporation: sqlite3.Row) -> dict:
    evidence_stats = conn.execute(
        """
        SELECT
          COUNT(*) AS evidence_count,
          SUM(CASE WHEN review_status='approved' THEN 1 ELSE 0 END) AS approved_evidence_count
        FROM corporation_evidence_documents
        WHERE corporation_id=?
        """,
        (corporation["id"],),
    ).fetchone()
    candidate_stats = conn.execute(
        """
        SELECT COUNT(*) AS approved_candidate_count
        FROM corporation_profile_update_candidates
        WHERE corporation_id=? AND status='approved'
        """,
        (corporation["id"],),
    ).fetchone()
    evidence_count = evidence_stats["evidence_count"] or 0
    approved_evidence_count = evidence_stats["approved_evidence_count"] or 0
    approved_candidate_count = candidate_stats["approved_candidate_count"] or 0
    checks = [
        {
            "key": "business_registration_number",
            "label": "사업자등록번호",
            "ready": bool(clean_text(corporation["business_registration_number"])),
        },
        {
            "key": "representative_name",
            "label": "대표자",
            "ready": bool(clean_text(corporation["representative_name"])),
        },
        {
            "key": "business_address",
            "label": "사업장 주소",
            "ready": bool(clean_text(corporation["business_address"]) or clean_text(corporation["headquarters_address"])),
        },
        {
            "key": "business_category",
            "label": "업종/종목",
            "ready": bool(
                clean_text(corporation["business_category"])
                or clean_text(corporation["business_type"])
                or clean_text(corporation["business_item"])
            ),
        },
        {
            "key": "region",
            "label": "지역",
            "ready": bool(clean_text(corporation["region"])),
        },
        {
            "key": "company_size_classification",
            "label": "기업 규모",
            "ready": bool(clean_text(corporation["company_size_classification"])),
        },
        {
            "key": "certifications_json",
            "label": "인증/확인서",
            "ready": has_json_list_value(corporation["certifications_json"]),
        },
        {
            "key": "preference_or_direct_production",
            "label": "우대조건/직접생산",
            "ready": has_json_list_value(corporation["preference_tags_json"])
            or has_json_list_value(corporation["direct_production_items_json"]),
        },
        {
            "key": "license_or_procurement",
            "label": "면허/나라장터 등록",
            "ready": bool(
                clean_text(corporation["license_summary"])
                or clean_text(corporation["procurement_registration_status"])
            ),
        },
        {
            "key": "approved_evidence",
            "label": "승인된 증빙 이력",
            "ready": corporation["evidence_verification_status"] == "evidence_reviewed"
            or approved_evidence_count > 0
            or approved_candidate_count > 0,
        },
    ]
    ready_count = sum(1 for check in checks if check["ready"])
    score = round((ready_count / len(checks)) * 100)
    if score >= 80:
        status = "ready_basis"
        status_label = "기초 판단 준비"
    elif score >= 50:
        status = "partial"
        status_label = "일부 보완 필요"
    else:
        status = "needs_evidence"
        status_label = "증빙 우선 필요"
    missing_items = [check["label"] for check in checks if not check["ready"]]
    return {
        "corporation_id": corporation["id"],
        "corporation_name": corporation["name"],
        "management_group_name": corporation["management_group_name"],
        "score": score,
        "status": status,
        "status_label": status_label,
        "ready_count": ready_count,
        "total_count": len(checks),
        "missing_items": missing_items,
        "checks": checks,
        "evidence_count": evidence_count,
        "approved_evidence_count": approved_evidence_count,
        "approved_candidate_count": approved_candidate_count,
        "updated_at": corporation["updated_at"],
    }


def find_corporation_registration_duplicates(
    conn: sqlite3.Connection,
    business_registration_number: str,
    management_group_name: str,
    exclude_id: int | None = None,
) -> dict[str, list[dict]]:
    match_key = business_registration_match_key(business_registration_number)
    if not match_key:
        return {"same_group": [], "other_groups": []}

    rows = conn.execute(
        """
        SELECT id, name, management_group_name, business_registration_number
        FROM corporations
        WHERE business_registration_number <> ''
        ORDER BY id DESC
        """
    ).fetchall()
    same_group: list[dict] = []
    other_groups: list[dict] = []
    target_group = normalize_management_group_name(management_group_name)
    for row in rows:
        if exclude_id and row["id"] == exclude_id:
            continue
        if business_registration_match_key(row["business_registration_number"]) != match_key:
            continue
        summary = {
            "id": row["id"],
            "name": row["name"],
            "management_group_name": normalize_management_group_name(row["management_group_name"]),
            "business_registration_number": row["business_registration_number"],
        }
        if normalize_management_group_name(row["management_group_name"]) == target_group:
            same_group.append(summary)
        else:
            other_groups.append(summary)
    return {"same_group": same_group, "other_groups": other_groups}


def duplicate_other_group_warnings(duplicates: dict[str, list[dict]]) -> list[str]:
    if not duplicates.get("other_groups"):
        return []
    group_names = ", ".join(
        dict.fromkeys(row["management_group_name"] for row in duplicates["other_groups"])
    )
    return [f"동일한 사업자등록번호가 다른 관리 법인그룹에 이미 존재합니다: {group_names}"]


def clear_corporation_evidence_documents(conn: sqlite3.Connection, corporation_id: int) -> None:
    rows = conn.execute(
        "SELECT id, stored_file_path FROM corporation_evidence_documents WHERE corporation_id=?",
        (corporation_id,),
    ).fetchall()
    for row in rows:
        if row["stored_file_path"]:
            safe_unlink(Path(row["stored_file_path"]))
        conn.execute("DELETE FROM corporation_profile_update_candidates WHERE evidence_document_id=?", (row["id"],))
    conn.execute("DELETE FROM corporation_evidence_documents WHERE corporation_id=?", (corporation_id,))


SUMMARY_PROMPT_VERSION = "v1"
SUMMARY_JSON_KEYS = [
    "document_summary",
    "key_dates",
    "requirements",
    "required_documents",
    "risks",
    "questions_to_check",
    "confidence_note",
]


def build_summary_prompt(text: str) -> str:
    return "\n".join(
        [
            "당신은 대한민국 조달문서 분석 보조자입니다.",
            "아래 문서 텍스트를 행정사가 빠르게 이해할 수 있도록 요약하세요.",
            "반드시 JSON 객체만 반환하세요.",
            "문서에 없는 내용은 추측하지 말고, 불확실하면 confidence_note 또는 questions_to_check에 남기세요.",
            "JSON keys: " + ", ".join(SUMMARY_JSON_KEYS),
            "",
            "[문서 텍스트]",
            text[:120000],
        ]
    )


def parse_ai_json_output(raw_text: str) -> dict:
    cleaned = clean_text(raw_text)
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("AI response must be a JSON object")
    for key in SUMMARY_JSON_KEYS:
        payload.setdefault(key, [] if key.endswith("s") or key == "questions_to_check" else "")
    return payload


def render_summary_markdown(payload: dict) -> str:
    requirements = payload.get("requirements") or []
    return "\n".join(
        [
            "## 문서 요약",
            str(payload.get("document_summary") or ""),
            "",
            "## 요구사항",
            *[f"- {x}" for x in requirements],
            "",
            f"신뢰도 메모: {payload.get('confidence_note') or ''}",
        ]
    )


def summarize_with_fallback(
    text: str,
    requested_provider: str | None = None,
    requested_model: str | None = None,
) -> tuple[dict, str, dict]:
    if not text:
        payload = {
            "document_summary": "문서에서 추출 가능한 텍스트가 부족합니다.",
            "key_dates": [],
            "requirements": [],
            "required_documents": [],
            "risks": [],
            "questions_to_check": ["원문 파일 품질(OCR) 재확인 필요"],
            "confidence_note": "Low confidence",
        }
    else:
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        payload = {
            "document_summary": " ".join(lines[:4])[:500],
            "key_dates": [],
            "requirements": lines[4:10],
            "required_documents": [],
            "risks": [],
            "questions_to_check": ["핵심 일정/제출 서류를 원문에서 재확인하세요."],
            "confidence_note": "Fallback summary (no API key or API failed)",
        }

    markdown = render_summary_markdown(payload)
    usage = {"provider": "fallback", "model": "local", "input_chars": len(text)}
    if requested_provider:
        usage["requested_provider"] = requested_provider
    if requested_model:
        usage["requested_model"] = requested_model
    return payload, markdown, usage


def summarize_with_openai(text: str, model: str | None = None) -> tuple[dict, str, dict]:
    from openai import OpenAI

    model_name = model or OPENAI_MODEL_PRIMARY
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": "You are a Korean procurement summary assistant. Return strict JSON only.",
            },
            {"role": "user", "content": build_summary_prompt(text)},
        ],
        text={"format": {"type": "json_object"}},
    )
    payload = parse_ai_json_output(resp.output_text)
    markdown = render_summary_markdown(payload)
    usage = {"provider": "openai", "model": model_name, "input_chars": len(text)}
    return payload, markdown, usage


def summarize_with_gemini(text: str, model: str | None = None) -> tuple[dict, str, dict]:
    from google import genai

    model_name = model or GEMINI_MODEL_PRIMARY
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=model_name,
        contents=build_summary_prompt(text),
        config={"response_mime_type": "application/json"},
    )
    payload = parse_ai_json_output(response.text)
    markdown = render_summary_markdown(payload)
    usage = {"provider": "gemini", "model": model_name, "input_chars": len(text)}
    return payload, markdown, usage


def summarize_with_ai(text: str, selection: dict) -> tuple[dict, str, dict]:
    provider = selection["provider"]
    model = selection["model"]
    if not selection["configured"]:
        payload, markdown, usage = summarize_with_fallback(text, provider, model)
        usage["fallback_reason"] = f"{provider.upper()} API key is not configured"
        return payload, markdown, usage
    if provider == "openai":
        return summarize_with_openai(text, model)
    if provider == "gemini":
        return summarize_with_gemini(text, model)
    payload, markdown, usage = summarize_with_fallback(text, provider, model)
    usage["fallback_reason"] = f"Unsupported AI provider: {provider}"
    return payload, markdown, usage


def run_analysis(
    document_id: int,
    force: bool = False,
    ai_provider: str | None = None,
    ai_model: str | None = None,
) -> tuple[dict, int]:
    with db_conn() as conn:
        doc = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not doc:
            return {"detail": "Document not found"}, 404

        file_path = Path(doc["stored_file_path"])
        if not file_path.exists():
            conn.execute(
                "UPDATE project_documents SET parsing_status=?, analysis_status=?, updated_at=? WHERE id=?",
                ("failed", "failed", now_iso(), document_id),
            )
            conn.commit()
            return {"detail": "Stored file is missing"}, 400

        try:
            parsed = extract_document(file_path)
        except Exception as exc:
            conn.execute(
                "UPDATE project_documents SET parsing_status=?, analysis_status=?, updated_at=? WHERE id=?",
                ("failed", "failed", now_iso(), document_id),
            )
            conn.commit()
            return {"detail": f"Document parsing failed: {exc}"}, 500

        ocr_result = run_ocr_if_needed(parsed.text, file_path, parsed.kind, parsed.metadata)
        text = ocr_result.text or parsed.text
        ocr_status = ocr_result.status
        input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        selection = resolve_ai_model_selection(ai_provider, ai_model)
        cache_model_provider = selection["provider"] if selection["configured"] else "fallback"
        cache_model_name = selection["model"] if selection["configured"] else "local"

        if not force:
            cached = conn.execute(
                """
                SELECT * FROM analyses
                WHERE project_document_id=? AND input_hash=? AND model_provider=? AND model_name=? AND prompt_version=?
                ORDER BY id DESC LIMIT 1
                """,
                (document_id, input_hash, cache_model_provider, cache_model_name, SUMMARY_PROMPT_VERSION),
            ).fetchone()
            if cached:
                conn.execute(
                    "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
                    ("completed", ocr_status, "cached", cached["id"], now_iso(), document_id),
                )
                conn.commit()
                return {"analysis_id": cached["id"], "status": "cached", "message": "Analysis reused from cache"}, 200

        try:
            output_json, output_md, usage = summarize_with_ai(text, selection)
        except Exception as exc:
            output_json, output_md, usage = summarize_with_fallback(text, selection["provider"], selection["model"])
            usage["fallback_reason"] = str(exc)

        usage["extraction"] = parsed.metadata
        usage["ocr"] = ocr_result.to_dict()
        model_provider = usage.get("provider", "fallback")
        model_name = usage.get("model", selection["model"] if model_provider in AI_PROVIDERS else "local")

        cur = conn.execute(
            """
            INSERT INTO analyses (
              project_document_id, analysis_type, model_provider, model_name, prompt_version,
              input_hash, output_json, output_markdown, token_usage_json, status, error_message, created_at
            ) VALUES (?, 'summary', ?, ?, ?, ?, ?, ?, ?, 'completed', '', ?)
            """,
            (
                document_id,
                model_provider,
                model_name,
                SUMMARY_PROMPT_VERSION,
                input_hash,
                json.dumps(output_json, ensure_ascii=False),
                output_md,
                json.dumps(usage, ensure_ascii=False),
                now_iso(),
            ),
        )
        analysis_id = cur.lastrowid

        conn.execute(
            "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
            ("completed", ocr_status, "completed", analysis_id, now_iso(), document_id),
        )
        conn.commit()

    return {"analysis_id": analysis_id, "status": "completed", "message": "Analysis completed"}, 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    with db_conn() as conn:
        corp = conn.execute("SELECT COUNT(*) c FROM corporations").fetchone()["c"]
        proj = conn.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
        docs = conn.execute("SELECT COUNT(*) c FROM project_documents").fetchone()["c"]
    return jsonify({"corporation_count": corp, "project_count": proj, "document_count": docs})


@app.route("/api/corporations", methods=["GET"])
def list_corporations():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM corporations ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/corporations", methods=["POST"])
def create_corporation():
    payload = get_json_payload()
    name = clean_text(payload.get("name"))
    if not name:
        return jsonify({"detail": "name is required"}), 400

    management_group_name = normalize_management_group_name(payload.get("management_group_name"))
    business_registration_number = normalize_business_registration_number(payload.get("business_registration_number"))
    now = now_iso()
    with db_conn() as conn:
        duplicates = find_corporation_registration_duplicates(
            conn,
            business_registration_number,
            management_group_name,
        )
        if duplicates["same_group"]:
            return (
                jsonify(
                    {
                        "detail": "같은 관리 법인그룹에 동일한 사업자등록번호 법인이 이미 존재합니다.",
                        "duplicate_corporations": duplicates["same_group"],
                    }
                ),
                409,
            )

        cur = conn.execute(
            """
            INSERT INTO corporations (
              name, management_group_name, business_category, region, certifications_json, company_size_classification,
              internal_notes, business_registration_number, representative_name,
              corporate_registration_number, business_address, headquarters_address,
              opening_date, business_type, business_item, preference_tags_json,
              direct_production_items_json, license_summary, procurement_registration_status,
              evidence_expiry_summary, evidence_verification_status,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                management_group_name,
                clean_text(payload.get("business_category")),
                clean_text(payload.get("region")),
                normalize_json_list(payload.get("certifications_json")),
                clean_text(payload.get("company_size_classification")),
                clean_text(payload.get("internal_notes")),
                business_registration_number,
                clean_text(payload.get("representative_name")),
                clean_text(payload.get("corporate_registration_number")),
                clean_text(payload.get("business_address")),
                clean_text(payload.get("headquarters_address")),
                clean_text(payload.get("opening_date")),
                clean_text(payload.get("business_type")),
                clean_text(payload.get("business_item")),
                normalize_json_list(payload.get("preference_tags_json")),
                normalize_json_list(payload.get("direct_production_items_json")),
                clean_text(payload.get("license_summary")),
                clean_text(payload.get("procurement_registration_status")),
                clean_text(payload.get("evidence_expiry_summary")),
                clean_text(payload.get("evidence_verification_status"), "manual"),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (cur.lastrowid,)).fetchone()
    response_payload = dict(row)
    warnings = duplicate_other_group_warnings(duplicates)
    if warnings:
        response_payload["warnings"] = warnings
        response_payload["duplicate_corporations"] = duplicates["other_groups"]
    return jsonify(response_payload), 201


@app.route("/api/corporations/readiness", methods=["GET"])
def list_corporation_readiness():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM corporations ORDER BY id DESC").fetchall()
        payload = [build_corporation_readiness(conn, row) for row in rows]
    return jsonify(payload)


@app.route("/api/corporations/<int:corporation_id>/readiness", methods=["GET"])
def get_corporation_readiness(corporation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Corporation not found"}), 404
        payload = build_corporation_readiness(conn, row)
    return jsonify(payload)


@app.route("/api/corporations/<int:corporation_id>", methods=["GET"])
def get_corporation(corporation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Corporation not found"}), 404
    return jsonify(dict(row))


@app.route("/api/corporations/<int:corporation_id>", methods=["PATCH"])
def update_corporation(corporation_id: int):
    payload = get_json_payload()
    updates = {
        field: normalize_profile_update_value(field, payload[field])
        for field in corporation_allowed_update_fields()
        if field in payload
    }
    if "name" in updates and not updates["name"]:
        return jsonify({"detail": "name is required"}), 400
    if not updates:
        return jsonify({"detail": "No supported fields to update"}), 400

    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{field}=?" for field in updates)
    values = tuple(updates.values()) + (corporation_id,)

    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Corporation not found"}), 404
        target_business_registration_number = updates.get(
            "business_registration_number",
            row["business_registration_number"],
        )
        target_management_group_name = updates.get(
            "management_group_name",
            row["management_group_name"],
        )
        duplicates = find_corporation_registration_duplicates(
            conn,
            target_business_registration_number,
            target_management_group_name,
            exclude_id=corporation_id,
        )
        if duplicates["same_group"]:
            return (
                jsonify(
                    {
                        "detail": "같은 관리 법인그룹에 동일한 사업자등록번호 법인이 이미 존재합니다.",
                        "duplicate_corporations": duplicates["same_group"],
                    }
                ),
                409,
            )
        conn.execute(f"UPDATE corporations SET {assignments} WHERE id=?", values)
        conn.commit()
        updated = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
    response_payload = dict(updated)
    warnings = duplicate_other_group_warnings(duplicates)
    if warnings:
        response_payload["warnings"] = warnings
        response_payload["duplicate_corporations"] = duplicates["other_groups"]
    return jsonify(response_payload)


@app.route("/api/corporations/<int:corporation_id>", methods=["DELETE"])
def delete_corporation(corporation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Corporation not found"}), 404

        project_count = conn.execute("SELECT COUNT(*) c FROM projects WHERE corporation_id=?", (corporation_id,)).fetchone()["c"]
        if project_count:
            return jsonify({"detail": "Cannot delete corporation with linked projects"}), 409

        clear_corporation_evidence_documents(conn, corporation_id)
        conn.execute("DELETE FROM corporations WHERE id=?", (corporation_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/corporations/<int:corporation_id>/evidence-documents", methods=["GET"])
def list_corporation_evidence_documents(corporation_id: int):
    with db_conn() as conn:
        corp = conn.execute("SELECT id FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not corp:
            return jsonify({"detail": "Corporation not found"}), 404
        rows = conn.execute(
            """
            SELECT * FROM corporation_evidence_documents
            WHERE corporation_id=?
            ORDER BY id DESC
            """,
            (corporation_id,),
        ).fetchall()
        payload = evidence_list_payload(conn, rows)
    return jsonify(payload)


@app.route("/api/corporation-evidence-documents", methods=["GET"])
def list_all_corporation_evidence_documents():
    corporation_id = parse_int(request.args.get("corporation_id"), 0)
    with db_conn() as conn:
        if corporation_id:
            rows = conn.execute(
                "SELECT * FROM corporation_evidence_documents WHERE corporation_id=? ORDER BY id DESC",
                (corporation_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM corporation_evidence_documents ORDER BY id DESC").fetchall()
        payload = evidence_list_payload(conn, rows)
    return jsonify(payload)


@app.route("/api/corporation-evidence-documents", methods=["POST"])
def upload_corporation_evidence_document():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"detail": "file is required"}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in EVIDENCE_ALLOWED_EXTENSIONS:
        return jsonify({"detail": "Only PDF, DOCX, JPG, JPEG, and PNG evidence files are supported"}), 400

    corporation_id = parse_int(request.form.get("corporation_id"), 0) or None
    memo = clean_text(request.form.get("memo"))
    requested_document_type = clean_text(request.form.get("document_type")) or "auto"
    management_group_name = normalize_management_group_name(request.form.get("management_group_name"))

    with db_conn() as conn:
        if corporation_id:
            corp = conn.execute("SELECT id, management_group_name FROM corporations WHERE id=?", (corporation_id,)).fetchone()
            if not corp:
                return jsonify({"detail": "Corporation not found"}), 404
            management_group_name = normalize_management_group_name(corp["management_group_name"])

    evidence_dir = STORAGE_ROOT / evidence_storage_subdir(corporation_id)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stored_path = evidence_dir / f"{uuid.uuid4().hex}{suffix}"
    file.save(stored_path)

    now = now_iso()
    processing = process_corporation_evidence_analysis(stored_path, file.filename, requested_document_type)
    analysis = processing["analysis"]
    extraction_status = processing["extraction_status"]
    ocr_status = processing["ocr_status"]
    extracted_text = processing["extracted_text"]
    extraction_payload = processing["extraction_payload"]
    error_message = processing["error_message"]
    document_type = analysis.document_type
    classification_status = analysis.classification_status
    classification_confidence = analysis.classification_confidence

    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO corporation_evidence_documents (
              corporation_id, management_group_name, document_type, classification_status, classification_confidence,
              original_file_name, stored_file_path, mime_type, file_size, memo,
              extraction_status, ocr_status, review_status, extracted_text,
              extracted_text_preview, extraction_json, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                corporation_id,
                management_group_name,
                document_type,
                classification_status,
                classification_confidence,
                file.filename,
                str(stored_path),
                file.mimetype or "",
                stored_path.stat().st_size if stored_path.exists() else 0,
                memo,
                extraction_status,
                ocr_status,
                "pending",
                extracted_text,
                extracted_text[:1200],
                json.dumps({**analysis.to_dict(), "pipeline": extraction_payload}, ensure_ascii=False),
                error_message,
                now,
                now,
            ),
        )
        evidence_id = cur.lastrowid
        for candidate in analysis.candidates:
            conn.execute(
                """
                INSERT INTO corporation_profile_update_candidates (
                  evidence_document_id, corporation_id, field_key, field_label,
                  extracted_value, confidence, source_text, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    evidence_id,
                    corporation_id,
                    candidate.field_key,
                    candidate.field_label,
                    candidate.extracted_value,
                    candidate.confidence,
                    candidate.source_text,
                    now,
                    now,
                ),
            )
        conn.commit()
        payload = evidence_detail(conn, evidence_id)

    return jsonify(payload), 201


@app.route("/api/corporation-evidence-documents/<int:evidence_id>", methods=["GET"])
def get_corporation_evidence_document(evidence_id: int):
    with db_conn() as conn:
        payload = evidence_detail(conn, evidence_id)
    if not payload:
        return jsonify({"detail": "Evidence document not found"}), 404
    return jsonify(payload)


@app.route("/api/corporation-evidence-documents/<int:evidence_id>", methods=["PATCH"])
def update_corporation_evidence_document(evidence_id: int):
    payload = get_json_payload()
    with db_conn() as conn:
        evidence = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
        if not evidence:
            return jsonify({"detail": "Evidence document not found"}), 404

        update_values: dict[str, Any] = {}
        if "document_type" in payload:
            document_type = clean_text(payload.get("document_type"))
            if document_type:
                update_values["document_type"] = document_type
        if "memo" in payload:
            update_values["memo"] = clean_text(payload.get("memo"))
        if "review_status" in payload:
            review_status = clean_text(payload.get("review_status"))
            if review_status in {"pending", "approved", "rejected", "needs_review"}:
                update_values["review_status"] = review_status

        corporation_id = evidence["corporation_id"]
        if "corporation_id" in payload:
            corporation_id = parse_int(payload.get("corporation_id"), 0) or None
            if corporation_id:
                corp = conn.execute(
                    "SELECT id, management_group_name FROM corporations WHERE id=?",
                    (corporation_id,),
                ).fetchone()
                if not corp:
                    return jsonify({"detail": "Corporation not found"}), 404
                update_values["corporation_id"] = corporation_id
                update_values["management_group_name"] = normalize_management_group_name(corp["management_group_name"])
            else:
                update_values["corporation_id"] = None
                update_values["management_group_name"] = normalize_management_group_name(
                    payload.get("management_group_name") or evidence["management_group_name"]
                )
        elif "management_group_name" in payload and not corporation_id:
            update_values["management_group_name"] = normalize_management_group_name(payload.get("management_group_name"))

        if not update_values:
            return jsonify(evidence_detail(conn, evidence_id))

        now = now_iso()
        update_values["updated_at"] = now
        assignments = ", ".join(f"{field}=?" for field in update_values)
        conn.execute(
            f"UPDATE corporation_evidence_documents SET {assignments} WHERE id=?",
            tuple(update_values.values()) + (evidence_id,),
        )
        if "corporation_id" in update_values:
            conn.execute(
                """
                UPDATE corporation_profile_update_candidates
                SET corporation_id=?, updated_at=?
                WHERE evidence_document_id=? AND status='pending'
                """,
                (update_values["corporation_id"], now, evidence_id),
            )
        conn.commit()
        updated = evidence_detail(conn, evidence_id)
    return jsonify(updated)


@app.route("/api/corporation-evidence-documents/<int:evidence_id>/reprocess", methods=["POST"])
def reprocess_corporation_evidence_document(evidence_id: int):
    payload = get_json_payload()
    requested_document_type = clean_text(payload.get("document_type")) or "auto"

    with db_conn() as conn:
        evidence = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
        if not evidence:
            return jsonify({"detail": "Evidence document not found"}), 404

        stored_path_value = clean_text(evidence["stored_file_path"])
        if not stored_path_value:
            return jsonify({"detail": "Stored evidence file is missing"}), 409
        stored_path = Path(stored_path_value)
        if not stored_path.exists():
            return jsonify({"detail": "Stored evidence file is missing"}), 409

        processing = process_corporation_evidence_analysis(
            stored_path,
            evidence["original_file_name"],
            requested_document_type,
        )
        analysis = processing["analysis"]
        now = now_iso()
        extraction_payload = processing["extraction_payload"]
        conn.execute(
            """
            UPDATE corporation_evidence_documents
            SET document_type=?, classification_status=?, classification_confidence=?,
                extraction_status=?, ocr_status=?, review_status='pending',
                extracted_text=?, extracted_text_preview=?, extraction_json=?,
                error_message=?, updated_at=?
            WHERE id=?
            """,
            (
                analysis.document_type,
                analysis.classification_status,
                analysis.classification_confidence,
                processing["extraction_status"],
                processing["ocr_status"],
                processing["extracted_text"],
                processing["extracted_text"][:1200],
                json.dumps(
                    {
                        **analysis.to_dict(),
                        "pipeline": extraction_payload,
                        "reprocessed_at": now,
                    },
                    ensure_ascii=False,
                ),
                processing["error_message"],
                now,
                evidence_id,
            ),
        )
        conn.execute(
            "DELETE FROM corporation_profile_update_candidates WHERE evidence_document_id=? AND status='pending'",
            (evidence_id,),
        )
        approved_identities = approved_candidate_identity_set(conn, evidence_id)
        for candidate in analysis.candidates:
            if (candidate.field_key, clean_text(candidate.extracted_value)) in approved_identities:
                continue
            conn.execute(
                """
                INSERT INTO corporation_profile_update_candidates (
                  evidence_document_id, corporation_id, field_key, field_label,
                  extracted_value, confidence, source_text, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    evidence_id,
                    evidence["corporation_id"],
                    candidate.field_key,
                    candidate.field_label,
                    candidate.extracted_value,
                    candidate.confidence,
                    candidate.source_text,
                    now,
                    now,
                ),
            )
        conn.commit()
        updated = evidence_detail(conn, evidence_id)
    return jsonify(updated)


@app.route("/api/corporation-evidence-documents/<int:evidence_id>/reanalyze-text", methods=["POST"])
def reanalyze_corporation_evidence_text(evidence_id: int):
    payload = get_json_payload()
    corrected_text = clean_text(payload.get("extracted_text"))
    requested_document_type = clean_text(payload.get("document_type")) or "auto"
    if not corrected_text:
        return jsonify({"detail": "extracted_text is required"}), 400

    with db_conn() as conn:
        evidence = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
        if not evidence:
            return jsonify({"detail": "Evidence document not found"}), 404

        analysis = analyze_corporation_evidence_text(
            corrected_text,
            evidence["original_file_name"],
            requested_document_type,
        )
        now = now_iso()
        conn.execute(
            """
            UPDATE corporation_evidence_documents
            SET document_type=?, classification_status=?, classification_confidence=?,
                extraction_status='completed', ocr_status='corrected', review_status='pending',
                extracted_text=?, extracted_text_preview=?, extraction_json=?,
                error_message='', updated_at=?
            WHERE id=?
            """,
            (
                analysis.document_type,
                analysis.classification_status,
                analysis.classification_confidence,
                corrected_text,
                corrected_text[:1200],
                json.dumps(
                    {
                        **analysis.to_dict(),
                        "manual_text_correction": True,
                        "corrected_at": now,
                    },
                    ensure_ascii=False,
                ),
                now,
                evidence_id,
            ),
        )
        conn.execute(
            "DELETE FROM corporation_profile_update_candidates WHERE evidence_document_id=? AND status='pending'",
            (evidence_id,),
        )
        approved_identities = approved_candidate_identity_set(conn, evidence_id)
        for candidate in analysis.candidates:
            if (candidate.field_key, clean_text(candidate.extracted_value)) in approved_identities:
                continue
            conn.execute(
                """
                INSERT INTO corporation_profile_update_candidates (
                  evidence_document_id, corporation_id, field_key, field_label,
                  extracted_value, confidence, source_text, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    evidence_id,
                    evidence["corporation_id"],
                    candidate.field_key,
                    candidate.field_label,
                    candidate.extracted_value,
                    candidate.confidence,
                    candidate.source_text,
                    now,
                    now,
                ),
            )
        conn.commit()
        updated = evidence_detail(conn, evidence_id)
    return jsonify(updated)


@app.route("/api/corporation-evidence-documents/<int:evidence_id>/approve", methods=["POST"])
def approve_corporation_evidence_document(evidence_id: int):
    payload = get_json_payload()
    candidate_ids = payload.get("candidate_ids")
    field_values = payload.get("field_values") if isinstance(payload.get("field_values"), dict) else {}
    requested_status = clean_text(payload.get("review_status"), "approved") or "approved"

    with db_conn() as conn:
        evidence = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
        if not evidence:
            return jsonify({"detail": "Evidence document not found"}), 404

        params: list[Any] = [evidence_id]
        candidate_filter = ""
        if isinstance(candidate_ids, list):
            if not candidate_ids and not field_values:
                return jsonify({"detail": "No approved candidate fields to apply"}), 400
            if not candidate_ids:
                candidate_filter = " AND 1=0"
            else:
                placeholders = ",".join("?" for _ in candidate_ids)
                candidate_filter = f" AND id IN ({placeholders})"
                params.extend(parse_int(value) for value in candidate_ids)

        candidate_rows = conn.execute(
            f"""
            SELECT * FROM corporation_profile_update_candidates
            WHERE evidence_document_id=? AND status='pending'{candidate_filter}
            ORDER BY id
            """,
            tuple(params),
        ).fetchall()

        update_values: dict[str, str] = {}
        allowed_fields = corporation_allowed_update_fields() & allowed_profile_update_fields()
        for row in candidate_rows:
            field_key = row["field_key"]
            if field_key in allowed_fields and row["extracted_value"]:
                update_values[field_key] = normalize_profile_update_value(field_key, row["extracted_value"])

        for field_key, value in field_values.items():
            if field_key in allowed_fields:
                update_values[field_key] = normalize_profile_update_value(field_key, value)

        if not update_values:
            return jsonify({"detail": "No approved candidate fields to apply"}), 400

        update_values["evidence_verification_status"] = "evidence_reviewed"
        now = now_iso()
        corporation_id = evidence["corporation_id"]
        warnings: list[str] = []

        if corporation_id:
            corp = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
            if not corp:
                return jsonify({"detail": "Linked corporation not found"}), 404
            for field_key in JSON_LIST_PROFILE_FIELDS:
                if field_key in update_values:
                    update_values[field_key] = merge_json_list_values(corp[field_key], update_values[field_key])
            target_business_registration_number = update_values.get(
                "business_registration_number",
                corp["business_registration_number"],
            )
            target_management_group_name = update_values.get(
                "management_group_name",
                corp["management_group_name"],
            )
            duplicates = find_corporation_registration_duplicates(
                conn,
                target_business_registration_number,
                target_management_group_name,
                exclude_id=corporation_id,
            )
            if duplicates["same_group"]:
                return (
                    jsonify(
                        {
                            "detail": "같은 관리 법인그룹에 동일한 사업자등록번호 법인이 이미 존재합니다.",
                            "duplicate_corporations": duplicates["same_group"],
                        }
                    ),
                    409,
                )
            warnings.extend(duplicate_other_group_warnings(duplicates))
            update_payload = {**update_values, "updated_at": now}
            assignments = ", ".join(f"{field}=?" for field in update_payload)
            conn.execute(
                f"UPDATE corporations SET {assignments} WHERE id=?",
                tuple(update_payload.values()) + (corporation_id,),
            )
        else:
            name = update_values.get("name")
            if not name:
                return jsonify({"detail": "name candidate is required to create a corporation from evidence"}), 400
            management_group_name = normalize_management_group_name(
                update_values.get("management_group_name") or evidence["management_group_name"]
            )
            business_registration_number = normalize_business_registration_number(
                update_values.get("business_registration_number", "")
            )
            duplicates = find_corporation_registration_duplicates(
                conn,
                business_registration_number,
                management_group_name,
            )
            if duplicates["same_group"]:
                return (
                    jsonify(
                        {
                            "detail": "같은 관리 법인그룹에 동일한 사업자등록번호 법인이 이미 존재합니다.",
                            "duplicate_corporations": duplicates["same_group"],
                        }
                    ),
                    409,
                )
            warnings.extend(duplicate_other_group_warnings(duplicates))
            insert_fields = [
                "name",
                "management_group_name",
                "business_category",
                "region",
                "certifications_json",
                "company_size_classification",
                "internal_notes",
                "business_registration_number",
                "representative_name",
                "corporate_registration_number",
                "business_address",
                "headquarters_address",
                "opening_date",
                "business_type",
                "business_item",
                "preference_tags_json",
                "direct_production_items_json",
                "license_summary",
                "procurement_registration_status",
                "evidence_expiry_summary",
                "evidence_verification_status",
                "created_at",
                "updated_at",
            ]
            insert_values = {
                "name": update_values.get("name", ""),
                "management_group_name": management_group_name,
                "business_category": update_values.get("business_category", ""),
                "region": update_values.get("region", ""),
                "certifications_json": "[]",
                "company_size_classification": "",
                "internal_notes": "증빙자료 자동 추출로 생성",
                "business_registration_number": business_registration_number,
                "representative_name": update_values.get("representative_name", ""),
                "corporate_registration_number": update_values.get("corporate_registration_number", ""),
                "business_address": update_values.get("business_address", ""),
                "headquarters_address": update_values.get("headquarters_address", ""),
                "opening_date": update_values.get("opening_date", ""),
                "business_type": update_values.get("business_type", ""),
                "business_item": update_values.get("business_item", ""),
                "preference_tags_json": update_values.get("preference_tags_json", "[]"),
                "direct_production_items_json": update_values.get("direct_production_items_json", "[]"),
                "license_summary": update_values.get("license_summary", ""),
                "procurement_registration_status": update_values.get("procurement_registration_status", ""),
                "evidence_expiry_summary": update_values.get("evidence_expiry_summary", ""),
                "evidence_verification_status": "evidence_reviewed",
                "created_at": now,
                "updated_at": now,
            }
            if "certifications_json" in update_values:
                insert_values["certifications_json"] = update_values["certifications_json"]
            placeholders = ", ".join("?" for _ in insert_fields)
            cur = conn.execute(
                f"INSERT INTO corporations ({', '.join(insert_fields)}) VALUES ({placeholders})",
                tuple(insert_values[field] for field in insert_fields),
            )
            corporation_id = cur.lastrowid
            conn.execute(
                "UPDATE corporation_evidence_documents SET corporation_id=?, updated_at=? WHERE id=?",
                (corporation_id, now, evidence_id),
            )

        if candidate_rows:
            approved_ids = [row["id"] for row in candidate_rows]
            placeholders = ",".join("?" for _ in approved_ids)
            conn.execute(
                f"""
                UPDATE corporation_profile_update_candidates
                SET status='approved', corporation_id=?, applied_at=?, updated_at=?
                WHERE id IN ({placeholders})
                """,
                (corporation_id, now, now, *approved_ids),
            )

        conn.execute(
            """
            UPDATE corporation_evidence_documents
            SET corporation_id=?, review_status=?, updated_at=?
            WHERE id=?
            """,
            (corporation_id, requested_status, now, evidence_id),
        )
        conn.commit()
        corporation = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        evidence_payload = evidence_detail(conn, evidence_id)

    return jsonify(
        {
            "status": "applied",
            "corporation": dict(corporation),
            "evidence": evidence_payload,
            "applied_fields": sorted(update_values.keys()),
            "warnings": warnings,
        }
    )


@app.route("/api/corporation-evidence-documents/<int:evidence_id>", methods=["DELETE"])
def delete_corporation_evidence_document(evidence_id: int):
    with db_conn() as conn:
        evidence = conn.execute("SELECT * FROM corporation_evidence_documents WHERE id=?", (evidence_id,)).fetchone()
        if not evidence:
            return jsonify({"detail": "Evidence document not found"}), 404
        if evidence["stored_file_path"]:
            safe_unlink(Path(evidence["stored_file_path"]))
        conn.execute("DELETE FROM corporation_profile_update_candidates WHERE evidence_document_id=?", (evidence_id,))
        conn.execute("DELETE FROM corporation_evidence_documents WHERE id=?", (evidence_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/projects", methods=["GET"])
def list_projects():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/projects", methods=["POST"])
def create_project():
    payload = get_json_payload()
    now = now_iso()
    name = clean_text(payload.get("name"))
    corp_id = parse_int(payload.get("corporation_id"), 0)
    if not name:
        return jsonify({"detail": "name is required"}), 400

    with db_conn() as conn:
        corp = conn.execute("SELECT id FROM corporations WHERE id=?", (corp_id,)).fetchone()
        if not corp:
            return jsonify({"detail": "Invalid corporation_id"}), 400

        cur = conn.execute(
            "INSERT INTO projects (name, corporation_id, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                name,
                corp_id,
                clean_text(payload.get("status"), "active"),
                clean_text(payload.get("notes")),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Project not found"}), 404
    return jsonify(dict(row))


@app.route("/api/projects/<int:project_id>", methods=["PATCH"])
def update_project(project_id: int):
    payload = get_json_payload()
    updates = {}
    if "name" in payload:
        name = clean_text(payload.get("name"))
        if not name:
            return jsonify({"detail": "name is required"}), 400
        updates["name"] = name
    if "corporation_id" in payload:
        updates["corporation_id"] = parse_int(payload.get("corporation_id"), 0)
    if "status" in payload:
        updates["status"] = clean_text(payload.get("status"), "active")
    if "notes" in payload:
        updates["notes"] = clean_text(payload.get("notes"))
    if not updates:
        return jsonify({"detail": "No supported fields to update"}), 400

    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{field}=?" for field in updates)
    values = tuple(updates.values()) + (project_id,)

    with db_conn() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Project not found"}), 404
        if "corporation_id" in updates:
            corp = conn.execute("SELECT id FROM corporations WHERE id=?", (updates["corporation_id"],)).fetchone()
            if not corp:
                return jsonify({"detail": "Invalid corporation_id"}), 400
        conn.execute(f"UPDATE projects SET {assignments} WHERE id=?", values)
        conn.commit()
        updated = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return jsonify(dict(updated))


@app.route("/api/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    with db_conn() as conn:
        project = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            return jsonify({"detail": "Project not found"}), 404

        docs = conn.execute("SELECT * FROM project_documents WHERE project_id=?", (project_id,)).fetchall()
        doc_ids = [doc["id"] for doc in docs]
        for doc in docs:
            safe_unlink(Path(doc["stored_file_path"]))

        if doc_ids:
            placeholders = ",".join("?" for _ in doc_ids)
            conn.execute(f"DELETE FROM analyses WHERE project_document_id IN ({placeholders})", tuple(doc_ids))
            conn.execute(f"DELETE FROM project_documents WHERE id IN ({placeholders})", tuple(doc_ids))
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/documents", methods=["GET"])
def list_documents():
    project_id = request.args.get("project_id")
    with db_conn() as conn:
        if project_id:
            rows = conn.execute("SELECT * FROM project_documents WHERE project_id=? ORDER BY id DESC", (project_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM project_documents ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/documents", methods=["POST"])
def upload_document():
    project_id = parse_int(request.form.get("project_id"), 0)
    document_type = clean_text(request.form.get("document_type"), "general")
    memo = clean_text(request.form.get("memo"))
    revision_note = clean_text(request.form.get("revision_note"))
    file = request.files.get("file")

    if not file or not file.filename:
        return jsonify({"detail": "file is required"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"detail": "Only PDF and DOCX are supported"}), 400

    with db_conn() as conn:
        project = conn.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            return jsonify({"detail": "Invalid project_id"}), 400

        target_dir = STORAGE_ROOT / "uploads" / str(project_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = target_dir / stored_name
        file.save(stored_path)
        file_size = stored_path.stat().st_size

        now = now_iso()
        cur = conn.execute(
            """
            INSERT INTO project_documents (
              project_id, document_type, original_file_name, stored_file_path, mime_type,
              file_size, memo, revision_note, parsing_status, ocr_status, analysis_status,
              latest_analysis_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'pending', 'pending', NULL, ?, ?)
            """,
            (
                project_id,
                document_type,
                file.filename,
                str(stored_path),
                file.mimetype or "",
                file_size,
                memo,
                revision_note,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/documents/<int:document_id>", methods=["GET"])
def get_document(document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Document not found"}), 404
    return jsonify(dict(row))


@app.route("/api/documents/<int:document_id>", methods=["PATCH"])
def update_document(document_id: int):
    payload = get_json_payload()
    allowed_fields = {
        "document_type": clean_text,
        "memo": clean_text,
        "revision_note": clean_text,
    }
    updates = {field: converter(payload[field]) for field, converter in allowed_fields.items() if field in payload}
    if not updates:
        return jsonify({"detail": "No supported fields to update"}), 400

    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{field}=?" for field in updates)
    values = tuple(updates.values()) + (document_id,)

    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Document not found"}), 404
        conn.execute(f"UPDATE project_documents SET {assignments} WHERE id=?", values)
        conn.commit()
        updated = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
    return jsonify(dict(updated))


@app.route("/api/documents/<int:document_id>", methods=["DELETE"])
def delete_document(document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Document not found"}), 404

        safe_unlink(Path(row["stored_file_path"]))
        conn.execute("DELETE FROM analyses WHERE project_document_id=?", (document_id,))
        conn.execute("DELETE FROM project_documents WHERE id=?", (document_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/documents/<int:document_id>/analyze", methods=["POST"])
def analyze_document(document_id: int):
    selection = resolve_ai_model_selection_from_payload(get_json_payload())
    payload, code = run_analysis(
        document_id,
        force=False,
        ai_provider=selection["provider"],
        ai_model=selection["model"],
    )
    return jsonify(payload), code


@app.route("/api/documents/<int:document_id>/reanalyze", methods=["POST"])
def reanalyze_document(document_id: int):
    selection = resolve_ai_model_selection_from_payload(get_json_payload())
    payload, code = run_analysis(
        document_id,
        force=True,
        ai_provider=selection["provider"],
        ai_model=selection["model"],
    )
    return jsonify(payload), code


@app.route("/api/analyses/<int:analysis_id>", methods=["GET"])
def get_analysis(analysis_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Analysis not found"}), 404
    return jsonify(dict(row))


@app.route("/api/analyses/latest/by-document/<int:document_id>", methods=["GET"])
def latest_analysis(document_id: int):
    with db_conn() as conn:
        doc = conn.execute("SELECT latest_analysis_id FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not doc or not doc["latest_analysis_id"]:
            return jsonify({"detail": "Latest analysis not found"}), 404

        row = conn.execute("SELECT * FROM analyses WHERE id=?", (doc["latest_analysis_id"],)).fetchone()
    if not row:
        return jsonify({"detail": "Analysis not found"}), 404
    return jsonify(dict(row))


@app.route("/api/documents/<int:document_id>/latest-analysis", methods=["GET"])
def latest_analysis_alias(document_id: int):
    return latest_analysis(document_id)


@app.route("/api/nara/notices/search", methods=["GET"])
def search_nara_notices():
    if not NARA_API_SERVICE_KEY:
        return jsonify({"detail": "NARA_API_SERVICE_KEY is missing"}), 400

    end_default = datetime.now(KST).date()
    start_default = end_default - timedelta(days=3)
    start_date = request.args.get("start_date") or start_default.isoformat()
    end_date = request.args.get("end_date") or end_default.isoformat()
    page_no = str(max(parse_int(request.args.get("page_no"), 1), 1))
    page_size = str(min(max(parse_int(request.args.get("page_size"), 20), 1), 100))
    keyword = clean_text(request.args.get("keyword"))

    params = {
        "ServiceKey": NARA_API_SERVICE_KEY,
        "numOfRows": page_size,
        "pageNo": page_no,
        "type": NARA_API_RESPONSE_TYPE,
        "inqryDiv": "1",
        "inqryBgnDt": date_to_api_datetime(start_date, "0000"),
        "inqryEndDt": date_to_api_datetime(end_date, "2359"),
    }
    if keyword:
        params["bidNtceNm"] = keyword

    try:
        parsed = request_nara_operation("getBidPblancListInfoCnstwkPPSSrch", params)
    except Exception as exc:
        return jsonify({"detail": f"Nara API request failed: {exc}"}), 502

    notices = []
    for item in parsed.get("items", []):
        attachments = collect_nara_attachments([item])
        normalized = normalize_nara_notice(item, attachments)
        notices.append({**normalized, "attachments": attachments})

    return jsonify(
        {
            "items": notices,
            "total_count": parsed.get("total_count", len(notices)),
            "page_no": parse_int(page_no, 1),
            "page_size": parse_int(page_size, 20),
            "result_code": (parsed.get("header") or {}).get("resultCode", ""),
            "result_msg": (parsed.get("header") or {}).get("resultMsg", ""),
            "http_status": parsed.get("http_status"),
            "queried_at": now_iso(),
        }
    )


def get_nara_notice_with_attachments(conn: sqlite3.Connection, notice_id: int) -> dict | None:
    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    if not notice:
        return None
    attachments = conn.execute(
        "SELECT * FROM nara_notice_attachments WHERE nara_notice_id=? ORDER BY id",
        (notice_id,),
    ).fetchall()
    payload = dict(notice)
    payload["attachments"] = rows_to_dict(attachments)
    return payload


def latest_integration_test_result(conn: sqlite3.Connection, integration_name: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT * FROM integration_test_results
        WHERE integration_name=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (integration_name,),
    ).fetchone()


def save_integration_test_result(
    integration_name: str,
    status: str,
    http_status: int | None,
    result_code: str,
    result_msg: str,
    total_count: int,
    detail: str = "",
) -> None:
    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO integration_test_results (
              integration_name, status, http_status, result_code, result_msg,
              total_count, detail, tested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (integration_name, status, http_status, result_code, result_msg, total_count, detail, now_iso()),
        )
        conn.commit()


def clear_nara_notice_attachments(conn: sqlite3.Connection, notice_id: int) -> None:
    rows = conn.execute(
        "SELECT stored_file_path FROM nara_notice_attachments WHERE nara_notice_id=?",
        (notice_id,),
    ).fetchall()
    for row in rows:
        if row["stored_file_path"]:
            safe_unlink(Path(row["stored_file_path"]))
    conn.execute("DELETE FROM nara_notice_attachments WHERE nara_notice_id=?", (notice_id,))


def create_nara_notice_processing_placeholder(base_item: dict) -> tuple[dict, int]:
    if not isinstance(base_item, dict):
        return {"detail": "notice must be an object"}, 400

    bid_no = item_first(base_item, ["bidNtceNo", "bid_ntce_no"])
    bid_ord = item_first(base_item, ["bidNtceOrd", "bid_ntce_ord"]) or "000"
    if not bid_no:
        return {"detail": "bidNtceNo is required"}, 400

    normalized = normalize_nara_notice(base_item, collect_nara_attachments([base_item]))
    now = now_iso()

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM nara_notices WHERE bid_ntce_no=? AND bid_ntce_ord=?",
            (normalized["bid_ntce_no"], normalized["bid_ntce_ord"]),
        ).fetchone()

        values = (
            normalized["bid_ntce_nm"],
            normalized["ntce_instt_nm"],
            normalized["dminstt_nm"],
            normalized["bid_ntce_dt"],
            normalized["bid_begin_dt"],
            normalized["bid_clse_dt"],
            normalized["openg_dt"],
            normalized["presmpt_prce"],
            normalized["bdgt_amt"],
            normalized["bssamt"],
            normalized["region_text"],
            normalized["license_text"],
            normalized["source_url"],
            json.dumps(base_item, ensure_ascii=False),
            "{}",
            "saving",
            "pending",
            "pending",
            "{}",
            "",
            "",
            now,
        )

        if existing:
            notice_id = existing["id"]
            clear_nara_notice_attachments(conn, notice_id)
            conn.execute(
                """
                UPDATE nara_notices SET
                  bid_ntce_nm=?, ntce_instt_nm=?, dminstt_nm=?, bid_ntce_dt=?,
                  bid_begin_dt=?, bid_clse_dt=?, openg_dt=?, presmpt_prce=?,
                  bdgt_amt=?, bssamt=?, region_text=?, license_text=?, source_url=?,
                  raw_json=?, detail_json=?, save_status=?, download_status=?,
                  analysis_status=?, analysis_summary_json=?, analysis_summary_markdown=?,
                  error_message=?, updated_at=?
                WHERE id=?
                """,
                values + (notice_id,),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO nara_notices (
                  bid_ntce_no, bid_ntce_ord, bid_ntce_nm, ntce_instt_nm, dminstt_nm,
                  bid_ntce_dt, bid_begin_dt, bid_clse_dt, openg_dt, presmpt_prce,
                  bdgt_amt, bssamt, region_text, license_text, source_url, raw_json,
                  detail_json, save_status, download_status, analysis_status,
                  analysis_summary_json, analysis_summary_markdown, error_message,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["bid_ntce_no"],
                    normalized["bid_ntce_ord"],
                    *values,
                    now,
                ),
            )
            notice_id = cur.lastrowid

        result = get_nara_notice_with_attachments(conn, notice_id)

    return {"status": "queued", "notice": result}, 202


def mark_nara_notice_job_failed(notice_id: int, exc: Exception) -> None:
    with db_conn() as conn:
        conn.execute(
            """
            UPDATE nara_notices SET
              save_status=?, download_status=?, analysis_status=?,
              error_message=?, updated_at=?
            WHERE id=?
            """,
            ("failed", "failed", "failed", str(exc), now_iso(), notice_id),
        )


def run_nara_notice_analysis_job(
    notice_id: int,
    base_item: dict,
    ai_provider: str | None = None,
    ai_model: str | None = None,
) -> None:
    try:
        save_and_analyze_nara_notice_item(base_item, ai_provider=ai_provider, ai_model=ai_model)
    except Exception as exc:
        mark_nara_notice_job_failed(notice_id, exc)


def enqueue_nara_notice_analysis(
    base_item: dict,
    ai_provider: str | None = None,
    ai_model: str | None = None,
) -> tuple[dict, int]:
    result, code = create_nara_notice_processing_placeholder(base_item)
    if code >= 400:
        return result, code

    notice_id = result["notice"]["id"]
    NARA_NOTICE_EXECUTOR.submit(run_nara_notice_analysis_job, notice_id, base_item, ai_provider, ai_model)
    return result, code


def save_and_analyze_nara_notice_item(
    base_item: dict,
    ai_provider: str | None = None,
    ai_model: str | None = None,
) -> tuple[dict, int]:
    if not isinstance(base_item, dict):
        return {"detail": "notice must be an object"}, 400

    bid_no = item_first(base_item, ["bidNtceNo", "bid_ntce_no"])
    bid_ord = item_first(base_item, ["bidNtceOrd", "bid_ntce_ord"]) or "000"
    if not bid_no:
        return {"detail": "bidNtceNo is required"}, 400

    detail_bundle = fetch_nara_detail_bundle(bid_no, bid_ord)
    detail_items = detail_bundle.get("items", [])
    merged_item = merge_notice_items(base_item, detail_items)
    attachments = collect_nara_attachments([merged_item, *detail_items])
    normalized = normalize_nara_notice(merged_item, attachments)
    now = now_iso()

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM nara_notices WHERE bid_ntce_no=? AND bid_ntce_ord=?",
            (normalized["bid_ntce_no"], normalized["bid_ntce_ord"]),
        ).fetchone()

        values = (
            normalized["bid_ntce_nm"],
            normalized["ntce_instt_nm"],
            normalized["dminstt_nm"],
            normalized["bid_ntce_dt"],
            normalized["bid_begin_dt"],
            normalized["bid_clse_dt"],
            normalized["openg_dt"],
            normalized["presmpt_prce"],
            normalized["bdgt_amt"],
            normalized["bssamt"],
            normalized["region_text"],
            normalized["license_text"],
            normalized["source_url"],
            json.dumps(merged_item, ensure_ascii=False),
            json.dumps(detail_bundle, ensure_ascii=False),
            "saving",
            "pending",
            "pending",
            "",
            now,
        )

        if existing:
            notice_id = existing["id"]
            clear_nara_notice_attachments(conn, notice_id)
            conn.execute(
                """
                UPDATE nara_notices SET
                  bid_ntce_nm=?, ntce_instt_nm=?, dminstt_nm=?, bid_ntce_dt=?,
                  bid_begin_dt=?, bid_clse_dt=?, openg_dt=?, presmpt_prce=?,
                  bdgt_amt=?, bssamt=?, region_text=?, license_text=?, source_url=?,
                  raw_json=?, detail_json=?, save_status=?, download_status=?,
                  analysis_status=?, error_message=?, updated_at=?
                WHERE id=?
                """,
                values + (notice_id,),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO nara_notices (
                  bid_ntce_no, bid_ntce_ord, bid_ntce_nm, ntce_instt_nm, dminstt_nm,
                  bid_ntce_dt, bid_begin_dt, bid_clse_dt, openg_dt, presmpt_prce,
                  bdgt_amt, bssamt, region_text, license_text, source_url, raw_json,
                  detail_json, save_status, download_status, analysis_status,
                  error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["bid_ntce_no"],
                    normalized["bid_ntce_ord"],
                    *values,
                    now,
                ),
            )
            notice_id = cur.lastrowid

        conn.commit()

        notice_dir = STORAGE_ROOT / "nara-notices" / str(notice_id)
        notice_dir.mkdir(parents=True, exist_ok=True)
        attachment_texts: list[str] = []
        supported_count = 0
        failed_count = 0

        for attachment in attachments:
            support_status = attachment["support_status"]
            download_status = "skipped" if support_status != "supported" else "pending"
            parse_status = "skipped" if support_status != "supported" else "pending"
            error_message = "" if support_status == "supported" else "지원 제외 확장자"
            stored_file_path = ""
            file_size = 0
            preview = ""

            if support_status == "supported":
                supported_count += 1
                try:
                    http_status, headers, body = request_binary(attachment["source_url"])
                    content_type = headers.get("content-type", "")
                    suffix = attachment["file_extension"] or attachment_extension(
                        attachment["file_name"],
                        attachment["source_url"],
                        content_type,
                    )
                    if suffix not in NARA_SUPPORTED_EXTENSIONS:
                        raise ValueError(f"unsupported downloaded file extension: {suffix or 'unknown'}")
                    if suffix == ".pdf" and not body.startswith(b"%PDF"):
                        raise ValueError("downloaded file is not a valid PDF")
                    if suffix == ".docx" and not body.startswith(b"PK\x03\x04"):
                        raise ValueError("downloaded file is not a valid DOCX")
                    if http_status != 200:
                        raise ValueError(f"download failed with HTTP {http_status}")

                    stored_path = notice_dir / f"{uuid.uuid4().hex}{suffix}"
                    stored_path.write_bytes(body)
                    stored_file_path = str(stored_path)
                    file_size = len(body)
                    download_status = "completed"

                    parsed = extract_document(stored_path)
                    ocr_result = run_ocr_if_needed(parsed.text, stored_path, parsed.kind, parsed.metadata)
                    extracted_text = ocr_result.text or parsed.text
                    parse_status = "completed"
                    preview = extracted_text[:1000]
                    if extracted_text:
                        attachment_texts.append(extracted_text)
                except Exception as exc:
                    failed_count += 1
                    download_status = "failed"
                    parse_status = "failed"
                    error_message = str(exc)

            conn.execute(
                """
                INSERT INTO nara_notice_attachments (
                  nara_notice_id, file_name, source_url, source_field, file_extension,
                  support_status, download_status, stored_file_path, file_size,
                  parse_status, analysis_status, extracted_text_preview, error_message,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    notice_id,
                    attachment["file_name"],
                    attachment["source_url"],
                    attachment["source_field"],
                    attachment["file_extension"],
                    support_status,
                    download_status,
                    stored_file_path,
                    file_size,
                    parse_status,
                    "completed" if parse_status == "completed" else parse_status,
                    preview,
                    error_message,
                    now_iso(),
                    now_iso(),
                ),
            )

        notice_text = build_nara_summary_text(normalized, attachment_texts)
        notice_requirements = extract_notice_requirements(normalized, notice_text)
        selection = resolve_ai_model_selection(ai_provider, ai_model)
        try:
            summary_json, summary_markdown, _usage = summarize_with_ai(notice_text, selection)
        except Exception as exc:
            summary_json, summary_markdown, _usage = summarize_with_fallback(
                notice_text,
                selection["provider"],
                selection["model"],
            )
            _usage["fallback_reason"] = str(exc)
        summary_json["notice_requirements"] = notice_requirements
        summary_markdown = f"{summary_markdown}\n{render_notice_requirements_markdown(notice_requirements)}"

        if supported_count == 0:
            download_status = "no_supported_attachments"
        elif failed_count:
            download_status = "partial_failed"
        else:
            download_status = "completed"

        analysis_status = "completed" if failed_count == 0 else "partial_failed"
        conn.execute(
            """
            UPDATE nara_notices SET
              save_status=?, download_status=?, analysis_status=?,
              analysis_summary_json=?, analysis_summary_markdown=?, updated_at=?
            WHERE id=?
            """,
            (
                "saved",
                download_status,
                analysis_status,
                json.dumps(summary_json, ensure_ascii=False),
                summary_markdown,
                now_iso(),
                notice_id,
            ),
        )
        conn.commit()

        result = get_nara_notice_with_attachments(conn, notice_id)

    return {"status": analysis_status, "notice": result}, 200


@app.route("/api/nara/notices/save-and-analyze", methods=["POST"])
def save_and_analyze_nara_notice():
    payload = get_json_payload()
    notice_item = payload.get("notice") or payload.get("raw")
    selection = resolve_ai_model_selection_from_payload(payload)
    result, code = enqueue_nara_notice_analysis(
        notice_item,
        ai_provider=selection["provider"],
        ai_model=selection["model"],
    )
    return jsonify(result), code


@app.route("/api/nara/saved-notices", methods=["GET"])
def list_saved_nara_notices():
    keyword = clean_text(request.args.get("keyword")).lower()
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM nara_notices ORDER BY id DESC").fetchall()
    notices = rows_to_dict(rows)
    if keyword:
        notices = [
            row
            for row in notices
            if keyword
            in " ".join(
                [
                    row.get("bid_ntce_nm", ""),
                    row.get("ntce_instt_nm", ""),
                    row.get("dminstt_nm", ""),
                    row.get("bid_ntce_no", ""),
                ]
            ).lower()
        ]
    return jsonify(notices)


@app.route("/api/nara/saved-notices/<int:notice_id>", methods=["GET"])
def get_saved_nara_notice(notice_id: int):
    with db_conn() as conn:
        result = get_nara_notice_with_attachments(conn, notice_id)
    if not result:
        return jsonify({"detail": "Saved notice not found"}), 404
    return jsonify(result)


@app.route("/api/nara/saved-notices/<int:notice_id>/reanalyze", methods=["POST"])
def reanalyze_saved_nara_notice(notice_id: int):
    payload = get_json_payload()
    selection = resolve_ai_model_selection_from_payload(payload)
    with db_conn() as conn:
        row = conn.execute("SELECT raw_json FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Saved notice not found"}), 404
    result, code = enqueue_nara_notice_analysis(
        json.loads(row["raw_json"]),
        ai_provider=selection["provider"],
        ai_model=selection["model"],
    )
    return jsonify(result), code


@app.route("/api/nara/saved-notices/<int:notice_id>", methods=["DELETE"])
def delete_saved_nara_notice(notice_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Saved notice not found"}), 404
        clear_nara_notice_attachments(conn, notice_id)
        conn.execute("DELETE FROM nara_notices WHERE id=?", (notice_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/nara/attachments/preview", methods=["GET"])
def preview_nara_attachment():
    url = clean_text(request.args.get("url"))
    file_name = clean_text(request.args.get("name")) or Path(urllib.parse.urlparse(url).path).name or "attachment"
    if not url:
        return jsonify({"detail": "url is required"}), 400
    if not is_safe_external_url(url):
        return jsonify({"detail": "Only external HTTP/HTTPS attachment URLs are allowed"}), 400

    try:
        http_status, headers, body = request_binary(url)
    except Exception as exc:
        return jsonify({"detail": f"Attachment preview failed: {exc}"}), 502

    if http_status != 200:
        return jsonify({"detail": f"Attachment download failed with HTTP {http_status}"}), 502

    content_type = inline_content_type(file_name, url, headers.get("content-type", ""), body)
    safe_file_name = file_name.replace("\r", "").replace("\n", "")
    encoded_file_name = urllib.parse.quote(safe_file_name)
    response = Response(body, content_type=content_type)
    response.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{encoded_file_name}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/api/settings/ai-models", methods=["GET"])
def ai_model_settings():
    default_selection = resolve_ai_model_selection(AI_PROVIDER_DEFAULT, AI_MODEL_DEFAULT)
    return jsonify(
        {
            "default_provider": default_selection["provider"],
            "default_model": default_selection["model"],
            "providers": {
                "gemini": {
                    "configured": bool(GEMINI_API_KEY),
                    "masked_key": mask_secret(GEMINI_API_KEY),
                    "default_model": GEMINI_MODEL_PRIMARY,
                },
                "openai": {
                    "configured": bool(OPENAI_API_KEY),
                    "masked_key": mask_secret(OPENAI_API_KEY),
                    "default_model": OPENAI_MODEL_PRIMARY,
                    "secondary_model": OPENAI_MODEL_SECONDARY,
                },
            },
            "options": ai_model_options(),
        }
    )


@app.route("/api/settings/integrations/nara/status", methods=["GET"])
def nara_integration_status():
    with db_conn() as conn:
        latest = latest_integration_test_result(conn, "nara")

    return jsonify(
        {
            "configured": bool(NARA_API_SERVICE_KEY),
            "masked_key": mask_secret(NARA_API_SERVICE_KEY),
            "bid_public_base_url": NARA_BID_PUBLIC_API_BASE_URL,
            "pubdata_base_url": NARA_PUBDATA_API_BASE_URL,
            "response_type": NARA_API_RESPONSE_TYPE,
            "last_tested_at": latest["tested_at"] if latest else None,
            "last_test_status": latest["status"] if latest else "not_run",
            "last_test_http_status": latest["http_status"] if latest else None,
            "last_test_result_code": latest["result_code"] if latest else "",
            "last_test_result_msg": latest["result_msg"] if latest else "",
            "last_test_total_count": latest["total_count"] if latest else 0,
            "last_test_detail": latest["detail"] if latest else "",
        }
    )


@app.route("/api/settings/integrations/nara/test", methods=["POST"])
def test_nara_integration():
    if not NARA_API_SERVICE_KEY:
        return jsonify({"status": "not_configured", "detail": "NARA_API_SERVICE_KEY is missing"}), 400

    now = datetime.now(KST)
    begin = now - timedelta(days=30)
    params = {
        "ServiceKey": NARA_API_SERVICE_KEY,
        "numOfRows": "1",
        "pageNo": "1",
        "type": NARA_API_RESPONSE_TYPE,
        "inqryDiv": "1",
        "inqryBgnDt": begin.strftime("%Y%m%d0000"),
        "inqryEndDt": now.strftime("%Y%m%d2359"),
    }
    url = (
        NARA_BID_PUBLIC_API_BASE_URL.rstrip("/")
        + "/getBidPblancListInfoCnstwkPPSSrch?"
        + urllib.parse.urlencode(params, safe="%")
    )

    try:
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json, application/xml;q=0.9, */*;q=0.8",
                "User-Agent": "SMART-Procurement-Calculator/local-settings-test",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            body = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            http_status = response.status
    except Exception as exc:
        save_integration_test_result("nara", "error", None, "", "", 0, str(exc))
        return (
            jsonify(
                {
                    "status": "error",
                    "http_status": None,
                    "result_code": "",
                    "result_msg": "",
                    "total_count": 0,
                    "tested_at": now_iso(),
                    "detail": str(exc),
                }
            ),
            502,
        )

    try:
        parsed = parse_public_data_text(body)
        header = parsed.get("header") or {}
        result_code = str(header.get("resultCode", ""))
        result_msg = str(header.get("resultMsg", ""))
        total_count = parse_int(parsed.get("total_count"), 0)
    except Exception as exc:
        result_code, result_msg, total_count = "", f"Response parse failed: {exc}", 0

    status = "ok" if http_status == 200 and result_code == "00" else "error"
    save_integration_test_result("nara", status, http_status, result_code, result_msg, total_count)
    return jsonify(
        {
            "status": status,
            "http_status": http_status,
            "result_code": result_code,
            "result_msg": result_msg,
            "total_count": total_count,
            "tested_at": now_iso(),
        }
    )


init_db()


if __name__ == "__main__":
    app_port = int(os.getenv("APP_PORT", "18000"))
    app.run(host="127.0.0.1", port=app_port, debug=False)
