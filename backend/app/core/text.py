import re


def clean_text(value, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def parse_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def format_korean_won_amount(value) -> str:
    text = clean_text(value)
    if not text:
        return ""
    compact = text.replace(",", "").replace(" ", "")
    if compact.endswith("원"):
        compact = compact[:-1]
    if re.fullmatch(r"\d+(?:\.0+)?", compact):
        amount = int(float(compact))
        return f"{amount:,}원"
    return text


def basis_tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", text or "")]


def basis_vector_for_text(text: str) -> dict[str, int]:
    vector: dict[str, int] = {}
    for token in basis_tokenize(text):
        vector[token] = vector.get(token, 0) + 1
    return vector
