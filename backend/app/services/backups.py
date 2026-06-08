import hashlib
import json
import sqlite3
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.logging import get_logger, log_event, log_exception

KST = timezone(timedelta(hours=9))
LOGGER = get_logger("services.backups")
BACKUP_VERSION = "phase4_backup_v1"
REQUIRED_STORAGE_DIRS = [
    "uploads",
    "corporation-evidence",
    "basis",
    "basis-index",
    "nara-notices",
    "contracts",
]


def _is_env_file(rel_path: str) -> bool:
    return any(part == ".env" or part.startswith(".env.") for part in rel_path.split("/"))


def _now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def _timestamp() -> str:
    return datetime.now(KST).strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_sqlite_snapshot(sqlite_path: Path, snapshot_path: Path) -> None:
    if snapshot_path.exists():
        snapshot_path.unlink()
    log_event(
        LOGGER,
        "backup.sqlite_snapshot.started",
        sqlite_path=str(sqlite_path),
        snapshot_path=str(snapshot_path),
    )
    source = sqlite3.connect(f"file:{sqlite_path}?mode=ro", uri=True)
    target = sqlite3.connect(str(snapshot_path))
    try:
        source.backup(target)
        log_event(
            LOGGER,
            "backup.sqlite_snapshot.completed",
            snapshot_path=str(snapshot_path),
            file_size_bytes=snapshot_path.stat().st_size if snapshot_path.exists() else 0,
        )
    finally:
        target.close()
        source.close()


def backup_run_payload(row: sqlite3.Row | dict) -> dict[str, Any]:
    payload = dict(row)
    for key in ["manifest_json", "validation_json"]:
        raw = payload.pop(key, "{}")
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {}
        payload[key.replace("_json", "")] = parsed if isinstance(parsed, dict) else {}
    return payload


def _add_directory(zip_file: zipfile.ZipFile, root: Path, archive_root: str) -> list[str]:
    included: list[str] = []
    if not root.exists():
        return included
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith("backups/") or rel.endswith(".tmp") or _is_env_file(rel):
            continue
        archive_name = f"{archive_root}/{rel}"
        zip_file.write(path, archive_name)
        included.append(archive_name)
    return included


def create_backup_run(conn: sqlite3.Connection, *, sqlite_path: Path, storage_root: Path) -> dict[str, Any]:
    backup_root = storage_root / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    now = _now_iso()
    log_event(
        LOGGER,
        "backup.create.started",
        sqlite_path=str(sqlite_path),
        storage_root=str(storage_root),
    )
    cur = conn.execute(
        """
        INSERT INTO backup_runs (
          backup_type, status, file_name, file_path, manifest_json,
          validation_json, created_at, updated_at
        ) VALUES ('full_local', 'running', '', '', '{}', '{}', ?, ?)
        """,
        (now, now),
    )
    backup_id = cur.lastrowid
    file_name = f"smart-procurement-backup-{_timestamp()}-{backup_id}.zip"
    backup_path = backup_root / file_name
    snapshot_path = backup_root / f"{file_name}.db.snapshot.tmp"

    try:
        if not sqlite_path.exists():
            raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")
        create_sqlite_snapshot(sqlite_path, snapshot_path)

        manifest: dict[str, Any] = {
            "backup_version": BACKUP_VERSION,
            "created_at": now,
            "app_name": "SMART 조달청 계산기",
            "database": {
                "path": "database/app.db",
                "sha256": sha256_file(snapshot_path),
            },
            "basis_index": {
                "path": "storage/basis-index/basis-index.json",
                "status": "missing",
                "sha256": "",
            },
            "storage": {
                "included_paths": [f"storage/{name}" for name in REQUIRED_STORAGE_DIRS],
                "included_file_count": 0,
            },
            "notes": [".env and raw API keys are not included."],
        }
        basis_index_path = storage_root / "basis-index" / "basis-index.json"
        if basis_index_path.exists():
            manifest["basis_index"] = {
                "path": "storage/basis-index/basis-index.json",
                "status": "included",
                "sha256": sha256_file(basis_index_path),
            }

        included_files: list[str] = []
        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(snapshot_path, "database/app.db")
            included_files.append("database/app.db")
            for directory_name in REQUIRED_STORAGE_DIRS:
                included_files.extend(_add_directory(zip_file, storage_root / directory_name, f"storage/{directory_name}"))
            manifest["storage"]["included_file_count"] = len([path for path in included_files if path.startswith("storage/")])
            zip_file.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            included_files.append("manifest.json")

        validation = validate_backup_file(backup_path)
        if validation["valid"]:
            log_event(
                LOGGER,
                "backup.validation.completed",
                backup_id=backup_id,
                file_name=file_name,
                file_size_bytes=backup_path.stat().st_size,
                warning_count=len(validation.get("warnings", [])),
            )
        else:
            log_event(
                LOGGER,
                "backup.validation.failed",
                level="warning",
                backup_id=backup_id,
                file_name=file_name,
                error_count=len(validation.get("errors", [])),
                warning_count=len(validation.get("warnings", [])),
            )
        completed_at = _now_iso()
        conn.execute(
            """
            UPDATE backup_runs
            SET status=?, file_name=?, file_path=?, file_size_bytes=?,
                manifest_json=?, validation_json=?, error_message='',
                completed_at=?, updated_at=?
            WHERE id=?
            """,
            (
                "completed" if validation["valid"] else "failed",
                file_name,
                str(backup_path),
                backup_path.stat().st_size,
                json.dumps(manifest, ensure_ascii=False),
                json.dumps(validation, ensure_ascii=False),
                completed_at,
                completed_at,
                backup_id,
            ),
        )
        log_event(
            LOGGER,
            "backup.create.completed",
            backup_id=backup_id,
            status="completed" if validation["valid"] else "failed",
            file_name=file_name,
            included_file_count=len(included_files),
        )
    except Exception as exc:
        log_exception(
            LOGGER,
            "backup.create.failed",
            exc,
            backup_id=backup_id,
            file_name=file_name,
            sqlite_path=str(sqlite_path),
            storage_root=str(storage_root),
        )
        completed_at = _now_iso()
        validation = {
            "valid": False,
            "errors": [str(exc)],
            "warnings": [],
            "manifest": {},
            "file_path": str(backup_path),
            "file_size_bytes": backup_path.stat().st_size if backup_path.exists() else 0,
        }
        conn.execute(
            """
            UPDATE backup_runs
            SET status='failed', file_name=?, file_path=?, file_size_bytes=?,
                validation_json=?, error_message=?,
                completed_at=?, updated_at=?
            WHERE id=?
            """,
            (
                file_name,
                str(backup_path),
                validation["file_size_bytes"],
                json.dumps(validation, ensure_ascii=False),
                str(exc),
                completed_at,
                completed_at,
                backup_id,
            ),
        )
    finally:
        try:
            snapshot_path.unlink(missing_ok=True)
        except OSError:
            pass

    row = conn.execute("SELECT * FROM backup_runs WHERE id=?", (backup_id,)).fetchone()
    return backup_run_payload(row)


def validate_backup_file(path: Path) -> dict[str, Any]:
    log_event(LOGGER, "backup.validate.started", file_path=str(path))
    result: dict[str, Any] = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "manifest": {},
        "file_path": str(path),
        "file_size_bytes": path.stat().st_size if path.exists() else 0,
    }
    if not path.exists():
        result["errors"].append("Backup file does not exist.")
        log_event(LOGGER, "backup.validate.failed", level="warning", file_path=str(path), error_count=1)
        return result
    try:
        with zipfile.ZipFile(path, "r") as zip_file:
            names = set(zip_file.namelist())
            if "manifest.json" not in names:
                result["errors"].append("manifest.json is missing.")
                return result
            manifest = json.loads(zip_file.read("manifest.json").decode("utf-8"))
            result["manifest"] = manifest if isinstance(manifest, dict) else {}
            if result["manifest"].get("backup_version") != BACKUP_VERSION:
                result["errors"].append("Unsupported backup version.")
            db_path = result["manifest"].get("database", {}).get("path")
            db_sha = result["manifest"].get("database", {}).get("sha256")
            if not db_path or db_path not in names:
                result["errors"].append("Database backup is missing.")
            elif db_sha:
                digest = hashlib.sha256(zip_file.read(db_path)).hexdigest()
                if digest != db_sha:
                    result["errors"].append("Database checksum mismatch.")
            basis_index = result["manifest"].get("basis_index", {})
            if isinstance(basis_index, dict) and basis_index.get("status") == "included":
                index_path = basis_index.get("path")
                index_sha = basis_index.get("sha256")
                if not index_path or index_path not in names:
                    result["errors"].append("Basis index backup is missing.")
                elif index_sha:
                    digest = hashlib.sha256(zip_file.read(index_path)).hexdigest()
                    if digest != index_sha:
                        result["errors"].append("Basis index checksum mismatch.")
            leaked = [name for name in names if _is_env_file(name)]
            if leaked:
                result["errors"].append(".env files must not be included.")
            for directory_name in REQUIRED_STORAGE_DIRS:
                prefix = f"storage/{directory_name}/"
                if not any(name.startswith(prefix) for name in names):
                    result["warnings"].append(f"{prefix} has no files in this backup.")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        log_exception(LOGGER, "backup.validate.exception", exc, file_path=str(path))
        result["errors"].append(str(exc))
    result["valid"] = not result["errors"]
    log_event(
        LOGGER,
        "backup.validate.completed" if result["valid"] else "backup.validate.failed",
        level="info" if result["valid"] else "warning",
        file_path=str(path),
        valid=result["valid"],
        error_count=len(result["errors"]),
        warning_count=len(result["warnings"]),
    )
    return result


def restore_plan_for_backup(path: Path) -> dict[str, Any]:
    log_event(LOGGER, "backup.restore_plan.started", file_path=str(path))
    validation = validate_backup_file(path)
    log_event(
        LOGGER,
        "backup.restore_plan.completed",
        file_path=str(path),
        can_restore=bool(validation["valid"]),
        error_count=len(validation.get("errors", [])),
    )
    return {
        "dry_run": True,
        "can_restore": bool(validation["valid"]),
        "validation": validation,
        "restore_steps": [
            "Validate manifest and checksums.",
            "Create a safety backup of the current DB and storage.",
            "Stop or restart the local app before replacing files.",
            "Restore database/app.db and storage/* from the backup archive.",
            "Run health check and operations summary after restart.",
        ],
        "policy": "Phase 4D exposes restore dry-run only. Direct file replacement is intentionally not enabled yet.",
    }


def list_backup_runs_payload(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM backup_runs ORDER BY id DESC").fetchall()
    return [backup_run_payload(row) for row in rows]


def get_backup_run_payload(conn: sqlite3.Connection, backup_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM backup_runs WHERE id=?", (backup_id,)).fetchone()
    return backup_run_payload(row) if row else None
