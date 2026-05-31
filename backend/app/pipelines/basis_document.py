import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.core.json_utils import parse_json_dict
from app.core.text import basis_tokenize, basis_vector_for_text, clean_text, parse_int
from app.pipelines.ocr import run_ocr_if_needed
from app.pipelines.parser import extract_document

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = BASE_DIR / "backend"
KST = timezone(timedelta(hours=9))


def _resolve_local_path(raw_value: str) -> Path:
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


STORAGE_ROOT = _resolve_local_path(os.getenv("STORAGE_ROOT", "./storage"))
BASIS_EMBEDDING_MODEL = os.getenv("BASIS_EMBEDDING_MODEL", "local-token-v1")
BASIS_INDEX_DIR = STORAGE_ROOT / "basis-index"
BASIS_INDEX_PATH = BASIS_INDEX_DIR / "basis-index.json"
BASIS_INDEX_SCHEMA_VERSION = "basis-index-v2"
BASIS_INDEX_SOURCE = "sqlite:basis_document_chunks"
BASIS_MAX_CHUNK_CHARS = 1600
BASIS_CHUNK_OVERLAP_CHARS = 180
try:
    BASIS_CITATION_MIN_SCORE = float(os.getenv("BASIS_CITATION_MIN_SCORE", "0.25"))
except ValueError:
    BASIS_CITATION_MIN_SCORE = 0.25


class BasisIndexError(RuntimeError):
    """Raised when the operational JSON basis index cannot be trusted."""


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def normalize_basis_text(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    blank_seen = False
    for line in lines:
        if not line:
            if paragraphs and not blank_seen:
                paragraphs.append("")
            blank_seen = True
            continue
        paragraphs.append(line)
        blank_seen = False
    return "\n".join(paragraphs).strip()


def basis_page_ranges(parser_metadata: dict[str, Any], normalized_text: str) -> list[dict[str, int]]:
    pages = parser_metadata.get("pages") if isinstance(parser_metadata, dict) else []
    if not isinstance(pages, list) or not pages:
        page_count = parse_int(parser_metadata.get("page_count") if isinstance(parser_metadata, dict) else None, 0)
        if page_count <= 0:
            return []
        return [{"page_number": 1, "start": 0, "end": len(normalized_text)}]

    ranges: list[dict[str, int]] = []
    cursor = 0
    for page in pages:
        if not isinstance(page, dict):
            continue
        char_count = parse_int(page.get("char_count"), 0)
        page_number = parse_int(page.get("page_number"), len(ranges) + 1)
        start = cursor
        end = min(len(normalized_text), cursor + max(char_count, 0))
        if end < start:
            end = start
        ranges.append({"page_number": page_number, "start": start, "end": end})
        cursor = end
    if ranges:
        ranges[-1]["end"] = max(ranges[-1]["end"], len(normalized_text))
    return ranges


def page_for_offset(page_ranges: list[dict[str, int]], offset: int) -> int | None:
    if not page_ranges:
        return None
    for page in page_ranges:
        if page["start"] <= offset <= page["end"]:
            return page["page_number"]
    return page_ranges[-1]["page_number"]


def detect_basis_section_title(chunk_text: str) -> str:
    for line in chunk_text.splitlines():
        candidate = clean_text(line)
        if not candidate:
            continue
        if len(candidate) > 80:
            continue
        if re.match(r"^(제\s*\d+\s*[장조절관항]|[0-9]+[.)]|[가-힣]\.)", candidate):
            return candidate
    first_line = clean_text(chunk_text.splitlines()[0] if chunk_text.splitlines() else "")
    return first_line[:80]


def basis_chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_basis_text_into_chunks(
    normalized_text: str,
    parser_metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized_text) if part.strip()]
    if not paragraphs and normalized_text.strip():
        paragraphs = [normalized_text.strip()]

    page_ranges = basis_page_ranges(parser_metadata, normalized_text)
    chunks: list[dict[str, Any]] = []
    cursor = 0
    current_parts: list[str] = []
    current_start = 0

    def flush() -> None:
        nonlocal current_parts, current_start
        chunk_text = "\n\n".join(current_parts).strip()
        if not chunk_text:
            current_parts = []
            return
        start = current_start
        end = start + len(chunk_text)
        chunks.append(
            {
                "chunk_index": len(chunks),
                "chunk_text": chunk_text,
                "chunk_text_normalized": chunk_text,
                "page_start": page_for_offset(page_ranges, start),
                "page_end": page_for_offset(page_ranges, end),
                "section_title": detect_basis_section_title(chunk_text),
                "article_label": "",
                "chunk_hash": basis_chunk_hash(chunk_text),
                "token_count": len(basis_tokenize(chunk_text)),
                "metadata": {
                    "char_start": start,
                    "char_end": end,
                    "chunker": "paragraph-window-v1",
                    "max_chars": BASIS_MAX_CHUNK_CHARS,
                    "overlap_chars": BASIS_CHUNK_OVERLAP_CHARS,
                },
            }
        )

        overlap = chunk_text[-BASIS_CHUNK_OVERLAP_CHARS:].strip()
        current_parts = [overlap] if overlap and len(overlap) < len(chunk_text) else []
        current_start = end - len(overlap) if overlap else end

    for paragraph in paragraphs:
        paragraph_offset = normalized_text.find(paragraph, cursor)
        if paragraph_offset < 0:
            paragraph_offset = cursor
        candidate = "\n\n".join([*current_parts, paragraph]).strip()
        if current_parts and len(candidate) > BASIS_MAX_CHUNK_CHARS:
            flush()
        if not current_parts:
            current_start = paragraph_offset
        if len(paragraph) > BASIS_MAX_CHUNK_CHARS:
            for start in range(0, len(paragraph), BASIS_MAX_CHUNK_CHARS - BASIS_CHUNK_OVERLAP_CHARS):
                current_parts = [paragraph[start : start + BASIS_MAX_CHUNK_CHARS]]
                current_start = paragraph_offset + start
                flush()
            current_parts = []
        else:
            current_parts.append(paragraph)
        cursor = paragraph_offset + len(paragraph)

    flush()
    return chunks


def default_basis_index_payload() -> dict[str, Any]:
    now = now_iso()
    return {
        "schema_version": BASIS_INDEX_SCHEMA_VERSION,
        "model": BASIS_EMBEDDING_MODEL,
        "created_at": now,
        "updated_at": now,
        "source": BASIS_INDEX_SOURCE,
        "chunk_count": 0,
        "checksum": "",
        "chunks": {},
    }


def basis_index_checksum(payload: dict[str, Any]) -> str:
    checksum_payload = dict(payload)
    checksum_payload.pop("checksum", None)
    encoded = json.dumps(
        checksum_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def finalize_basis_index_payload(payload: dict[str, Any], *, update_timestamp: bool = True) -> dict[str, Any]:
    now = now_iso()
    chunks = payload.get("chunks") if isinstance(payload, dict) else {}
    normalized_chunks = chunks if isinstance(chunks, dict) else {}
    finalized = {
        "schema_version": BASIS_INDEX_SCHEMA_VERSION,
        "model": clean_text(payload.get("model") if isinstance(payload, dict) else "") or BASIS_EMBEDDING_MODEL,
        "created_at": clean_text(payload.get("created_at") if isinstance(payload, dict) else "") or now,
        "updated_at": now if update_timestamp else clean_text(payload.get("updated_at") if isinstance(payload, dict) else "") or now,
        "source": BASIS_INDEX_SOURCE,
        "chunk_count": len(normalized_chunks),
        "checksum": "",
        "chunks": normalized_chunks,
    }
    finalized["checksum"] = basis_index_checksum(finalized)
    return finalized


def load_basis_index_state() -> dict[str, Any]:
    if not BASIS_INDEX_PATH.exists():
        return {
            "status": "missing",
            "valid": True,
            "payload": default_basis_index_payload(),
            "errors": [],
            "warnings": ["basis-index.json does not exist yet."],
            "path": str(BASIS_INDEX_PATH),
        }

    try:
        with BASIS_INDEX_PATH.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "corrupt",
            "valid": False,
            "payload": None,
            "errors": [str(exc)],
            "warnings": [],
            "path": str(BASIS_INDEX_PATH),
        }

    if not isinstance(payload, dict):
        return {
            "status": "invalid_schema",
            "valid": False,
            "payload": None,
            "errors": ["basis-index.json root must be an object."],
            "warnings": [],
            "path": str(BASIS_INDEX_PATH),
        }

    errors: list[str] = []
    if payload.get("schema_version") != BASIS_INDEX_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BASIS_INDEX_SCHEMA_VERSION}.")
    if payload.get("source") != BASIS_INDEX_SOURCE:
        errors.append(f"source must be {BASIS_INDEX_SOURCE}.")
    if payload.get("model") != BASIS_EMBEDDING_MODEL:
        errors.append(f"model must be {BASIS_EMBEDDING_MODEL}.")
    chunks = payload.get("chunks")
    if not isinstance(chunks, dict):
        errors.append("chunks must be an object.")
        chunks = {}
    if parse_int(payload.get("chunk_count"), -1) != len(chunks):
        errors.append("chunk_count does not match chunks length.")
    expected_checksum = basis_index_checksum({**payload, "chunks": chunks})
    if payload.get("checksum") != expected_checksum:
        errors.append("checksum mismatch.")

    if errors:
        status = "checksum_mismatch" if errors == ["checksum mismatch."] else "invalid_schema"
        return {
            "status": status,
            "valid": False,
            "payload": None,
            "errors": errors,
            "warnings": [],
            "path": str(BASIS_INDEX_PATH),
        }

    return {
        "status": "ok",
        "valid": True,
        "payload": finalize_basis_index_payload(payload, update_timestamp=False),
        "errors": [],
        "warnings": [],
        "path": str(BASIS_INDEX_PATH),
    }


def load_basis_index() -> dict[str, Any]:
    state = load_basis_index_state()
    if state["valid"]:
        return state["payload"]
    raise BasisIndexError("; ".join(state["errors"]) or f"Basis index is {state['status']}.")


def save_basis_index(payload: dict[str, Any], *, update_timestamp: bool = True) -> None:
    BASIS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = BASIS_INDEX_PATH.with_suffix(".tmp")
    finalized = finalize_basis_index_payload(payload, update_timestamp=update_timestamp)
    with tmp_path.open("w", encoding="utf-8") as stream:
        json.dump(finalized, stream, ensure_ascii=False, indent=2)
    tmp_path.replace(BASIS_INDEX_PATH)


def delete_basis_vectors(conn: sqlite3.Connection, basis_document_id: int) -> None:
    payload = load_basis_index()
    chunks = payload.get("chunks", {})
    if isinstance(chunks, dict):
        payload["chunks"] = {
            vector_id: item
            for vector_id, item in chunks.items()
            if not isinstance(item, dict) or item.get("basis_document_id") != basis_document_id
        }
        save_basis_index(payload)
    conn.execute(
        """
        UPDATE basis_document_chunks
        SET vector_id='', vector_status='pending', updated_at=?
        WHERE basis_document_id=?
        """,
        (now_iso(), basis_document_id),
    )


def delete_basis_vectors_for_run(basis_document_id: int, processing_run_id: str) -> None:
    payload = load_basis_index()
    chunks = payload.get("chunks", {})
    if isinstance(chunks, dict):
        payload["chunks"] = {
            vector_id: item
            for vector_id, item in chunks.items()
            if not (
                isinstance(item, dict)
                and item.get("basis_document_id") == basis_document_id
                and item.get("processing_run_id") == processing_run_id
            )
        }
        save_basis_index(payload)


def delete_basis_vectors_except_run(basis_document_id: int, processing_run_id: str) -> None:
    payload = load_basis_index()
    chunks = payload.get("chunks", {})
    if isinstance(chunks, dict):
        payload["chunks"] = {
            vector_id: item
            for vector_id, item in chunks.items()
            if not (
                isinstance(item, dict)
                and item.get("basis_document_id") == basis_document_id
                and item.get("processing_run_id") != processing_run_id
            )
        }
        save_basis_index(payload)


def mark_basis_rule_candidates_for_revalidation(conn: sqlite3.Connection, basis_document_id: int) -> None:
    now = now_iso()
    conn.execute(
        """
        UPDATE basis_rule_candidates
        SET status='needs_review',
            citation_candidate_id='',
            review_note=CASE
                WHEN review_note='' THEN '기준문서 재처리로 citation 재검토 필요'
                ELSE review_note || ' / 기준문서 재처리로 citation 재검토 필요'
            END,
            reviewed_at='',
            reviewer_name='',
            updated_at=?
        WHERE basis_document_id=?
        """,
        (now, basis_document_id),
    )


def index_basis_chunks(conn: sqlite3.Connection, basis_document_id: int, processing_run_id: str | None = None) -> int:
    index_payload = load_basis_index()
    index_chunks = index_payload.setdefault("chunks", {})
    if not isinstance(index_chunks, dict):
        index_chunks = {}
        index_payload["chunks"] = index_chunks

    run_clause = "AND processing_run_id=?" if processing_run_id else ""
    params: tuple[Any, ...] = (basis_document_id, processing_run_id) if processing_run_id else (basis_document_id,)
    rows = conn.execute(
        f"""
        SELECT id, basis_document_id, chunk_index, chunk_text_normalized, page_start,
               page_end, section_title, article_label, chunk_hash, metadata_json,
               processing_run_id
        FROM basis_document_chunks
        WHERE basis_document_id=?
        {run_clause}
        ORDER BY chunk_index
        """,
        params,
    ).fetchall()

    now = now_iso()
    count = 0
    for row in rows:
        vector_id = f"basis-{row['basis_document_id']}-{row['id']}-{row['chunk_hash'][:12]}"
        vector = basis_vector_for_text(row["chunk_text_normalized"])
        index_chunks[vector_id] = {
            "basis_document_id": row["basis_document_id"],
            "chunk_id": row["id"],
            "chunk_index": row["chunk_index"],
            "chunk_hash": row["chunk_hash"],
            "processing_run_id": row["processing_run_id"],
            "tokens": vector,
            "text_preview": row["chunk_text_normalized"][:400],
            "metadata": {
                **parse_json_dict(row["metadata_json"]),
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "section_title": row["section_title"],
                "article_label": row["article_label"],
            },
        }
        conn.execute(
            """
            UPDATE basis_document_chunks
            SET vector_id=?, vector_status='indexed', embedding_model=?,
                index_error_message='', updated_at=?
            WHERE id=?
            """,
            (vector_id, BASIS_EMBEDDING_MODEL, now, row["id"]),
        )
        count += 1

    save_basis_index(index_payload)
    return count


def basis_document_payload(conn: sqlite3.Connection, row: sqlite3.Row, include_chunks: bool = False) -> dict:
    payload = dict(row)
    payload["metadata"] = parse_json_dict(payload.pop("metadata_json", "{}"))
    if include_chunks:
        chunk_rows = conn.execute(
            """
            SELECT * FROM basis_document_chunks
            WHERE basis_document_id=?
            ORDER BY chunk_index
            """,
            (row["id"],),
        ).fetchall()
        payload["chunks"] = [basis_chunk_payload(chunk) for chunk in chunk_rows]
    return payload


def basis_chunk_payload(row: sqlite3.Row | dict) -> dict:
    payload = dict(row)
    payload["metadata"] = parse_json_dict(payload.pop("metadata_json", "{}"))
    return payload


def process_basis_document(conn: sqlite3.Connection, basis_document_id: int) -> dict:
    row = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
    if not row:
        raise ValueError("Basis document not found")

    path = Path(row["stored_file_path"])
    if not path.exists():
        now = now_iso()
        conn.execute(
            """
            UPDATE basis_documents
            SET processing_status='failed', parse_status='failed', chunk_status='failed',
                index_status='failed', error_message='Stored file not found', updated_at=?
            WHERE id=?
            """,
            (now, basis_document_id),
        )
        return basis_document_payload(conn, conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone())

    savepoint_name = "basis_document_process"
    savepoint_active = False
    try:
        index_snapshot = load_basis_index()
    except BasisIndexError as exc:
        now = now_iso()
        conn.execute(
            """
            UPDATE basis_documents
            SET processing_status='failed', parse_status='pending', chunk_status='skipped',
                index_status='failed', error_message=?, updated_at=?
            WHERE id=?
            """,
            (f"Basis index unavailable: {exc}", now, basis_document_id),
        )
        return basis_document_payload(conn, conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone())
    index_mutated = False
    processing_run_id = ""
    conn.execute(f"SAVEPOINT {savepoint_name}")
    savepoint_active = True
    try:
        now = now_iso()
        conn.execute(
            """
            UPDATE basis_documents
            SET processing_status='parsing', parse_status='processing', ocr_status='pending',
                chunk_status='pending', index_status='pending', error_message='', updated_at=?
            WHERE id=?
            """,
            (now, basis_document_id),
        )

        parsed = extract_document(path)
        ocr_result = run_ocr_if_needed(parsed.text, path, parsed.kind, parsed.metadata)
        raw_text = ocr_result.text or parsed.text
        normalized_text = normalize_basis_text(raw_text)
        chunks = split_basis_text_into_chunks(normalized_text, parsed.metadata) if normalized_text else []

        processing_run_id = f"{datetime.now(KST).strftime('%Y%m%d%H%M%S%f')}-{row['file_hash'][:12]}"
        page_count = parse_int(parsed.metadata.get("page_count"), ocr_result.page_count)
        ocr_status = ocr_result.status
        vector_count = 0
        processing_status = "completed"
        chunk_status = "completed" if chunks else "empty"
        index_status = "pending" if chunks else "empty"
        error_message = ""
        if not normalized_text and ocr_status in {"needs_ocr_setup", "unavailable", "failed"}:
            processing_status = ocr_status
            chunk_status = "skipped"
            index_status = "skipped"
            error_message = ocr_result.error_message or "No extractable text was found."
        elif not normalized_text:
            processing_status = "failed"
            chunk_status = "failed"
            index_status = "skipped"
            error_message = "No extractable text was found."

        if processing_status == "completed":
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO basis_document_chunks (
                      basis_document_id, processing_run_id, chunk_index, chunk_text,
                      chunk_text_normalized, page_start, page_end, section_title,
                      article_label, chunk_hash, token_count, metadata_json,
                      vector_id, vector_status, embedding_model, index_error_message,
                      created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 'pending', ?, '', ?, ?)
                    """,
                    (
                        basis_document_id,
                        processing_run_id,
                        chunk["chunk_index"],
                        chunk["chunk_text"],
                        chunk["chunk_text_normalized"],
                        chunk["page_start"],
                        chunk["page_end"],
                        chunk["section_title"],
                        chunk["article_label"],
                        chunk["chunk_hash"],
                        chunk["token_count"],
                        json.dumps(chunk["metadata"], ensure_ascii=False),
                        BASIS_EMBEDDING_MODEL,
                        now,
                        now,
                    ),
                )
            if chunks:
                index_mutated = True
                vector_count = index_basis_chunks(conn, basis_document_id, processing_run_id)
            chunk_status = "completed" if chunks else "empty"
            index_status = "completed" if vector_count else "empty"
            index_mutated = True
            delete_basis_vectors_except_run(basis_document_id, processing_run_id)
            conn.execute(
                "DELETE FROM basis_document_chunks WHERE basis_document_id=? AND processing_run_id<>?",
                (basis_document_id, processing_run_id),
            )
            mark_basis_rule_candidates_for_revalidation(conn, basis_document_id)
        else:
            conn.execute(
                """
                UPDATE basis_documents
                SET processing_status=?, parse_status='completed', ocr_status=?,
                    chunk_status=?, index_status=?, error_message=?, updated_at=?
                WHERE id=?
                """,
                (
                    processing_status,
                    ocr_status,
                    chunk_status,
                    index_status,
                    error_message,
                    now_iso(),
                    basis_document_id,
                ),
            )
            conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            savepoint_active = False
            return basis_document_payload(conn, conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone())

        metadata = {
            "parser": parsed.metadata,
            "ocr": ocr_result.to_dict(),
            "normalizer": {"name": "basis-normalize-v1", "char_count": len(normalized_text)},
            "chunker": {
                "name": "paragraph-window-v1",
                "max_chars": BASIS_MAX_CHUNK_CHARS,
                "overlap_chars": BASIS_CHUNK_OVERLAP_CHARS,
            },
            "indexer": {"name": BASIS_EMBEDDING_MODEL, "vector_count": vector_count},
        }
        processed_at = now_iso()
        conn.execute(
            """
            UPDATE basis_documents
            SET processing_status=?, parse_status='completed', ocr_status=?,
                chunk_status=?, index_status=?, page_count=?, chunk_count=?,
                vector_count=?, extracted_text_preview=?, metadata_json=?,
                error_message=?, processed_at=?, updated_at=?
            WHERE id=?
            """,
            (
                processing_status,
                ocr_status,
                chunk_status,
                index_status,
                page_count,
                len(chunks),
                vector_count,
                normalized_text[:1200],
                json.dumps(metadata, ensure_ascii=False),
                error_message,
                processed_at,
                processed_at,
                basis_document_id,
            ),
        )
        conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
        savepoint_active = False
    except Exception as exc:
        if savepoint_active:
            try:
                conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
            except sqlite3.Error:
                pass
            savepoint_active = False
        if index_mutated:
            try:
                save_basis_index(index_snapshot, update_timestamp=False)
            except Exception:
                pass
        elif processing_run_id:
            delete_basis_vectors_for_run(basis_document_id, processing_run_id)
        if processing_run_id:
            conn.execute(
                "DELETE FROM basis_document_chunks WHERE basis_document_id=? AND processing_run_id=?",
                (basis_document_id, processing_run_id),
            )
        now = now_iso()
        conn.execute(
            """
            UPDATE basis_documents
            SET processing_status='failed', parse_status='failed', chunk_status='failed',
                index_status='failed', error_message=?, updated_at=?
            WHERE id=?
            """,
            (str(exc), now, basis_document_id),
        )

    updated = conn.execute("SELECT * FROM basis_documents WHERE id=?", (basis_document_id,)).fetchone()
    return basis_document_payload(conn, updated)


def basis_index_db_chunk_rows(
    conn: sqlite3.Connection,
    *,
    category: str = "",
    document_version: str = "",
) -> list[sqlite3.Row]:
    clauses = [
        "d.processing_status='completed'",
        "d.index_status='completed'",
        "c.vector_status='indexed'",
        "c.vector_id<>''",
    ]
    params: list[Any] = []
    if category:
        clauses.append("d.category=?")
        params.append(category)
    if document_version:
        clauses.append("d.document_version=?")
        params.append(document_version)
    return conn.execute(
        f"""
        SELECT c.*, d.title, d.category, d.document_version, d.issuing_agency,
               d.processing_status, d.index_status
        FROM basis_document_chunks c
        JOIN basis_documents d ON d.id = c.basis_document_id
        WHERE {' AND '.join(clauses)}
        ORDER BY d.id DESC, c.chunk_index
        """,
        tuple(params),
    ).fetchall()


def _basis_index_status_from_state(state: dict[str, Any]) -> dict[str, Any]:
    payload = state.get("payload") if isinstance(state.get("payload"), dict) else {}
    return {
        "status": state.get("status", "unknown"),
        "valid": bool(state.get("valid")),
        "path": state.get("path", str(BASIS_INDEX_PATH)),
        "schema_version": payload.get("schema_version", ""),
        "model": payload.get("model", BASIS_EMBEDDING_MODEL),
        "source": payload.get("source", ""),
        "chunk_count": parse_int(payload.get("chunk_count"), 0),
        "checksum": payload.get("checksum", ""),
        "created_at": payload.get("created_at", ""),
        "updated_at": payload.get("updated_at", ""),
        "errors": list(state.get("errors") or []),
        "warnings": list(state.get("warnings") or []),
    }


def validate_basis_index(conn: sqlite3.Connection) -> dict[str, Any]:
    state = load_basis_index_state()
    payload = state.get("payload") if isinstance(state.get("payload"), dict) else None
    db_rows = basis_index_db_chunk_rows(conn)
    db_by_vector_id = {row["vector_id"]: row for row in db_rows}

    result = _basis_index_status_from_state(state)
    result.update(
        {
            "db_indexed_chunk_count": len(db_rows),
            "missing_from_index": [],
            "missing_from_db": [],
            "mismatched_chunks": [],
            "invalid_index_items": [],
            "rebuild_required": False,
            "can_search": False,
            "payload": payload,
        }
    )

    if not state.get("valid"):
        result["rebuild_required"] = True
        return result

    if state.get("status") == "missing" and db_rows:
        result["status"] = "missing"
        result["valid"] = False
        result["errors"].append("basis-index.json is missing while DB has indexed chunks.")
        result["rebuild_required"] = True
        return result

    index_chunks = payload.get("chunks", {}) if payload else {}
    if not isinstance(index_chunks, dict):
        result["status"] = "invalid_schema"
        result["valid"] = False
        result["errors"].append("chunks must be an object.")
        result["rebuild_required"] = True
        return result

    missing_from_index = sorted(set(db_by_vector_id) - set(index_chunks))
    missing_from_db = sorted(set(index_chunks) - set(db_by_vector_id))
    invalid_index_items: list[str] = []
    mismatched: list[dict[str, Any]] = []
    for vector_id, item in index_chunks.items():
        if not isinstance(item, dict):
            invalid_index_items.append(vector_id)
            continue
        if not isinstance(item.get("tokens"), dict):
            invalid_index_items.append(vector_id)
            continue
        if vector_id not in db_by_vector_id:
            continue
        row = db_by_vector_id[vector_id]
        if (
            parse_int(item.get("basis_document_id"), 0) != row["basis_document_id"]
            or parse_int(item.get("chunk_id"), 0) != row["id"]
            or clean_text(item.get("chunk_hash")) != row["chunk_hash"]
        ):
            mismatched.append(
                {
                    "vector_id": vector_id,
                    "chunk_id": item.get("chunk_id"),
                    "db_chunk_id": row["id"],
                }
            )

    result["missing_from_index"] = missing_from_index
    result["missing_from_db"] = missing_from_db
    result["mismatched_chunks"] = mismatched
    result["invalid_index_items"] = invalid_index_items

    if missing_from_index or missing_from_db or mismatched or invalid_index_items:
        result["status"] = "inconsistent"
        result["valid"] = False
        if missing_from_index:
            result["errors"].append("DB has indexed chunks missing from basis-index.json.")
        if missing_from_db:
            result["errors"].append("basis-index.json contains chunks missing from DB.")
        if mismatched:
            result["errors"].append("basis-index.json chunk metadata does not match DB.")
        if invalid_index_items:
            result["errors"].append("basis-index.json contains invalid chunk items.")
        result["rebuild_required"] = True
        return result

    result["valid"] = True
    result["can_search"] = bool(index_chunks)
    result["rebuild_required"] = False
    return result


def basis_index_status_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    payload = validate_basis_index(conn)
    payload.pop("payload", None)
    return payload


def archive_invalid_basis_index() -> str:
    if not BASIS_INDEX_PATH.exists():
        return ""
    stamp = datetime.now(KST).strftime("%Y%m%d%H%M%S")
    archived_path = BASIS_INDEX_PATH.with_name(f"{BASIS_INDEX_PATH.name}.corrupt-{stamp}")
    BASIS_INDEX_PATH.replace(archived_path)
    return str(archived_path)


def rebuild_basis_index(conn: sqlite3.Connection) -> dict[str, Any]:
    state = load_basis_index_state()
    archived_path = archive_invalid_basis_index() if not state.get("valid") else ""
    payload = default_basis_index_payload()
    chunks = payload["chunks"]
    for row in basis_index_db_chunk_rows(conn):
        vector_id = row["vector_id"]
        chunks[vector_id] = {
            "basis_document_id": row["basis_document_id"],
            "chunk_id": row["id"],
            "chunk_index": row["chunk_index"],
            "chunk_hash": row["chunk_hash"],
            "processing_run_id": row["processing_run_id"],
            "tokens": basis_vector_for_text(row["chunk_text_normalized"]),
            "text_preview": row["chunk_text_normalized"][:400],
            "metadata": {
                **parse_json_dict(row["metadata_json"]),
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "section_title": row["section_title"],
                "article_label": row["article_label"],
            },
        }
    save_basis_index(payload)
    result = basis_index_status_payload(conn)
    result["rebuilt_chunk_count"] = len(chunks)
    result["archived_path"] = archived_path
    return result


def basis_search_results(
    conn: sqlite3.Connection,
    query: str,
    category: str = "",
    document_version: str = "",
    top_k: int = 5,
) -> list[dict[str, Any]]:
    query_tokens = set(basis_tokenize(query))
    if not query_tokens:
        return []

    validation = validate_basis_index(conn)
    if not validation["valid"]:
        raise BasisIndexError("; ".join(validation["errors"]) or "Basis index validation failed.")
    if not validation["can_search"]:
        return []

    index_chunks = validation["payload"].get("chunks", {})

    scored_items: list[tuple[float, str, dict[str, Any]]] = []
    for vector_id, item in index_chunks.items():
        if not isinstance(item, dict):
            continue
        vector = item.get("tokens") if isinstance(item.get("tokens"), dict) else {}
        shared = sum(vector.get(token, 0) for token in query_tokens)
        if shared <= 0:
            continue
        score = shared / max(len(query_tokens), 1)
        scored_items.append((score, vector_id, item))

    scored: list[dict[str, Any]] = []
    for score, vector_id, item in sorted(scored_items, key=lambda item: item[0], reverse=True):
        clauses = [
            "c.id=?",
            "c.vector_id=?",
            "d.processing_status='completed'",
            "d.index_status='completed'",
            "c.vector_status='indexed'",
        ]
        params: list[Any] = [parse_int(item.get("chunk_id"), 0), vector_id]
        if category:
            clauses.append("d.category=?")
            params.append(category)
        if document_version:
            clauses.append("d.document_version=?")
            params.append(document_version)
        row = conn.execute(
            f"""
            SELECT c.*, d.title, d.category, d.document_version, d.issuing_agency,
                   d.processing_status, d.index_status
            FROM basis_document_chunks c
            JOIN basis_documents d ON d.id = c.basis_document_id
            WHERE {' AND '.join(clauses)}
            """,
            tuple(params),
        ).fetchone()
        if not row:
            continue
        scored.append(
            {
                "score": round(score, 4),
                "citation_candidate_id": f"basis:{row['basis_document_id']}:chunk:{row['id']}",
                "chunk": basis_chunk_payload(row),
                "document": {
                    "id": row["basis_document_id"],
                    "title": row["title"],
                    "category": row["category"],
                    "document_version": row["document_version"],
                    "issuing_agency": row["issuing_agency"],
                    "processing_status": row["processing_status"],
                    "index_status": row["index_status"],
                },
                "index_source": "json_basis_index",
            }
        )
        if len(scored) >= max(1, min(top_k, 20)):
            break

    return scored
