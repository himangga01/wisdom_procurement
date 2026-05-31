import re
from typing import Any

from app.core.text import clean_text


BASIS_CITATION_ID_RE = re.compile(r"^basis:(\d+):chunk:(\d+)$")


def expected_basis_citation_candidate_id(basis_document_id: Any, basis_chunk_id: Any) -> str:
    return f"basis:{basis_document_id}:chunk:{basis_chunk_id}"


def parse_basis_citation_candidate_id(value: Any) -> tuple[int, int] | None:
    match = BASIS_CITATION_ID_RE.match(clean_text(value))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))
