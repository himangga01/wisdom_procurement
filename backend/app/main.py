import hashlib
import json
import mimetypes
import os
import re
import sqlite3
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from app.core.citations import expected_basis_citation_candidate_id
from app.core.json_utils import parse_json_dict, parse_json_list
from app.core.text import clean_text, parse_int
from app.pipelines.corporation_evidence import (
    FIELD_LABELS,
    EvidenceExtractionResult,
    EvidenceFieldCandidate,
    allowed_profile_update_fields,
    analyze_corporation_evidence,
    evidence_storage_subdir,
    normalize_business_kind_values,
)
from app.pipelines.ocr import run_ocr, run_ocr_if_needed
from app.pipelines.basis_document import (
    BASIS_CITATION_MIN_SCORE,
    BASIS_INDEX_DIR,
    BasisIndexError,
    basis_chunk_payload,
    basis_document_payload,
    basis_index_status_payload,
    basis_search_results,
    delete_basis_vectors,
    process_basis_document,
    rebuild_basis_index,
    validate_basis_index,
)
from app.pipelines.parser import extract_document
from app.services.basis_rule_candidates import (
    basis_rule_candidate_match_score,
    merge_citation_results,
    prepare_basis_rule_candidate_update,
)
from app.services.backups import (
    create_backup_run,
    get_backup_run_payload,
    list_backup_runs_payload,
    restore_plan_for_backup,
    validate_backup_file,
)
from app.services.nara_api import (
    attachment_extension,
    build_nara_summary_text,
    build_nara_url,
    collect_nara_attachments,
    date_to_api_datetime,
    decode_http_body,
    inline_content_type,
    is_safe_external_url,
    item_first,
    merge_notice_items,
    normalize_nara_notice,
    parse_nara_response,
    parse_public_data_text,
    request_binary,
    request_text,
)
from app.services.operations import build_operations_summary
from app.services.operations import (
    error_code_for_status,
    get_operation_run_payload,
    list_operation_runs_payload,
    record_operation_run,
)

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
BASIS_ALLOWED_EXTENSIONS = {".pdf"}
EVIDENCE_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
EVIDENCE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
UNSUPPORTED_NARA_EXTENSIONS = {".hwp", ".hwpx", ".xlsx", ".xls", ".zip"}
NARA_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
DEFAULT_MANAGEMENT_GROUP_NAME = "기본 관리그룹"
KST = timezone(timedelta(hours=9))

REQUIREMENT_TYPE_LABELS = {
    "region": "지역 제한",
    "license": "면허/업종",
    "company_type": "기업유형",
    "required_document": "제출/증빙서류",
    "money": "금액 조건",
    "date": "일정 조건",
    "requirement_line": "원문 요구조건",
}

COMPARISON_STATUS_LABELS = {
    "prepared": "준비된 항목",
    "possibly_missing": "부족 가능성",
    "needs_review": "확인 필요",
    "not_found": "법인 정보 없음",
}

JUDGMENT_STATUS_LABELS = {
    "matched": "준비 확인",
    "missing": "부족 조건",
    "uncertain": "불확실",
    "needs_review": "확인 필요",
    "not_applicable": "해당 없음",
}

PHASE3_CONTRACT_VERSION = "phase3_gap_judgment_contract_v1"

EVIDENCE_DOCUMENT_LABELS = {
    "business_registration_certificate": "사업자등록증",
    "business_registration_proof": "사업자등록증명",
    "small_business_confirmation": "중소기업확인서",
    "women_owned_business_confirmation": "여성기업확인서",
    "disabled_owned_business_confirmation": "장애인기업확인서",
    "direct_production_confirmation": "직접생산확인증명서",
    "procurement_registration_certificate": "나라장터 경쟁입찰참가자격 등록증",
    "license_registration_certificate": "면허/등록/허가증",
    "tax_payment_certificate": "국세 납세증명서",
    "local_tax_payment_certificate": "지방세 납세증명서",
    "insurance_payment_certificate": "4대보험 완납증명서",
    "credit_rating_certificate": "기업신용평가등급확인서",
    "performance_certificate": "실적증명서",
    "financial_statement_certificate": "재무/매출 증빙",
}

REGION_ALIAS_GROUPS = {
    "서울": ["서울", "서울특별시"],
    "부산": ["부산", "부산광역시"],
    "대구": ["대구", "대구광역시"],
    "인천": ["인천", "인천광역시"],
    "광주": ["광주", "광주광역시"],
    "대전": ["대전", "대전광역시"],
    "울산": ["울산", "울산광역시"],
    "세종": ["세종", "세종특별자치시"],
    "경기": ["경기", "경기도"],
    "강원": ["강원", "강원도", "강원특별자치도"],
    "충북": ["충북", "충청북도"],
    "충남": ["충남", "충청남도"],
    "전북": ["전북", "전라북도", "전북특별자치도"],
    "전남": ["전남", "전라남도"],
    "경북": ["경북", "경상북도"],
    "경남": ["경남", "경상남도"],
    "제주": ["제주", "제주도", "제주특별자치도"],
}

LICENSE_TOKEN_GROUPS = {
    "건설업": ["건설업"],
    "조경식재": ["조경식재", "조경식재공사업", "조경식재·시설물공사업", "조경식재시설물공사업"],
    "조경시설물": ["조경시설물", "조경시설물설치공사업", "조경식재·시설물공사업", "조경식재시설물공사업"],
    "산림사업법인": ["산림사업법인", "산림사업"],
    "전기공사업": ["전기공사업", "전기공사"],
    "정보통신공사업": ["정보통신공사업", "정보통신공사"],
    "소방시설공사업": ["소방시설공사업", "전문소방시설공사업", "일반소방시설공사업"],
    "폐기물처리": ["폐기물처리", "폐기물처리업"],
    "엔지니어링사업자": ["엔지니어링사업자", "엔지니어링활동주체"],
    "소프트웨어사업자": ["소프트웨어사업자", "소프트웨어사업"],
    "직접생산확인": ["직접생산확인", "직접생산확인증명서"],
}

COMPANY_TYPE_TOKEN_GROUPS = {
    "중소기업": ["중소기업", "중소기업자"],
    "소기업": ["소기업"],
    "소상공인": ["소상공인"],
    "여성기업": ["여성기업"],
    "장애인기업": ["장애인기업"],
    "사회적기업": ["사회적기업"],
    "창업기업": ["창업기업"],
    "벤처기업": ["벤처기업"],
}

DOCUMENT_TOKEN_GROUPS = {
    "사업자등록증": ["사업자등록증", "사업자 등록증"],
    "법인등기부등본": ["법인등기부등본", "법인 등기부 등본", "등기사항전부증명서"],
    "인감증명서": ["인감증명서", "법인인감증명서"],
    "사용인감계": ["사용인감계"],
    "국세 납세증명서": ["국세 납세증명서", "국세납세증명서"],
    "지방세 납세증명서": ["지방세 납세증명서", "지방세납세증명서"],
    "4대보험 완납증명서": ["4대보험 완납증명서", "4대 보험 완납증명서", "보험료 완납증명서"],
    "중소기업확인서": ["중소기업확인서", "중소기업 확인서"],
    "직접생산확인증명서": ["직접생산확인증명서", "직접생산 확인증명서", "직접생산확인"],
    "나라장터 경쟁입찰참가자격 등록증": ["경쟁입찰참가자격 등록증", "입찰참가자격 등록증", "나라장터 등록증"],
    "기업신용평가등급확인서": ["기업신용평가등급확인서", "신용평가등급확인서", "신용평가등급"],
    "실적증명서": ["실적증명서", "수행실적증명서"],
    "입찰보증서": ["입찰보증서", "입찰보증금"],
    "청렴계약이행서약서": ["청렴계약이행서약서", "청렴계약 이행서약서"],
}

COMPARISON_AFFECTING_CORPORATION_FIELDS = {
    "name",
    "management_group_name",
    "business_category",
    "region",
    "certifications_json",
    "company_size_classification",
    "business_registration_number",
    "business_address",
    "headquarters_address",
    "business_type",
    "business_item",
    "preference_tags_json",
    "direct_production_items_json",
    "license_summary",
    "procurement_registration_status",
    "evidence_verification_status",
}

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["JSON_AS_ASCII"] = False
CORS(app)


@app.after_request
def ensure_utf8_json_response(response: Response) -> Response:
    if response.mimetype == "application/json" and "charset=" not in response.content_type.lower():
        response.content_type = "application/json; charset=utf-8"
    return response


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


def _find_notice_token_labels(text: str, token_groups: dict[str, list[str]]) -> list[str]:
    compact = compact_match_value(text)
    found: list[str] = []
    for label, aliases in token_groups.items():
        if any(token_alias_in_compact_text(compact, compact_match_value(alias)) for alias in aliases):
            found.append(label)
    return found


def token_alias_in_compact_text(text_compact: str, alias_compact: str) -> bool:
    if not text_compact or not alias_compact:
        return False
    if alias_compact == "소기업":
        # `중소기업` is a broader concept and must not be treated as an explicit small-enterprise condition.
        return alias_compact in text_compact.replace("중소기업", "")
    return alias_compact in text_compact


def _extract_notice_region_candidates(notice: dict, text: str) -> list[str]:
    candidates = [notice.get("region_text", "")]
    compact = compact_match_value(text)
    for canonical, aliases in REGION_ALIAS_GROUPS.items():
        if any(compact_match_value(alias) in compact for alias in aliases):
            candidates.append(canonical)

    for match in re.findall(r"[가-힣]{2,12}(?:시|군|구)", text):
        if match in {"공고시", "개찰시", "입찰시", "공고일시", "입찰개시", "개찰일시"}:
            continue
        candidates.append(match)

    return _dedupe_text_items(candidates)


def extract_notice_requirements(notice: dict, notice_text: str) -> dict:
    text = notice_text or ""
    requirement_lines = []
    for line in text.splitlines():
        cleaned = clean_text(line)
        if not cleaned:
            continue
        if any(
            token in cleaned
            for token in [
                "참가자격",
                "입찰참가",
                "입찰 참가",
                "제출서류",
                "제출 서류",
                "구비서류",
                "자격요건",
                "등록요건",
                "면허",
                "업종",
                "직접생산",
                "중소기업",
                "소기업",
                "소상공인",
                "지역제한",
                "영업소",
            ]
        ):
            requirement_lines.append(cleaned[:260])
        if len(requirement_lines) >= 16:
            break

    return {
        "extraction_method": "rule_based_phase_1_7_stabilized",
        "regions": _extract_notice_region_candidates(notice, text),
        "licenses": _dedupe_text_items([notice.get("license_text", ""), *_find_notice_token_labels(text, LICENSE_TOKEN_GROUPS)]),
        "company_types": _dedupe_text_items(_find_notice_token_labels(text, COMPANY_TYPE_TOKEN_GROUPS)),
        "required_documents": _dedupe_text_items(_find_notice_token_labels(text, DOCUMENT_TOKEN_GROUPS)),
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
            "Phase 1.7에서는 요구조건 후보와 부족 가능성만 정리하며 최종 자격 판정은 수행하지 않습니다."
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
            "※ 위 항목은 자동 추출 후보이며, 최종 자격 판정이 아닙니다.",
        ]
    )


def compact_match_value(value) -> str:
    return "".join(ch.lower() for ch in clean_text(value) if ch.isalnum())


def parse_json_list_value(value) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return _dedupe_text_items([clean_text(item) for item in value])
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return parse_json_list_value(parsed)
        except json.JSONDecodeError:
            pass
        return _dedupe_text_items([item.strip() for item in stripped.split(",") if item.strip()])
    return []


def make_requirement_candidate(
    requirement_type: str,
    value: str,
    source_text: str = "",
    requirement_key: str = "",
    confidence: float = 0.78,
) -> dict:
    cleaned = clean_text(value)
    return {
        "requirement_type": requirement_type,
        "requirement_key": requirement_key or compact_match_value(cleaned),
        "label": REQUIREMENT_TYPE_LABELS.get(requirement_type, requirement_type),
        "required_value": cleaned,
        "normalized_value": compact_match_value(cleaned),
        "confidence": confidence,
        "source_text": source_text or cleaned,
        "status": "candidate",
        "extraction_method": "rule_based_phase_1_7",
    }


def build_notice_requirement_candidates(requirements: dict) -> list[dict]:
    candidates: list[dict] = []

    for value in requirements.get("regions") or []:
        candidates.append(make_requirement_candidate("region", value, "공고 지역 제한", confidence=0.84))
    for value in requirements.get("licenses") or []:
        candidates.append(make_requirement_candidate("license", value, "공고 면허/업종 제한", confidence=0.86))
    for value in requirements.get("company_types") or []:
        candidates.append(make_requirement_candidate("company_type", value, "공고 기업유형/우대조건", confidence=0.8))
    for value in requirements.get("required_documents") or []:
        candidates.append(make_requirement_candidate("required_document", value, "공고 제출/증빙서류", confidence=0.76))

    money = requirements.get("money") if isinstance(requirements.get("money"), dict) else {}
    for key, label in {"presmpt_prce": "추정가격", "bdgt_amt": "예산금액", "bssamt": "기초금액"}.items():
        if clean_text(money.get(key)):
            candidates.append(
                make_requirement_candidate(
                    "money",
                    f"{label}: {money[key]}",
                    "공고 금액 조건",
                    requirement_key=key,
                    confidence=0.72,
                )
            )

    dates = requirements.get("dates") if isinstance(requirements.get("dates"), dict) else {}
    for key, label in {"bid_ntce_dt": "공고일시", "bid_begin_dt": "입찰개시", "bid_clse_dt": "입찰마감", "openg_dt": "개찰일시"}.items():
        if clean_text(dates.get(key)):
            candidates.append(
                make_requirement_candidate(
                    "date",
                    f"{label}: {dates[key]}",
                    "공고 일정 조건",
                    requirement_key=key,
                    confidence=0.72,
                )
            )

    for line in (requirements.get("requirement_lines") or [])[:12]:
        candidates.append(make_requirement_candidate("requirement_line", line, line, confidence=0.64))

    deduped: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["requirement_type"], candidate["normalized_value"] or candidate["required_value"])
        if not candidate["required_value"] or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def summarize_requirement_candidates(candidates: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for candidate in candidates:
        requirement_type = candidate.get("requirement_type", "unknown")
        counts[requirement_type] = counts.get(requirement_type, 0) + 1
    return {
        "total_count": len(candidates),
        "type_counts": counts,
        "status": "candidate_only",
        "note": "Phase 1.7A/B 요구조건 후보입니다. 최종 지원 가능 여부 판정이 아닙니다.",
    }


def requirements_from_saved_notice(notice: dict) -> dict:
    summary_payload: dict = {}
    try:
        parsed = json.loads(clean_text(notice.get("analysis_summary_json")) or "{}")
        if isinstance(parsed, dict):
            summary_payload = parsed
    except json.JSONDecodeError:
        summary_payload = {}

    requirements = summary_payload.get("notice_requirements")
    if isinstance(requirements, dict) and requirements:
        return requirements

    text = "\n".join(
        [
            build_nara_summary_text(notice, []),
            clean_text(notice.get("analysis_summary_markdown")),
        ]
    )
    return extract_notice_requirements(notice, text)


def store_notice_requirement_candidates(conn: sqlite3.Connection, notice_id: int, requirements: dict) -> list[dict]:
    candidates = build_notice_requirement_candidates(requirements)
    now = now_iso()
    conn.execute("DELETE FROM notice_requirement_candidates WHERE nara_notice_id=?", (notice_id,))
    conn.execute("DELETE FROM notice_corporation_comparisons WHERE nara_notice_id=?", (notice_id,))
    conn.execute("DELETE FROM judgment_runs WHERE nara_notice_id=?", (notice_id,))
    for candidate in candidates:
        conn.execute(
            """
            INSERT INTO notice_requirement_candidates (
              nara_notice_id, requirement_type, requirement_key, label,
              required_value, normalized_value, confidence, source_text,
              status, extraction_method, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notice_id,
                candidate["requirement_type"],
                candidate["requirement_key"],
                candidate["label"],
                candidate["required_value"],
                candidate["normalized_value"],
                candidate["confidence"],
                candidate["source_text"],
                candidate["status"],
                candidate["extraction_method"],
                now,
                now,
            ),
        )
    return candidates


def invalidate_corporation_comparisons(conn: sqlite3.Connection, corporation_id: int | None) -> None:
    if corporation_id:
        conn.execute("DELETE FROM notice_corporation_comparisons WHERE corporation_id=?", (corporation_id,))
        conn.execute("DELETE FROM judgment_runs WHERE corporation_id=?", (corporation_id,))


def ensure_notice_requirement_candidates(conn: sqlite3.Connection, notice_id: int, force: bool = False) -> list[dict] | None:
    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    if not notice:
        return None

    if not force:
        rows = conn.execute(
            "SELECT * FROM notice_requirement_candidates WHERE nara_notice_id=? ORDER BY id",
            (notice_id,),
        ).fetchall()
        if rows:
            return rows_to_dict(rows)

    requirements = requirements_from_saved_notice(dict(notice))
    store_notice_requirement_candidates(conn, notice_id, requirements)
    rows = conn.execute(
        "SELECT * FROM notice_requirement_candidates WHERE nara_notice_id=? ORDER BY id",
        (notice_id,),
    ).fetchall()
    return rows_to_dict(rows)


def notice_requirement_payload(conn: sqlite3.Connection, notice_id: int, force: bool = False) -> dict | None:
    candidates = ensure_notice_requirement_candidates(conn, notice_id, force=force)
    if candidates is None:
        return None
    return {
        "notice_id": notice_id,
        "requirements": candidates,
        "summary": summarize_requirement_candidates(candidates),
    }


def append_unique_text(target: list[str], values: list[Any]) -> None:
    existing = {compact_match_value(item) for item in target}
    for value in values:
        cleaned = clean_text(value)
        key = compact_match_value(cleaned)
        if not cleaned or not key or key in existing:
            continue
        existing.add(key)
        target.append(cleaned)


def extract_region_terms(*values: Any) -> list[str]:
    text = " ".join(clean_text(value) for value in values if clean_text(value))
    compact = compact_match_value(text)
    candidates: list[str] = []
    for canonical, aliases in REGION_ALIAS_GROUPS.items():
        if any(compact_match_value(alias) in compact for alias in aliases):
            candidates.append(canonical)
    candidates.extend(re.findall(r"[가-힣]{2,12}(?:시|군|구)", text))
    return _dedupe_text_items(candidates)


def build_corporation_comparison_profile(conn: sqlite3.Connection, corporation: sqlite3.Row | dict) -> dict:
    corp = dict(corporation)
    evidence_rows = conn.execute(
        """
        SELECT document_type, review_status, original_file_name
        FROM corporation_evidence_documents
        WHERE corporation_id=?
        ORDER BY id DESC
        """,
        (corp["id"],),
    ).fetchall()
    approved_evidence = [dict(row) for row in evidence_rows if row["review_status"] == "approved"]
    approved_document_labels = _dedupe_text_items(
        [
            EVIDENCE_DOCUMENT_LABELS.get(row["document_type"], row["document_type"])
            for row in approved_evidence
            if clean_text(row["document_type"])
        ]
    )

    certifications = parse_json_list_value(corp.get("certifications_json"))
    preference_tags = parse_json_list_value(corp.get("preference_tags_json"))
    direct_production_items = parse_json_list_value(corp.get("direct_production_items_json"))
    business_category_values = parse_json_list_value(corp.get("business_category"))
    business_type_values = parse_json_list_value(corp.get("business_type"))
    business_item_values = parse_json_list_value(corp.get("business_item"))
    license_values = parse_json_list_value(corp.get("license_summary"))
    procurement_values = parse_json_list_value(corp.get("procurement_registration_status"))

    regions: list[str] = []
    append_unique_text(regions, [corp.get("region")])
    append_unique_text(
        regions,
        extract_region_terms(corp.get("business_address"), corp.get("headquarters_address"), corp.get("region")),
    )

    business_types: list[str] = []
    append_unique_text(
        business_types,
        [
            *business_category_values,
            *business_type_values,
            *business_item_values,
            *direct_production_items,
        ],
    )

    licenses: list[str] = []
    append_unique_text(
        licenses,
        [
            *license_values,
            *procurement_values,
            *business_type_values,
            *business_item_values,
            *business_category_values,
        ],
    )

    company_types: list[str] = []
    append_unique_text(
        company_types,
        [
            corp.get("company_size_classification"),
            *certifications,
            *preference_tags,
        ],
    )

    required_documents: list[str] = []
    append_unique_text(required_documents, approved_document_labels)
    if clean_text(corp.get("business_registration_number")):
        append_unique_text(required_documents, ["사업자등록증", "사업자등록증명"])
    if clean_text(corp.get("company_size_classification")) or any("중소" in item or "소기업" in item for item in company_types):
        append_unique_text(required_documents, ["중소기업확인서"])
    if direct_production_items:
        append_unique_text(required_documents, ["직접생산확인증명서"])
    if clean_text(corp.get("procurement_registration_status")):
        append_unique_text(required_documents, ["나라장터 경쟁입찰참가자격 등록증"])
    if clean_text(corp.get("license_summary")):
        append_unique_text(required_documents, ["면허/등록/허가증"])
    if any("여성기업" in item for item in company_types):
        append_unique_text(required_documents, ["여성기업확인서"])
    if any("장애인기업" in item for item in company_types):
        append_unique_text(required_documents, ["장애인기업확인서"])

    return {
        "corporation_id": corp["id"],
        "corporation_name": corp["name"],
        "management_group_name": corp.get("management_group_name", ""),
        "regions": regions,
        "business_types": business_types,
        "licenses": licenses,
        "company_types": company_types,
        "certifications": certifications,
        "preference_tags": preference_tags,
        "direct_production_items": direct_production_items,
        "required_documents": required_documents,
        "approved_evidence_count": len(approved_evidence),
        "approved_evidence_labels": approved_document_labels,
        "profile_note": "Phase 1.7 비교용 정규화 프로필입니다. 사용자 검토 없이 최종 판정 근거로 사용하지 않습니다.",
    }


def region_match_keys(value: str) -> set[str]:
    cleaned = clean_text(value)
    compact = compact_match_value(cleaned)
    keys: set[str] = set()
    for canonical, aliases in REGION_ALIAS_GROUPS.items():
        if any(compact_match_value(alias) in compact for alias in aliases):
            keys.add(canonical)
    for match in re.findall(r"[가-힣]{2,12}(?:시|군|구)", cleaned):
        keys.add(compact_match_value(match))
    if compact:
        keys.add(compact)
    return keys


def token_group_key(value: str, token_groups: dict[str, list[str]]) -> str:
    compact = compact_match_value(value)
    for label, aliases in token_groups.items():
        keys = [compact_match_value(label), *(compact_match_value(alias) for alias in aliases)]
        if compact in keys or any(key and key in compact for key in keys):
            return label
    return ""


def controlled_text_match(required_key: str, value_key: str) -> bool:
    if not required_key or not value_key:
        return False
    if required_key == value_key:
        return True
    min_len = min(len(required_key), len(value_key))
    if min_len < 5:
        return False
    return required_key in value_key or value_key in required_key


def match_profile_values(required_value: str, profile_values: list[str], requirement_type: str = "") -> tuple[bool, str]:
    required_key = compact_match_value(required_value)
    if not required_key:
        return False, ""

    if requirement_type == "region":
        required_keys = region_match_keys(required_value)
        for value in profile_values:
            value_keys = region_match_keys(value)
            if required_keys & value_keys:
                return True, value
        return False, ""

    token_groups: dict[str, list[str]] = {}
    if requirement_type == "license":
        token_groups = LICENSE_TOKEN_GROUPS
    elif requirement_type == "company_type":
        token_groups = COMPANY_TYPE_TOKEN_GROUPS
    elif requirement_type == "required_document":
        token_groups = DOCUMENT_TOKEN_GROUPS

    required_group = token_group_key(required_value, token_groups) if token_groups else ""
    for value in profile_values:
        value_key = compact_match_value(value)
        if not value_key:
            continue
        if required_group and required_group == token_group_key(value, token_groups):
            return True, value
        if controlled_text_match(required_key, value_key):
            return True, value
    return False, ""


def compare_requirement_candidate(candidate: dict, profile: dict) -> dict:
    requirement_type = candidate.get("requirement_type", "")
    required_value = clean_text(candidate.get("required_value"))
    bucket_map = {
        "region": profile.get("regions", []),
        "license": [*profile.get("licenses", []), *profile.get("business_types", [])],
        "company_type": [*profile.get("company_types", []), *profile.get("certifications", []), *profile.get("preference_tags", [])],
        "required_document": [*profile.get("required_documents", []), *profile.get("approved_evidence_labels", [])],
    }

    if requirement_type in {"money", "date", "requirement_line"}:
        status = "needs_review"
        reason = "자동 비교만으로 판단하기 어려운 항목입니다. 원문과 법인 보유 자료를 함께 확인해야 합니다."
        matched_value = ""
    else:
        profile_values = bucket_map.get(requirement_type, [])
        if not profile_values:
            status = "not_found"
            reason = "비교할 법인 프로필 또는 승인 증빙 정보가 아직 충분하지 않습니다."
            matched_value = ""
        else:
            matched, matched_value = match_profile_values(required_value, profile_values, requirement_type)
            if matched:
                status = "prepared"
                reason = f"법인 프로필 또는 승인 증빙에서 '{matched_value}' 값을 찾았습니다."
            else:
                status = "possibly_missing"
                reason = f"법인 정보에서 '{required_value}'와 직접 일치하는 준비 항목을 찾지 못했습니다."

    return {
        "requirement_candidate_id": candidate.get("id"),
        "requirement_type": requirement_type,
        "label": candidate.get("label") or REQUIREMENT_TYPE_LABELS.get(requirement_type, requirement_type),
        "required_value": required_value,
        "normalized_value": candidate.get("normalized_value", ""),
        "source_text": candidate.get("source_text", ""),
        "confidence": candidate.get("confidence", 0),
        "status": status,
        "status_label": COMPARISON_STATUS_LABELS.get(status, status),
        "matched_value": matched_value,
        "reason": reason,
    }


def summarize_comparison_items(items: list[dict]) -> dict:
    counts = {status: 0 for status in COMPARISON_STATUS_LABELS}
    for item in items:
        status = item.get("status", "needs_review")
        counts[status] = counts.get(status, 0) + 1
    return {
        "requirement_count": len(items),
        "prepared_count": counts.get("prepared", 0),
        "possibly_missing_count": counts.get("possibly_missing", 0),
        "needs_review_count": counts.get("needs_review", 0),
        "not_found_count": counts.get("not_found", 0),
        "status": "preview_only",
        "note": "부족조건 미리보기 결과입니다. 최종 자격 판정이 아닙니다.",
    }


def comparison_row_payload(conn: sqlite3.Connection, row: sqlite3.Row | dict) -> dict:
    payload = dict(row)
    try:
        payload["summary"] = json.loads(payload.get("summary_json") or "{}")
    except json.JSONDecodeError:
        payload["summary"] = {}
    try:
        result = json.loads(payload.get("result_json") or "{}")
    except json.JSONDecodeError:
        result = {}
    payload["items"] = result.get("items", []) if isinstance(result, dict) else []
    payload["profile"] = result.get("profile", {}) if isinstance(result, dict) else {}

    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (payload["nara_notice_id"],)).fetchone()
    corporation = conn.execute("SELECT * FROM corporations WHERE id=?", (payload["corporation_id"],)).fetchone()
    payload["notice"] = row_to_dict(notice)
    payload["corporation"] = row_to_dict(corporation)
    return payload


def build_notice_corporation_comparison(
    conn: sqlite3.Connection,
    notice_id: int,
    corporation_id: int,
) -> dict | None:
    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    corporation = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
    if not notice or not corporation:
        return None

    candidates = ensure_notice_requirement_candidates(conn, notice_id)
    if candidates is None:
        return None

    profile = build_corporation_comparison_profile(conn, corporation)
    items = [compare_requirement_candidate(candidate, profile) for candidate in candidates]
    summary = summarize_comparison_items(items)
    now = now_iso()

    cur = conn.execute(
        """
        INSERT INTO notice_corporation_comparisons (
          nara_notice_id, corporation_id, status, summary_json, result_json,
          requirement_count, prepared_count, possibly_missing_count,
          needs_review_count, not_found_count, prompt_version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            notice_id,
            corporation_id,
            "preview",
            json.dumps(summary, ensure_ascii=False),
            json.dumps({"items": items, "profile": profile}, ensure_ascii=False),
            summary["requirement_count"],
            summary["prepared_count"],
            summary["possibly_missing_count"],
            summary["needs_review_count"],
            summary["not_found_count"],
            "phase_1_7_rule_v1",
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM notice_corporation_comparisons WHERE id=?", (cur.lastrowid,)).fetchone()
    return comparison_row_payload(conn, row)


def ensure_table_columns(conn: sqlite3.Connection, table_name: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for column_name, ddl in columns.items():
        if column_name not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}")


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "uploads").mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "corporation-evidence").mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "basis").mkdir(parents=True, exist_ok=True)
    BASIS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

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

            CREATE TABLE IF NOT EXISTS basis_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT DEFAULT '',
                document_version TEXT DEFAULT '',
                issuing_agency TEXT DEFAULT '',
                effective_date TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                original_file_name TEXT NOT NULL,
                stored_file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                file_hash TEXT DEFAULT '',
                memo TEXT DEFAULT '',
                processing_status TEXT DEFAULT 'pending',
                parse_status TEXT DEFAULT 'pending',
                ocr_status TEXT DEFAULT 'pending',
                chunk_status TEXT DEFAULT 'pending',
                index_status TEXT DEFAULT 'pending',
                page_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                vector_count INTEGER DEFAULT 0,
                extracted_text_preview TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                processed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS basis_document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                basis_document_id INTEGER NOT NULL,
                processing_run_id TEXT DEFAULT '',
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_text_normalized TEXT NOT NULL,
                page_start INTEGER,
                page_end INTEGER,
                section_title TEXT DEFAULT '',
                article_label TEXT DEFAULT '',
                chunk_hash TEXT DEFAULT '',
                token_count INTEGER DEFAULT 0,
                metadata_json TEXT DEFAULT '{}',
                vector_id TEXT DEFAULT '',
                vector_status TEXT DEFAULT 'pending',
                embedding_model TEXT DEFAULT '',
                index_error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(basis_document_id) REFERENCES basis_documents(id)
            );

            CREATE TABLE IF NOT EXISTS basis_rule_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                basis_document_id INTEGER NOT NULL,
                basis_chunk_id INTEGER NOT NULL,
                rule_type TEXT NOT NULL,
                condition_text TEXT NOT NULL,
                target_scope TEXT DEFAULT '',
                required_evidence_types_json TEXT DEFAULT '[]',
                related_profile_fields_json TEXT DEFAULT '[]',
                citation_candidate_id TEXT DEFAULT '',
                confidence REAL DEFAULT 0,
                source_condition_text TEXT DEFAULT '',
                source_required_evidence_types_json TEXT DEFAULT '[]',
                source_related_profile_fields_json TEXT DEFAULT '[]',
                source_confidence REAL DEFAULT 0,
                source_condition_hash TEXT DEFAULT '',
                extraction_key TEXT DEFAULT '',
                status TEXT DEFAULT 'needs_review',
                review_note TEXT DEFAULT '',
                reviewed_at TEXT DEFAULT '',
                reviewer_name TEXT DEFAULT '',
                extraction_method TEXT DEFAULT 'basis_rule_candidate_v1',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(basis_document_id) REFERENCES basis_documents(id),
                FOREIGN KEY(basis_chunk_id) REFERENCES basis_document_chunks(id)
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

            CREATE TABLE IF NOT EXISTS notice_requirement_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nara_notice_id INTEGER NOT NULL,
                requirement_type TEXT NOT NULL,
                requirement_key TEXT DEFAULT '',
                label TEXT DEFAULT '',
                required_value TEXT DEFAULT '',
                normalized_value TEXT DEFAULT '',
                confidence REAL DEFAULT 0,
                source_text TEXT DEFAULT '',
                status TEXT DEFAULT 'candidate',
                extraction_method TEXT DEFAULT 'rule_based_phase_1_7',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(nara_notice_id) REFERENCES nara_notices(id)
            );

            CREATE TABLE IF NOT EXISTS notice_corporation_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nara_notice_id INTEGER NOT NULL,
                corporation_id INTEGER NOT NULL,
                status TEXT DEFAULT 'preview',
                summary_json TEXT DEFAULT '{}',
                result_json TEXT DEFAULT '{}',
                requirement_count INTEGER DEFAULT 0,
                prepared_count INTEGER DEFAULT 0,
                possibly_missing_count INTEGER DEFAULT 0,
                needs_review_count INTEGER DEFAULT 0,
                not_found_count INTEGER DEFAULT 0,
                prompt_version TEXT DEFAULT 'phase_1_7_rule_v1',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(nara_notice_id) REFERENCES nara_notices(id),
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS basis_retrieval_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query_set_json TEXT NOT NULL,
                result_json TEXT DEFAULT '{}',
                query_count INTEGER DEFAULT 0,
                citation_coverage REAL DEFAULT 0,
                average_top_score REAL DEFAULT 0,
                status TEXT DEFAULT 'completed',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS judgment_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nara_notice_id INTEGER NOT NULL,
                corporation_id INTEGER NOT NULL,
                status TEXT DEFAULT 'completed',
                review_status TEXT DEFAULT 'pending',
                reviewer_note TEXT DEFAULT '',
                input_snapshot_json TEXT DEFAULT '{}',
                result_json TEXT DEFAULT '{}',
                summary_json TEXT DEFAULT '{}',
                matched_count INTEGER DEFAULT 0,
                missing_count INTEGER DEFAULT 0,
                uncertain_count INTEGER DEFAULT 0,
                needs_review_count INTEGER DEFAULT 0,
                not_applicable_count INTEGER DEFAULT 0,
                citation_coverage REAL DEFAULT 0,
                rule_version TEXT DEFAULT 'phase3_gap_judgment_rule_v1',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(nara_notice_id) REFERENCES nara_notices(id),
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS nara_collection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'completed',
                mode TEXT DEFAULT 'api',
                keyword TEXT DEFAULT '',
                start_date TEXT DEFAULT '',
                end_date TEXT DEFAULT '',
                searched_count INTEGER DEFAULT 0,
                saved_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                error_message TEXT DEFAULT '',
                criteria_json TEXT DEFAULT '{}',
                result_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS operation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                target_type TEXT DEFAULT '',
                target_id INTEGER,
                status TEXT NOT NULL,
                requested_by TEXT DEFAULT 'local_admin',
                request_json TEXT DEFAULT '{}',
                result_json TEXT DEFAULT '{}',
                error_message TEXT DEFAULT '',
                error_code TEXT DEFAULT '',
                retry_of_run_id INTEGER,
                retry_count INTEGER DEFAULT 0,
                started_at TEXT,
                finished_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS backup_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type TEXT NOT NULL,
                status TEXT NOT NULL,
                file_name TEXT DEFAULT '',
                file_path TEXT DEFAULT '',
                file_size_bytes INTEGER DEFAULT 0,
                manifest_json TEXT DEFAULT '{}',
                validation_json TEXT DEFAULT '{}',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                updated_at TEXT NOT NULL
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

            CREATE INDEX IF NOT EXISTS idx_basis_rule_candidates_status
            ON basis_rule_candidates(status);
            CREATE INDEX IF NOT EXISTS idx_basis_rule_candidates_basis_document
            ON basis_rule_candidates(basis_document_id);
            CREATE INDEX IF NOT EXISTS idx_basis_rule_candidates_rule_type
            ON basis_rule_candidates(rule_type);
            CREATE INDEX IF NOT EXISTS idx_judgment_runs_notice_corporation
            ON judgment_runs(nara_notice_id, corporation_id);
            CREATE INDEX IF NOT EXISTS idx_judgment_runs_created_at
            ON judgment_runs(created_at);
            CREATE INDEX IF NOT EXISTS idx_nara_collection_runs_created_at
            ON nara_collection_runs(created_at);
            CREATE INDEX IF NOT EXISTS idx_nara_collection_runs_status
            ON nara_collection_runs(status);
            CREATE INDEX IF NOT EXISTS idx_basis_retrieval_evaluations_created_at
            ON basis_retrieval_evaluations(created_at);
            CREATE INDEX IF NOT EXISTS idx_operation_runs_created_at
            ON operation_runs(created_at);
            CREATE INDEX IF NOT EXISTS idx_operation_runs_status
            ON operation_runs(status);
            CREATE INDEX IF NOT EXISTS idx_operation_runs_type
            ON operation_runs(operation_type);
            CREATE INDEX IF NOT EXISTS idx_backup_runs_created_at
            ON backup_runs(created_at);
            CREATE INDEX IF NOT EXISTS idx_backup_runs_status
            ON backup_runs(status);
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
        ensure_table_columns(
            conn,
            "basis_rule_candidates",
            {
                "review_note": "TEXT DEFAULT ''",
                "reviewed_at": "TEXT DEFAULT ''",
                "reviewer_name": "TEXT DEFAULT ''",
                "source_condition_text": "TEXT DEFAULT ''",
                "source_required_evidence_types_json": "TEXT DEFAULT '[]'",
                "source_related_profile_fields_json": "TEXT DEFAULT '[]'",
                "source_confidence": "REAL DEFAULT 0",
                "source_condition_hash": "TEXT DEFAULT ''",
                "extraction_key": "TEXT DEFAULT ''",
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_phase2_known_issues() -> list[dict[str, Any]]:
    explicit_path = clean_text(os.getenv("NARA_NOTICE_PDF_KNOWN_ISSUES_PATH"))
    issue_paths = []
    if explicit_path:
        issue_paths.append(Path(explicit_path))
    issue_paths.extend(
        [
            BASE_DIR / "backend" / "tests" / "nara-notice-pdf-samples" / "qa-known-issues.json",
            BASE_DIR / "backend" / "tests" / "nara-notice-pdf-samples" / "manifest.json",
        ]
    )
    for path in issue_paths:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, list):
            issues = payload
        elif isinstance(payload, dict):
            issues = payload.get("known_issues") or payload.get("issues") or []
        else:
            issues = []
        if not isinstance(issues, list):
            continue
        normalized = [issue for issue in issues if isinstance(issue, dict)]
        if normalized:
            return normalized
    return []


def phase2_closeout_summary() -> dict[str, Any]:
    return {
        "status": "phase2_mvp_complete",
        "generated_at": now_iso(),
        "test_baseline": {
            "default_backend": "py -3.13 -m unittest discover -s tests -v",
            "encoding": "py -3.13 scripts\\check-encoding.py",
            "diff_check": "git diff --check",
            "phase17_pdf_opt_in": "$env:RUN_NARA_PHASE17_QA='1'; py -3.13 -m unittest tests.test_nara_phase17_live_samples -v",
            "phase2_pdf_opt_in": "$env:RUN_NARA_PHASE2_QA='1'; py -3.13 -m unittest tests.test_nara_phase2_basis_qa_samples -v",
        },
        "sample_policy": {
            "notice_pdf_cache": "backend/tests/nara-notice-pdf-samples/",
            "notice_pdf_manifest": "backend/tests/nara-notice-pdf-samples/manifest.json",
            "notice_pdf_use": "공고문 PDF 파이프라인 안정성 테스트용",
            "basis_pdf_use": "법령/예규/기준문서 검색과 citation 품질 평가용으로 별도 선정",
            "git_policy": "PDF 샘플과 temp 비교 결과는 로컬 QA 산출물로 두고 Git에는 포함하지 않음",
        },
        "known_issues": load_phase2_known_issues(),
        "guardrails": [
            "Phase 3 전후 출력은 부족조건/확인 필요/citation 후보 중심으로 유지",
            "citation 없는 조건은 확정 근거로 사용하지 않음",
            "나라장터 자동화는 API 기반으로만 확장하고 HTML 크롤링은 도입하지 않음",
        ],
    }


def basis_rule_candidate_payload(row: sqlite3.Row | dict) -> dict:
    payload = dict(row)
    payload["required_evidence_types"] = parse_json_list(payload.pop("required_evidence_types_json", "[]"))
    payload["related_profile_fields"] = parse_json_list(payload.pop("related_profile_fields_json", "[]"))
    payload["source_required_evidence_types"] = parse_json_list(payload.pop("source_required_evidence_types_json", "[]"))
    payload["source_related_profile_fields"] = parse_json_list(payload.pop("source_related_profile_fields_json", "[]"))
    return payload


def basis_rule_candidate_detail_payload(conn: sqlite3.Connection, row: sqlite3.Row | dict) -> dict:
    payload = basis_rule_candidate_payload(row)
    basis = conn.execute("SELECT * FROM basis_documents WHERE id=?", (payload["basis_document_id"],)).fetchone()
    chunk = conn.execute("SELECT * FROM basis_document_chunks WHERE id=?", (payload["basis_chunk_id"],)).fetchone()
    payload["basis_document"] = basis_document_payload(conn, basis) if basis else None
    payload["chunk"] = basis_chunk_payload(chunk) if chunk else None
    expected_citation_id = expected_basis_citation_candidate_id(payload["basis_document_id"], payload["basis_chunk_id"])
    payload["expected_citation_candidate_id"] = expected_citation_id
    payload["citation_candidate_valid"] = payload["citation_candidate_id"] == expected_citation_id
    payload["citation_options"] = [
        {
            "citation_candidate_id": expected_citation_id,
            "basis_document_id": payload["basis_document_id"],
            "basis_chunk_id": payload["basis_chunk_id"],
            "basis_document_title": basis["title"] if basis else "",
            "page_start": chunk["page_start"] if chunk else None,
            "page_end": chunk["page_end"] if chunk else None,
            "section_title": chunk["section_title"] if chunk else "",
            "text_preview": clean_text(chunk["chunk_text_normalized"] if chunk else payload["condition_text"])[:500],
        }
    ]
    return payload


def update_basis_rule_candidate(
    conn: sqlite3.Connection,
    candidate_id: int,
    payload: dict[str, Any],
    forced_status: str = "",
) -> tuple[dict[str, Any] | None, str]:
    row = conn.execute("SELECT * FROM basis_rule_candidates WHERE id=?", (candidate_id,)).fetchone()
    if not row:
        return None, "not_found"

    current = basis_rule_candidate_payload(row)
    next_values, error = prepare_basis_rule_candidate_update(
        conn,
        current,
        payload,
        forced_status=forced_status,
        reviewed_at_now=now_iso(),
    )
    if error:
        return None, error
    now = now_iso()
    conn.execute(
        """
        UPDATE basis_rule_candidates
        SET rule_type=?, condition_text=?, target_scope=?,
            required_evidence_types_json=?, related_profile_fields_json=?,
            citation_candidate_id=?, confidence=?, status=?, review_note=?,
            reviewed_at=?, reviewer_name=?, updated_at=?
        WHERE id=?
        """,
        (
            next_values["rule_type"],
            next_values["condition_text"],
            next_values["target_scope"],
            json.dumps([clean_text(value) for value in next_values["required_evidence_types"] if clean_text(value)], ensure_ascii=False),
            json.dumps([clean_text(value) for value in next_values["related_profile_fields"] if clean_text(value)], ensure_ascii=False),
            next_values["citation_candidate_id"],
            next_values["confidence"],
            next_values["status"],
            next_values["review_note"],
            next_values["reviewed_at"],
            next_values["reviewer_name"],
            now,
            candidate_id,
        ),
    )
    updated = conn.execute("SELECT * FROM basis_rule_candidates WHERE id=?", (candidate_id,)).fetchone()
    return basis_rule_candidate_detail_payload(conn, updated), ""


def rule_candidate_profile_fields(rule_type: str) -> list[str]:
    return {
        "region": ["region", "business_address", "headquarters_address"],
        "license": ["license_summary", "business_type", "business_item", "procurement_registration_status"],
        "company_type": ["company_size_classification", "certifications_json", "preference_tags_json"],
        "required_document": ["approved_evidence_labels", "corporation_evidence_documents"],
    }.get(rule_type, ["manual_review"])


def rule_candidate_evidence_types(rule_type: str, condition_text: str) -> list[str]:
    if rule_type == "license":
        return ["면허/등록/허가증"]
    if rule_type == "region":
        return ["사업장 소재지 증빙"]
    if rule_type == "company_type":
        labels = _find_notice_token_labels(condition_text, COMPANY_TYPE_TOKEN_GROUPS)
        if any("여성" in label for label in labels):
            return ["여성기업확인서"]
        if any("장애인" in label for label in labels):
            return ["장애인기업확인서"]
        if any("소기업" in label or "소상공인" in label or "중소기업" in label for label in labels):
            return ["중소기업확인서"]
        return ["기업유형 확인서"]
    if rule_type == "required_document":
        labels = _find_notice_token_labels(condition_text, DOCUMENT_TOKEN_GROUPS)
        return labels or ["제출서류"]
    return []


def detect_basis_rule_types(condition_text: str) -> list[str]:
    rule_types: list[str] = []
    if _extract_notice_region_candidates({}, condition_text):
        rule_types.append("region")
    if _find_notice_token_labels(condition_text, LICENSE_TOKEN_GROUPS):
        rule_types.append("license")
    if _find_notice_token_labels(condition_text, COMPANY_TYPE_TOKEN_GROUPS):
        rule_types.append("company_type")
    if _find_notice_token_labels(condition_text, DOCUMENT_TOKEN_GROUPS):
        rule_types.append("required_document")
    lowered = condition_text.lower()
    if any(token in lowered for token in ["small business", "women-owned", "disabled-owned", "company type"]):
        rule_types.append("company_type")
    if any(token in lowered for token in ["license", "permit", "registered contractor", "construction business"]):
        rule_types.append("license")
    if any(token in lowered for token in ["certificate", "document", "tax payment", "business registration"]):
        rule_types.append("required_document")
    if any(token in condition_text for token in ["하여야", "해야", "제출", "등록", "보유", "갖추"]):
        rule_types.append("basis_rule")
    if any(token in lowered for token in ["must", "shall", "submit", "hold", "required"]):
        rule_types.append("basis_rule")
    return _dedupe_text_items(rule_types)


def stable_rule_source_hash(text: str) -> str:
    normalized = compact_match_value(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def basis_rule_candidate_extraction_key(
    *,
    basis_document_id: int,
    rule_type: str,
    chunk_hash: str,
    source_condition_hash: str,
) -> str:
    return (
        f"basis:{basis_document_id}:rule:{clean_text(rule_type)}:"
        f"chunk_hash:{clean_text(chunk_hash)}:source:{clean_text(source_condition_hash)}"
    )


def extract_basis_rule_candidates_from_chunk(chunk: sqlite3.Row) -> list[dict[str, Any]]:
    text = clean_text(chunk["chunk_text_normalized"] or chunk["chunk_text"])
    source_lines: list[str] = []
    for raw_line in text.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        lower_line = line.lower()
        if any(
            token in line or token in lower_line
            for token in [
                "참가자격",
                "입찰참가",
                "자격요건",
                "제출",
                "증빙",
                "확인서",
                "면허",
                "등록",
                "소기업",
                "중소기업",
                "여성기업",
                "직접생산",
                "지역",
                "영업소",
                "qualification",
                "license",
                "certificate",
                "document",
                "submit",
                "small business",
                "required",
            ]
        ):
            source_lines.append(line[:420])
    if not source_lines and len(text) <= 420:
        source_lines.append(text)

    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    citation_id = f"basis:{chunk['basis_document_id']}:chunk:{chunk['id']}"
    for line in source_lines[:12]:
        source_condition_hash = stable_rule_source_hash(line)
        for rule_type in detect_basis_rule_types(line):
            key = (rule_type, compact_match_value(line))
            if not key[1] or key in seen:
                continue
            seen.add(key)
            required_evidence_types = rule_candidate_evidence_types(rule_type, line)
            related_profile_fields = rule_candidate_profile_fields(rule_type)
            confidence = 0.72 if rule_type != "basis_rule" else 0.58
            candidates.append(
                {
                    "basis_document_id": chunk["basis_document_id"],
                    "basis_chunk_id": chunk["id"],
                    "rule_type": rule_type,
                    "condition_text": line,
                    "target_scope": "procurement_readiness",
                    "required_evidence_types": required_evidence_types,
                    "related_profile_fields": related_profile_fields,
                    "citation_candidate_id": citation_id,
                    "confidence": confidence,
                    "source_condition_text": line,
                    "source_required_evidence_types": required_evidence_types,
                    "source_related_profile_fields": related_profile_fields,
                    "source_confidence": confidence,
                    "source_condition_hash": source_condition_hash,
                    "extraction_key": basis_rule_candidate_extraction_key(
                        basis_document_id=chunk["basis_document_id"],
                        rule_type=rule_type,
                        chunk_hash=chunk["chunk_hash"],
                        source_condition_hash=source_condition_hash,
                    ),
                    "status": "needs_review",
                    "extraction_method": "basis_rule_candidate_v1",
                }
            )
    return candidates


def basis_rule_candidate_value(candidate: sqlite3.Row | dict[str, Any], key: str, default: Any = "") -> Any:
    if isinstance(candidate, dict):
        return candidate.get(key, default)
    return candidate[key] if key in candidate.keys() else default


def basis_rule_candidate_match_key(candidate: sqlite3.Row | dict[str, Any]) -> tuple[str, str, str]:
    return (
        clean_text(basis_rule_candidate_value(candidate, "rule_type")),
        compact_match_value(basis_rule_candidate_value(candidate, "condition_text")),
        clean_text(basis_rule_candidate_value(candidate, "target_scope")),
    )


def basis_rule_candidate_stable_key(candidate: sqlite3.Row | dict[str, Any]) -> str:
    return clean_text(basis_rule_candidate_value(candidate, "extraction_key"))


def basis_rule_extraction_readiness(conn: sqlite3.Connection, basis: sqlite3.Row) -> dict[str, Any]:
    indexed_chunk_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM basis_document_chunks
        WHERE basis_document_id=?
          AND vector_status='indexed'
          AND vector_id<>''
        """,
        (basis["id"],),
    ).fetchone()[0]
    ready = (
        basis["processing_status"] == "completed"
        and basis["index_status"] == "completed"
        and int(indexed_chunk_count or 0) > 0
    )
    return {
        "ready": ready,
        "processing_status": basis["processing_status"],
        "index_status": basis["index_status"],
        "indexed_chunk_count": int(indexed_chunk_count or 0),
    }


def extract_basis_rule_candidates(conn: sqlite3.Connection, basis_document_id: int) -> dict[str, Any] | None:
    basis = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
    if not basis:
        return None
    readiness = basis_rule_extraction_readiness(conn, basis)
    if not readiness["ready"]:
        existing_rows = conn.execute(
            """
            SELECT * FROM basis_rule_candidates
            WHERE basis_document_id=?
            ORDER BY id
            """,
            (basis_document_id,),
        ).fetchall()
        return {
            "basis_document_id": basis_document_id,
            "candidate_count": len(existing_rows),
            "new_candidate_count": 0,
            "updated_candidate_count": 0,
            "revalidation_candidate_count": 0,
            "deleted_candidate_count": 0,
            "status": "basis_not_ready",
            "detail": "Basis document must be completed and indexed before rule candidate extraction.",
            **readiness,
            "candidates": [basis_rule_candidate_payload(row) for row in existing_rows],
        }
    chunks = conn.execute(
        """
        SELECT * FROM basis_document_chunks
        WHERE basis_document_id=?
          AND vector_status='indexed'
          AND vector_id<>''
        ORDER BY chunk_index
        """,
        (basis_document_id,),
    ).fetchall()

    generated_candidates: list[dict[str, Any]] = []
    generated_keys: set[str] = set()
    for chunk in chunks:
        for candidate in extract_basis_rule_candidates_from_chunk(chunk):
            key = basis_rule_candidate_stable_key(candidate)
            if not key or key in generated_keys:
                continue
            generated_keys.add(key)
            generated_candidates.append(candidate)

    now = now_iso()
    existing_rows = conn.execute(
        """
        SELECT * FROM basis_rule_candidates
        WHERE basis_document_id=?
        ORDER BY id
        """,
        (basis_document_id,),
    ).fetchall()
    if not generated_candidates:
        return {
            "basis_document_id": basis_document_id,
            "candidate_count": len(existing_rows),
            "new_candidate_count": 0,
            "updated_candidate_count": 0,
            "revalidation_candidate_count": 0,
            "deleted_candidate_count": 0,
            "status": "no_candidates_extracted_existing_preserved" if existing_rows else "no_candidates_extracted",
            "note": "새 규칙 후보가 없어 기존 후보를 보존했습니다.",
            "candidates": [basis_rule_candidate_payload(row) for row in existing_rows],
        }

    existing_by_stable_key: dict[str, sqlite3.Row] = {}
    existing_by_legacy_key: dict[tuple[str, str, str], sqlite3.Row] = {}
    for row in existing_rows:
        stable_key = basis_rule_candidate_stable_key(row)
        if stable_key:
            existing_by_stable_key.setdefault(stable_key, row)
        else:
            existing_by_legacy_key.setdefault(basis_rule_candidate_match_key(row), row)

    inserted = 0
    updated = 0
    revalidated = 0
    deleted = 0
    used_existing_ids: set[int] = set()

    for candidate in generated_candidates:
        existing = existing_by_stable_key.get(basis_rule_candidate_stable_key(candidate))
        if not existing:
            existing = existing_by_legacy_key.get(basis_rule_candidate_match_key(candidate))
        if existing:
            used_existing_ids.add(existing["id"])
            reviewed = existing["status"] in {"approved", "rejected"}
            citation_changed = bool(clean_text(existing["citation_candidate_id"])) and (
                clean_text(existing["citation_candidate_id"]) != clean_text(candidate["citation_candidate_id"])
            )
            if reviewed and citation_changed:
                conn.execute(
                    """
                    UPDATE basis_rule_candidates
                    SET basis_chunk_id=?, source_condition_text=?,
                        source_required_evidence_types_json=?, source_related_profile_fields_json=?,
                        source_confidence=?, source_condition_hash=?, extraction_key=?,
                        citation_candidate_id='', status='needs_review',
                        review_note=CASE
                            WHEN review_note='' THEN '재추출 결과 citation 후보가 변경되어 재검토 필요'
                            ELSE review_note || ' / 재추출 결과 citation 후보가 변경되어 재검토 필요'
                        END,
                        reviewed_at='', reviewer_name='', extraction_method=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        candidate["basis_chunk_id"],
                        candidate["source_condition_text"],
                        json.dumps(candidate["source_required_evidence_types"], ensure_ascii=False),
                        json.dumps(candidate["source_related_profile_fields"], ensure_ascii=False),
                        candidate["source_confidence"],
                        candidate["source_condition_hash"],
                        candidate["extraction_key"],
                        candidate["extraction_method"],
                        now,
                        existing["id"],
                    ),
                )
                revalidated += 1
                continue
            if reviewed:
                conn.execute(
                    """
                    UPDATE basis_rule_candidates
                    SET basis_chunk_id=?, source_condition_text=?,
                        source_required_evidence_types_json=?, source_related_profile_fields_json=?,
                        source_confidence=?, source_condition_hash=?, extraction_key=?,
                        extraction_method=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        candidate["basis_chunk_id"],
                        candidate["source_condition_text"],
                        json.dumps(candidate["source_required_evidence_types"], ensure_ascii=False),
                        json.dumps(candidate["source_related_profile_fields"], ensure_ascii=False),
                        candidate["source_confidence"],
                        candidate["source_condition_hash"],
                        candidate["extraction_key"],
                        candidate["extraction_method"],
                        now,
                        existing["id"],
                    ),
                )
                updated += 1
                continue
            conn.execute(
                """
                UPDATE basis_rule_candidates
                SET basis_chunk_id=?, rule_type=?, condition_text=?, target_scope=?,
                    required_evidence_types_json=?, related_profile_fields_json=?,
                    citation_candidate_id=?, confidence=?,
                    source_condition_text=?, source_required_evidence_types_json=?,
                    source_related_profile_fields_json=?, source_confidence=?,
                    source_condition_hash=?, extraction_key=?, extraction_method=?, updated_at=?
                WHERE id=?
                """,
                (
                    candidate["basis_chunk_id"],
                    candidate["rule_type"],
                    candidate["condition_text"],
                    candidate["target_scope"],
                    json.dumps(candidate["required_evidence_types"], ensure_ascii=False),
                    json.dumps(candidate["related_profile_fields"], ensure_ascii=False),
                    candidate["citation_candidate_id"],
                    candidate["confidence"],
                    candidate["source_condition_text"],
                    json.dumps(candidate["source_required_evidence_types"], ensure_ascii=False),
                    json.dumps(candidate["source_related_profile_fields"], ensure_ascii=False),
                    candidate["source_confidence"],
                    candidate["source_condition_hash"],
                    candidate["extraction_key"],
                    candidate["extraction_method"],
                    now,
                    existing["id"],
                ),
            )
            updated += 1
            continue

        conn.execute(
            """
            INSERT INTO basis_rule_candidates (
              basis_document_id, basis_chunk_id, rule_type, condition_text,
              target_scope, required_evidence_types_json, related_profile_fields_json,
              citation_candidate_id, confidence, source_condition_text,
              source_required_evidence_types_json, source_related_profile_fields_json,
              source_confidence, source_condition_hash, extraction_key, status,
              extraction_method, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate["basis_document_id"],
                candidate["basis_chunk_id"],
                candidate["rule_type"],
                candidate["condition_text"],
                candidate["target_scope"],
                json.dumps(candidate["required_evidence_types"], ensure_ascii=False),
                json.dumps(candidate["related_profile_fields"], ensure_ascii=False),
                candidate["citation_candidate_id"],
                candidate["confidence"],
                candidate["source_condition_text"],
                json.dumps(candidate["source_required_evidence_types"], ensure_ascii=False),
                json.dumps(candidate["source_related_profile_fields"], ensure_ascii=False),
                candidate["source_confidence"],
                candidate["source_condition_hash"],
                candidate["extraction_key"],
                candidate["status"],
                candidate["extraction_method"],
                now,
                now,
            ),
        )
        inserted += 1

    for row in existing_rows:
        if row["id"] in used_existing_ids:
            continue
        if row["status"] in {"approved", "rejected"}:
            conn.execute(
                """
                UPDATE basis_rule_candidates
                SET status='needs_review',
                    citation_candidate_id='',
                    review_note=CASE
                        WHEN review_note='' THEN '재추출 결과 현재 청크에서 같은 조건을 찾지 못해 재검토 필요'
                        ELSE review_note || ' / 재추출 결과 현재 청크에서 같은 조건을 찾지 못해 재검토 필요'
                    END,
                    reviewed_at='',
                    reviewer_name='',
                    updated_at=?
                WHERE id=?
                """,
                (now, row["id"]),
            )
            revalidated += 1
        elif row["status"] != "archived":
            conn.execute("DELETE FROM basis_rule_candidates WHERE id=?", (row["id"],))
            deleted += 1

    rows = conn.execute(
        "SELECT * FROM basis_rule_candidates WHERE basis_document_id=? ORDER BY id",
        (basis_document_id,),
    ).fetchall()
    return {
        "basis_document_id": basis_document_id,
        "candidate_count": len(rows),
        "new_candidate_count": inserted,
        "updated_candidate_count": updated,
        "revalidation_candidate_count": revalidated,
        "deleted_candidate_count": deleted,
        "status": "candidates_extracted",
        "note": "기준문서 규칙 후보이며 관리자 검토 전에는 판단 근거로 확정하지 않습니다.",
        "candidates": [basis_rule_candidate_payload(row) for row in rows],
    }


def list_basis_rule_candidates_payload(
    conn: sqlite3.Connection,
    basis_document_id: int | None = None,
    status: str = "",
    rule_type: str = "",
    keyword: str = "",
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if basis_document_id:
        clauses.append("basis_document_id=?")
        params.append(basis_document_id)
    if status:
        clauses.append("status=?")
        params.append(status)
    if rule_type:
        clauses.append("rule_type=?")
        params.append(rule_type)
    if keyword:
        clauses.append("(condition_text LIKE ? OR target_scope LIKE ? OR citation_candidate_id LIKE ?)")
        like_value = f"%{keyword}%"
        params.extend([like_value, like_value, like_value])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM basis_rule_candidates {where} ORDER BY id DESC",
        tuple(params),
    ).fetchall()
    return [basis_rule_candidate_payload(row) for row in rows]


def structured_requirement_profile_fields(requirement_type: str) -> list[str]:
    return {
        "region": ["region", "business_address", "headquarters_address"],
        "license": ["license_summary", "business_type", "business_item", "procurement_registration_status"],
        "company_type": ["company_size_classification", "certifications_json", "preference_tags_json"],
        "required_document": ["corporation_evidence_documents", "approved_evidence_labels"],
        "money": ["manual_review"],
        "date": ["manual_review"],
        "requirement_line": ["manual_review"],
    }.get(requirement_type, ["manual_review"])


def structured_requirement_evidence_types(requirement_type: str, required_value: str) -> list[str]:
    if requirement_type == "required_document":
        return _find_notice_token_labels(required_value, DOCUMENT_TOKEN_GROUPS) or [required_value]
    if requirement_type == "company_type":
        return rule_candidate_evidence_types("company_type", required_value)
    if requirement_type == "license":
        return ["면허/등록/허가증"]
    if requirement_type == "region":
        return ["사업장 소재지 증빙"]
    return []


def phase3_requirement_input_from_candidate(candidate: dict) -> dict[str, Any]:
    requirement_type = candidate.get("requirement_type", "")
    required_value = clean_text(candidate.get("required_value"))
    needs_review = requirement_type in {"money", "date", "requirement_line"} or not required_value
    return {
        "requirement_input_id": f"notice_requirement:{candidate.get('id')}",
        "requirement_candidate_id": candidate.get("id"),
        "requirement_type": requirement_type,
        "label": candidate.get("label") or REQUIREMENT_TYPE_LABELS.get(requirement_type, requirement_type),
        "required_value": required_value,
        "normalized_value": candidate.get("normalized_value") or compact_match_value(required_value),
        "source_text": candidate.get("source_text", ""),
        "confidence": candidate.get("confidence", 0),
        "status": "phase3_input_candidate",
        "needs_review": needs_review,
        "related_profile_fields": structured_requirement_profile_fields(requirement_type),
        "required_evidence_types": structured_requirement_evidence_types(requirement_type, required_value),
        "comparison_strategy": "manual_review" if needs_review else "controlled_text_match",
    }


def phase3_notice_requirement_payload(conn: sqlite3.Connection, notice_id: int, force: bool = False) -> dict | None:
    candidates = ensure_notice_requirement_candidates(conn, notice_id, force=force)
    if candidates is None:
        return None
    inputs = [phase3_requirement_input_from_candidate(candidate) for candidate in candidates]
    type_counts: dict[str, int] = {}
    review_count = 0
    for item in inputs:
        type_counts[item["requirement_type"]] = type_counts.get(item["requirement_type"], 0) + 1
        if item["needs_review"]:
            review_count += 1
    return {
        "notice_id": notice_id,
        "contract_version": PHASE3_CONTRACT_VERSION,
        "requirement_count": len(inputs),
        "needs_review_count": review_count,
        "type_counts": type_counts,
        "requirements": inputs,
        "note": "Phase 3 판단 입력 후보입니다. 이 응답만으로 준비 상태를 확정하지 않습니다.",
    }


def normalize_evaluation_queries(raw_queries: Any) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    if not isinstance(raw_queries, list):
        return queries
    for index, item in enumerate(raw_queries):
        if isinstance(item, str):
            query = clean_text(item)
            expected = []
        elif isinstance(item, dict):
            query = clean_text(item.get("query"))
            expected_raw = item.get("expected_citation_candidate_ids") or []
            expected = [clean_text(value) for value in expected_raw if clean_text(value)] if isinstance(expected_raw, list) else []
        else:
            continue
        if query:
            queries.append({"id": f"q{index + 1}", "query": query, "expected_citation_candidate_ids": expected})
    return queries


def create_basis_retrieval_evaluation(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    name = clean_text(payload.get("name")) or f"검색 평가 {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}"
    queries = normalize_evaluation_queries(payload.get("queries"))
    top_k = max(1, min(parse_int(payload.get("top_k"), 5), 20))
    category = clean_text(payload.get("category"))
    document_version = clean_text(payload.get("document_version"))
    query_results: list[dict[str, Any]] = []
    top_scores: list[float] = []
    result_hits = 0
    expected_query_count = 0
    expected_citation_hits = 0

    for query_item in queries:
        results = basis_search_results(conn, query_item["query"], category, document_version, top_k)
        citation_candidate_ids = [item["citation_candidate_id"] for item in results]
        expected_ids = query_item.get("expected_citation_candidate_ids") or []
        matched_expected_ids = [candidate_id for candidate_id in expected_ids if candidate_id in citation_candidate_ids]
        missed_expected_ids = [candidate_id for candidate_id in expected_ids if candidate_id not in citation_candidate_ids]
        if results:
            result_hits += 1
            top_scores.append(float(results[0]["score"]))
        if expected_ids:
            expected_query_count += 1
            if matched_expected_ids:
                expected_citation_hits += 1
        query_results.append(
            {
                **query_item,
                "result_count": len(results),
                "result_hit": bool(results),
                "top_score": results[0]["score"] if results else 0,
                "citation_candidate_ids": citation_candidate_ids,
                "matched_expected_citation_ids": matched_expected_ids,
                "missed_expected_citation_ids": missed_expected_ids,
                "expected_citation_hit": bool(matched_expected_ids) if expected_ids else None,
                "expected_citation_coverage": round(len(matched_expected_ids) / len(expected_ids), 4) if expected_ids else None,
                "results": results,
            }
        )

    query_count = len(queries)
    result_coverage = round(result_hits / query_count, 4) if query_count else 0
    expected_citation_coverage = (
        round(expected_citation_hits / expected_query_count, 4) if expected_query_count else None
    )
    citation_coverage = expected_citation_coverage if expected_citation_coverage is not None else result_coverage
    average_top_score = round(sum(top_scores) / len(top_scores), 4) if top_scores else 0
    result = {
        "query_results": query_results,
        "metrics": {
            "result_coverage": result_coverage,
            "expected_citation_query_count": expected_query_count,
            "expected_citation_coverage": expected_citation_coverage,
            "citation_coverage": citation_coverage,
            "average_top_score": average_top_score,
        },
        "policy": "검색 결과는 JSON 기준문서 인덱스 기준 citation 후보이며, 기대 citation이 지정된 평가는 실제 citation id 일치 여부를 별도로 검증합니다.",
        "index_source": "json_basis_index",
    }
    now = now_iso()
    cur = conn.execute(
        """
        INSERT INTO basis_retrieval_evaluations (
          name, query_set_json, result_json, query_count, citation_coverage,
          average_top_score, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            json.dumps({"queries": queries, "top_k": top_k, "category": category, "document_version": document_version}, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            query_count,
            citation_coverage,
            average_top_score,
            "completed",
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM basis_retrieval_evaluations WHERE id=?", (cur.lastrowid,)).fetchone()
    return basis_retrieval_evaluation_payload(row)


def basis_retrieval_evaluation_payload(row: sqlite3.Row | dict) -> dict[str, Any]:
    payload = dict(row)
    payload["query_set"] = parse_json_dict(payload.pop("query_set_json", "{}"))
    payload["result"] = parse_json_dict(payload.pop("result_json", "{}"))
    return payload


def judgment_contract_payload() -> dict[str, Any]:
    return {
        "contract_version": PHASE3_CONTRACT_VERSION,
        "input_schema": {
            "notice_snapshot": ["id", "bid_ntce_no", "bid_ntce_ord", "bid_ntce_nm", "dates", "amounts"],
            "corporation_profile_snapshot": [
                "corporation_id",
                "regions",
                "licenses",
                "company_types",
                "required_documents",
                "approved_evidence_labels",
            ],
            "notice_requirement_inputs": [
                "requirement_input_id",
                "requirement_type",
                "required_value",
                "related_profile_fields",
                "required_evidence_types",
                "needs_review",
            ],
            "basis_citation_candidates": [
                "citation_candidate_id",
                "basis_document_id",
                "chunk_id",
                "page",
                "section",
                "score",
                "min_score",
                "meets_min_score",
            ],
        },
        "output_schema": {
            "item_statuses": list(JUDGMENT_STATUS_LABELS.keys()),
            "judgment_items": [
                "requirement_input_id",
                "match_status",
                "matched_value",
                "gap_reason",
                "recommended_action",
                "citation_status",
                "citation_candidates",
                "review_evidence_ready",
            ],
            "summary": [
                "matched_count",
                "missing_count",
                "uncertain_count",
                "needs_review_count",
                "not_applicable_count",
                "citation_coverage",
            ],
            "preparation_guide": ["required_documents", "actions", "uncertainty_notes"],
        },
        "guardrails": [
            "결과는 준비 상태와 부족 조건 중심으로 제공한다.",
            "기준 점수 미만이거나 citation 후보가 없는 조건은 검토 필요 상태로 유지한다.",
            "AI 출력은 사용자 검토 후보로만 저장한다.",
        ],
        "citation_policy": {
            "min_score": BASIS_CITATION_MIN_SCORE,
            "review_evidence_ready_requires": [
                "citation_candidate_id",
                "basis_document_id",
                "chunk_id",
                "score >= min_score",
            ],
        },
    }


def judgment_status_from_comparison(comparison: dict) -> str:
    return {
        "prepared": "matched",
        "possibly_missing": "missing",
        "not_found": "missing",
        "needs_review": "needs_review",
    }.get(comparison.get("status"), "uncertain")


def judgment_action_for_item(requirement: dict, status: str, citations: list[dict[str, Any]]) -> str:
    value = requirement.get("required_value") or requirement.get("label") or "요구조건"
    if status == "matched":
        if citations:
            return "보유 정보와 일치하는 후보가 있습니다. 기준문서 citation과 원문을 검토해 확정하세요."
        return "보유 정보는 일치하지만 기준문서 citation 후보가 부족합니다. 원문 근거를 추가 확인하세요."
    if status == "missing":
        evidence = ", ".join(requirement.get("required_evidence_types") or [])
        if evidence:
            return f"{value} 조건을 충족할 증빙({evidence})을 준비하거나 법인 프로필을 보강하세요."
        return f"{value} 조건을 충족하는 법인 정보 또는 증빙을 확인하세요."
    if status == "needs_review":
        return f"{value} 항목은 자동 비교만으로 결론을 내리기 어렵습니다. 공고 원문과 기준문서 후보를 함께 검토하세요."
    if not citations:
        return "관련 기준문서 citation 후보가 부족합니다. 기준문서 검색 품질을 먼저 보강하세요."
    return "검토가 필요한 항목입니다."


def citation_payload_from_search_result(result: dict[str, Any]) -> dict[str, Any]:
    chunk = result.get("chunk") or {}
    document = result.get("document") or {}
    try:
        score = float(result.get("score", 0) or 0)
    except (TypeError, ValueError):
        score = 0
    return {
        "citation_candidate_id": result.get("citation_candidate_id", ""),
        "score": score,
        "min_score": BASIS_CITATION_MIN_SCORE,
        "meets_min_score": score >= BASIS_CITATION_MIN_SCORE,
        "basis_document_id": document.get("id"),
        "basis_document_title": document.get("title", ""),
        "basis_document_version": document.get("document_version", ""),
        "chunk_id": chunk.get("id"),
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "section_title": chunk.get("section_title", ""),
        "text_preview": clean_text(chunk.get("chunk_text_normalized"))[:500],
        "source_type": result.get("source_type", "basis_search"),
        "basis_rule_candidate_id": result.get("basis_rule_candidate_id"),
        "basis_rule_candidate_status": result.get("basis_rule_candidate_status", ""),
        "basis_rule_candidate_rule_type": result.get("basis_rule_candidate_rule_type", ""),
    }


def citation_candidate_review_ready(candidate: dict[str, Any]) -> bool:
    try:
        score = float(candidate.get("score", 0) or 0)
    except (TypeError, ValueError):
        score = 0
    return bool(
        clean_text(candidate.get("citation_candidate_id"))
        and candidate.get("basis_document_id") is not None
        and candidate.get("chunk_id") is not None
        and score >= BASIS_CITATION_MIN_SCORE
    )


def approved_basis_rule_candidate_results(
    conn: sqlite3.Connection,
    requirement: dict[str, Any],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          rc.id AS rule_candidate_id,
          rc.basis_document_id,
          rc.basis_chunk_id,
          rc.rule_type,
          rc.condition_text,
          rc.target_scope,
          rc.required_evidence_types_json,
          rc.related_profile_fields_json,
          rc.citation_candidate_id,
          rc.confidence,
          rc.status,
          c.id AS chunk_id,
          c.chunk_index,
          c.chunk_text,
          c.chunk_text_normalized,
          c.page_start,
          c.page_end,
          c.section_title,
          c.article_label,
          c.token_count,
          c.metadata_json,
          d.id AS document_id,
          d.title,
          d.category,
          d.document_version,
          d.issuing_agency,
          d.processing_status,
          d.index_status,
          c.vector_status,
          c.vector_id
        FROM basis_rule_candidates rc
        JOIN basis_document_chunks c
          ON c.id = rc.basis_chunk_id
         AND c.basis_document_id = rc.basis_document_id
        JOIN basis_documents d ON d.id = rc.basis_document_id
        WHERE rc.status='approved'
          AND d.processing_status='completed'
          AND d.index_status='completed'
          AND c.vector_status='indexed'
          AND c.vector_id<>''
        ORDER BY rc.updated_at DESC, rc.id DESC
        """,
    ).fetchall()
    scored: list[dict[str, Any]] = []
    for row in rows:
        candidate = {
            "rule_type": row["rule_type"],
            "condition_text": row["condition_text"],
            "target_scope": row["target_scope"],
            "required_evidence_types": parse_json_list(row["required_evidence_types_json"]),
            "related_profile_fields": parse_json_list(row["related_profile_fields_json"]),
            "confidence": row["confidence"],
        }
        score = basis_rule_candidate_match_score(requirement, candidate)
        if score <= 0:
            continue
        expected_citation_id = expected_basis_citation_candidate_id(row["basis_document_id"], row["basis_chunk_id"])
        if row["citation_candidate_id"] != expected_citation_id:
            continue
        chunk = {
            "id": row["chunk_id"],
            "basis_document_id": row["basis_document_id"],
            "chunk_index": row["chunk_index"],
            "chunk_text": row["chunk_text"],
            "chunk_text_normalized": row["chunk_text_normalized"],
            "page_start": row["page_start"],
            "page_end": row["page_end"],
            "section_title": row["section_title"],
            "article_label": row["article_label"],
            "token_count": row["token_count"],
            "metadata_json": row["metadata_json"],
        }
        scored.append(
            {
                "score": score,
                "citation_candidate_id": row["citation_candidate_id"],
                "chunk": basis_chunk_payload(chunk),
                "document": {
                    "id": row["document_id"],
                    "title": row["title"],
                    "category": row["category"],
                    "document_version": row["document_version"],
                    "issuing_agency": row["issuing_agency"],
                    "processing_status": row["processing_status"],
                    "index_status": row["index_status"],
                },
                "source_type": "approved_rule_candidate",
                "basis_rule_candidate_id": row["rule_candidate_id"],
                "basis_rule_candidate_status": row["status"],
                "basis_rule_candidate_rule_type": row["rule_type"],
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[: max(1, min(top_k, 20))]


def build_judgment_run(conn: sqlite3.Connection, notice_id: int, corporation_id: int, top_k: int = 3) -> dict[str, Any] | None:
    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    corporation = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
    if not notice or not corporation:
        return None

    structured_payload = phase3_notice_requirement_payload(conn, notice_id)
    if structured_payload is None:
        return None
    requirements = structured_payload["requirements"]
    profile = build_corporation_comparison_profile(conn, corporation)
    items: list[dict[str, Any]] = []
    cited_count = 0
    required_documents: list[str] = []
    actions: list[str] = []
    uncertainty_notes: list[str] = []

    for requirement in requirements:
        candidate_for_compare = {
            "id": requirement["requirement_candidate_id"],
            "requirement_type": requirement["requirement_type"],
            "label": requirement["label"],
            "required_value": requirement["required_value"],
            "normalized_value": requirement["normalized_value"],
            "source_text": requirement["source_text"],
            "confidence": requirement["confidence"],
        }
        comparison = compare_requirement_candidate(candidate_for_compare, profile)
        match_status = judgment_status_from_comparison(comparison)
        citation_query = " ".join(
            [
                requirement.get("required_value", ""),
                requirement.get("source_text", ""),
                " ".join(requirement.get("required_evidence_types") or []),
            ]
        )
        approved_results = approved_basis_rule_candidate_results(conn, requirement, top_k=top_k)
        approved_candidates = [citation_payload_from_search_result(result) for result in approved_results]
        approved_review_ready = [candidate for candidate in approved_candidates if citation_candidate_review_ready(candidate)]
        fallback_used = not approved_review_ready
        basis_index_error = ""
        try:
            fallback_results = basis_search_results(conn, citation_query, top_k=top_k) if fallback_used else []
        except BasisIndexError as exc:
            fallback_results = []
            basis_index_error = str(exc)
        citation_results = merge_citation_results(approved_results, fallback_results, top_k)
        citation_candidates = [citation_payload_from_search_result(result) for result in citation_results]
        review_ready_citations = [candidate for candidate in citation_candidates if citation_candidate_review_ready(candidate)]
        if review_ready_citations:
            cited_count += 1
        citation_status = "candidate_found" if review_ready_citations else "weak_candidate" if citation_candidates else "missing"
        action = judgment_action_for_item(requirement, match_status, review_ready_citations)
        if match_status in {"missing", "needs_review", "uncertain"}:
            actions.append(action)
            append_unique_text(required_documents, requirement.get("required_evidence_types") or [])
        if citation_status == "missing":
            uncertainty_notes.append(f"{requirement['label']} / {requirement['required_value']}: 기준문서 citation 후보가 없습니다.")
        elif citation_status == "weak_candidate":
            uncertainty_notes.append(
                f"{requirement['label']} / {requirement['required_value']}: 기준문서 citation 후보 점수가 낮아 원문 검토가 필요합니다."
            )
        if basis_index_error:
            uncertainty_notes.append(
                f"{requirement['label']} / {requirement['required_value']}: 기준문서 인덱스 오류로 검색 citation을 사용할 수 없습니다."
            )
        item = {
            "requirement_input_id": requirement["requirement_input_id"],
            "requirement_candidate_id": requirement["requirement_candidate_id"],
            "requirement_type": requirement["requirement_type"],
            "label": requirement["label"],
            "required_value": requirement["required_value"],
            "source_text": requirement["source_text"],
            "match_status": match_status,
            "status_label": JUDGMENT_STATUS_LABELS.get(match_status, match_status),
            "matched_value": comparison.get("matched_value", ""),
            "gap_reason": comparison.get("reason", ""),
            "recommended_action": action,
            "required_evidence_types": requirement.get("required_evidence_types") or [],
            "related_profile_fields": requirement.get("related_profile_fields") or [],
            "citation_status": citation_status,
            "citation_candidates": citation_candidates,
            "review_ready_citation_candidates": review_ready_citations,
            "citation_min_score": BASIS_CITATION_MIN_SCORE,
            "review_evidence_ready": bool(review_ready_citations),
            "basis_search_fallback_used": fallback_used,
            "basis_index_error": basis_index_error,
            "approved_rule_candidate_ids": [
                candidate["basis_rule_candidate_id"]
                for candidate in citation_candidates
                if candidate.get("source_type") == "approved_rule_candidate" and candidate.get("basis_rule_candidate_id") is not None
            ],
        }
        items.append(item)

    counts = {status: 0 for status in JUDGMENT_STATUS_LABELS}
    for item in items:
        counts[item["match_status"]] = counts.get(item["match_status"], 0) + 1
    total = len(items)
    citation_coverage = round(cited_count / total, 4) if total else 0
    summary = {
        "status": "review_ready",
        "contract_version": PHASE3_CONTRACT_VERSION,
        "requirement_count": total,
        "matched_count": counts.get("matched", 0),
        "missing_count": counts.get("missing", 0),
        "uncertain_count": counts.get("uncertain", 0),
        "needs_review_count": counts.get("needs_review", 0),
        "not_applicable_count": counts.get("not_applicable", 0),
        "citation_coverage": citation_coverage,
        "note": "부족조건 중심 검토 결과입니다. 준비 상태를 확정하지 않습니다.",
    }
    result = {
        "items": items,
        "preparation_guide": {
            "required_documents": required_documents,
            "actions": _dedupe_text_items(actions),
            "uncertainty_notes": _dedupe_text_items(uncertainty_notes),
        },
    }
    input_snapshot = {
        "notice": row_to_dict(notice),
        "corporation": {"id": corporation["id"], "name": corporation["name"]},
        "corporation_profile": profile,
        "notice_requirements": requirements,
        "basis_search_top_k": top_k,
        "basis_citation_min_score": BASIS_CITATION_MIN_SCORE,
        "approved_rule_candidate_policy": "approved candidates are preferred before generic basis search; generic search is fallback",
    }
    now = now_iso()
    cur = conn.execute(
        """
        INSERT INTO judgment_runs (
          nara_notice_id, corporation_id, status, review_status, reviewer_note,
          input_snapshot_json, result_json, summary_json, matched_count,
          missing_count, uncertain_count, needs_review_count, not_applicable_count,
          citation_coverage, rule_version, created_at, updated_at
        ) VALUES (?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            notice_id,
            corporation_id,
            "completed",
            "pending",
            json.dumps(input_snapshot, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            json.dumps(summary, ensure_ascii=False),
            summary["matched_count"],
            summary["missing_count"],
            summary["uncertain_count"],
            summary["needs_review_count"],
            summary["not_applicable_count"],
            citation_coverage,
            "phase3_gap_judgment_rule_v1",
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM judgment_runs WHERE id=?", (cur.lastrowid,)).fetchone()
    return judgment_run_payload(conn, row)


def judgment_run_payload(conn: sqlite3.Connection, row: sqlite3.Row | dict) -> dict[str, Any]:
    payload = dict(row)
    payload["input_snapshot"] = parse_json_dict(payload.pop("input_snapshot_json", "{}"))
    payload["result"] = parse_json_dict(payload.pop("result_json", "{}"))
    payload["summary"] = parse_json_dict(payload.pop("summary_json", "{}"))
    notice = conn.execute("SELECT * FROM nara_notices WHERE id=?", (payload["nara_notice_id"],)).fetchone()
    corporation = conn.execute("SELECT * FROM corporations WHERE id=?", (payload["corporation_id"],)).fetchone()
    payload["notice"] = row_to_dict(notice)
    payload["corporation"] = row_to_dict(corporation)
    return payload


def save_discovered_nara_notice(conn: sqlite3.Connection, item: dict[str, Any]) -> tuple[str, int | None]:
    if not isinstance(item, dict):
        return "skipped", None
    normalized = normalize_nara_notice(item, collect_nara_attachments([item]))
    if not normalized.get("bid_ntce_no"):
        return "skipped", None
    existing = conn.execute(
        "SELECT id FROM nara_notices WHERE bid_ntce_no=? AND bid_ntce_ord=?",
        (normalized["bid_ntce_no"], normalized["bid_ntce_ord"]),
    ).fetchone()
    if existing:
        return "skipped", existing["id"]
    now = now_iso()
    cur = conn.execute(
        """
        INSERT INTO nara_notices (
          bid_ntce_no, bid_ntce_ord, bid_ntce_nm, ntce_instt_nm, dminstt_nm,
          bid_ntce_dt, bid_begin_dt, bid_clse_dt, openg_dt, presmpt_prce,
          bdgt_amt, bssamt, region_text, license_text, source_url, raw_json,
          detail_json, save_status, download_status, analysis_status,
          analysis_summary_json, analysis_summary_markdown, error_message,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}',
          'discovered', 'not_started', 'not_started', '{}', '', '', ?, ?)
        """,
        (
            normalized["bid_ntce_no"],
            normalized["bid_ntce_ord"],
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
            json.dumps(item, ensure_ascii=False),
            now,
            now,
        ),
    )
    return "saved", cur.lastrowid


def create_nara_collection_run(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    retry_of_run_id: int | None = None,
) -> tuple[dict[str, Any], int]:
    keyword = clean_text(payload.get("keyword"))
    end_default = datetime.now(KST).date()
    start_default = end_default - timedelta(days=3)
    start_date = clean_text(payload.get("start_date")) or start_default.isoformat()
    end_date = clean_text(payload.get("end_date")) or end_default.isoformat()
    dry_run = bool(payload.get("dry_run", False))
    save_discovered = bool(payload.get("save", not dry_run))
    injected_notices = payload.get("notices")
    mode = "injected" if isinstance(injected_notices, list) else "api"
    items: list[dict[str, Any]] = []
    error_message = ""
    status = "completed"
    http_code = 201

    if isinstance(injected_notices, list):
        items = [item for item in injected_notices if isinstance(item, dict)]
    elif not NARA_API_SERVICE_KEY:
        status = "not_configured"
        error_message = "NARA_API_SERVICE_KEY is missing"
    else:
        params = {
            "ServiceKey": NARA_API_SERVICE_KEY,
            "numOfRows": str(min(max(parse_int(payload.get("page_size"), 20), 1), 100)),
            "pageNo": str(max(parse_int(payload.get("page_no"), 1), 1)),
            "type": NARA_API_RESPONSE_TYPE,
            "inqryDiv": "1",
            "inqryBgnDt": date_to_api_datetime(start_date, "0000"),
            "inqryEndDt": date_to_api_datetime(end_date, "2359"),
        }
        if keyword:
            params["bidNtceNm"] = keyword
        try:
            parsed = request_nara_operation("getBidPblancListInfoCnstwkPPSSrch", params)
            items = [item for item in parsed.get("items", []) if isinstance(item, dict)]
        except Exception as exc:
            status = "failed"
            error_message = str(exc)

    saved_ids: list[int] = []
    skipped_count = 0
    save_failure_count = 0
    if status == "completed" and save_discovered:
        for item in items:
            save_status, notice_id = save_discovered_nara_notice(conn, item)
            if save_status == "saved" and notice_id:
                saved_ids.append(notice_id)
            else:
                skipped_count += 1
                normalized_for_skip = normalize_nara_notice(item, collect_nara_attachments([item]))
                if not clean_text(normalized_for_skip.get("bid_ntce_no")):
                    save_failure_count += 1
        if saved_ids and save_failure_count:
            status = "partial_failed"
            error_message = error_message or "Some discovered notices could not be saved"

    normalized_items = []
    for item in items:
        attachments = collect_nara_attachments([item])
        normalized_items.append({**normalize_nara_notice(item, attachments), "attachment_count": len(attachments)})

    result = {
        "items": normalized_items,
        "saved_notice_ids": saved_ids,
        "dry_run": dry_run,
        "counts": {
            "searched": len(items),
            "saved": len(saved_ids),
            "skipped": skipped_count,
            "save_failures": save_failure_count,
        },
        "failure_reason": error_message,
        "retryable": status in {"failed", "partial_failed", "not_configured"},
        "policy": "나라장터 자동 수집은 API 기반 모니터링만 수행하며 HTML 크롤링은 사용하지 않습니다.",
    }
    criteria = {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "dry_run": dry_run,
        "save": save_discovered,
        "mode": mode,
    }
    now = now_iso()
    cur = conn.execute(
        """
        INSERT INTO nara_collection_runs (
          status, mode, keyword, start_date, end_date, searched_count,
          saved_count, skipped_count, error_message, criteria_json,
          result_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            status,
            mode,
            keyword,
            start_date,
            end_date,
            len(items),
            len(saved_ids),
            skipped_count,
            error_message,
            json.dumps(criteria, ensure_ascii=False),
            json.dumps(result, ensure_ascii=False),
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM nara_collection_runs WHERE id=?", (cur.lastrowid,)).fetchone()
    run_payload = nara_collection_run_payload(row)
    record_operation_run(
        conn,
        operation_type="nara_collection",
        target_type="nara_collection_run",
        target_id=run_payload["id"],
        status=status,
        request_payload={**criteria, "page_size": parse_int(payload.get("page_size"), 20), "page_no": parse_int(payload.get("page_no"), 1)},
        result_payload=result,
        error_message=error_message,
        error_code=error_code_for_status(status, error_message),
        retry_of_run_id=retry_of_run_id,
        started_at=now,
        finished_at=now,
    )
    return run_payload, http_code


def nara_collection_run_payload(row: sqlite3.Row | dict) -> dict[str, Any]:
    payload = dict(row)
    payload["criteria"] = parse_json_dict(payload.pop("criteria_json", "{}"))
    payload["result"] = parse_json_dict(payload.pop("result_json", "{}"))
    return payload


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
            "business_type에는 '사업의 종류', '업태', '종목' 같은 표 라벨을 절대 넣지 마세요.",
            "business_item에는 표 라벨이나 업태값만 단독으로 넣지 말고 세부 종목만 배열로 넣으세요.",
            "예: OCR이 '업태\\n건설업\\n종목\\n전기공사,신재생에너지설비설치전문기\\n업'이면 business_type=[\"건설업\"], business_item=[\"전기공사\",\"신재생에너지설비설치전문기업\"] 입니다.",
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

    business_type_values, business_item_values = normalize_business_kind_values(
        payload.get("business_type"),
        payload.get("business_item"),
    )
    business_type_text = ", ".join(business_type_values)
    business_item_text = ", ".join(business_item_values)
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


@app.route("/api/operations/summary", methods=["GET"])
def operations_summary():
    provider = AI_PROVIDER_DEFAULT
    with db_conn() as conn:
        payload = build_operations_summary(
            conn,
            storage_root=STORAGE_ROOT,
            nara_api_configured=bool(NARA_API_SERVICE_KEY),
            nara_api_masked_key=mask_secret(NARA_API_SERVICE_KEY),
            ai_provider=provider,
            ai_model=default_model_for_provider(provider),
            ai_configured=bool(api_key_for_provider(provider)),
        )
    return jsonify(payload)


@app.route("/api/operation-runs", methods=["GET"])
def list_operation_runs():
    status = clean_text(request.args.get("status"))
    operation_type = clean_text(request.args.get("operation_type"))
    keyword = clean_text(request.args.get("keyword"))
    with db_conn() as conn:
        payload = list_operation_runs_payload(
            conn,
            status=status,
            operation_type=operation_type,
            keyword=keyword,
        )
    return jsonify(payload)


@app.route("/api/operation-runs/<int:operation_run_id>", methods=["GET"])
def get_operation_run(operation_run_id: int):
    with db_conn() as conn:
        payload = get_operation_run_payload(conn, operation_run_id)
    if not payload:
        return jsonify({"detail": "Operation run not found"}), 404
    return jsonify(payload)


@app.route("/api/operation-runs/<int:operation_run_id>/retry", methods=["POST"])
def retry_operation_run_api(operation_run_id: int):
    with db_conn() as conn:
        original = get_operation_run_payload(conn, operation_run_id)
        if not original:
            return jsonify({"detail": "Operation run not found"}), 404
        operation_type = original["operation_type"]
        request_payload = original.get("request") or {}

        if operation_type == "nara_collection":
            create_nara_collection_run(conn, request_payload, retry_of_run_id=operation_run_id)
        elif operation_type == "judgment_run":
            notice_id = parse_int(request_payload.get("nara_notice_id") or request_payload.get("notice_id"))
            corporation_id = parse_int(request_payload.get("corporation_id"))
            top_k = max(1, min(parse_int(request_payload.get("top_k"), 3), 10))
            result = build_judgment_run(conn, notice_id, corporation_id, top_k=top_k)
            if not result:
                return jsonify({"detail": "Saved notice or corporation not found"}), 404
            record_operation_run(
                conn,
                operation_type="judgment_run",
                target_type="judgment_run",
                target_id=result["id"],
                status=result["status"],
                request_payload={"nara_notice_id": notice_id, "corporation_id": corporation_id, "top_k": top_k},
                result_payload={"summary": result.get("summary", {})},
                retry_of_run_id=operation_run_id,
                started_at=result["created_at"],
                finished_at=result["updated_at"],
            )
        elif operation_type == "basis_document_processing":
            basis_document_id = parse_int(request_payload.get("basis_document_id") or original.get("target_id"))
            row = conn.execute("SELECT id FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
            if not row:
                return jsonify({"detail": "Basis document not found"}), 404
            result = process_basis_document(conn, basis_document_id)
            status = "completed" if result.get("processing_status") == "completed" else result.get("processing_status", "failed")
            record_operation_run(
                conn,
                operation_type="basis_document_processing",
                target_type="basis_document",
                target_id=basis_document_id,
                status=status,
                request_payload={"basis_document_id": basis_document_id, "action": "reprocess"},
                result_payload={
                    "processing_status": result.get("processing_status"),
                    "chunk_count": result.get("chunk_count"),
                    "vector_count": result.get("vector_count"),
                },
                error_message=result.get("error_message", ""),
                error_code=error_code_for_status(status, result.get("error_message", "")),
                retry_of_run_id=operation_run_id,
                started_at=result.get("updated_at"),
                finished_at=result.get("updated_at"),
            )
        elif operation_type == "basis_rule_candidate_extraction":
            basis_document_id = parse_int(request_payload.get("basis_document_id") or original.get("target_id"))
            result = extract_basis_rule_candidates(conn, basis_document_id)
            if not result:
                return jsonify({"detail": "Basis document not found"}), 404
            status = "failed" if result.get("status") == "basis_not_ready" else "completed"
            record_operation_run(
                conn,
                operation_type="basis_rule_candidate_extraction",
                target_type="basis_document",
                target_id=basis_document_id,
                status=status,
                request_payload={"basis_document_id": basis_document_id, "action": "extract_rule_candidates"},
                result_payload={"candidate_count": result.get("candidate_count", 0), "status": result.get("status", "")},
                error_message=result.get("detail", "") if status == "failed" else "",
                error_code="basis_not_ready" if status == "failed" else "",
                retry_of_run_id=operation_run_id,
            )
        else:
            return jsonify({"detail": "This operation type is not retryable"}), 400

        retried = conn.execute(
            "SELECT * FROM operation_runs WHERE retry_of_run_id=? ORDER BY id DESC LIMIT 1",
            (operation_run_id,),
        ).fetchone()
        payload = get_operation_run_payload(conn, retried["id"]) if retried else None
    return jsonify(payload), 201


def _resolve_allowed_backup_file_path(raw_path: str) -> Path | None:
    backup_root = (STORAGE_ROOT / "backups").resolve()
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = backup_root / candidate.name if len(candidate.parts) == 1 else STORAGE_ROOT / candidate
    resolved = candidate.resolve()
    if resolved.suffix.lower() != ".zip":
        return None
    if not resolved.is_relative_to(backup_root):
        return None
    return resolved


def _backup_path_from_payload(conn: sqlite3.Connection, payload: dict[str, Any]) -> Path | None:
    backup_id = parse_int(payload.get("backup_id"), 0)
    if backup_id:
        backup = get_backup_run_payload(conn, backup_id)
        if not backup:
            return None
        raw_backup_path = clean_text(backup.get("file_path"))
        return _resolve_allowed_backup_file_path(raw_backup_path) if raw_backup_path else None
    raw_path = clean_text(payload.get("file_path"))
    return _resolve_allowed_backup_file_path(raw_path) if raw_path else None


@app.route("/api/backups", methods=["GET"])
def list_backups():
    with db_conn() as conn:
        payload = list_backup_runs_payload(conn)
    return jsonify(payload)


@app.route("/api/backups", methods=["POST"])
def create_backup_api():
    with db_conn() as conn:
        payload = create_backup_run(conn, sqlite_path=SQLITE_PATH, storage_root=STORAGE_ROOT)
        record_operation_run(
            conn,
            operation_type="backup_create",
            target_type="backup_run",
            target_id=payload["id"],
            status=payload["status"],
            request_payload={"backup_type": payload["backup_type"]},
            result_payload={
                "file_name": payload["file_name"],
                "file_size_bytes": payload["file_size_bytes"],
                "validation": payload.get("validation", {}),
            },
            error_message=payload.get("error_message", ""),
            error_code=error_code_for_status(payload["status"], payload.get("error_message", "")),
            started_at=payload["created_at"],
            finished_at=payload.get("completed_at") or payload["updated_at"],
        )
    return jsonify(payload), 201


@app.route("/api/backups/<int:backup_id>", methods=["GET"])
def get_backup(backup_id: int):
    with db_conn() as conn:
        payload = get_backup_run_payload(conn, backup_id)
    if not payload:
        return jsonify({"detail": "Backup not found"}), 404
    return jsonify(payload)


@app.route("/api/backups/validate", methods=["POST"])
def validate_backup_api():
    payload = get_json_payload()
    with db_conn() as conn:
        backup_path = _backup_path_from_payload(conn, payload)
    if not backup_path:
        return jsonify({"detail": "backup_id or file_path is required"}), 400
    return jsonify(validate_backup_file(backup_path))


@app.route("/api/backups/restore-plan", methods=["POST"])
def backup_restore_plan_api():
    payload = get_json_payload()
    with db_conn() as conn:
        backup_path = _backup_path_from_payload(conn, payload)
        if not backup_path:
            return jsonify({"detail": "backup_id or file_path is required"}), 400
        plan = restore_plan_for_backup(backup_path)
        record_operation_run(
            conn,
            operation_type="backup_restore",
            target_type="backup_file",
            target_id=parse_int(payload.get("backup_id"), 0) or None,
            status="completed" if plan["can_restore"] else "failed",
            request_payload={"backup_id": payload.get("backup_id"), "file_path": str(backup_path), "dry_run": True},
            result_payload=plan,
            error_message="; ".join(plan["validation"].get("errors", [])),
            error_code="" if plan["can_restore"] else "validation_error",
        )
    return jsonify(plan)


@app.route("/api/backups/<int:backup_id>/restore", methods=["POST"])
def backup_restore_api(backup_id: int):
    payload = get_json_payload()
    if payload.get("dry_run", True) is False:
        return jsonify({"detail": "Direct restore is not enabled in Phase 4D. Run restore dry-run first."}), 400
    with db_conn() as conn:
        backup = get_backup_run_payload(conn, backup_id)
        if not backup:
            return jsonify({"detail": "Backup not found"}), 404
        backup_path = _resolve_allowed_backup_file_path(clean_text(backup.get("file_path")))
        if not backup_path:
            return jsonify({"detail": "Backup file path is outside the allowed backup directory"}), 400
        plan = restore_plan_for_backup(backup_path)
        record_operation_run(
            conn,
            operation_type="backup_restore",
            target_type="backup_run",
            target_id=backup_id,
            status="completed" if plan["can_restore"] else "failed",
            request_payload={"backup_id": backup_id, "dry_run": True},
            result_payload=plan,
            error_message="; ".join(plan["validation"].get("errors", [])),
            error_code="" if plan["can_restore"] else "validation_error",
        )
    return jsonify(plan)


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
        if set(updates) & COMPARISON_AFFECTING_CORPORATION_FIELDS:
            invalidate_corporation_comparisons(conn, corporation_id)
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

        invalidate_corporation_comparisons(conn, corporation_id)
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
            invalidate_corporation_comparisons(conn, evidence["corporation_id"])
            invalidate_corporation_comparisons(conn, update_values["corporation_id"])
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
        invalidate_corporation_comparisons(conn, evidence["corporation_id"])
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
        invalidate_corporation_comparisons(conn, evidence["corporation_id"])
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
        invalidate_corporation_comparisons(conn, corporation_id)
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
        invalidate_corporation_comparisons(conn, evidence["corporation_id"])
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


@app.route("/api/basis-documents", methods=["GET"])
def list_basis_documents():
    keyword = clean_text(request.args.get("keyword")).lower()
    category = clean_text(request.args.get("category"))
    clauses: list[str] = []
    params: list[Any] = []
    if keyword:
        clauses.append("(LOWER(title) LIKE ? OR LOWER(original_file_name) LIKE ? OR LOWER(memo) LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like, like])
    if category:
        clauses.append("category=?")
        params.append(category)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with db_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM basis_documents {where} ORDER BY id DESC",
            tuple(params),
        ).fetchall()
        payload = [basis_document_payload(conn, row) for row in rows]
    return jsonify(payload)


@app.route("/api/basis-documents", methods=["POST"])
def upload_basis_document():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"detail": "file is required"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in BASIS_ALLOWED_EXTENSIONS:
        return jsonify({"detail": "Only PDF basis documents are supported"}), 400

    title = clean_text(request.form.get("title")) or Path(file.filename).stem
    category = clean_text(request.form.get("category"))
    document_version = clean_text(request.form.get("document_version"))
    issuing_agency = clean_text(request.form.get("issuing_agency"))
    effective_date = clean_text(request.form.get("effective_date"))
    source_url = clean_text(request.form.get("source_url"))
    memo = clean_text(request.form.get("memo"))

    target_dir = STORAGE_ROOT / "basis"
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / f"{uuid.uuid4().hex}{ext}"
    file.save(stored_path)
    file_size = stored_path.stat().st_size
    file_hash = file_sha256(stored_path)
    now = now_iso()

    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO basis_documents (
              title, category, document_version, issuing_agency, effective_date,
              source_url, original_file_name, stored_file_path, mime_type,
              file_size, file_hash, memo, processing_status, parse_status,
              ocr_status, chunk_status, index_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'pending',
              'pending', 'pending', 'pending', ?, ?)
            """,
            (
                title,
                category,
                document_version,
                issuing_agency,
                effective_date,
                source_url,
                file.filename,
                str(stored_path),
                file.mimetype or mimetypes.guess_type(file.filename)[0] or "",
                file_size,
                file_hash,
                memo,
                now,
                now,
            ),
        )
        basis_document_id = cur.lastrowid
        payload = process_basis_document(conn, basis_document_id)
    return jsonify(payload), 201


@app.route("/api/basis-documents/<int:basis_document_id>", methods=["GET"])
def get_basis_document(basis_document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis document not found"}), 404
        payload = basis_document_payload(conn, row, include_chunks=True)
    return jsonify(payload)


@app.route("/api/basis-documents/<int:basis_document_id>", methods=["PATCH"])
def update_basis_document(basis_document_id: int):
    payload = get_json_payload()
    allowed_fields = {
        "title": clean_text,
        "category": clean_text,
        "document_version": clean_text,
        "issuing_agency": clean_text,
        "effective_date": clean_text,
        "source_url": clean_text,
        "memo": clean_text,
    }
    updates = {field: converter(payload[field]) for field, converter in allowed_fields.items() if field in payload}
    if "title" in updates and not updates["title"]:
        return jsonify({"detail": "title is required"}), 400
    if not updates:
        return jsonify({"detail": "No supported fields to update"}), 400

    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{field}=?" for field in updates)
    values = tuple(updates.values()) + (basis_document_id,)

    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis document not found"}), 404
        conn.execute(f"UPDATE basis_documents SET {assignments} WHERE id=?", values)
        updated = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        payload = basis_document_payload(conn, updated)
    return jsonify(payload)


@app.route("/api/basis-documents/<int:basis_document_id>/reprocess", methods=["POST"])
def reprocess_basis_document(basis_document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis document not found"}), 404
        payload = process_basis_document(conn, basis_document_id)
        status = "completed" if payload.get("processing_status") == "completed" else payload.get("processing_status", "failed")
        record_operation_run(
            conn,
            operation_type="basis_document_processing",
            target_type="basis_document",
            target_id=basis_document_id,
            status=status,
            request_payload={"basis_document_id": basis_document_id, "action": "reprocess"},
            result_payload={
                "processing_status": payload.get("processing_status"),
                "chunk_count": payload.get("chunk_count"),
                "vector_count": payload.get("vector_count"),
            },
            error_message=payload.get("error_message", ""),
            error_code=error_code_for_status(status, payload.get("error_message", "")),
            started_at=payload.get("updated_at"),
            finished_at=payload.get("updated_at"),
        )
    return jsonify(payload)


@app.route("/api/basis-documents/<int:basis_document_id>/chunks", methods=["GET"])
def list_basis_document_chunks(basis_document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT id FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis document not found"}), 404
        chunks = conn.execute(
            """
            SELECT * FROM basis_document_chunks
            WHERE basis_document_id=?
            ORDER BY chunk_index
            """,
            (basis_document_id,),
        ).fetchall()
    return jsonify([basis_chunk_payload(chunk) for chunk in chunks])


@app.route("/api/basis-documents/<int:basis_document_id>", methods=["DELETE"])
def delete_basis_document(basis_document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis document not found"}), 404
        index_validation = validate_basis_index(conn)
        if index_validation.get("rebuild_required"):
            errors = list(index_validation.get("errors") or [])
            detail = "; ".join(errors) or "Basis index rebuild is required before deleting basis documents."
            return (
                jsonify(
                    {
                        "detail": detail,
                        "status": "basis_index_unavailable",
                        "index_status": index_validation.get("status", "unknown"),
                        "rebuild_required": True,
                        "errors": errors,
                    }
                ),
                409,
            )
        try:
            delete_basis_vectors(conn, basis_document_id)
        except BasisIndexError as exc:
            return (
                jsonify(
                    {
                        "detail": str(exc),
                        "status": "basis_index_unavailable",
                        "rebuild_required": True,
                    }
                ),
                409,
            )
        safe_unlink(Path(row["stored_file_path"]))
        conn.execute("DELETE FROM basis_rule_candidates WHERE basis_document_id=?", (basis_document_id,))
        conn.execute("DELETE FROM basis_document_chunks WHERE basis_document_id=?", (basis_document_id,))
        conn.execute("DELETE FROM basis_documents WHERE id=?", (basis_document_id,))
    return jsonify({"status": "deleted"})


@app.route("/api/basis-search", methods=["POST"])
def search_basis_documents():
    payload = get_json_payload()
    query = clean_text(payload.get("query"))
    if not query:
        return jsonify({"detail": "query is required"}), 400
    category = clean_text(payload.get("category"))
    document_version = clean_text(payload.get("document_version"))
    top_k = parse_int(payload.get("top_k"), 5)
    with db_conn() as conn:
        try:
            results = basis_search_results(conn, query, category, document_version, top_k)
        except BasisIndexError as exc:
            return (
                jsonify(
                    {
                        "detail": str(exc),
                        "status": "basis_index_unavailable",
                        "rebuild_required": True,
                    }
                ),
                409,
            )
    return jsonify(
        {
            "query": query,
            "top_k": max(1, min(top_k, 20)),
            "result_count": len(results),
            "results": results,
            "index_source": "json_basis_index",
            "note": "Phase 2 search returns reusable chunk candidates only, not eligibility judgments.",
        }
    )


@app.route("/api/basis-index/status", methods=["GET"])
def get_basis_index_status():
    with db_conn() as conn:
        payload = basis_index_status_payload(conn)
    return jsonify(payload)


@app.route("/api/basis-index/validate", methods=["POST"])
def validate_basis_index_api():
    with db_conn() as conn:
        payload = basis_index_status_payload(conn)
    return jsonify(payload)


@app.route("/api/basis-index/rebuild", methods=["POST"])
def rebuild_basis_index_api():
    with db_conn() as conn:
        payload = rebuild_basis_index(conn)
        record_operation_run(
            conn,
            operation_type="basis_index_rebuild",
            target_type="basis_index",
            status="completed" if payload.get("valid") else "failed",
            request_payload={"action": "rebuild_basis_index"},
            result_payload=payload,
            error_message="; ".join(payload.get("errors", [])),
            error_code="" if payload.get("valid") else "validation_error",
        )
    return jsonify(payload)


@app.route("/api/qa/phase2-closeout", methods=["GET"])
def get_phase2_closeout_summary():
    return jsonify(phase2_closeout_summary())


@app.route("/api/basis-documents/<int:basis_document_id>/rule-candidates", methods=["GET"])
def get_basis_document_rule_candidates(basis_document_id: int):
    with db_conn() as conn:
        basis = conn.execute("SELECT id FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not basis:
            return jsonify({"detail": "Basis document not found"}), 404
        candidates = list_basis_rule_candidates_payload(conn, basis_document_id=basis_document_id)
    return jsonify(
        {
            "basis_document_id": basis_document_id,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "note": "기준문서 규칙 후보이며 관리자 검토 전에는 판단 근거로 확정하지 않습니다.",
        }
    )


@app.route("/api/basis-documents/<int:basis_document_id>/rule-candidates/extract", methods=["POST"])
def extract_basis_document_rule_candidates(basis_document_id: int):
    with db_conn() as conn:
        payload = extract_basis_rule_candidates(conn, basis_document_id)
        if payload:
            operation_status = "failed" if payload.get("status") == "basis_not_ready" else "completed"
            record_operation_run(
                conn,
                operation_type="basis_rule_candidate_extraction",
                target_type="basis_document",
                target_id=basis_document_id,
                status=operation_status,
                request_payload={"basis_document_id": basis_document_id, "action": "extract_rule_candidates"},
                result_payload={"candidate_count": payload.get("candidate_count", 0), "status": payload.get("status", "")},
                error_message=payload.get("detail", "") if operation_status == "failed" else "",
                error_code="basis_not_ready" if operation_status == "failed" else "",
            )
    if not payload:
        return jsonify({"detail": "Basis document not found"}), 404
    if payload.get("status") == "basis_not_ready":
        return jsonify(payload), 409
    return jsonify(payload)


@app.route("/api/basis-rule-candidates", methods=["GET"])
def list_basis_rule_candidates():
    status = clean_text(request.args.get("status"))
    basis_document_id = parse_int(request.args.get("basis_document_id"), 0)
    rule_type = clean_text(request.args.get("rule_type"))
    keyword = clean_text(request.args.get("keyword"))
    with db_conn() as conn:
        candidates = list_basis_rule_candidates_payload(
            conn,
            basis_document_id=basis_document_id or None,
            status=status,
            rule_type=rule_type,
            keyword=keyword,
        )
    return jsonify({"candidate_count": len(candidates), "candidates": candidates})


@app.route("/api/basis-rule-candidates/<int:candidate_id>", methods=["GET"])
def get_basis_rule_candidate(candidate_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_rule_candidates WHERE id=?", (candidate_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Basis rule candidate not found"}), 404
        payload = basis_rule_candidate_detail_payload(conn, row)
    return jsonify(payload)


@app.route("/api/basis-rule-candidates/<int:candidate_id>", methods=["PATCH"])
def patch_basis_rule_candidate(candidate_id: int):
    payload = get_json_payload()
    with db_conn() as conn:
        updated, error = update_basis_rule_candidate(conn, candidate_id, payload)
    if error == "not_found":
        return jsonify({"detail": "Basis rule candidate not found"}), 404
    if error:
        return jsonify({"detail": error}), 400
    return jsonify(updated)


@app.route("/api/basis-rule-candidates/<int:candidate_id>/approve", methods=["POST"])
def approve_basis_rule_candidate(candidate_id: int):
    payload = get_json_payload()
    with db_conn() as conn:
        updated, error = update_basis_rule_candidate(conn, candidate_id, payload, forced_status="approved")
    if error == "not_found":
        return jsonify({"detail": "Basis rule candidate not found"}), 404
    if error:
        return jsonify({"detail": error}), 400
    return jsonify(updated)


@app.route("/api/basis-rule-candidates/<int:candidate_id>/reject", methods=["POST"])
def reject_basis_rule_candidate(candidate_id: int):
    payload = get_json_payload()
    with db_conn() as conn:
        updated, error = update_basis_rule_candidate(conn, candidate_id, payload, forced_status="rejected")
    if error == "not_found":
        return jsonify({"detail": "Basis rule candidate not found"}), 404
    if error:
        return jsonify({"detail": error}), 400
    return jsonify(updated)


@app.route("/api/basis-retrieval-evaluations", methods=["GET"])
def list_basis_retrieval_evaluations():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM basis_retrieval_evaluations ORDER BY id DESC").fetchall()
    return jsonify([basis_retrieval_evaluation_payload(row) for row in rows])


@app.route("/api/basis-retrieval-evaluations", methods=["POST"])
def create_basis_retrieval_evaluation_api():
    payload = get_json_payload()
    if not normalize_evaluation_queries(payload.get("queries")):
        return jsonify({"detail": "queries must include at least one query"}), 400
    with db_conn() as conn:
        try:
            result = create_basis_retrieval_evaluation(conn, payload)
        except BasisIndexError as exc:
            return (
                jsonify(
                    {
                        "detail": str(exc),
                        "status": "basis_index_unavailable",
                        "rebuild_required": True,
                    }
                ),
                409,
            )
    return jsonify(result), 201


@app.route("/api/basis-retrieval-evaluations/<int:evaluation_id>", methods=["GET"])
def get_basis_retrieval_evaluation(evaluation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM basis_retrieval_evaluations WHERE id=?", (evaluation_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Retrieval evaluation not found"}), 404
    return jsonify(basis_retrieval_evaluation_payload(row))


@app.route("/api/judgment-contract", methods=["GET"])
def get_judgment_contract():
    return jsonify(judgment_contract_payload())


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
        previous_has_results = False
        if existing:
            previous_attachment_count = conn.execute(
                "SELECT COUNT(*) FROM nara_notice_attachments WHERE nara_notice_id=?",
                (existing["id"],),
            ).fetchone()[0]
            previous_requirement_count = conn.execute(
                "SELECT COUNT(*) FROM notice_requirement_candidates WHERE nara_notice_id=?",
                (existing["id"],),
            ).fetchone()[0]
            previous_has_results = bool(
                previous_attachment_count
                or previous_requirement_count
                or clean_text(existing["analysis_summary_markdown"])
                or clean_text(existing["analysis_summary_json"]) not in {"", "{}"}
            )

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
        attachment_records: list[tuple[Any, ...]] = []
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

            attachment_records.append(
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
                )
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

        preserve_existing_reason = ""
        if previous_has_results and supported_count == 0:
            analysis_status = "partial_failed"
            preserve_existing_reason = "재분석에서 지원 가능한 첨부가 없어 기존 분석 결과를 유지했습니다."
        elif failed_count:
            analysis_status = "partial_failed"
            preserve_existing_reason = "재분석이 부분 실패하여 기존 분석 결과를 유지했습니다." if previous_has_results else ""
        else:
            analysis_status = "completed"

        replace_existing_results = not previous_has_results or not preserve_existing_reason
        if replace_existing_results:
            clear_nara_notice_attachments(conn, notice_id)
            conn.execute("DELETE FROM notice_requirement_candidates WHERE nara_notice_id=?", (notice_id,))
            conn.execute("DELETE FROM notice_corporation_comparisons WHERE nara_notice_id=?", (notice_id,))
            conn.execute("DELETE FROM judgment_runs WHERE nara_notice_id=?", (notice_id,))
            conn.executemany(
                """
                INSERT INTO nara_notice_attachments (
                  nara_notice_id, file_name, source_url, source_field, file_extension,
                  support_status, download_status, stored_file_path, file_size,
                  parse_status, analysis_status, extracted_text_preview, error_message,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                attachment_records,
            )
            store_notice_requirement_candidates(conn, notice_id, notice_requirements)
            conn.execute(
                """
                UPDATE nara_notices SET
                  save_status=?, download_status=?, analysis_status=?,
                  analysis_summary_json=?, analysis_summary_markdown=?, error_message='', updated_at=?
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
        else:
            for attachment_record in attachment_records:
                stored_file_path = clean_text(attachment_record[7])
                if stored_file_path:
                    safe_unlink(Path(stored_file_path))
            conn.execute(
                """
                UPDATE nara_notices SET
                  download_status=?, analysis_status=?, error_message=?, updated_at=?
                WHERE id=?
                """,
                (
                    download_status,
                    analysis_status,
                    preserve_existing_reason,
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


@app.route("/api/nara/saved-notices/<int:notice_id>/requirements", methods=["GET"])
def get_saved_nara_notice_requirements(notice_id: int):
    force = clean_text(request.args.get("force")).lower() in {"1", "true", "yes"}
    with db_conn() as conn:
        payload = notice_requirement_payload(conn, notice_id, force=force)
    if not payload:
        return jsonify({"detail": "Saved notice not found"}), 404
    return jsonify(payload)


@app.route("/api/nara/saved-notices/<int:notice_id>/requirements/extract", methods=["POST"])
def extract_saved_nara_notice_requirements(notice_id: int):
    with db_conn() as conn:
        payload = notice_requirement_payload(conn, notice_id, force=True)
    if not payload:
        return jsonify({"detail": "Saved notice not found"}), 404
    return jsonify(payload)


@app.route("/api/nara/saved-notices/<int:notice_id>/requirements/structured", methods=["GET"])
def get_saved_nara_notice_structured_requirements(notice_id: int):
    force = clean_text(request.args.get("force")).lower() in {"1", "true", "yes"}
    with db_conn() as conn:
        payload = phase3_notice_requirement_payload(conn, notice_id, force=force)
    if not payload:
        return jsonify({"detail": "Saved notice not found"}), 404
    return jsonify(payload)


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
        conn.execute("DELETE FROM notice_corporation_comparisons WHERE nara_notice_id=?", (notice_id,))
        conn.execute("DELETE FROM judgment_runs WHERE nara_notice_id=?", (notice_id,))
        conn.execute("DELETE FROM notice_requirement_candidates WHERE nara_notice_id=?", (notice_id,))
        clear_nara_notice_attachments(conn, notice_id)
        conn.execute("DELETE FROM nara_notices WHERE id=?", (notice_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/corporations/<int:corporation_id>/comparison-profile", methods=["GET"])
def get_corporation_comparison_profile(corporation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Corporation not found"}), 404
        payload = build_corporation_comparison_profile(conn, row)
    return jsonify(payload)


@app.route("/api/notice-comparisons", methods=["GET"])
def list_notice_comparisons():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM notice_corporation_comparisons ORDER BY id DESC").fetchall()
        payload = [comparison_row_payload(conn, row) for row in rows]
    return jsonify(payload)


@app.route("/api/notice-comparisons", methods=["POST"])
def create_notice_comparison():
    payload = get_json_payload()
    notice_id = parse_int(payload.get("nara_notice_id") or payload.get("notice_id"))
    corporation_id = parse_int(payload.get("corporation_id"))
    if not notice_id or not corporation_id:
        return jsonify({"detail": "nara_notice_id and corporation_id are required"}), 400

    with db_conn() as conn:
        comparison = build_notice_corporation_comparison(conn, notice_id, corporation_id)
    if not comparison:
        return jsonify({"detail": "Saved notice or corporation not found"}), 404
    return jsonify(comparison), 201


@app.route("/api/notice-comparisons/<int:comparison_id>", methods=["GET"])
def get_notice_comparison(comparison_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM notice_corporation_comparisons WHERE id=?", (comparison_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Comparison not found"}), 404
        payload = comparison_row_payload(conn, row)
    return jsonify(payload)


@app.route("/api/nara/saved-notices/<int:notice_id>/comparisons", methods=["GET"])
def list_notice_comparisons_by_notice(notice_id: int):
    with db_conn() as conn:
        notice = conn.execute("SELECT id FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
        if not notice:
            return jsonify({"detail": "Saved notice not found"}), 404
        rows = conn.execute(
            "SELECT * FROM notice_corporation_comparisons WHERE nara_notice_id=? ORDER BY id DESC",
            (notice_id,),
        ).fetchall()
        payload = [comparison_row_payload(conn, row) for row in rows]
    return jsonify(payload)


@app.route("/api/judgment-runs", methods=["GET"])
def list_judgment_runs():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM judgment_runs ORDER BY id DESC").fetchall()
        payload = [judgment_run_payload(conn, row) for row in rows]
    return jsonify(payload)


@app.route("/api/judgment-runs", methods=["POST"])
def create_judgment_run():
    payload = get_json_payload()
    notice_id = parse_int(payload.get("nara_notice_id") or payload.get("notice_id"))
    corporation_id = parse_int(payload.get("corporation_id"))
    top_k = max(1, min(parse_int(payload.get("top_k"), 3), 10))
    if not notice_id or not corporation_id:
        return jsonify({"detail": "nara_notice_id and corporation_id are required"}), 400
    with db_conn() as conn:
        result = build_judgment_run(conn, notice_id, corporation_id, top_k=top_k)
        if result:
            record_operation_run(
                conn,
                operation_type="judgment_run",
                target_type="judgment_run",
                target_id=result["id"],
                status=result["status"],
                request_payload={"nara_notice_id": notice_id, "corporation_id": corporation_id, "top_k": top_k},
                result_payload={"summary": result.get("summary", {})},
                error_message="",
                error_code="",
                started_at=result["created_at"],
                finished_at=result["updated_at"],
            )
    if not result:
        return jsonify({"detail": "Saved notice or corporation not found"}), 404
    return jsonify(result), 201


@app.route("/api/judgment-runs/<int:judgment_run_id>", methods=["GET"])
def get_judgment_run(judgment_run_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM judgment_runs WHERE id=?", (judgment_run_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Judgment run not found"}), 404
        payload = judgment_run_payload(conn, row)
    return jsonify(payload)


@app.route("/api/judgment-runs/<int:judgment_run_id>/review", methods=["PATCH"])
def update_judgment_run_review(judgment_run_id: int):
    payload = get_json_payload()
    review_status = clean_text(payload.get("review_status"), "pending")
    reviewer_note = clean_text(payload.get("reviewer_note"))
    if review_status not in {"pending", "reviewed", "needs_followup", "archived"}:
        return jsonify({"detail": "Unsupported review_status"}), 400
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM judgment_runs WHERE id=?", (judgment_run_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Judgment run not found"}), 404
        conn.execute(
            """
            UPDATE judgment_runs
            SET review_status=?, reviewer_note=?, updated_at=?
            WHERE id=?
            """,
            (review_status, reviewer_note, now_iso(), judgment_run_id),
        )
        updated = conn.execute("SELECT * FROM judgment_runs WHERE id=?", (judgment_run_id,)).fetchone()
        payload = judgment_run_payload(conn, updated)
    return jsonify(payload)


@app.route("/api/nara/collection-runs", methods=["GET"])
def list_nara_collection_runs():
    status = clean_text(request.args.get("status"))
    keyword = clean_text(request.args.get("keyword"))
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    if keyword:
        clauses.append("(keyword LIKE ? OR error_message LIKE ? OR criteria_json LIKE ? OR result_json LIKE ?)")
        like_value = f"%{keyword}%"
        params.extend([like_value, like_value, like_value, like_value])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with db_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM nara_collection_runs {where} ORDER BY id DESC",
            tuple(params),
        ).fetchall()
    return jsonify([nara_collection_run_payload(row) for row in rows])


@app.route("/api/nara/collection-runs", methods=["POST"])
def create_nara_collection_run_api():
    payload = get_json_payload()
    with db_conn() as conn:
        result, code = create_nara_collection_run(conn, payload)
    return jsonify(result), code


@app.route("/api/nara/collection-runs/<int:collection_run_id>", methods=["GET"])
def get_nara_collection_run(collection_run_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM nara_collection_runs WHERE id=?", (collection_run_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Nara collection run not found"}), 404
    return jsonify(nara_collection_run_payload(row))


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
            body = decode_http_body(response.read(), response.headers.get_content_charset())
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
