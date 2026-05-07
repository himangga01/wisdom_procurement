import hashlib
import json
import mimetypes
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_PRIMARY = os.getenv("OPENAI_MODEL_PRIMARY", "gpt-5.1")
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
UNSUPPORTED_NARA_EXTENSIONS = {".hwp", ".hwpx", ".xlsx", ".xls", ".zip"}
NARA_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
KST = timezone(timedelta(hours=9))

app = Flask(__name__)
CORS(app)

SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
GLOBAL_CONN = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
GLOBAL_CONN.row_factory = sqlite3.Row


def db_conn() -> sqlite3.Connection:
    return GLOBAL_CONN


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json_payload() -> dict:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def clean_text(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def parse_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "uploads").mkdir(parents=True, exist_ok=True)

    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS corporations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
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
                model_provider TEXT DEFAULT 'openai',
                model_name TEXT DEFAULT 'gpt-5.1',
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


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def one_or_404(conn: sqlite3.Connection, query: str, params: tuple):
    row = conn.execute(query, params).fetchone()
    if not row:
        return None, (jsonify({"detail": "Not found"}), 404)
    return row, None


def extract_text(file_path: Path) -> str:
    return extract_document(file_path).text


def summarize_with_fallback(text: str) -> tuple[dict, str, dict]:
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

    markdown = "\n".join(
        [
            "## 문서 요약",
            payload["document_summary"],
            "",
            "## 요구사항",
            *[f"- {x}" for x in payload["requirements"]],
            "",
            f"신뢰도 메모: {payload['confidence_note']}",
        ]
    )
    usage = {"provider": "fallback", "input_chars": len(text)}
    return payload, markdown, usage


def summarize_with_openai(text: str) -> tuple[dict, str, dict]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=OPENAI_MODEL_PRIMARY,
        input=[
            {
                "role": "system",
                "content": "You are a Korean procurement summary assistant. Return strict JSON only.",
            },
            {"role": "user", "content": text[:120000]},
        ],
        text={"format": {"type": "json_object"}},
    )
    payload = json.loads(resp.output_text)
    markdown = "## 문서 요약\n" + payload.get("document_summary", "")
    usage = {"provider": "openai", "model": OPENAI_MODEL_PRIMARY, "input_chars": len(text)}
    return payload, markdown, usage


def run_analysis(document_id: int, force: bool = False) -> tuple[dict, int]:
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

        text = parsed.text
        ocr_status = "needs_ocr" if parsed.metadata.get("needs_ocr") else "skipped"
        input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        cache_model_name = OPENAI_MODEL_PRIMARY if OPENAI_API_KEY else "local"

        if not force:
            cached = conn.execute(
                """
                SELECT * FROM analyses
                WHERE project_document_id=? AND input_hash=? AND model_name=? AND prompt_version='v1'
                ORDER BY id DESC LIMIT 1
                """,
                (document_id, input_hash, cache_model_name),
            ).fetchone()
            if cached:
                conn.execute(
                    "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
                    ("completed", ocr_status, "cached", cached["id"], now_iso(), document_id),
                )
                conn.commit()
                return {"analysis_id": cached["id"], "status": "cached", "message": "Analysis reused from cache"}, 200

        if OPENAI_API_KEY:
            try:
                output_json, output_md, usage = summarize_with_openai(text)
            except Exception as exc:
                output_json, output_md, usage = summarize_with_fallback(text)
                usage["fallback_reason"] = str(exc)
        else:
            output_json, output_md, usage = summarize_with_fallback(text)

        usage["extraction"] = parsed.metadata
        model_provider = usage.get("provider", "fallback")
        model_name = usage.get("model", OPENAI_MODEL_PRIMARY if model_provider == "openai" else "local")

        cur = conn.execute(
            """
            INSERT INTO analyses (
              project_document_id, analysis_type, model_provider, model_name, prompt_version,
              input_hash, output_json, output_markdown, token_usage_json, status, error_message, created_at
            ) VALUES (?, 'summary', ?, ?, 'v1', ?, ?, ?, ?, 'completed', '', ?)
            """,
            (
                document_id,
                model_provider,
                model_name,
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

    now = now_iso()
    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO corporations (
              name, business_category, region, certifications_json, company_size_classification,
              internal_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                clean_text(payload.get("business_category")),
                clean_text(payload.get("region")),
                normalize_certifications(payload.get("certifications_json")),
                clean_text(payload.get("company_size_classification")),
                clean_text(payload.get("internal_notes")),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


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
    allowed_fields = {
        "name": clean_text,
        "business_category": clean_text,
        "region": clean_text,
        "certifications_json": normalize_certifications,
        "company_size_classification": clean_text,
        "internal_notes": clean_text,
    }

    updates = {field: converter(payload[field]) for field, converter in allowed_fields.items() if field in payload}
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
        conn.execute(f"UPDATE corporations SET {assignments} WHERE id=?", values)
        conn.commit()
        updated = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
    return jsonify(dict(updated))


@app.route("/api/corporations/<int:corporation_id>", methods=["DELETE"])
def delete_corporation(corporation_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (corporation_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Corporation not found"}), 404

        project_count = conn.execute("SELECT COUNT(*) c FROM projects WHERE corporation_id=?", (corporation_id,)).fetchone()["c"]
        if project_count:
            return jsonify({"detail": "Cannot delete corporation with linked projects"}), 409

        conn.execute("DELETE FROM corporations WHERE id=?", (corporation_id,))
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
    payload, code = run_analysis(document_id, force=False)
    return jsonify(payload), code


@app.route("/api/documents/<int:document_id>/reanalyze", methods=["POST"])
def reanalyze_document(document_id: int):
    payload, code = run_analysis(document_id, force=True)
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


def save_and_analyze_nara_notice_item(base_item: dict) -> tuple[dict, int]:
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
                    parse_status = "completed"
                    preview = parsed.text[:1000]
                    if parsed.text:
                        attachment_texts.append(parsed.text)
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
        if OPENAI_API_KEY:
            try:
                summary_json, summary_markdown, _usage = summarize_with_openai(notice_text)
            except Exception:
                summary_json, summary_markdown, _usage = summarize_with_fallback(notice_text)
        else:
            summary_json, summary_markdown, _usage = summarize_with_fallback(notice_text)

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
    result, code = save_and_analyze_nara_notice_item(notice_item)
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
    with db_conn() as conn:
        row = conn.execute("SELECT raw_json FROM nara_notices WHERE id=?", (notice_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Saved notice not found"}), 404
    result, code = save_and_analyze_nara_notice_item(json.loads(row["raw_json"]))
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
