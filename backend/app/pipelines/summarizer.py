import json
from typing import Any

from app.core.config import settings


SUMMARY_SCHEMA = {
    "document_summary": "",
    "key_dates": [],
    "requirements": [],
    "required_documents": [],
    "risks": [],
    "questions_to_check": [],
    "confidence_note": "",
}


def summarize_document(text: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    if not text.strip():
        empty = SUMMARY_SCHEMA.copy()
        empty["confidence_note"] = "No extractable text found."
        return empty, "문서 텍스트를 추출하지 못했습니다.", {"input_chars": 0}

    if settings.openai_api_key:
        try:
            return _summarize_with_openai(text)
        except Exception:
            # Fail-safe to deterministic local summary so phase-1 UX is not blocked.
            pass

    return _fallback_summary(text)


def _summarize_with_openai(text: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "You are a Korean procurement document assistant. "
        "Return strict JSON with keys: document_summary, key_dates, requirements, "
        "required_documents, risks, questions_to_check, confidence_note. "
        "Never fabricate unknown facts."
    )

    response = client.responses.create(
        model=settings.openai_model_primary,
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text[:120000]},
        ],
        text={"format": {"type": "json_object"}},
    )

    parsed = json.loads(response.output_text)
    markdown = _json_to_markdown(parsed)
    usage = {
        "input_chars": len(text),
        "provider": "openai",
        "model": settings.openai_model_primary,
    }
    return parsed, markdown, usage


def _fallback_summary(text: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    summary = SUMMARY_SCHEMA.copy()
    summary["document_summary"] = " ".join(lines[:4])[:500] if lines else "요약할 텍스트가 부족합니다."
    summary["requirements"] = lines[4:10]
    summary["questions_to_check"] = ["핵심 일정과 제출 서류를 원문에서 다시 확인하세요."]
    summary["confidence_note"] = "Fallback summary was used because API key is missing or API failed."

    markdown = _json_to_markdown(summary)
    usage = {"input_chars": len(text), "provider": "fallback", "model": "local"}
    return summary, markdown, usage


def _json_to_markdown(data: dict[str, Any]) -> str:
    reqs = data.get("requirements", []) or []
    docs = data.get("required_documents", []) or []
    risks = data.get("risks", []) or []

    return "\n".join(
        [
            "## 문서 요약",
            data.get("document_summary", ""),
            "",
            "## 요구사항",
            *(f"- {item}" for item in reqs),
            "",
            "## 제출 문서",
            *(f"- {item}" for item in docs),
            "",
            "## 리스크",
            *(f"- {item}" for item in risks),
            "",
            f"신뢰도 메모: {data.get('confidence_note', '')}",
        ]
    )
