import json
import ipaddress
import mimetypes
from pathlib import Path
import socket
from typing import Any
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from app.core.logging import get_logger, log_event, log_exception, sanitize_log_value
from app.core.text import clean_text, parse_int

DEFAULT_NARA_SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
LOGGER = get_logger("services.nara_api")


def parse_nara_response(payload: dict) -> tuple[str, str, int]:
    response = payload.get("response", payload) if isinstance(payload, dict) else {}
    header = response.get("header", {}) if isinstance(response, dict) else {}
    body = response.get("body", {}) if isinstance(response, dict) else {}
    return (
        str(header.get("resultCode", "")),
        str(header.get("resultMsg", "")),
        parse_int(body.get("totalCount"), 0),
    )


def normalize_json_items(items: Any) -> list[dict]:
    if not items:
        return []
    if isinstance(items, dict):
        item = items.get("item")
        if isinstance(item, list):
            return [row for row in item if isinstance(row, dict)]
        if isinstance(item, dict):
            return [item]
    if isinstance(items, list):
        return [row for row in items if isinstance(row, dict)]
    return []


def xml_children_to_dict(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    return {child.tag: (child.text or "") for child in list(element)}


def parse_public_data_text(raw_text: str) -> dict:
    text = raw_text.strip()
    if not text:
        return {"format": "empty", "header": {}, "body": {}, "items": [], "total_count": 0}

    if text.startswith("{") or text.startswith("["):
        payload = json.loads(text)
        response = payload.get("response", payload) if isinstance(payload, dict) else {}
        header = response.get("header", {}) if isinstance(response, dict) else {}
        body = response.get("body", {}) if isinstance(response, dict) else {}
        items = normalize_json_items(body.get("items")) if isinstance(body, dict) else []
        return {
            "format": "json",
            "header": header,
            "body": body,
            "items": items,
            "total_count": parse_int(body.get("totalCount", len(items))) if isinstance(body, dict) else len(items),
        }

    root = ET.fromstring(text)
    body = xml_children_to_dict(root.find("./body"))
    items = [xml_children_to_dict(item) for item in root.findall("./body/items/item")]
    return {
        "format": "xml",
        "header": xml_children_to_dict(root.find("./header")),
        "body": body,
        "items": items,
        "total_count": parse_int(body.get("totalCount", len(items))),
    }


def build_nara_url(base_url: str, operation: str, params: dict[str, str]) -> str:
    return f"{base_url.rstrip('/')}/{operation}?{urllib.parse.urlencode(params, doseq=True, safe='%')}"


def decode_http_body(body: bytes, charset: str | None = None) -> str:
    candidates = [charset, "utf-8-sig", "utf-8", "cp949", "euc-kr"]
    seen: set[str] = set()
    for candidate in candidates:
        encoding = (candidate or "").strip().lower()
        if not encoding or encoding in seen:
            continue
        seen.add(encoding)
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def request_text(url: str, timeout: int = 20) -> tuple[int, str]:
    parsed_url = urllib.parse.urlsplit(url)
    log_event(
        LOGGER,
        "nara.http.request.started",
        domain="nara",
        method="GET",
        url=sanitize_log_value(url),
        host=parsed_url.netloc,
        path=parsed_url.path,
        timeout=timeout,
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, application/xml;q=0.9, */*;q=0.8",
            "User-Agent": "SMART-Procurement-Calculator/local-portal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = decode_http_body(response.read(), response.headers.get_content_charset())
            log_event(
                LOGGER,
                "nara.http.request.completed",
                domain="nara",
                method="GET",
                host=parsed_url.netloc,
                path=parsed_url.path,
                status_code=response.status,
                response_chars=len(body),
            )
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = decode_http_body(exc.read(), exc.headers.get_content_charset() if exc.headers else None)
        log_event(
            LOGGER,
            "nara.http.request.http_error",
            level="warning",
            domain="nara",
            method="GET",
            host=parsed_url.netloc,
            path=parsed_url.path,
            status_code=exc.code,
            response_chars=len(body),
        )
        return exc.code, body
    except Exception as exc:
        log_exception(
            LOGGER,
            "nara.http.request.failed",
            exc,
            domain="nara",
            method="GET",
            host=parsed_url.netloc,
            path=parsed_url.path,
        )
        raise


def date_to_api_datetime(value: str, suffix: str) -> str:
    cleaned = clean_text(value)
    if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
        return cleaned.replace("-", "") + suffix
    if len(cleaned) == 8 and cleaned.isdigit():
        return cleaned + suffix
    return cleaned


def item_first(item: dict, keys: list[str]) -> str:
    for key in keys:
        value = clean_text(item.get(key))
        if value:
            return value
    return ""


def attachment_extension(name: str, url: str, content_type: str = "") -> str:
    candidates = [name, urllib.parse.urlparse(url).path]
    for candidate in candidates:
        suffix = Path(candidate).suffix.lower()
        if suffix:
            return suffix
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else ""
    return guessed or ""


def collect_nara_attachments(
    items: list[dict],
    supported_extensions: set[str] = DEFAULT_NARA_SUPPORTED_EXTENSIONS,
) -> list[dict]:
    attachments: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_attachment(name: str, url: str, source_field: str) -> None:
        name = clean_text(name) or Path(urllib.parse.urlparse(url).path).name or source_field
        url = clean_text(url)
        if not url and name == source_field:
            return
        key = (name, url)
        if key in seen or (not name and not url):
            return
        seen.add(key)
        suffix = attachment_extension(name, url)
        support_status = "supported" if url and suffix in supported_extensions else "unsupported"
        if not suffix and not url:
            support_status = "unsupported"
        attachments.append(
            {
                "file_name": name,
                "source_url": url,
                "source_field": source_field,
                "file_extension": suffix,
                "support_status": support_status,
            }
        )

    for item in items:
        for index in range(1, 11):
            add_attachment(
                clean_text(item.get(f"ntceSpecFileNm{index}")),
                clean_text(item.get(f"ntceSpecDocUrl{index}")),
                f"ntceSpecDocUrl{index}",
            )

        std_notice_url = clean_text(item.get("stdNtceDocUrl"))
        if std_notice_url:
            add_attachment("표준공고문.pdf", std_notice_url, "stdNtceDocUrl")
        add_attachment(clean_text(item.get("eorderAtchFileNm")), clean_text(item.get("eorderAtchFileUrl")), "eorderAtchFileUrl")

    return attachments


def normalize_nara_notice(item: dict, attachments: list[dict] | None = None) -> dict:
    attachment_rows = attachments if attachments is not None else collect_nara_attachments([item])
    supported_count = len([row for row in attachment_rows if row["support_status"] == "supported"])
    return {
        "bid_ntce_no": item_first(item, ["bidNtceNo"]),
        "bid_ntce_ord": item_first(item, ["bidNtceOrd"]) or "000",
        "bid_ntce_nm": item_first(item, ["bidNtceNm"]),
        "ntce_instt_nm": item_first(item, ["ntceInsttNm"]),
        "dminstt_nm": item_first(item, ["dminsttNm"]),
        "bid_ntce_dt": item_first(item, ["bidNtceDt"]),
        "bid_begin_dt": item_first(item, ["bidBeginDt"]),
        "bid_clse_dt": item_first(item, ["bidClseDt"]),
        "openg_dt": item_first(item, ["opengDt"]),
        "presmpt_prce": item_first(item, ["presmptPrce", "asignBdgtAmt"]),
        "bdgt_amt": item_first(item, ["bdgtAmt", "asignBdgtAmt"]),
        "bssamt": item_first(item, ["bssamt", "bssAmt"]),
        "region_text": item_first(item, ["prtcptPsblRgnNm", "cnstrtsiteRgnNm", "rgstTyNm"]),
        "license_text": item_first(item, ["lcnsLmtNm", "indstrytyNm", "indstrytyLmtYn"]),
        "source_url": item_first(item, ["bidNtceUrl", "bidNtceDtlUrl"]),
        "attachment_count": len(attachment_rows),
        "supported_attachment_count": supported_count,
        "raw": item,
    }


def merge_notice_items(base_item: dict, detail_items: list[dict]) -> dict:
    merged = dict(base_item)
    for item in detail_items:
        for key, value in item.items():
            if clean_text(value) and not clean_text(merged.get(key)):
                merged[key] = value
    return merged


def request_binary(url: str, timeout: int = 30, max_bytes: int = 50 * 1024 * 1024) -> tuple[int, dict[str, str], bytes]:
    parsed_url = urllib.parse.urlsplit(url)
    log_event(
        LOGGER,
        "nara.attachment.request.started",
        domain="nara",
        method="GET",
        url=sanitize_log_value(url),
        host=parsed_url.netloc,
        path=parsed_url.path,
        timeout=timeout,
        max_bytes=max_bytes,
    )
    safe, reason = validate_external_attachment_url(url)
    if not safe:
        log_event(
            LOGGER,
            "nara.attachment.url_unsafe",
            level="error",
            domain="nara",
            host=parsed_url.netloc,
            path=parsed_url.path,
            reason=reason,
        )
        raise ValueError(f"Unsafe attachment URL: {reason}")
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, */*",
            "User-Agent": "SMART-Procurement-Calculator/attachment-download",
        },
    )
    opener = urllib.request.build_opener(SafeAttachmentRedirectHandler)
    with opener.open(req, timeout=timeout) as response:
        final_url = response.geturl()
        final_safe, final_reason = validate_external_attachment_url(final_url)
        if not final_safe:
            raise ValueError(f"Unsafe attachment redirect URL: {final_reason}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                log_event(
                    LOGGER,
                    "nara.attachment.download_too_large",
                    level="error",
                    domain="nara",
                    host=parsed_url.netloc,
                    path=parsed_url.path,
                    total_bytes=total,
                    max_bytes=max_bytes,
                )
                raise ValueError("download exceeded 50MB limit")
            chunks.append(chunk)
        body = b"".join(chunks)
        log_event(
            LOGGER,
            "nara.attachment.request.completed",
            domain="nara",
            method="GET",
            host=parsed_url.netloc,
            path=parsed_url.path,
            status_code=response.status,
            content_type=response.headers.get("content-type", ""),
            response_bytes=len(body),
        )
        return response.status, {key.lower(): value for key, value in response.headers.items()}, body


def _unsafe_ip_reason(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str:
    if address.is_loopback:
        return "loopback address is not allowed"
    if address.is_link_local:
        return "link-local address is not allowed"
    if address.is_private:
        return "private network address is not allowed"
    if address.is_multicast:
        return "multicast address is not allowed"
    if address.is_unspecified:
        return "unspecified address is not allowed"
    if address.is_reserved:
        return "reserved address is not allowed"
    if not address.is_global:
        return "non-global address is not allowed"
    return ""


def validate_external_attachment_url(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(clean_text(url))
    if parsed.scheme not in {"http", "https"}:
        return False, "only HTTP/HTTPS URLs are allowed"
    if not parsed.hostname:
        return False, "hostname is required"

    hostname = parsed.hostname.strip().rstrip(".").lower()
    if hostname == "localhost":
        return False, "localhost is not allowed"

    try:
        address = ipaddress.ip_address(hostname)
        reason = _unsafe_ip_reason(address)
        return (False, reason) if reason else (True, "")
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        return False, f"hostname could not be resolved: {exc}"

    resolved_addresses = {info[4][0] for info in infos if info and info[4]}
    if not resolved_addresses:
        return False, "hostname did not resolve to an address"
    for resolved in resolved_addresses:
        try:
            address = ipaddress.ip_address(resolved)
        except ValueError:
            return False, "hostname resolved to an invalid address"
        reason = _unsafe_ip_reason(address)
        if reason:
            return False, reason
    return True, ""


def is_safe_external_url(url: str) -> bool:
    return validate_external_attachment_url(url)[0]


class SafeAttachmentRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe, reason = validate_external_attachment_url(newurl)
        if not safe:
            raise ValueError(f"Unsafe attachment redirect URL: {reason}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def inline_content_type(file_name: str, url: str, upstream_content_type: str, body: bytes) -> str:
    suffix = attachment_extension(file_name, url, upstream_content_type)
    if body.startswith(b"%PDF") or suffix == ".pdf":
        return "application/pdf"
    if body.startswith(b"PK\x03\x04") or suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return upstream_content_type.split(";")[0].strip() or "application/octet-stream"


def build_nara_summary_text(notice: dict, attachment_texts: list[str]) -> str:
    lines = [
        f"공고명: {notice.get('bid_ntce_nm', '')}",
        f"공고번호: {notice.get('bid_ntce_no', '')}-{notice.get('bid_ntce_ord', '')}",
        f"공고기관: {notice.get('ntce_instt_nm', '')}",
        f"수요기관: {notice.get('dminstt_nm', '')}",
        f"공고일시: {notice.get('bid_ntce_dt', '')}",
        f"입찰개시: {notice.get('bid_begin_dt', '')}",
        f"입찰마감: {notice.get('bid_clse_dt', '')}",
        f"개찰일시: {notice.get('openg_dt', '')}",
        f"추정가격: {notice.get('presmpt_prce', '')}",
        f"기초금액: {notice.get('bssamt', '')}",
        f"지역: {notice.get('region_text', '')}",
        f"면허/업종 제한: {notice.get('license_text', '')}",
        "",
        "첨부문서 추출 내용:",
    ]
    for index, text in enumerate(attachment_texts, start=1):
        lines.extend([f"[첨부 {index}]", text[:20000], ""])
    return "\n".join(lines).strip()
