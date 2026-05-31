import json
import os
import unittest
from pathlib import Path
from typing import Any


TESTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TESTS_DIR.parents[1]
DEFAULT_NOTICE_SAMPLE_DIR = TESTS_DIR / "nara-notice-pdf-samples"


def resolve_sample_manifest(
    phase_env_var: str,
    legacy_sample_dir: Path,
) -> Path:
    explicit_phase_manifest = os.getenv(phase_env_var)
    if explicit_phase_manifest:
        return Path(explicit_phase_manifest)

    explicit_notice_manifest = os.getenv("NARA_NOTICE_PDF_SAMPLE_MANIFEST")
    if explicit_notice_manifest:
        return Path(explicit_notice_manifest)

    shared_manifest = DEFAULT_NOTICE_SAMPLE_DIR / "manifest.json"
    if shared_manifest.exists():
        return shared_manifest

    return legacy_sample_dir / "manifest.json"


def load_sample_manifest(
    phase_env_var: str,
    legacy_sample_dir: Path,
    min_samples: int,
    label: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], Path]:
    manifest_path = resolve_sample_manifest(phase_env_var, legacy_sample_dir)
    if not manifest_path.exists():
        raise unittest.SkipTest(f"{label} sample manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    samples = manifest.get("samples") or []
    if len(samples) < min_samples:
        raise unittest.SkipTest(f"{label} requires at least {min_samples} downloaded Nara PDF samples.")
    return manifest, samples, manifest_path


def sample_path(sample: dict[str, Any]) -> Path:
    saved_path = Path(sample.get("saved_path", ""))
    if saved_path.is_absolute():
        return saved_path
    return ROOT_DIR / saved_path
