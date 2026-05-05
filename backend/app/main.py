import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.pipelines.parser import extract_document

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"


def _resolve_local_path(raw_value: str) -> Path:
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


STORAGE_ROOT = _resolve_local_path(os.getenv("STORAGE_ROOT", "./storage"))
SQLITE_PATH = _resolve_local_path(os.getenv("SQLITE_PATH", "./app.db"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_PRIMARY = os.getenv("OPENAI_MODEL_PRIMARY", "gpt-5.1")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

app = Flask(__name__)
CORS(app)

SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
GLOBAL_CONN = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
GLOBAL_CONN.row_factory = sqlite3.Row


def db_conn() -> sqlite3.Connection:
    return GLOBAL_CONN


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STORAGE_ROOT / "uploads").mkdir(parents=True, exist_ok=True)

    with db_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS corporations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                business_category TEXT DEFAULT '',
                region TEXT DEFAULT '',
                certifications_json TEXT DEFAULT '[]',
                company_size_classification TEXT DEFAULT '',
                internal_notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                corporation_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(corporation_id) REFERENCES corporations(id)
            );

            CREATE TABLE IF NOT EXISTS project_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                document_type TEXT DEFAULT 'general',
                original_file_name TEXT NOT NULL,
                stored_file_path TEXT NOT NULL,
                mime_type TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                memo TEXT DEFAULT '',
                revision_note TEXT DEFAULT '',
                parsing_status TEXT DEFAULT 'pending',
                ocr_status TEXT DEFAULT 'pending',
                analysis_status TEXT DEFAULT 'pending',
                latest_analysis_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_document_id INTEGER NOT NULL,
                analysis_type TEXT DEFAULT 'summary',
                model_provider TEXT DEFAULT 'openai',
                model_name TEXT DEFAULT 'gpt-5.1',
                prompt_version TEXT DEFAULT 'v1',
                input_hash TEXT NOT NULL,
                output_json TEXT NOT NULL,
                output_markdown TEXT NOT NULL,
                token_usage_json TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                error_message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_document_id) REFERENCES project_documents(id)
            );
            """
        )


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def one_or_404(conn: sqlite3.Connection, query: str, params: tuple):
    row = conn.execute(query, params).fetchone()
    if not row:
        return None, (jsonify({"detail": "Not found"}), 404)
    return row, None


def extract_text(file_path: Path) -> str:
    return extract_document(file_path).text


def summarize_with_fallback(text: str) -> tuple[dict, str, dict]:
    if not text:
        payload = {
            "document_summary": "문서에서 추출 가능한 텍스트가 부족합니다.",
            "key_dates": [],
            "requirements": [],
            "required_documents": [],
            "risks": [],
            "questions_to_check": ["원문 파일 품질(OCR) 재확인 필요"],
            "confidence_note": "Low confidence",
        }
    else:
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        payload = {
            "document_summary": " ".join(lines[:4])[:500],
            "key_dates": [],
            "requirements": lines[4:10],
            "required_documents": [],
            "risks": [],
            "questions_to_check": ["핵심 일정/제출 서류를 원문에서 재확인하세요."],
            "confidence_note": "Fallback summary (no API key or API failed)",
        }

    markdown = "\n".join(
        [
            "## 문서 요약",
            payload["document_summary"],
            "",
            "## 요구사항",
            *[f"- {x}" for x in payload["requirements"]],
            "",
            f"신뢰도 메모: {payload['confidence_note']}",
        ]
    )
    usage = {"provider": "fallback", "input_chars": len(text)}
    return payload, markdown, usage


def summarize_with_openai(text: str) -> tuple[dict, str, dict]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=OPENAI_MODEL_PRIMARY,
        input=[
            {
                "role": "system",
                "content": "You are a Korean procurement summary assistant. Return strict JSON only.",
            },
            {"role": "user", "content": text[:120000]},
        ],
        text={"format": {"type": "json_object"}},
    )
    payload = json.loads(resp.output_text)
    markdown = "## 문서 요약\n" + payload.get("document_summary", "")
    usage = {"provider": "openai", "model": OPENAI_MODEL_PRIMARY, "input_chars": len(text)}
    return payload, markdown, usage


def run_analysis(document_id: int, force: bool = False) -> tuple[dict, int]:
    with db_conn() as conn:
        doc = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not doc:
            return {"detail": "Document not found"}, 404

        file_path = Path(doc["stored_file_path"])
        parsed = extract_document(file_path)
        text = parsed.text
        ocr_status = "needs_ocr" if parsed.metadata.get("needs_ocr") else "skipped"
        input_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        if not force:
            cached = conn.execute(
                "SELECT * FROM analyses WHERE project_document_id=? AND input_hash=? ORDER BY id DESC LIMIT 1",
                (document_id, input_hash),
            ).fetchone()
            if cached:
                conn.execute(
                    "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
                    ("completed", ocr_status, "cached", cached["id"], now_iso(), document_id),
                )
                conn.commit()
                return {"analysis_id": cached["id"], "status": "completed", "message": "Analysis completed (cache)"}, 200

        if OPENAI_API_KEY:
            try:
                output_json, output_md, usage = summarize_with_openai(text)
            except Exception:
                output_json, output_md, usage = summarize_with_fallback(text)
        else:
            output_json, output_md, usage = summarize_with_fallback(text)

        usage["extraction"] = parsed.metadata

        cur = conn.execute(
            """
            INSERT INTO analyses (
              project_document_id, analysis_type, model_provider, model_name, prompt_version,
              input_hash, output_json, output_markdown, token_usage_json, status, error_message, created_at
            ) VALUES (?, 'summary', 'openai', ?, 'v1', ?, ?, ?, ?, 'completed', '', ?)
            """,
            (
                document_id,
                OPENAI_MODEL_PRIMARY,
                input_hash,
                json.dumps(output_json, ensure_ascii=False),
                output_md,
                json.dumps(usage, ensure_ascii=False),
                now_iso(),
            ),
        )
        analysis_id = cur.lastrowid

        conn.execute(
            "UPDATE project_documents SET parsing_status=?, ocr_status=?, analysis_status=?, latest_analysis_id=?, updated_at=? WHERE id=?",
            ("completed", ocr_status, "completed", analysis_id, now_iso(), document_id),
        )
        conn.commit()

    return {"analysis_id": analysis_id, "status": "completed", "message": "Analysis completed"}, 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    with db_conn() as conn:
        corp = conn.execute("SELECT COUNT(*) c FROM corporations").fetchone()["c"]
        proj = conn.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
        docs = conn.execute("SELECT COUNT(*) c FROM project_documents").fetchone()["c"]
    return jsonify({"corporation_count": corp, "project_count": proj, "document_count": docs})


@app.route("/api/corporations", methods=["GET"])
def list_corporations():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM corporations ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/corporations", methods=["POST"])
def create_corporation():
    payload = request.get_json(force=True)
    now = now_iso()
    with db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO corporations (
              name, business_category, region, certifications_json, company_size_classification,
              internal_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("name", ""),
                payload.get("business_category", ""),
                payload.get("region", ""),
                payload.get("certifications_json", "[]"),
                payload.get("company_size_classification", ""),
                payload.get("internal_notes", ""),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM corporations WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/projects", methods=["GET"])
def list_projects():
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/projects", methods=["POST"])
def create_project():
    payload = request.get_json(force=True)
    now = now_iso()
    corp_id = int(payload.get("corporation_id", 0))

    with db_conn() as conn:
        corp = conn.execute("SELECT id FROM corporations WHERE id=?", (corp_id,)).fetchone()
        if not corp:
            return jsonify({"detail": "Invalid corporation_id"}), 400

        cur = conn.execute(
            "INSERT INTO projects (name, corporation_id, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                payload.get("name", ""),
                corp_id,
                payload.get("status", "active"),
                payload.get("notes", ""),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/documents", methods=["GET"])
def list_documents():
    project_id = request.args.get("project_id")
    with db_conn() as conn:
        if project_id:
            rows = conn.execute("SELECT * FROM project_documents WHERE project_id=? ORDER BY id DESC", (project_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM project_documents ORDER BY id DESC").fetchall()
    return jsonify(rows_to_dict(rows))


@app.route("/api/documents", methods=["POST"])
def upload_document():
    project_id = int(request.form.get("project_id", "0"))
    document_type = request.form.get("document_type", "general")
    memo = request.form.get("memo", "")
    revision_note = request.form.get("revision_note", "")
    file = request.files.get("file")

    if not file:
        return jsonify({"detail": "file is required"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"detail": "Only PDF and DOCX are supported"}), 400

    with db_conn() as conn:
        project = conn.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            return jsonify({"detail": "Invalid project_id"}), 400

        target_dir = STORAGE_ROOT / "uploads" / str(project_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid.uuid4().hex}{ext}"
        stored_path = target_dir / stored_name
        file.save(stored_path)
        file_size = stored_path.stat().st_size

        now = now_iso()
        cur = conn.execute(
            """
            INSERT INTO project_documents (
              project_id, document_type, original_file_name, stored_file_path, mime_type,
              file_size, memo, revision_note, parsing_status, ocr_status, analysis_status,
              latest_analysis_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'pending', 'pending', NULL, ?, ?)
            """,
            (
                project_id,
                document_type,
                file.filename,
                str(stored_path),
                file.mimetype or "",
                file_size,
                memo,
                revision_note,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/documents/<int:document_id>", methods=["GET"])
def get_document(document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Document not found"}), 404
    return jsonify(dict(row))


@app.route("/api/documents/<int:document_id>", methods=["DELETE"])
def delete_document(document_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not row:
            return jsonify({"detail": "Document not found"}), 404

        file_path = Path(row["stored_file_path"])
        if file_path.exists():
            file_path.unlink()

        conn.execute("DELETE FROM project_documents WHERE id=?", (document_id,))
        conn.commit()
    return jsonify({"status": "deleted"})


@app.route("/api/documents/<int:document_id>/analyze", methods=["POST"])
def analyze_document(document_id: int):
    payload, code = run_analysis(document_id, force=False)
    return jsonify(payload), code


@app.route("/api/documents/<int:document_id>/reanalyze", methods=["POST"])
def reanalyze_document(document_id: int):
    payload, code = run_analysis(document_id, force=True)
    return jsonify(payload), code


@app.route("/api/analyses/<int:analysis_id>", methods=["GET"])
def get_analysis(analysis_id: int):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    if not row:
        return jsonify({"detail": "Analysis not found"}), 404
    return jsonify(dict(row))


@app.route("/api/analyses/latest/by-document/<int:document_id>", methods=["GET"])
def latest_analysis(document_id: int):
    with db_conn() as conn:
        doc = conn.execute("SELECT latest_analysis_id FROM project_documents WHERE id=?", (document_id,)).fetchone()
        if not doc or not doc["latest_analysis_id"]:
            return jsonify({"detail": "Latest analysis not found"}), 404

        row = conn.execute("SELECT * FROM analyses WHERE id=?", (doc["latest_analysis_id"],)).fetchone()
    if not row:
        return jsonify({"detail": "Analysis not found"}), 404
    return jsonify(dict(row))


if __name__ == "__main__":
    init_db()
    app_port = int(os.getenv("APP_PORT", "18000"))
    app.run(host="127.0.0.1", port=app_port, debug=False)
