from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docx import Document

from app.pipelines.pdf_readers import read_pdf_document


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    kind: str
    metadata: dict[str, Any]


def extract_text_from_file(file_path: str | Path) -> tuple[str, str]:
    parsed = extract_document(file_path)
    return parsed.text, parsed.kind


def extract_document(file_path: str | Path) -> ParsedDocument:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        result = read_pdf_document(path)
        return ParsedDocument(text=result.text, kind="pdf", metadata=result.metadata)
    if suffix == ".docx":
        text = _extract_docx_text(path)
        return ParsedDocument(
            text=text,
            kind="docx",
            metadata={"engine": "python-docx", "char_count": len(text), "needs_ocr": False},
        )

    raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")


def _extract_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    text = "\n".join(parts).replace("\u2024", ".")
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
