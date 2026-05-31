import os
import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

KST = timezone(timedelta(hours=9))
FAILURE_STATUSES = {"failed", "partial_failed", "needs_ocr_setup", "unavailable", "not_configured"}
RUNNING_STATUSES = {"pending", "queued", "saving", "parsing", "processing", "running"}


def _now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def _since_24h() -> str:
    return (datetime.now(KST) - timedelta(hours=24)).isoformat(timespec="seconds")


def _scalar(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    if row is None:
        return 0
    return int(row[0] or 0)


def operation_run_payload(row: sqlite3.Row | dict) -> dict[str, Any]:
    payload = dict(row)
    for key in ["request_json", "result_json"]:
        raw = payload.pop(key, "{}")
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {}
        payload[key.replace("_json", "")] = parsed if isinstance(parsed, dict) else {}
    return payload


def record_operation_run(
    conn: sqlite3.Connection,
    *,
    operation_type: str,
    target_type: str = "",
    target_id: int | None = None,
    status: str,
    request_payload: dict[str, Any] | None = None,
    result_payload: dict[str, Any] | None = None,
    error_message: str = "",
    error_code: str = "",
    retry_of_run_id: int | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> dict[str, Any]:
    now = _now_iso()
    retry_count = 0
    if retry_of_run_id:
        retry_count = _scalar(conn, "SELECT COUNT(*) FROM operation_runs WHERE retry_of_run_id=?", (retry_of_run_id,)) + 1
    cur = conn.execute(
        """
        INSERT INTO operation_runs (
          operation_type, target_type, target_id, status, requested_by,
          request_json, result_json, error_message, error_code,
          retry_of_run_id, retry_count, started_at, finished_at,
          created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'local_admin', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            operation_type,
            target_type,
            target_id,
            status,
            json.dumps(request_payload or {}, ensure_ascii=False),
            json.dumps(result_payload or {}, ensure_ascii=False),
            error_message,
            error_code,
            retry_of_run_id,
            retry_count,
            started_at or now,
            finished_at or now,
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM operation_runs WHERE id=?", (cur.lastrowid,)).fetchone()
    return operation_run_payload(row)


def list_operation_runs_payload(
    conn: sqlite3.Connection,
    *,
    status: str = "",
    operation_type: str = "",
    keyword: str = "",
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    if operation_type:
        clauses.append("operation_type=?")
        params.append(operation_type)
    if keyword:
        clauses.append(
            "(operation_type LIKE ? OR target_type LIKE ? OR request_json LIKE ? OR result_json LIKE ? OR error_message LIKE ?)"
        )
        like_value = f"%{keyword}%"
        params.extend([like_value, like_value, like_value, like_value, like_value])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM operation_runs {where} ORDER BY id DESC",
        tuple(params),
    ).fetchall()
    return [operation_run_payload(row) for row in rows]


def get_operation_run_payload(conn: sqlite3.Connection, operation_run_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM operation_runs WHERE id=?", (operation_run_id,)).fetchone()
    return operation_run_payload(row) if row else None


def error_code_for_status(status: str, error_message: str = "") -> str:
    if status == "not_configured":
        return "missing_api_key"
    if status in {"failed", "partial_failed"}:
        lowered = error_message.lower()
        if "timeout" in lowered or "network" in lowered or "urlopen" in lowered:
            return "network_error"
        if "ocr" in lowered:
            return "ocr_failed"
        if "stored file not found" in lowered:
            return "storage_error"
        return "unknown_error"
    return ""


def _storage_health(storage_root: Path) -> dict[str, Any]:
    check_path = storage_root if storage_root.exists() else storage_root.parent
    try:
        usage = shutil.disk_usage(check_path)
    except OSError as exc:
        return {
            "status": "warning",
            "message": f"Storage path is not readable: {exc}",
            "path_exists": storage_root.exists(),
        }
    free_gb = round(usage.free / (1024**3), 2)
    return {
        "status": "ok" if storage_root.exists() else "warning",
        "message": "Storage root is available." if storage_root.exists() else "Storage root does not exist yet.",
        "path_exists": storage_root.exists(),
        "free_space_gb": free_gb,
    }


def _ocr_health() -> dict[str, Any]:
    engine = os.getenv("OCR_ENGINE", "noop").strip().lower()
    if not engine or engine == "noop":
        return {
            "status": "unavailable",
            "engine": engine or "noop",
            "message": "OCR engine is not configured; text-first parsing still works.",
        }
    return {
        "status": "configured",
        "engine": engine,
        "message": "OCR engine is configured.",
    }


def _basis_index_health(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        from app.pipelines.basis_document import basis_index_status_payload

        payload = basis_index_status_payload(conn)
    except Exception as exc:
        return {
            "status": "failed",
            "message": f"Basis index status check failed: {exc}",
        }
    status = payload.get("status", "unknown")
    if payload.get("valid"):
        health_status = "ok" if payload.get("can_search") else "warning"
    else:
        health_status = "action_required" if payload.get("rebuild_required") else "warning"
    return {
        "status": health_status,
        "message": (
            f"Basis index {status}: {payload.get('chunk_count', 0)} indexed chunks, "
            f"{payload.get('db_indexed_chunk_count', 0)} DB chunks."
        ),
        "configured": bool(payload.get("chunk_count")),
        "rebuild_required": bool(payload.get("rebuild_required")),
        "can_search": bool(payload.get("can_search")),
        "chunk_count": payload.get("chunk_count", 0),
        "db_indexed_chunk_count": payload.get("db_indexed_chunk_count", 0),
    }


def _failure_item(
    operation_type: str,
    target_type: str,
    row: sqlite3.Row,
    *,
    label: str,
    status: str,
    error_message: str,
    detail_url: str,
) -> dict[str, Any]:
    return {
        "operation_type": operation_type,
        "target_type": target_type,
        "target_id": row["id"],
        "target_label": label or f"{target_type} #{row['id']}",
        "status": status,
        "error_message": error_message or "No failure detail was recorded.",
        "occurred_at": row["updated_at"] or row["created_at"],
        "detail_url": detail_url,
    }


def _bad_status(*values: str) -> str:
    for value in values:
        if value in FAILURE_STATUSES:
            return value
    return ""


def _collect_recent_failures(conn: sqlite3.Connection, limit: int = 8) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []

    for row in conn.execute(
        """
        SELECT id, original_file_name, parsing_status, ocr_status, analysis_status,
               '' AS error_message, created_at, updated_at
        FROM project_documents
        WHERE parsing_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR analysis_status IN ('failed', 'partial_failed')
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        status = _bad_status(row["analysis_status"], row["ocr_status"], row["parsing_status"])
        failures.append(
            _failure_item(
                "document_analysis",
                "project_document",
                row,
                label=row["original_file_name"],
                status=status,
                error_message=row["error_message"],
                detail_url="/documents",
            )
        )

    for row in conn.execute(
        """
        SELECT id, original_file_name, extraction_status, ocr_status, classification_status,
               error_message, created_at, updated_at
        FROM corporation_evidence_documents
        WHERE extraction_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR classification_status='failed'
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        status = _bad_status(row["extraction_status"], row["ocr_status"], row["classification_status"])
        failures.append(
            _failure_item(
                "corporation_evidence_analysis",
                "corporation_evidence_document",
                row,
                label=row["original_file_name"],
                status=status,
                error_message=row["error_message"],
                detail_url="/corporations",
            )
        )

    for row in conn.execute(
        """
        SELECT id, title, processing_status, parse_status, ocr_status, chunk_status,
               index_status, error_message, created_at, updated_at
        FROM basis_documents
        WHERE processing_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR parse_status='failed'
           OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
           OR chunk_status='failed'
           OR index_status='failed'
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        status = _bad_status(
            row["processing_status"],
            row["parse_status"],
            row["ocr_status"],
            row["chunk_status"],
            row["index_status"],
        )
        failures.append(
            _failure_item(
                "basis_document_processing",
                "basis_document",
                row,
                label=row["title"],
                status=status,
                error_message=row["error_message"],
                detail_url="/basis-documents",
            )
        )

    for row in conn.execute(
        """
        SELECT id, bid_ntce_nm, save_status, download_status, analysis_status,
               error_message, created_at, updated_at
        FROM nara_notices
        WHERE save_status='failed'
           OR download_status IN ('failed', 'partial_failed')
           OR analysis_status IN ('failed', 'partial_failed')
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        status = _bad_status(row["analysis_status"], row["download_status"], row["save_status"])
        failures.append(
            _failure_item(
                "nara_notice_analysis",
                "nara_notice",
                row,
                label=row["bid_ntce_nm"],
                status=status,
                error_message=row["error_message"],
                detail_url=f"/nara-saved-notices/{row['id']}",
            )
        )

    for row in conn.execute(
        """
        SELECT id, file_name, nara_notice_id, download_status, parse_status,
               analysis_status, error_message, created_at, updated_at
        FROM nara_notice_attachments
        WHERE download_status='failed'
           OR parse_status='failed'
           OR analysis_status='failed'
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        status = _bad_status(row["analysis_status"], row["parse_status"], row["download_status"])
        failures.append(
            _failure_item(
                "nara_attachment_processing",
                "nara_notice_attachment",
                row,
                label=row["file_name"],
                status=status,
                error_message=row["error_message"],
                detail_url=f"/nara-saved-notices/{row['nara_notice_id']}",
            )
        )

    for row in conn.execute(
        """
        SELECT id, keyword, status, error_message, created_at, updated_at
        FROM nara_collection_runs
        WHERE status IN ('failed', 'partial_failed', 'not_configured')
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        failures.append(
            _failure_item(
                "nara_collection",
                "nara_collection_run",
                row,
                label=row["keyword"] or "나라장터 자동 수집",
                status=row["status"],
                error_message=row["error_message"],
                detail_url="/nara-collection-runs",
            )
        )

    for row in conn.execute(
        """
        SELECT id, status, reviewer_note AS error_message, created_at, updated_at
        FROM judgment_runs
        WHERE status IN ('failed', 'partial_failed')
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        failures.append(
            _failure_item(
                "judgment_run",
                "judgment_run",
                row,
                label=f"판단 실행 #{row['id']}",
                status=row["status"],
                error_message=row["error_message"],
                detail_url="/judgment-runs",
            )
        )

    for row in conn.execute(
        """
        SELECT id, file_name, status, error_message, created_at, completed_at, updated_at
        FROM backup_runs
        WHERE status='failed'
        ORDER BY updated_at DESC
        LIMIT 20
        """
    ).fetchall():
        failures.append(
            _failure_item(
                "backup_create",
                "backup_run",
                row,
                label=row["file_name"] or f"백업 #{row['id']}",
                status=row["status"],
                error_message=row["error_message"],
                detail_url="/backups",
            )
        )

    failures.sort(key=lambda item: item["occurred_at"] or "", reverse=True)
    return failures[:limit]


def _failed_jobs_24h(conn: sqlite3.Connection) -> int:
    since = _since_24h()
    return sum(
        [
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM project_documents
                WHERE updated_at>=?
                  AND (
                    parsing_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR analysis_status IN ('failed', 'partial_failed')
                  )
                """,
                (since,),
            ),
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM corporation_evidence_documents
                WHERE updated_at>=?
                  AND (
                    extraction_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR classification_status='failed'
                  )
                """,
                (since,),
            ),
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM basis_documents
                WHERE updated_at>=?
                  AND (
                    processing_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR parse_status='failed'
                    OR ocr_status IN ('failed', 'needs_ocr_setup', 'unavailable')
                    OR chunk_status='failed'
                    OR index_status='failed'
                  )
                """,
                (since,),
            ),
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM nara_notices
                WHERE updated_at>=?
                  AND (
                    save_status='failed'
                    OR download_status IN ('failed', 'partial_failed')
                    OR analysis_status IN ('failed', 'partial_failed')
                  )
                """,
                (since,),
            ),
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM nara_notice_attachments
                WHERE updated_at>=?
                  AND (
                    download_status='failed'
                    OR parse_status='failed'
                    OR analysis_status='failed'
                  )
                """,
                (since,),
            ),
            _scalar(
                conn,
                "SELECT COUNT(*) FROM nara_collection_runs WHERE updated_at>=? AND status IN ('failed', 'partial_failed', 'not_configured')",
                (since,),
            ),
            _scalar(
                conn,
                "SELECT COUNT(*) FROM judgment_runs WHERE updated_at>=? AND status IN ('failed', 'partial_failed')",
                (since,),
            ),
            _scalar(
                conn,
                "SELECT COUNT(*) FROM backup_runs WHERE updated_at>=? AND status='failed'",
                (since,),
            ),
        ]
    )


def _last_backup(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT id, status, file_name, file_size_bytes, error_message,
               created_at, completed_at, updated_at
        FROM backup_runs
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return {
            "status": "not_available",
            "message": "생성된 백업이 없습니다.",
            "created_at": None,
            "completed_at": None,
        }

    status = row["status"]
    message = {
        "completed": "마지막 백업이 정상 생성되었습니다.",
        "failed": row["error_message"] or "마지막 백업이 실패했습니다.",
        "running": "백업 생성이 진행 중입니다.",
    }.get(status, row["error_message"] or "백업 이력이 있습니다.")
    return {
        "id": row["id"],
        "status": status,
        "message": message,
        "file_name": row["file_name"],
        "file_size_bytes": row["file_size_bytes"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "updated_at": row["updated_at"],
        "detail_url": "/backups",
    }


def _review_queues(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    queues = [
        {
            "queue_type": "basis_rule_candidates",
            "label": "기준 규칙 후보 검토",
            "count": _scalar(conn, "SELECT COUNT(*) FROM basis_rule_candidates WHERE status='needs_review'"),
            "detail_url": "/basis-rule-candidates",
        },
        {
            "queue_type": "judgment_runs",
            "label": "판단 실행 검토",
            "count": _scalar(conn, "SELECT COUNT(*) FROM judgment_runs WHERE review_status='pending'"),
            "detail_url": "/judgment-runs",
        },
        {
            "queue_type": "corporation_evidence",
            "label": "법인 증빙자료 검토",
            "count": _scalar(conn, "SELECT COUNT(*) FROM corporation_evidence_documents WHERE review_status='pending'"),
            "detail_url": "/corporations",
        },
        {
            "queue_type": "profile_update_candidates",
            "label": "프로필 반영 후보",
            "count": _scalar(conn, "SELECT COUNT(*) FROM corporation_profile_update_candidates WHERE status='pending'"),
            "detail_url": "/corporations",
        },
    ]
    return [queue for queue in queues if queue["count"] > 0]


def build_operations_summary(
    conn: sqlite3.Connection,
    *,
    storage_root: Path,
    nara_api_configured: bool,
    nara_api_masked_key: str,
    ai_provider: str,
    ai_model: str,
    ai_configured: bool,
) -> dict[str, Any]:
    recent_failures = _collect_recent_failures(conn)
    review_queues = _review_queues(conn)
    failed_jobs_24h = _failed_jobs_24h(conn)
    pending_reviews = sum(queue["count"] for queue in review_queues)

    health = {
        "database": {"status": "ok", "message": "SQLite connection is available."},
        "storage": _storage_health(storage_root),
        "ocr": _ocr_health(),
        "nara_api": {
            "status": "configured_masked" if nara_api_configured else "not_configured",
            "configured": nara_api_configured,
            "masked_key": nara_api_masked_key if nara_api_configured else "",
        },
        "ai_provider": {
            "status": "configured_masked" if ai_configured else "not_configured",
            "provider": ai_provider,
            "model": ai_model,
            "configured": ai_configured,
        },
        "basis_index": _basis_index_health(conn),
    }

    counts = {
        "failed_jobs_24h": failed_jobs_24h,
        "pending_reviews": pending_reviews,
        "basis_documents_processing": _scalar(
            conn,
            """
            SELECT COUNT(*) FROM basis_documents
            WHERE processing_status IN ('pending', 'parsing', 'processing')
               OR parse_status IN ('pending', 'processing')
               OR chunk_status IN ('pending', 'processing')
               OR index_status IN ('pending', 'processing')
            """,
        ),
        "judgment_runs_24h": _scalar(conn, "SELECT COUNT(*) FROM judgment_runs WHERE created_at>=?", (_since_24h(),)),
        "nara_collection_runs_24h": _scalar(conn, "SELECT COUNT(*) FROM nara_collection_runs WHERE created_at>=?", (_since_24h(),)),
        "nara_notices_processing": _scalar(
            conn,
            "SELECT COUNT(*) FROM nara_notices WHERE analysis_status IN ('pending', 'queued', 'saving', 'processing')",
        ),
        "evidence_documents_pending": _scalar(
            conn,
            "SELECT COUNT(*) FROM corporation_evidence_documents WHERE extraction_status IN ('pending', 'processing')",
        ),
    }

    health_has_warning = any(item.get("status") not in {"ok", "configured", "configured_masked"} for item in health.values())
    if failed_jobs_24h:
        overall_status = "action_required"
    elif health_has_warning or pending_reviews:
        overall_status = "warning"
    else:
        overall_status = "ok"

    return {
        "overall_status": overall_status,
        "generated_at": _now_iso(),
        "health": health,
        "counts": counts,
        "recent_failures": recent_failures,
        "review_queues": review_queues,
        "last_backup": _last_backup(conn),
    }
