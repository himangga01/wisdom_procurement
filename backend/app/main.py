import hashlib
import json
import os
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pypdf import PdfReader

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"


def _resolve_local_path(raw_value: str) -> Path:
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


STORAGE_ROOT = _resolve_local_path(os.getenv("STORAGE_ROOT", "./storage"))
MEMORY_DB_URI = "file:smart_phase1?mode=memory&cache=shared"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_PRIMARY = os.getenv("OPENAI_MODEL_PRIMARY", "gpt-5.1")
ANALYSIS_PROMPT_VERSION = "v2_bid_qualification"
BASIS_ANALYSIS_PROMPT_VERSION = "v1_basis_direct_production"
DIRECT_PRODUCTION_CATEGORY = "direct_production_certificate"
DIRECT_PRODUCTION_BASIS_PATH = os.getenv("DIRECT_PRODUCTION_BASIS_PATH", "").strip()
DIRECT_PRODUCTION_BASIS_TITLE = os.getenv(
    "DIRECT_PRODUCTION_BASIS_TITLE",
    "직접생산확인증명 기준문서",
).strip()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
BASIS_ALLOWED_EXTENSIONS = {".pdf"}
QUALIFICATION_KEYWORDS = (
    "입찰참가자격",
    "참가자격",
    "자격",
    "면허",
    "등록",
    "신고",
    "실적",
    "지역",
    "업종",
    "중소기업",
    "직접생산",
    "공동수급",
)
LIMITATION_KEYWORDS = (
    "제한",
    "제외",
    "결격",
    "부정당",
    "휴업",
    "폐업",
    "정지",
    "불가",
)
REQUIRED_DOCUMENT_KEYWORDS = (
    "제출",
    "서류",
    "증명",
    "확인서",
    "등록증",
    "신고필증",
    "실적증명",
    "재무제표",
    "인감",
    "위임장",
)
DATE_PATTERNS = (
    r"\d{4}[./-]\d{1,2}[./-]\d{1,2}",
    r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
    r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일",
    r"\d{1,2}월\s*\d{1,2}일",
)

DIRECT_PRODUCTION_REQUIREMENT_KEYWORDS = (
    "직접생산",
    "생산공정",
    "직접생산확인",
    "세부품명",
    "완제품",
    "원재료",
)
DIRECT_PRODUCTION_FACILITY_KEYWORDS = (
    "시설",
    "설비",
    "장비",
    "공장",
    "작업장",
    "검사",
    "시험",
)
DIRECT_PRODUCTION_PERSONNEL_KEYWORDS = (
    "인력",
    "근로자",
    "기술자",
    "상시근로자",
    "기술인력",
    "재직",
)

app = Flask(__name__)
CORS(app)

GLOBAL_CONN = sqlite3.connect(MEMORY_DB_URI, uri=True, check_same_thread=False)
GLOBAL_CONN.row_factory = sqlite3.Row


def db_conn() -> sqlite3.Connection:
    return GLOBAL_CONN


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "uploads").mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "basis").mkdir(parents=True, exist_ok=True)

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

            CREATE TABLE IF NOT EXISTS basis_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                original_file_name TEXT NOT NULL,
                stored_file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT 'application/pdf',
                file_size INTEGER DEFAULT 0,
                source_type TEXT DEFAULT 'local_path',
                memo TEXT DEFAULT '',
                analysis_status TEXT DEFAULT 'pending',
                latest_analysis_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS basis_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                basis_document_id INTEGER NOT NULL,
                analysis_type TEXT DEFAULT 'basis_summary',
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
                FOREIGN KEY(basis_document_id) REFERENCES basis_documents(id)
            );
            """
        )
    _bootstrap_direct_production_basis()


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def extract_text(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()
    if ext == ".docx":
        doc = Document(str(file_path))
        return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
    raise ValueError("Unsupported file format")


def _clean_text_item(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t-•")


def _unique_items(values: list[str], limit: int | None = None) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in values:
        cleaned = _clean_text_item(raw)
        if not cleaned:
            continue

        key = cleaned.casefold()
        if key in seen:
            continue

        seen.add(key)
        items.append(cleaned)
        if limit is not None and len(items) >= limit:
            break
    return items


def _ensure_list(value: object) -> list[str]:
    if isinstance(value, list):
        return _unique_items([str(item) for item in value])
    if isinstance(value, str):
        return _unique_items([value])
    return []


def _find_lines_by_keywords(lines: list[str], keywords: tuple[str, ...], limit: int) -> list[str]:
    return _unique_items([line for line in lines if any(keyword in line for keyword in keywords)], limit)


def _line_has_date(line: str) -> bool:
    return any(re.search(pattern, line) for pattern in DATE_PATTERNS)


def _find_qualification_lines(lines: list[str], limit: int = 8) -> list[str]:
    matched = [
        line
        for line in lines
        if any(keyword in line for keyword in QUALIFICATION_KEYWORDS)
        and "제출기한" not in line
        and "마감" not in line
        and not line.startswith("제출서류")
    ]
    return _unique_items(matched, limit)


def _find_required_document_lines(lines: list[str], limit: int = 8) -> list[str]:
    matched = [
        line
        for line in lines
        if any(keyword in line for keyword in REQUIRED_DOCUMENT_KEYWORDS)
        and "제출기한" not in line
        and "마감" not in line
        and not _line_has_date(line)
    ]
    return _unique_items(matched, limit)


def _find_key_dates(lines: list[str], limit: int = 5) -> list[str]:
    matched = [line for line in lines if _line_has_date(line)]
    return _unique_items(matched, limit)


def _normalize_analysis_payload(payload: dict) -> dict:
    qualification_requirements = _ensure_list(
        payload.get("qualification_requirements") or payload.get("requirements")
    )
    disqualification_or_limitations = _ensure_list(
        payload.get("disqualification_or_limitations") or payload.get("risks")
    )
    required_documents = _ensure_list(payload.get("required_documents"))
    key_dates = _ensure_list(payload.get("key_dates"))
    preparation_checklist = _ensure_list(payload.get("preparation_checklist"))
    questions_to_check = _ensure_list(payload.get("questions_to_check"))

    bidder_qualification_summary = str(payload.get("bidder_qualification_summary") or "").strip()
    if not bidder_qualification_summary and qualification_requirements:
        bidder_qualification_summary = " / ".join(qualification_requirements[:2])

    document_summary = str(payload.get("document_summary") or "").strip()
    if not document_summary:
        document_summary = bidder_qualification_summary or "문서 요약을 생성하지 못했습니다."

    confidence_note = str(payload.get("confidence_note") or "").strip() or "참고용 요약입니다."

    return {
        "document_summary": document_summary,
        "bidder_qualification_summary": bidder_qualification_summary or "입찰참가자격 관련 항목을 원문에서 재확인하세요.",
        "qualification_requirements": qualification_requirements,
        "disqualification_or_limitations": disqualification_or_limitations,
        "required_documents": required_documents,
        "key_dates": key_dates,
        "preparation_checklist": preparation_checklist,
        "questions_to_check": questions_to_check,
        "confidence_note": confidence_note,
        "requirements": qualification_requirements,
        "risks": disqualification_or_limitations,
    }


def _build_analysis_markdown(payload: dict) -> str:
    sections: list[str] = ["## 문서 요약", payload["document_summary"], ""]

    section_pairs = [
        ("## 입찰참가자격 요약", [payload["bidder_qualification_summary"]]),
        ("## 확인된 자격 요건", payload["qualification_requirements"]),
        ("## 제한 또는 유의 사항", payload["disqualification_or_limitations"]),
        ("## 제출 서류", payload["required_documents"]),
        ("## 일정 메모", payload["key_dates"]),
        ("## 추가 확인 포인트", payload["questions_to_check"]),
    ]

    for title, items in section_pairs:
        sections.append(title)
        if items:
            sections.extend(f"- {item}" for item in items if item)
        else:
            sections.append("- 추출된 항목이 없습니다.")
        sections.append("")

    sections.append(f"신뢰도 메모: {payload['confidence_note']}")
    return "\n".join(sections)


def summarize_with_fallback(text: str) -> tuple[dict, str, dict]:
    if not text:
        payload = _normalize_analysis_payload(
            {
                "document_summary": "문서에서 추출 가능한 텍스트가 부족합니다.",
                "bidder_qualification_summary": "입찰참가자격 관련 문구를 확인할 수 없습니다.",
                "qualification_requirements": [],
                "disqualification_or_limitations": [],
                "required_documents": [],
                "key_dates": [],
                "preparation_checklist": [],
                "questions_to_check": ["원문 파일 품질(OCR) 재확인 필요"],
                "confidence_note": "Low confidence - extracted text is insufficient",
            }
        )
    else:
        lines = _unique_items([line for line in text.splitlines() if line.strip()])
        qualification_requirements = _find_qualification_lines(lines, limit=8)
        disqualification_or_limitations = _find_lines_by_keywords(lines, LIMITATION_KEYWORDS, limit=6)
        required_documents = _find_required_document_lines(lines, limit=8)
        key_dates = _find_key_dates(lines)

        bidder_qualification_summary = (
            " / ".join(qualification_requirements[:2])
            if qualification_requirements
            else "입찰참가자격 관련 핵심 문구를 원문에서 추가 확인하세요."
        )

        preparation_checklist = _unique_items(
            [f"자격요건 확인: {item}" for item in qualification_requirements[:3]]
            + [f"제출서류 준비: {item}" for item in required_documents[:3]]
            + [f"제한사항 검토: {item}" for item in disqualification_or_limitations[:2]],
            limit=6,
        )

        questions_to_check = _unique_items(
            [
                "입찰참가자격 항목이 법인 현황과 일치하는지 확인하세요.",
                "제출서류의 발급기관과 유효기간을 확인하세요.",
                "최종 참가 가능 여부는 원문 조항 기준으로 다시 검토하세요.",
                *([f"일정 관련 조항 확인: {key_dates[0]}"] if key_dates else []),
            ],
            limit=5,
        )

        payload = _normalize_analysis_payload(
            {
                "document_summary": " ".join(lines[:4])[:500],
                "bidder_qualification_summary": bidder_qualification_summary,
                "qualification_requirements": qualification_requirements,
                "disqualification_or_limitations": disqualification_or_limitations,
                "required_documents": required_documents,
                "key_dates": key_dates,
                "preparation_checklist": preparation_checklist,
                "questions_to_check": questions_to_check,
                "confidence_note": "Fallback summary focused on bid qualification (no API key or API failed)",
            }
        )

    markdown = _build_analysis_markdown(payload)
    usage = {"provider": "fallback", "model": "fallback", "input_chars": len(text)}
    return payload, markdown, usage


def summarize_with_openai(text: str) -> tuple[dict, str, dict]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=OPENAI_MODEL_PRIMARY,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a Korean procurement analysis assistant. "
                    "Focus on bidder qualification requirements from the source document. "
                    "Do not make a final eligible/ineligible decision. "
                    "Return strict JSON only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "다음 조달 문서를 읽고 입찰참가자격 중심으로 정리하세요. "
                    "최종 적격/부적격 판단은 하지 말고, 원문에 나온 자격요건, 제한사항, 제출서류, 일정, 추가 확인 포인트만 추출하세요. "
                    "반환 JSON 키는 정확히 아래와 같아야 합니다: "
                    "document_summary, bidder_qualification_summary, qualification_requirements, "
                    "disqualification_or_limitations, required_documents, key_dates, preparation_checklist, "
                    "questions_to_check, confidence_note. "
                    "배열 값은 모두 문자열 배열이어야 하며, 모르면 빈 배열을 사용하세요.\n\n"
                    f"{text[:120000]}"
                ),
            },
        ],
        text={"format": {"type": "json_object"}},
    )
    payload = _normalize_analysis_payload(json.loads(resp.output_text))
    markdown = _build_analysis_markdown(payload)
    usage = {"provider": "openai", "model": OPENAI_MODEL_PRIMARY, "input_chars": len(text)}
    return payload, markdown, usage


def run_analysis(document_id: int, force: bool = False) -> tuple[dict, int]:
    with db_conn() as conn:
        doc = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not doc:
            return {"detail": "Document not found"}, 404

        file_path = Path(doc["stored_file_path"])
        text = extract_text(file_path)
        input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        if not force:
            cached = conn.execute(
                "SELECT * FROM analyses WHERE project_document_id=? AND input_hash=? ORDER BY id DESC LIMIT 1",
                (document_id, input_hash),
            ).fetchone()
            if cached:
                conn.execute(
                    "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
                    ("completed", "skipped", "cached", cached["id"], now_iso(), document_id),
                )
                conn.commit()
                return {"analysis_id": cached["id"], "status": "completed", "message": "Analysis completed (cache)"}, 200

        if OPENAI_API_KEY:
            try:
                output_json, output_md, usage = summarize_with_openai(text)
            except Exception:
                output_json, output_md, usage = summarize_with_fallback(text)
        else:
            output_json, output_md, usage = summarize_with_fallback(text)

        model_provider = str(usage.get("provider", "openai"))
        model_name = str(usage.get("model", OPENAI_MODEL_PRIMARY))

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
                ANALYSIS_PROMPT_VERSION,
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
            ("completed", "skipped", "completed", analysis_id, now_iso(), document_id),
        )
        conn.commit()

    return {"analysis_id": analysis_id, "status": "completed", "message": "Analysis completed"}, 200


def _copy_basis_file(source_path: Path) -> tuple[Path, int]:
    stored_name = f"{uuid.uuid4().hex}{source_path.suffix.lower()}"
    target_dir = STORAGE_ROOT / "basis"
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / stored_name
    shutil.copy2(source_path, stored_path)
    return stored_path, stored_path.stat().st_size


def import_basis_document_from_local(file_path: str, title: str, category: str, memo: str = "") -> dict:
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError("Basis document file not found")

    if source_path.suffix.lower() not in BASIS_ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF is supported for basis documents")

    with db_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM basis_documents WHERE original_file_name=? AND category=? ORDER BY id DESC LIMIT 1",
            (source_path.name, category),
        ).fetchone()
        if existing:
            return dict(existing)

        stored_path, file_size = _copy_basis_file(source_path)
        now = now_iso()
        cur = conn.execute(
            """
            INSERT INTO basis_documents (
              title, category, original_file_name, stored_file_path, mime_type, file_size,
              source_type, memo, analysis_status, latest_analysis_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'application/pdf', ?, 'local_path', ?, 'pending', NULL, ?, ?)
            """,
            (
                title or source_path.stem,
                category,
                source_path.name,
                str(stored_path),
                file_size,
                memo,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


def _normalize_basis_analysis_payload(payload: dict) -> dict:
    qualification_requirements = _ensure_list(payload.get("qualification_requirements"))
    production_requirements = _ensure_list(payload.get("production_requirements"))
    facility_requirements = _ensure_list(payload.get("facility_requirements"))
    personnel_requirements = _ensure_list(payload.get("personnel_requirements"))
    required_documents = _ensure_list(payload.get("required_documents"))
    questions_to_check = _ensure_list(payload.get("questions_to_check"))

    basis_topic = str(payload.get("basis_topic") or "").strip() or "직접생산확인증명 기준"
    document_summary = str(payload.get("document_summary") or "").strip() or basis_topic
    applicability_scope = str(payload.get("applicability_scope") or "").strip() or "직접생산확인증명 관련 기준문서"
    confidence_note = str(payload.get("confidence_note") or "").strip() or "기준문서 참고용 요약입니다."

    return {
        "basis_topic": basis_topic,
        "document_summary": document_summary,
        "applicability_scope": applicability_scope,
        "qualification_requirements": qualification_requirements,
        "production_requirements": production_requirements,
        "facility_requirements": facility_requirements,
        "personnel_requirements": personnel_requirements,
        "required_documents": required_documents,
        "questions_to_check": questions_to_check,
        "confidence_note": confidence_note,
    }


def _build_basis_analysis_markdown(payload: dict) -> str:
    sections: list[str] = [
        "## 기준문서 요약",
        payload["document_summary"],
        "",
        "## 적용 범위",
        f"- {payload['applicability_scope']}",
        "",
    ]

    for title, items in [
        ("## 기본 자격 요건", payload["qualification_requirements"]),
        ("## 직접생산 요건", payload["production_requirements"]),
        ("## 시설 및 설비 요건", payload["facility_requirements"]),
        ("## 인력 요건", payload["personnel_requirements"]),
        ("## 요구 서류", payload["required_documents"]),
        ("## 추가 확인 포인트", payload["questions_to_check"]),
    ]:
        sections.append(title)
        if items:
            sections.extend(f"- {item}" for item in items)
        else:
            sections.append("- 추출된 항목이 없습니다.")
        sections.append("")

    sections.append(f"신뢰도 메모: {payload['confidence_note']}")
    return "\n".join(sections)


def summarize_basis_with_fallback(text: str, category: str) -> tuple[dict, str, dict]:
    if not text:
        payload = _normalize_basis_analysis_payload(
            {
                "basis_topic": "기준문서 요약 실패",
                "document_summary": "기준문서에서 추출 가능한 텍스트가 부족합니다.",
                "applicability_scope": category,
                "questions_to_check": ["기준문서 PDF의 텍스트 추출 상태를 다시 확인하세요."],
                "confidence_note": "Low confidence - extracted text is insufficient",
            }
        )
    else:
        lines = _unique_items([line for line in text.splitlines() if line.strip()], limit=600)
        payload = _normalize_basis_analysis_payload(
            {
                "basis_topic": "직접생산확인증명 기준",
                "document_summary": " ".join(lines[:5])[:700],
                "applicability_scope": "직접생산확인증명서 발급 및 유지 요건 검토용 기준문서",
                "qualification_requirements": _find_lines_by_keywords(lines, ("직접생산확인", "확인기준", "경쟁제품"), 10),
                "production_requirements": _find_lines_by_keywords(lines, DIRECT_PRODUCTION_REQUIREMENT_KEYWORDS, 10),
                "facility_requirements": _find_lines_by_keywords(lines, DIRECT_PRODUCTION_FACILITY_KEYWORDS, 8),
                "personnel_requirements": _find_lines_by_keywords(lines, DIRECT_PRODUCTION_PERSONNEL_KEYWORDS, 8),
                "required_documents": _find_required_document_lines(lines, 8),
                "questions_to_check": [
                    "세부품명별 직접생산 기준이 현재 검토 대상 품명과 일치하는지 확인하세요.",
                    "생산시설과 검사설비 요건이 실제 사업장 현황과 맞는지 대조하세요.",
                    "상시근로자 및 기술인력 요건이 최신 상태인지 확인하세요.",
                ],
                "confidence_note": "Fallback summary focused on direct production certificate basis",
            }
        )

    markdown = _build_basis_analysis_markdown(payload)
    usage = {"provider": "fallback", "model": "fallback", "input_chars": len(text)}
    return payload, markdown, usage


def summarize_basis_with_openai(text: str, category: str) -> tuple[dict, str, dict]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=OPENAI_MODEL_PRIMARY,
        input=[
            {
                "role": "system",
                "content": "You are a Korean basis document analysis assistant. Return strict JSON only.",
            },
            {
                "role": "user",
                "content": (
                    "다음 기준문서를 읽고 직접생산확인증명 기준을 정리하세요. "
                    "반환 JSON 키는 basis_topic, document_summary, applicability_scope, qualification_requirements, "
                    "production_requirements, facility_requirements, personnel_requirements, required_documents, "
                    "questions_to_check, confidence_note 이어야 합니다. "
                    f"문서 카테고리는 {category} 입니다.\n\n{text[:120000]}"
                ),
            },
        ],
        text={"format": {"type": "json_object"}},
    )
    payload = _normalize_basis_analysis_payload(json.loads(resp.output_text))
    markdown = _build_basis_analysis_markdown(payload)
    usage = {"provider": "openai", "model": OPENAI_MODEL_PRIMARY, "input_chars": len(text)}
    return payload, markdown, usage


def run_basis_analysis(basis_document_id: int, force: bool = False) -> tuple[dict, int]:
    with db_conn() as conn:
        doc = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not doc:
            return {"detail": "Basis document not found"}, 404

        file_path = Path(doc["stored_file_path"])
        text = extract_text(file_path)
        input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        if not force:
            cached = conn.execute(
                "SELECT * FROM basis_analyses WHERE basis_document_id=? AND input_hash=? ORDER BY id DESC LIMIT 1",
                (basis_document_id, input_hash),
            ).fetchone()
            if cached:
                conn.execute(
                    "UPDATE basis_documents SET analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
                    ("cached", cached["id"], now_iso(), basis_document_id),
                )
                conn.commit()
                return {"analysis_id": cached["id"], "status": "completed", "message": "Basis analysis completed (cache)"}, 200

        if OPENAI_API_KEY:
            try:
                output_json, output_md, usage = summarize_basis_with_openai(text, doc["category"])
            except Exception:
                output_json, output_md, usage = summarize_basis_with_fallback(text, doc["category"])
        else:
            output_json, output_md, usage = summarize_basis_with_fallback(text, doc["category"])

        model_provider = str(usage.get("provider", "openai"))
        model_name = str(usage.get("model", OPENAI_MODEL_PRIMARY))

        cur = conn.execute(
            """
            INSERT INTO basis_analyses (
              basis_document_id, analysis_type, model_provider, model_name, prompt_version,
              input_hash, output_json, output_markdown, token_usage_json, status, error_message, created_at
            ) VALUES (?, 'basis_summary', ?, ?, ?, ?, ?, ?, ?, 'completed', '', ?)
            """,
            (
                basis_document_id,
                model_provider,
                model_name,
                BASIS_ANALYSIS_PROMPT_VERSION,
                input_hash,
                json.dumps(output_json, ensure_ascii=False),
                output_md,
                json.dumps(usage, ensure_ascii=False),
                now_iso(),
            ),
        )
        analysis_id = cur.lastrowid

        conn.execute(
            "UPDATE basis_documents SET analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
            ("completed", analysis_id, now_iso(), basis_document_id),
        )
        conn.commit()

    return {"analysis_id": analysis_id, "status": "completed", "message": "Basis analysis completed"}, 200


def _bootstrap_direct_production_basis() -> None:
    if not DIRECT_PRODUCTION_BASIS_PATH:
        return

    try:
        doc = import_basis_document_from_local(
            file_path=DIRECT_PRODUCTION_BASIS_PATH,
            title=DIRECT_PRODUCTION_BASIS_TITLE,
            category=DIRECT_PRODUCTION_CATEGORY,
            memo="자동 등록된 직접생산확인증명 기준문서",
        )
        if not doc.get("latest_analysis_id"):
            run_basis_analysis(int(doc["id"]), force=False)
    except Exception as exc:
        print(f"[bootstrap] direct production basis import failed: {exc}")


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
    payload = request.get_json(force=True)
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
                payload.get("name", ""),
                payload.get("business_category", ""),
                payload.get("region", ""),
                payload.get("certifications_json", "[]"),
                payload.get("company_size_classification", ""),
                payload.get("internal_notes", ""),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/projects", methods=["GET"])
def list_projects():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/projects", methods=["POST"])
def create_project():
    payload = request.get_json(force=True)
    now = now_iso()
    corp_id = int(payload.get("corporation_id", 0))

    with db_conn() as conn:
        corp = conn.execute("SELECT id FROM corporations WHERE id=?", (corp_id,)).fetchone()
        if not corp:
            return jsonify({"detail": "Invalid corporation_id"}), 400

        cur = conn.execute(
            "INSERT INTO projects (name, corporation_id, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                payload.get("name", ""),
                corp_id,
                payload.get("status", "active"),
                payload.get("notes", ""),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


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
    project_id = int(request.form.get("project_id", "0"))
    document_type = request.form.get("document_type", "general")
    memo = request.form.get("memo", "")
    revision_note = request.form.get("revision_note", "")
    file = request.files.get("file")

    if not file:
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


@app.route("/api/documents/<int:document_id>", methods=["DELETE"])
def delete_document(document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Document not found"}), 404

        file_path = Path(row["stored_file_path"])
        if file_path.exists():
            file_path.unlink()

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


@app.route("/api/basis-documents", methods=["GET"])
def list_basis_documents():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM basis_documents ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/basis-documents/import-local", methods=["POST"])
def import_basis_document_local():
    payload = request.get_json(force=True)
    try:
        doc = import_basis_document_from_local(
            file_path=str(payload.get("file_path", "")),
            title=str(payload.get("title", "")).strip(),
            category=str(payload.get("category", DIRECT_PRODUCTION_CATEGORY)).strip() or DIRECT_PRODUCTION_CATEGORY,
            memo=str(payload.get("memo", "")).strip(),
        )
    except FileNotFoundError:
        return jsonify({"detail": "Basis document file not found"}), 400
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400

    return jsonify(doc), 201


@app.route("/api/basis-documents/<int:basis_document_id>/analyze", methods=["POST"])
def analyze_basis_document(basis_document_id: int):
    payload, code = run_basis_analysis(basis_document_id, force=False)
    return jsonify(payload), code


@app.route("/api/basis-documents/<int:basis_document_id>/reanalyze", methods=["POST"])
def reanalyze_basis_document(basis_document_id: int):
    payload, code = run_basis_analysis(basis_document_id, force=True)
    return jsonify(payload), code


@app.route("/api/basis-documents/<int:basis_document_id>/analysis/latest", methods=["GET"])
def latest_basis_analysis(basis_document_id: int):
    with db_conn() as conn:
        doc = conn.execute("SELECT latest_analysis_id FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
        if not doc or not doc["latest_analysis_id"]:
            return jsonify({"detail": "Latest basis analysis not found"}), 404

        row = conn.execute("SELECT * FROM basis_analyses WHERE id=?", (doc["latest_analysis_id"],)).fetchone()
    if not row:
        return jsonify({"detail": "Basis analysis not found"}), 404
    return jsonify(dict(row))


@app.route("/api/basis-documents/latest/by-category/<category>", methods=["GET"])
def latest_basis_by_category(category: str):
    with db_conn() as conn:
        doc = conn.execute(
            "SELECT * FROM basis_documents WHERE category=? ORDER BY id DESC LIMIT 1",
            (category,),
        ).fetchone()
        if not doc:
            return jsonify({"detail": "Basis document not found"}), 404

        analysis = None
        if doc["latest_analysis_id"]:
            analysis = conn.execute(
                "SELECT * FROM basis_analyses WHERE id=?",
                (doc["latest_analysis_id"],),
            ).fetchone()

    return jsonify(
        {
            "document": dict(doc),
            "analysis": dict(analysis) if analysis else None,
        }
    )


if __name__ == "__main__":
    init_db()
    app_port = int(os.getenv("APP_PORT", "18000"))
    app.run(host="127.0.0.1", port=app_port, debug=False)
