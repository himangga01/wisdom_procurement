"""RHWP CLI adapter. Document text is data; source files are never edited in place."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

HWP_EXTENSIONS = {".hwp", ".hwpx"}
BACKEND_DIR = Path(__file__).resolve().parents[2]
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024


class HwpEngineError(RuntimeError):
    def __init__(self, message: str, *, code: str = "hwp_processing_failed", status_code: int = 422):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class HwpReadResult:
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HwpWriteResult:
    output_path: Path
    output_format: str
    replaced_count: int
    page_count: int


def _local_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


def _configured_command() -> list[str]:
    explicit = os.getenv("RHWP_BIN_PATH", "").strip()
    if explicit:
        return [str(_local_path(explicit))]
    executable = "rhwp.exe" if os.name == "nt" else "rhwp"
    candidates = [BACKEND_DIR / "tools" / "rhwp" / executable]
    source_root = os.getenv("RHWP_SOURCE_DIR", "").strip()
    if source_root:
        candidates.extend(_local_path(source_root) / "target" / build / executable for build in ("release", "debug"))
    for path in candidates:
        if path.is_file():
            return [str(path)]
    return [shutil.which("rhwp") or str(candidates[0])]


class HwpEngine:
    def __init__(self, *, command: Sequence[str] | None = None, timeout_seconds: float | None = None):
        self.command = list(command) if command is not None else _configured_command()
        try:
            self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else os.getenv("RHWP_TIMEOUT_SECONDS", "60"))
        except ValueError:
            self.timeout_seconds = 60.0
        if not 0 < self.timeout_seconds <= 600:
            raise HwpEngineError("HWP 처리 시간 제한 설정이 올바르지 않습니다.", code="hwp_invalid_configuration", status_code=503)
        self.expected_version = os.getenv("RHWP_EXPECTED_VERSION", "0.8.6").strip()

    def status(self) -> dict[str, Any]:
        version = ""
        try:
            result = subprocess.run(self.command + ["--version"], stdin=subprocess.DEVNULL, capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=min(5, self.timeout_seconds),
                                    env={**os.environ, "PYTHONUTF8": "1"})
            match = re.fullmatch(r"rhwp v([0-9]+\.[0-9]+\.[0-9]+)", result.stdout.strip())
            if result.returncode == 0 and match:
                version = match.group(1)
        except (OSError, subprocess.TimeoutExpired):
            pass
        available = bool(version) and version == self.expected_version
        return {"engine": "rhwp", "available": available, "version": version,
                "expected_version": self.expected_version, "read_formats": ["hwp", "hwpx"],
                "write_formats": ["hwp", "hwpx"], "status": "ready" if available else "needs_hwp_setup"}

    def _ensure_available(self, deadline: float) -> None:
        if not self.status()["available"]:
            if time.monotonic() >= deadline:
                raise HwpEngineError("HWP 처리 시간이 초과되었습니다.", code="hwp_timeout", status_code=504)
            raise HwpEngineError("HWP 엔진을 사용할 수 없습니다. RHWP 설치와 버전 설정을 확인하세요.",
                                 code="needs_hwp_setup", status_code=503)

    @staticmethod
    def _validate_source(path: Path) -> None:
        if path.suffix.lower() not in HWP_EXTENSIONS or not path.is_file():
            raise HwpEngineError("HWP 또는 HWPX 원본 파일이 필요합니다.", code="hwp_invalid_source", status_code=400)
        if not 0 < path.stat().st_size <= MAX_SOURCE_BYTES:
            raise HwpEngineError("한글 문서 크기는 50 MiB 이하여야 합니다.", code="hwp_size_limit", status_code=413)
        with path.open("rb") as source:
            magic = source.read(8)
        if path.suffix.lower() == ".hwp":
            if magic != bytes.fromhex("d0cf11e0a1b11ae1"):
                raise HwpEngineError("올바른 HWP 5 문서가 아닙니다.", code="hwp_invalid_source")
        else:
            try:
                with zipfile.ZipFile(path) as archive:
                    entries = archive.infolist()
                    if len(entries) > 10000 or sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES:
                        raise HwpEngineError("HWPX 압축 해제 크기 제한을 초과했습니다.", code="hwp_size_limit", status_code=413)
                    if not any(entry.filename.startswith("Contents/section") and entry.filename.endswith(".xml") for entry in entries):
                        raise HwpEngineError("HWPX 본문이 없습니다.", code="hwp_invalid_source")
            except zipfile.BadZipFile as exc:
                raise HwpEngineError("올바른 HWPX 문서가 아닙니다.", code="hwp_invalid_source") from exc

    @staticmethod
    def _temporary_root() -> Path:
        value = os.getenv("RHWP_TEMP_DIR", "").strip()
        root = _local_path(value) if value else _local_path(os.getenv("STORAGE_ROOT", "./storage")) / "hwp-temp"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _run(self, args: list[str], deadline: float, *, json_output: bool = False) -> dict[str, Any]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise HwpEngineError("HWP 처리 시간이 초과되었습니다.", code="hwp_timeout", status_code=504)
        try:
            result = subprocess.run(self.command + args, stdin=subprocess.DEVNULL, capture_output=True,
                                    encoding="utf-8", errors="strict", timeout=remaining,
                                    env={**os.environ, "PYTHONUTF8": "1"})
        except subprocess.TimeoutExpired as exc:
            raise HwpEngineError("HWP 처리 시간이 초과되었습니다.", code="hwp_timeout", status_code=504) from exc
        except OSError as exc:
            raise HwpEngineError("HWP 엔진 실행 파일을 확인하세요.", code="needs_hwp_setup", status_code=503) from exc
        if result.returncode != 0:
            code = "hwp_verification_failed" if result.returncode in (3, 4) else "hwp_processing_failed"
            raise HwpEngineError("한글 문서를 처리하거나 저장본을 검증하지 못했습니다.", code=code)
        if not json_output:
            return {}
        try:
            payload = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise HwpEngineError("HWP 엔진 응답 형식이 올바르지 않습니다.", code="hwp_invalid_response") from exc
        if not isinstance(payload, dict) or payload.get("schemaVersion") != "1.0":
            raise HwpEngineError("지원하지 않는 HWP 엔진 응답입니다.", code="hwp_invalid_response")
        return payload

    def _extract(self, path: Path, deadline: float, *, allow_empty: bool = False) -> HwpReadResult:
        payload = self._run(["export-text", str(path), "--json", "--max-chars", "1000000"], deadline, json_output=True)
        pages = payload.get("pages")
        count = payload.get("pageCount")
        if type(count) is not int or not 1 <= count <= 500 or not isinstance(pages, list) or len(pages) != count:
            raise HwpEngineError("한글 문서의 페이지 정보를 확인할 수 없습니다.", code="hwp_invalid_response")
        if payload.get("truncated") is not False or payload.get("omittedCount") != 0:
            raise HwpEngineError("문서가 너무 길어 전체 텍스트를 읽지 못했습니다.", code="hwp_text_truncated")
        for index, page in enumerate(pages):
            if not isinstance(page, dict) or type(page.get("page")) is not int or page["page"] != index or not isinstance(page.get("text"), str):
                raise HwpEngineError("한글 문서의 페이지 순서 또는 텍스트가 올바르지 않습니다.", code="hwp_invalid_response")
        text = "\n\n".join(page["text"].strip() for page in pages).strip()
        if not text and not allow_empty:
            raise HwpEngineError("한글 문서에서 분석할 텍스트를 찾지 못했습니다.", code="hwp_insufficient_text")
        return HwpReadResult(text, {"engine": "rhwp", "engine_version": self.expected_version, "page_count": count,
            "char_count": len(text), "needs_ocr": False, "truncated": False, "omitted_count": 0,
            "untrusted_content": True,
            "pages": [{"page_number": page["page"] + 1, "char_count": len(page["text"])} for page in pages]})

    def read(self, source_path: str | Path) -> HwpReadResult:
        source = Path(source_path).resolve()
        self._validate_source(source)
        deadline = time.monotonic() + self.timeout_seconds
        self._ensure_available(deadline)
        with tempfile.TemporaryDirectory(prefix="read-", dir=self._temporary_root()) as raw:
            isolated = Path(raw) / ("source" + source.suffix.lower())
            shutil.copyfile(source, isolated)
            return self._extract(isolated, deadline)

    def write(self, source_path: str | Path, output_path: str | Path, *, find: str | None = None,
              replace: str = "") -> HwpWriteResult:
        source, destination = Path(source_path).resolve(), Path(output_path).resolve()
        self._validate_source(source)
        if destination.suffix.lower() not in HWP_EXTENSIONS or source == destination or destination.exists():
            raise HwpEngineError("원본과 다른 새 HWP/HWPX 출력 경로가 필요합니다.", code="hwp_invalid_output", status_code=400)
        if find is not None and (not isinstance(find, str) or not find or len(find) > 10000):
            raise HwpEngineError("치환할 문자열을 입력하세요. 최대 10,000자입니다.", code="hwp_invalid_edit", status_code=400)
        if not isinstance(replace, str) or len(replace) > 10000 or "\x00" in replace or (find is not None and "\x00" in find):
            raise HwpEngineError("치환 문자열이 올바르지 않습니다.", code="hwp_invalid_edit", status_code=400)
        deadline = time.monotonic() + self.timeout_seconds
        self._ensure_available(deadline)
        destination.parent.mkdir(parents=True, exist_ok=True)
        replaced = 0
        with tempfile.TemporaryDirectory(prefix="write-", dir=self._temporary_root()) as raw:
            root = Path(raw)
            current = root / ("source" + source.suffix.lower())
            shutil.copyfile(source, current)
            original_text = self._extract(current, deadline, allow_empty=True).text
            expected_text = original_text
            if find is not None:
                edited = root / ("edited" + source.suffix.lower())
                payload = self._run(["edit", "replace-text", str(current), "--find", find, "--replace", replace,
                                     "-o", str(edited), "--json"], deadline, json_output=True)
                replaced = payload.get("replacedCount", 0)
                if type(replaced) is not int or replaced <= 0 or not edited.is_file():
                    raise HwpEngineError("치환할 문자열을 찾지 못했습니다. 원본은 변경하지 않았습니다.", code="hwp_no_matches")
                compact = lambda value: re.sub(r"\s+", "", value)
                expected_candidates = set()
                if original_text.count(find) == replaced:
                    expected_candidates.add(compact(original_text.replace(find, replace)))
                compact_find = compact(find)
                if compact_find and compact(original_text).count(compact_find) == replaced:
                    expected_candidates.add(compact(original_text).replace(compact_find, compact(replace)))
                edited_text = self._extract(edited, deadline, allow_empty=True).text
                if compact(edited_text) not in expected_candidates:
                    raise HwpEngineError("치환 요청 외의 내용이 달라진 저장본을 감지했습니다. 원본은 보존했습니다.",
                                         code="hwp_edit_verification_failed")
                expected_text = edited_text
                current = edited
            saved = root / ("output" + destination.suffix.lower())
            if saved.suffix == ".hwpx":
                self._run(["export-hwpx", str(current), str(saved), "--verify", "--verify-pages", "--json"], deadline, json_output=True)
            else:
                self._run(["convert", str(current), str(saved), "--verify", "--verify-pages"], deadline)
            self._validate_source(saved)
            checked = self._extract(saved, deadline, allow_empty=True)
            if re.sub(r"\s+", "", expected_text) != re.sub(r"\s+", "", checked.text):
                raise HwpEngineError(
                    "형식 변환 과정에서 본문 또는 항목 번호가 달라졌습니다. 원래 문서 형식으로 내보내세요.",
                    code="hwp_text_verification_failed",
                )
            # Exclusive creation protects existing files even if another writer wins a race.
            try:
                with destination.open("xb") as target, saved.open("rb") as completed:
                    shutil.copyfileobj(completed, target)
            except FileExistsError as exc:
                raise HwpEngineError("출력 파일이 이미 존재합니다.", code="hwp_invalid_output", status_code=409) from exc
            except OSError:
                destination.unlink(missing_ok=True)
                raise
        return HwpWriteResult(destination, destination.suffix[1:].lower(), replaced, checked.metadata["page_count"])


def hwp_engine_status() -> dict[str, Any]:
    return HwpEngine().status()
