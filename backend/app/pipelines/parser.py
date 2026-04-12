from pathlib import Path


def extract_text_from_file(file_path: str) -> tuple[str, str]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf_text(path), "pdf"
    if suffix == ".docx":
        return _extract_docx_text(path), "docx"

    raise ValueError("Unsupported file type. Only PDF and DOCX are allowed.")


def _extract_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    text_parts: list[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()


def _extract_docx_text(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(parts).strip()
