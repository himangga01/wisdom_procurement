import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz


OCR_STATUS_SKIPPED = "skipped"
OCR_STATUS_COMPLETED = "completed"
OCR_STATUS_NEEDS_OCR = "needs_ocr"
OCR_STATUS_NEEDS_SETUP = "needs_ocr_setup"
OCR_STATUS_UNAVAILABLE = "unavailable"
OCR_STATUS_FAILED = "failed"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SUPPORTED_OCR_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | {".pdf"}


@dataclass(frozen=True)
class OcrPageResult:
    page_number: int | None
    text: str
    confidence: float | None = None
    boxes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "confidence": self.confidence,
            "boxes": self.boxes,
        }


@dataclass(frozen=True)
class OcrResult:
    text: str
    status: str
    engine: str
    language: str
    page_count: int = 0
    pages: list[OcrPageResult] = field(default_factory=list)
    average_confidence: float | None = None
    warnings: list[str] = field(default_factory=list)
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "status": self.status,
            "engine": self.engine,
            "language": self.language,
            "page_count": self.page_count,
            "pages": [page.to_dict() for page in self.pages],
            "average_confidence": self.average_confidence,
            "warnings": self.warnings,
            "error_message": self.error_message,
        }


class OcrEngine:
    name = "base"

    def __init__(self, language: str) -> None:
        self.language = language

    def is_available(self) -> bool:
        raise NotImplementedError

    def unavailable_reason(self) -> str:
        return ""

    def recognize_image(self, image_path: Path, page_number: int | None = None) -> OcrResult:
        raise NotImplementedError


class NoopOcrEngine(OcrEngine):
    name = "noop"

    def is_available(self) -> bool:
        return False

    def unavailable_reason(self) -> str:
        return "OCR engine is disabled or not configured."

    def recognize_image(self, image_path: Path, page_number: int | None = None) -> OcrResult:
        return _unavailable_result(self.name, self.language, self.unavailable_reason())


class PaddleOcrEngine(OcrEngine):
    name = "paddle"

    def __init__(self, language: str) -> None:
        super().__init__(language)
        self._ocr = None
        self._unavailable_reason = ""

    def is_available(self) -> bool:
        try:
            self._get_ocr()
            return True
        except Exception as exc:
            self._unavailable_reason = str(exc)
            return False

    def unavailable_reason(self) -> str:
        if self._unavailable_reason:
            return self._unavailable_reason
        try:
            self._get_ocr()
        except Exception as exc:
            self._unavailable_reason = str(exc)
        return self._unavailable_reason

    def recognize_image(self, image_path: Path, page_number: int | None = None) -> OcrResult:
        try:
            ocr = self._get_ocr()
            with _ascii_safe_image_path(image_path) as safe_image_path:
                raw = _predict_with_paddle(ocr, safe_image_path)
            texts, scores, boxes = _parse_paddle_output(raw)
            text = "\n".join(item for item in texts if item).strip()
            confidence = _average(scores)
            page = OcrPageResult(page_number=page_number, text=text, confidence=confidence, boxes=boxes)
            return OcrResult(
                text=text,
                status=OCR_STATUS_COMPLETED if text else OCR_STATUS_FAILED,
                engine=self.name,
                language=self.language,
                page_count=1,
                pages=[page],
                average_confidence=confidence,
                warnings=[] if text else ["OCR completed but returned no text."],
            )
        except Exception as exc:
            return OcrResult(
                text="",
                status=OCR_STATUS_FAILED,
                engine=self.name,
                language=self.language,
                page_count=1,
                error_message=str(exc),
            )

    def _get_ocr(self):
        if self._ocr is not None:
            return self._ocr

        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "paddleocr is not installed. Install OCR dependencies into the Python 3.13 runtime."
            ) from exc

        lang = _paddle_language(self.language)
        try:
            self._ocr = PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except TypeError:
            # Older PaddleOCR versions use different option names.
            self._ocr = PaddleOCR(lang=lang, use_angle_cls=True)
        return self._ocr


class TesseractOcrEngine(OcrEngine):
    name = "tesseract"

    def __init__(self, language: str) -> None:
        super().__init__(language)
        self._unavailable_reason = ""

    def is_available(self) -> bool:
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception as exc:
            self._unavailable_reason = str(exc)
            return False

    def unavailable_reason(self) -> str:
        return self._unavailable_reason or "Tesseract is not available."

    def recognize_image(self, image_path: Path, page_number: int | None = None) -> OcrResult:
        try:
            import pytesseract

            with _ascii_safe_image_path(image_path) as safe_image_path:
                text = pytesseract.image_to_string(
                    str(safe_image_path),
                    lang=_tesseract_language(self.language),
                ).strip()
            page = OcrPageResult(page_number=page_number, text=text)
            return OcrResult(
                text=text,
                status=OCR_STATUS_COMPLETED if text else OCR_STATUS_FAILED,
                engine=self.name,
                language=self.language,
                page_count=1,
                pages=[page],
                warnings=[] if text else ["OCR completed but returned no text."],
            )
        except Exception as exc:
            return OcrResult(
                text="",
                status=OCR_STATUS_FAILED,
                engine=self.name,
                language=self.language,
                page_count=1,
                error_message=str(exc),
            )


def should_run_ocr(extracted_text: str, min_text_length: int | None = None) -> bool:
    threshold = min_text_length if min_text_length is not None else _int_env("OCR_MIN_TEXT_LENGTH", 80)
    return len((extracted_text or "").strip()) < threshold


def maybe_run_ocr(
    extracted_text: str,
    source_path: str | Path | None = None,
    kind: str = "",
    metadata: dict[str, Any] | None = None,
) -> tuple[str, str]:
    result = run_ocr_if_needed(extracted_text, source_path, kind, metadata)
    return result.text or extracted_text, result.status


def run_ocr_if_needed(
    extracted_text: str,
    source_path: str | Path | None = None,
    kind: str = "",
    metadata: dict[str, Any] | None = None,
) -> OcrResult:
    if not should_run_ocr(extracted_text):
        return OcrResult(
            text=extracted_text,
            status=OCR_STATUS_SKIPPED,
            engine="none",
            language=_ocr_language(),
            warnings=[],
        )

    if source_path is None:
        return OcrResult(
            text=extracted_text,
            status=OCR_STATUS_NEEDS_OCR,
            engine="none",
            language=_ocr_language(),
            warnings=["OCR is required, but source_path was not provided."],
        )

    result = run_ocr(source_path, kind=kind or (metadata or {}).get("kind", ""))
    if result.text:
        return result

    return OcrResult(
        text=extracted_text,
        status=result.status,
        engine=result.engine,
        language=result.language,
        page_count=result.page_count,
        pages=result.pages,
        average_confidence=result.average_confidence,
        warnings=result.warnings,
        error_message=result.error_message,
    )


def run_ocr(file_path: str | Path, kind: str = "") -> OcrResult:
    path = Path(file_path)
    suffix = path.suffix.lower()
    language = _ocr_language()

    if suffix not in SUPPORTED_OCR_EXTENSIONS:
        return OcrResult(
            text="",
            status=OCR_STATUS_UNAVAILABLE,
            engine=_ocr_engine_name(),
            language=language,
            error_message=f"Unsupported OCR file type: {suffix or 'unknown'}",
        )

    engine = get_ocr_engine()
    if not engine.is_available():
        return _unavailable_result(engine.name, language, engine.unavailable_reason())

    if suffix == ".pdf" or kind == "pdf":
        return _run_pdf_ocr(path, engine)
    return engine.recognize_image(path, page_number=None)


def get_ocr_engine() -> OcrEngine:
    language = _ocr_language()
    engine_name = _ocr_engine_name()
    if engine_name in {"paddle", "paddleocr"}:
        return PaddleOcrEngine(language)
    if engine_name in {"tesseract", "pytesseract"}:
        return TesseractOcrEngine(language)
    return NoopOcrEngine(language)


def _run_pdf_ocr(path: Path, engine: OcrEngine) -> OcrResult:
    dpi = _int_env("OCR_RENDER_DPI", 220)
    zoom = dpi / 72
    page_results: list[OcrPageResult] = []
    warnings: list[str] = []
    errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="wisdom_ocr_") as tmp:
        tmp_dir = Path(tmp)
        with fitz.open(path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                image_path = tmp_dir / f"page_{page_index}.png"
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                pixmap.save(image_path)

                page_result = engine.recognize_image(image_path, page_number=page_index)
                if page_result.status == OCR_STATUS_COMPLETED:
                    if page_result.pages:
                        page_results.extend(page_result.pages)
                    else:
                        page_results.append(
                            OcrPageResult(
                                page_number=page_index,
                                text=page_result.text,
                                confidence=page_result.average_confidence,
                            )
                        )
                else:
                    warnings.extend(page_result.warnings)
                    if page_result.error_message:
                        errors.append(f"page {page_index}: {page_result.error_message}")

    text = "\n\n".join(page.text for page in page_results if page.text).strip()
    confidence = _average([page.confidence for page in page_results if page.confidence is not None])
    status = OCR_STATUS_COMPLETED if text else OCR_STATUS_FAILED
    return OcrResult(
        text=text,
        status=status,
        engine=engine.name,
        language=engine.language,
        page_count=len(page_results),
        pages=page_results,
        average_confidence=confidence,
        warnings=warnings,
        error_message="; ".join(errors),
    )


def _predict_with_paddle(ocr: Any, image_path: Path) -> Any:
    if hasattr(ocr, "predict"):
        return ocr.predict(str(image_path))
    if hasattr(ocr, "ocr"):
        try:
            return ocr.ocr(str(image_path), cls=True)
        except TypeError:
            return ocr.ocr(str(image_path))
    raise RuntimeError("Unsupported PaddleOCR object: neither predict nor ocr is available.")


@contextmanager
def _ascii_safe_image_path(image_path: Path):
    try:
        str(image_path).encode("ascii")
        yield image_path
        return
    except UnicodeEncodeError:
        pass

    with tempfile.TemporaryDirectory(prefix="wisdom_ocr_path_") as tmp:
        safe_path = Path(tmp) / f"ocr_input{image_path.suffix.lower() or '.png'}"
        shutil.copy2(image_path, safe_path)
        yield safe_path


def _parse_paddle_output(raw: Any) -> tuple[list[str], list[float], list[dict[str, Any]]]:
    texts: list[str] = []
    scores: list[float] = []
    boxes: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if node is None:
            return

        json_payload = getattr(node, "json", None)
        if callable(json_payload):
            try:
                json_payload = json_payload()
            except TypeError:
                json_payload = None
        if isinstance(json_payload, dict):
            visit(json_payload)
            return

        if isinstance(node, dict):
            if isinstance(node.get("res"), dict):
                visit(node["res"])
            rec_texts = _as_sequence(node.get("rec_texts"))
            if rec_texts:
                texts.extend(str(item) for item in rec_texts if str(item).strip())
                rec_scores = _as_sequence(node.get("rec_scores"))
                scores.extend(_coerce_float(item) for item in rec_scores if _coerce_float(item) is not None)
            rec_polys = node.get("rec_polys")
            if rec_polys is None:
                rec_polys = node.get("rec_boxes")
            if rec_polys is None:
                rec_polys = node.get("dt_polys")
            rec_polys = _as_sequence(rec_polys)
            if rec_polys:
                boxes.extend({"points": item} for item in rec_polys)
            for key, value in node.items():
                if key not in {"res", "rec_texts", "rec_scores", "rec_polys", "rec_boxes", "dt_polys"}:
                    visit(value)
            return

        if isinstance(node, (list, tuple)):
            if _looks_like_paddle_v2_text_tuple(node):
                text = str(node[1][0]).strip()
                score = _coerce_float(node[1][1])
                if text:
                    texts.append(text)
                if score is not None:
                    scores.append(score)
                boxes.append({"points": node[0]})
                return

            if len(node) >= 2 and isinstance(node[0], str):
                text = node[0].strip()
                score = _coerce_float(node[1])
                if text:
                    texts.append(text)
                if score is not None:
                    scores.append(score)
                return

            for item in node:
                visit(item)

    visit(raw)
    return texts, scores, boxes


def _looks_like_paddle_v2_text_tuple(node: Any) -> bool:
    return (
        isinstance(node, (list, tuple))
        and len(node) >= 2
        and isinstance(node[1], (list, tuple))
        and len(node[1]) >= 2
        and isinstance(node[1][0], str)
    )


def _unavailable_result(engine: str, language: str, reason: str) -> OcrResult:
    return OcrResult(
        text="",
        status=OCR_STATUS_NEEDS_SETUP,
        engine=engine,
        language=language,
        warnings=["OCR engine is not available."],
        error_message=reason,
    )


def _paddle_language(language: str) -> str:
    normalized = language.lower().replace("_", "+")
    if "kor" in normalized or "ko" in normalized:
        return "korean"
    if "eng" in normalized or "en" in normalized:
        return "en"
    return normalized.split("+", 1)[0] or "korean"


def _tesseract_language(language: str) -> str:
    normalized = language.lower().replace(",", "+").replace(" ", "")
    if "kor" in normalized and "eng" in normalized:
        return "kor+eng"
    if "kor" in normalized or "ko" in normalized:
        return "kor"
    if "eng" in normalized or "en" in normalized:
        return "eng"
    return normalized or "kor+eng"


def _ocr_language() -> str:
    return os.getenv("OCR_LANG", os.getenv("OCR_LANGUAGES", "kor+eng")).strip() or "kor+eng"


def _ocr_engine_name() -> str:
    return os.getenv("OCR_ENGINE", "paddle").strip().lower() or "paddle"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: list[float | None]) -> float | None:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        try:
            converted = tolist()
            if isinstance(converted, list):
                return converted
        except Exception:
            return []
    return []
