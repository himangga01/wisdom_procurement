
def maybe_run_ocr(extracted_text: str) -> tuple[str, str]:
    """Return text and OCR status.

    Phase 1 starts with a lightweight fallback.
    If parser extracted enough text, OCR is skipped.
    """
    if extracted_text and len(extracted_text.strip()) > 80:
        return extracted_text, "skipped"

    # OCR integration point for scanned PDFs.
    # TODO(phase1): Plug tesseract/paddle OCR implementation.
    return extracted_text, "needs_ocr"
