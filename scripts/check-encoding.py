from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCAN_TARGETS = [
    ROOT_DIR / "backend" / "app",
    ROOT_DIR / "backend" / "tests",
    ROOT_DIR / "scripts",
    ROOT_DIR / "docs",
    ROOT_DIR / "README.md",
    ROOT_DIR / "AGENTS.md",
]
TEXT_EXTENSIONS = {".py", ".ps1", ".md", ".txt", ".json", ".toml", ".yml", ".yaml"}
EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".venv", "venv", ".venv313", "node_modules", "dist", "storage", "temp"}

MOJIBAKE_TOKENS = [
    "\ufffd",
    "\u00c3",
    "\u00c2",
    "\u00ec",
    "\u00ed",
    "\u00ee",
    "\u00ef",
    "\u00ea",
    "\u00eb",
    "\u00e3",
    "\u00e2",
    "\u00f0",
    "\u7570",
    "\u5a9b",
    "\u5bc3",
    "\u63f4",
    "\u4ee5",
    "\uf9dd",
    "\u8084",
    "\u6f61",
    "\u613f",
    "\u8881",
    "\ub0c5\ub732",
    "\ub304\ub4dc",
    "\uae45\uae43",
    "\ub4e6\ub099",
    "\ub5ce\ub2e4",
]


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for target in SCAN_TARGETS:
        if not target.exists():
            continue
        if target.is_file():
            files.append(target)
            continue
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in EXCLUDED_DIRS]
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix.lower() in TEXT_EXTENSIONS or ".env" in path.name:
                    files.append(path)
    return sorted(set(files))


def scan_file(path: Path) -> list[str]:
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [f"UTF-8 decode failed: {exc}"]

    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if any(token in line for token in MOJIBAKE_TOKENS):
            findings.append(f"L{line_number}: possible mojibake: {line[:160]}")
    return findings


def main() -> int:
    findings: list[tuple[Path, list[str]]] = []
    for path in iter_text_files():
        file_findings = scan_file(path)
        if file_findings:
            findings.append((path, file_findings))

    if findings:
        print("ENCODING_CHECK_FAILED")
        for path, file_findings in findings:
            print(f"\n{path.relative_to(ROOT_DIR)}")
            for finding in file_findings[:20]:
                print(f"  {finding}")
        return 1

    print("ENCODING_CHECK_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
