import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
from docx import Document


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
        text, metadata = _extract_pdf_text(path)
        return ParsedDocument(text=text, kind="pdf", metadata=metadata)
    if suffix == ".docx":
        text = _extract_docx_text(path)
        return ParsedDocument(
            text=text,
            kind="docx",
            metadata={"engine": "python-docx", "char_count": len(text), "needs_ocr": False},
        )

    raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")


def _extract_pdf_text(path: Path) -> tuple[str, dict[str, Any]]:
    page_texts: list[str] = []
    page_metadata: list[dict[str, Any]] = []

    with fitz.open(path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            blocks = _order_blocks_for_reading(page, page.get_text("blocks", sort=False))
            block_texts = [_normalize_block_text(block[4]) for block in blocks if len(block) > 4 and block[4]]
            page_text = _normalize_procurement_text("\n".join(x for x in block_texts if x))
            page_texts.append(page_text)
            page_metadata.append(
                {
                    "page_number": page_index,
                    "char_count": len(page_text),
                    "block_count": len(block_texts),
                }
            )

    text = _normalize_procurement_text("\n\n".join(x for x in page_texts if x))
    metadata = {
        "engine": "PyMuPDF",
        "page_count": len(page_metadata),
        "char_count": len(text),
        "pages": page_metadata,
        "needs_ocr": len(text.strip()) < 80,
    }
    return text, metadata


def _order_blocks_for_reading(page: fitz.Page, blocks: list[tuple]) -> list[tuple]:
    if not blocks:
        return []

    page_width = float(page.rect.width)
    column_boundary = page_width * 0.52
    has_right_column = any(block[0] >= column_boundary for block in blocks)
    has_left_column = any(block[0] < column_boundary for block in blocks)

    if has_left_column and has_right_column:
        return sorted(blocks, key=lambda block: (0 if block[0] < column_boundary else 1, block[1], block[0]))

    return sorted(blocks, key=lambda block: (block[1], block[0]))


def _extract_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return _normalize_procurement_text("\n".join(parts))


def _normalize_block_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _normalize_procurement_text(text: str) -> str:
    text = text.replace("\u2024", ".")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Restore common procurement boundaries flattened by PDF text extraction.
    text = re.sub(r"(?<!\n)(?=\d+\.\s*[가-힣A-Za-z])", "\n", text)
    text = re.sub(r"(?<!\n)(?=[가-힣]\.\s*[가-힣A-Za-z])", "\n", text)
    text = re.sub(r"(?<=[가-힣)])(?=\d{4}\.\s*\d{1,2}\.\s*\d{1,2})", "\n", text)
    text = re.sub(r"(?<=원)(?=\s*[-가-힣])", "\n", text)

    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
