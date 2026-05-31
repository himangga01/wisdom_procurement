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


def basis_tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", text or "")]


def basis_vector_for_text(text: str) -> dict[str, int]:
    vector: dict[str, int] = {}
    for token in basis_tokenize(text):
        vector[token] = vector.get(token, 0) + 1
    return vector
