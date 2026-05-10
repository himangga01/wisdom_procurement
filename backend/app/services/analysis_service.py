import hashlib
import json

from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.document import ProjectDocument
from app.pipelines.ocr import maybe_run_ocr
from app.pipelines.parser import extract_document
from app.pipelines.summarizer import summarize_document


def run_document_analysis(db: Session, document: ProjectDocument, force: bool = False) -> Analysis:
    parsed = extract_document(document.stored_file_path)
    text_for_summary, ocr_status = maybe_run_ocr(
        parsed.text,
        document.stored_file_path,
        parsed.kind,
        parsed.metadata,
    )

    input_hash = hashlib.sha256(text_for_summary.encode("utf-8")).hexdigest()

    if not force:
        cached = (
            db.query(Analysis)
            .filter(Analysis.project_document_id == document.id, Analysis.input_hash == input_hash)
            .order_by(Analysis.id.desc())
            .first()
        )
        if cached:
            document.parsing_status = "completed"
            document.ocr_status = ocr_status
            document.analysis_status = "cached"
            document.latest_analysis_id = cached.id
            db.commit()
            db.refresh(document)
            return cached

    output_json, output_markdown, usage = summarize_document(text_for_summary)

    analysis = Analysis(
        project_document_id=document.id,
        input_hash=input_hash,
        output_json=json.dumps(output_json, ensure_ascii=False),
        output_markdown=output_markdown,
        token_usage_json=json.dumps(usage, ensure_ascii=False),
        status="completed",
    )
    db.add(analysis)
    db.flush()

    document.parsing_status = "completed"
    document.ocr_status = ocr_status
    document.analysis_status = "completed"
    document.latest_analysis_id = analysis.id

    db.commit()
    db.refresh(analysis)
    return analysis
