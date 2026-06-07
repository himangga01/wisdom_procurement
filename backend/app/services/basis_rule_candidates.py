import sqlite3
from typing import Any

from app.core.citations import parse_basis_citation_candidate_id
from app.core.text import basis_tokenize, basis_vector_for_text, clean_text


BASIS_RULE_CANDIDATE_STATUSES = {"needs_review", "approved", "rejected", "archived"}


def validate_basis_rule_candidate_approval(conn: sqlite3.Connection, values: dict[str, Any]) -> str:
    if not clean_text(values.get("condition_text")):
        return "condition_text is required before approval"
    citation_id = clean_text(values.get("citation_candidate_id"))
    if not citation_id:
        return "citation_candidate_id is required before approval"
    parsed_citation = parse_basis_citation_candidate_id(citation_id)
    if not parsed_citation:
        return "citation_candidate_id must match basis:{basis_document_id}:chunk:{basis_chunk_id}"
    citation_basis_document_id, citation_chunk_id = parsed_citation
    if citation_basis_document_id != int(values.get("basis_document_id") or 0):
        return "citation_candidate_id basis_document_id does not match this candidate"
    if citation_chunk_id != int(values.get("basis_chunk_id") or 0):
        return "citation_candidate_id basis_chunk_id does not match this candidate"
    basis = conn.execute(
        """
        SELECT id, processing_status, index_status
        FROM basis_documents
        WHERE id=?
        """,
        (values.get("basis_document_id"),),
    ).fetchone()
    if not basis:
        return "basis document does not exist"
    if basis["processing_status"] != "completed" or basis["index_status"] != "completed":
        return "basis document must be completed and indexed before approval"
    chunk = conn.execute(
        """
        SELECT id, vector_status, vector_id
        FROM basis_document_chunks
        WHERE id=? AND basis_document_id=?
        """,
        (values.get("basis_chunk_id"), values.get("basis_document_id")),
    ).fetchone()
    if not chunk:
        return "basis chunk does not exist"
    if chunk["vector_status"] != "indexed" or not clean_text(chunk["vector_id"]):
        return "basis chunk must be indexed before approval"
    return ""


def prepare_basis_rule_candidate_update(
    conn: sqlite3.Connection,
    current: dict[str, Any],
    payload: dict[str, Any],
    forced_status: str = "",
    reviewed_at_now: str = "",
) -> tuple[dict[str, Any] | None, str]:
    next_values = {
        "rule_type": clean_text(payload.get("rule_type"), current["rule_type"]),
        "condition_text": clean_text(payload.get("condition_text"), current["condition_text"]),
        "target_scope": clean_text(payload.get("target_scope"), current["target_scope"]),
        "required_evidence_types": payload.get("required_evidence_types", current["required_evidence_types"]),
        "related_profile_fields": payload.get("related_profile_fields", current["related_profile_fields"]),
        "citation_candidate_id": clean_text(payload.get("citation_candidate_id"), current["citation_candidate_id"]),
        "confidence": current["confidence"],
        "status": forced_status or clean_text(payload.get("status"), current["status"]),
        "review_note": clean_text(payload.get("review_note"), current.get("review_note", "")),
        "reviewer_name": clean_text(payload.get("reviewer_name"), current.get("reviewer_name", "")) or "local_admin",
        "basis_document_id": current["basis_document_id"],
        "basis_chunk_id": current["basis_chunk_id"],
    }
    if "confidence" in payload:
        try:
            next_values["confidence"] = float(payload.get("confidence"))
        except (TypeError, ValueError):
            return None, "confidence must be a number"
    if not isinstance(next_values["required_evidence_types"], list):
        return None, "required_evidence_types must be a list"
    if not isinstance(next_values["related_profile_fields"], list):
        return None, "related_profile_fields must be a list"
    if next_values["status"] not in BASIS_RULE_CANDIDATE_STATUSES:
        return None, "Unsupported status"
    if next_values["status"] == "approved":
        error = validate_basis_rule_candidate_approval(conn, next_values)
        if error:
            return None, error

    status_changed = next_values["status"] != current["status"]
    if next_values["status"] in {"approved", "rejected"} and status_changed:
        next_values["reviewed_at"] = reviewed_at_now
    elif next_values["status"] == "needs_review" and status_changed:
        next_values["reviewed_at"] = ""
        next_values["reviewer_name"] = ""
    elif next_values["status"] == "archived" and status_changed:
        next_values["reviewed_at"] = current.get("reviewed_at", "")
        next_values["reviewer_name"] = current.get("reviewer_name", "") or next_values["reviewer_name"]
    else:
        next_values["reviewed_at"] = current.get("reviewed_at", "")

    return next_values, ""


def basis_rule_candidate_match_score(requirement: dict[str, Any], candidate: dict[str, Any]) -> float:
    query_text = " ".join(
        [
            clean_text(requirement.get("required_value")),
            clean_text(requirement.get("source_text")),
            " ".join(requirement.get("required_evidence_types") or []),
        ]
    )
    query_tokens = set(basis_tokenize(query_text))
    if not query_tokens:
        return 0
    candidate_text = " ".join(
        [
            clean_text(candidate.get("condition_text")),
            clean_text(candidate.get("target_scope")),
            " ".join(candidate.get("required_evidence_types") or []),
            " ".join(candidate.get("related_profile_fields") or []),
        ]
    )
    candidate_vector = basis_vector_for_text(candidate_text)
    shared = sum(1 for token in query_tokens if candidate_vector.get(token, 0) > 0)
    if shared <= 0:
        return 0
    text_score = shared / max(len(query_tokens), 1)
    rule_type = clean_text(candidate.get("rule_type"))
    requirement_type = clean_text(requirement.get("requirement_type"))
    rule_type_bonus = 0.15 if rule_type == requirement_type else 0.05 if rule_type == "basis_rule" else 0
    try:
        confidence = float(candidate.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0
    confidence_bonus = min(max(confidence, 0), 1) * 0.1
    return round(min(1.0, text_score + rule_type_bonus + confidence_bonus), 4)


def merge_citation_results(primary: list[dict[str, Any]], fallback: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in primary + fallback:
        citation_id = clean_text(result.get("citation_candidate_id"))
        if not citation_id or citation_id in seen:
            continue
        seen.add(citation_id)
        merged.append(result)
        if len(merged) >= max(1, min(top_k, 20)):
            break
    return merged
