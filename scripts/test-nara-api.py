import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_ENV = ROOT_DIR / "backend" / ".env"
TEMP_DIR = ROOT_DIR / "temp"

DEFAULT_BID_PUBLIC_BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
DEFAULT_PUBDATA_BASE_URL = "https://apis.data.go.kr/1230000/ao/PubDataOpnStdService"


@dataclass
class ApiTest:
    name: str
    base_url: str
    operation: str
    params: dict[str, str]
    purpose: str


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def build_url(base_url: str, operation: str, params: dict[str, str]) -> str:
    base = base_url.rstrip("/")
    query = urllib.parse.urlencode(params, doseq=True, safe="%")
    return f"{base}/{operation}?{query}"


def request_text(url: str, timeout: int = 20) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json, application/xml;q=0.9, */*;q=0.8",
            "User-Agent": "SMART-Procurement-Calculator/phase-1.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, body.decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body


def request_binary(url: str, timeout: int = 30, max_bytes: int = 50 * 1024 * 1024) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, */*",
            "User-Agent": "SMART-Procurement-Calculator/phase-1.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"download exceeded max_bytes={max_bytes}")
                chunks.append(chunk)
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, b"".join(chunks)
    except urllib.error.HTTPError as exc:
        headers = {key.lower(): value for key, value in exc.headers.items()}
        return exc.code, headers, exc.read()


def parse_response(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if not text:
        return {"format": "empty", "header": {}, "body": {}, "items": [], "total_count": 0}

    if text.startswith("{") or text.startswith("["):
        payload = json.loads(text)
        response = payload.get("response", payload) if isinstance(payload, dict) else {}
        header = response.get("header", {}) if isinstance(response, dict) else {}
        body = response.get("body", {}) if isinstance(response, dict) else {}
        items = normalize_json_items(body.get("items")) if isinstance(body, dict) else []
        total_count = safe_int(body.get("totalCount", len(items))) if isinstance(body, dict) else len(items)
        return {
            "format": "json",
            "header": header,
            "body": body,
            "items": items,
            "total_count": total_count,
        }

    root = ET.fromstring(text)
    header_el = root.find("./header")
    body_el = root.find("./body")
    header = xml_children_to_dict(header_el)
    body = xml_children_to_dict(body_el)
    items = []
    for item_el in root.findall("./body/items/item"):
        items.append(xml_children_to_dict(item_el))
    total_count = safe_int(body.get("totalCount", len(items)))
    return {
        "format": "xml",
        "header": header,
        "body": body,
        "items": items,
        "total_count": total_count,
    }


def normalize_json_items(items: Any) -> list[dict[str, Any]]:
    if not items:
        return []
    if isinstance(items, dict):
        item = items.get("item")
        if isinstance(item, list):
            return [x for x in item if isinstance(x, dict)]
        if isinstance(item, dict):
            return [item]
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []


def xml_children_to_dict(element: ET.Element | None) -> dict[str, str]:
    if element is None:
        return {}
    return {child.tag: (child.text or "") for child in list(element)}


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "bidNtceNo",
        "bidNtceOrd",
        "bidNtceNm",
        "ntceInsttNm",
        "dminsttNm",
        "bidNtceDt",
        "bidBeginDt",
        "bidClseDt",
        "opengDt",
        "presmptPrce",
        "bdgtAmt",
        "bssamt",
        "indstrytyLmtYn",
        "cnstrtsiteRgnNm",
        "lcnsLmtNm",
        "prtcptPsblRgnNm",
        "stdNtceDocUrl",
        "ntceSpecDocUrl1",
        "ntceSpecFileNm1",
        "eorderAtchFileNm",
        "eorderAtchFileUrl",
        "bidNtceUrl",
    ]
    return {key: item.get(key) for key in keys if item.get(key) not in (None, "")}


def attachment_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    attachments: list[dict[str, str]] = []
    for item in items:
        for index in range(1, 11):
            url = str(item.get(f"ntceSpecDocUrl{index}", "") or "")
            name = str(item.get(f"ntceSpecFileNm{index}", "") or "")
            if url or name:
                attachments.append({"name": name, "url": url, "source": f"ntceSpecDocUrl{index}"})
        std_url = str(item.get("stdNtceDocUrl", "") or "")
        if std_url:
            attachments.append({"name": "standard_notice", "url": std_url, "source": "stdNtceDocUrl"})
        eorder_url = str(item.get("eorderAtchFileUrl", "") or "")
        eorder_name = str(item.get("eorderAtchFileNm", "") or "")
        if eorder_url or eorder_name:
            attachments.append({"name": eorder_name, "url": eorder_url, "source": "eorderAtchFileUrl"})

    supported = []
    unsupported = []
    for attachment in attachments:
        suffix = Path(urllib.parse.urlparse(attachment["name"]).path).suffix.lower()
        if not suffix:
            suffix = Path(urllib.parse.urlparse(attachment["url"]).path).suffix.lower()
        row = {**attachment, "suffix": suffix}
        if suffix in {".pdf", ".docx"}:
            supported.append(row)
        else:
            unsupported.append(row)
    return {"total": len(attachments), "supported": supported, "unsupported": unsupported}


def result_code(parsed: dict[str, Any]) -> str:
    header = parsed.get("header") or {}
    return str(header.get("resultCode", header.get("resultMsg", "")))


def first_download_candidate(results: list[dict[str, Any]]) -> dict[str, str] | None:
    candidates: list[dict[str, str]] = []
    for result in results:
        summary = result.get("attachment_summary") or {}
        for attachment in summary.get("supported") or []:
            url = str(attachment.get("url") or "")
            suffix = str(attachment.get("suffix") or "").lower()
            if url and suffix in {".pdf", ".docx"}:
                candidates.append(attachment)

    pdf_candidates = [candidate for candidate in candidates if str(candidate.get("suffix")).lower() == ".pdf"]
    if pdf_candidates:
        return pdf_candidates[0]
    return candidates[0] if candidates else None


def download_test(results: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = first_download_candidate(results)
    if not candidate:
        return {
            "attempted": False,
            "success": False,
            "reason": "No supported PDF/DOCX attachment was found in API responses.",
        }

    started = time.time()
    try:
        http_status, headers, body = request_binary(candidate["url"])
        elapsed_ms = int((time.time() - started) * 1000)
    except Exception as exc:
        return {
            "attempted": True,
            "success": False,
            "name": candidate.get("name", ""),
            "source": candidate.get("source", ""),
            "suffix": candidate.get("suffix", ""),
            "error": str(exc),
        }

    suffix = str(candidate.get("suffix") or "").lower()
    content_type = headers.get("content-type", "")
    pdf_signature = body.startswith(b"%PDF")
    docx_signature = body.startswith(b"PK\x03\x04")
    valid_signature = (suffix == ".pdf" and pdf_signature) or (suffix == ".docx" and docx_signature)

    return {
        "attempted": True,
        "success": http_status == 200 and valid_signature,
        "name": candidate.get("name", ""),
        "source": candidate.get("source", ""),
        "suffix": suffix,
        "url": candidate.get("url", ""),
        "http_status": http_status,
        "elapsed_ms": elapsed_ms,
        "content_type": content_type,
        "content_length_header": headers.get("content-length", ""),
        "downloaded_bytes": len(body),
        "pdf_signature": pdf_signature,
        "docx_zip_signature": docx_signature,
        "valid_signature": valid_signature,
    }


def make_base_params(service_key: str, date: str, page_size: int) -> dict[str, str]:
    return {
        "ServiceKey": service_key,
        "numOfRows": str(page_size),
        "pageNo": "1",
        "type": "json",
        "inqryDiv": "1",
        "inqryBgnDt": f"{date}0000",
        "inqryEndDt": f"{date}2359",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Nara Marketplace public data APIs.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    parser.add_argument("--num-of-rows", type=int, default=10)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    load_env_file(BACKEND_ENV)
    service_key = os.getenv("NARA_API_SERVICE_KEY", "").strip()
    if not service_key:
        print("ERROR: NARA_API_SERVICE_KEY is missing. Set it in environment or backend/.env.", file=sys.stderr)
        return 2

    bid_base_url = os.getenv("NARA_BID_PUBLIC_API_BASE_URL", DEFAULT_BID_PUBLIC_BASE_URL).strip()
    pubdata_base_url = os.getenv("NARA_PUBDATA_API_BASE_URL", DEFAULT_PUBDATA_BASE_URL).strip()
    base_params = make_base_params(service_key, args.date, args.num_of_rows)

    tests = [
        ApiTest(
            "bid_public_construction_search",
            bid_base_url,
            "getBidPblancListInfoCnstwkPPSSrch",
            base_params,
            "Portal notice search by date and filters",
        ),
        ApiTest(
            "bid_public_construction_list",
            bid_base_url,
            "getBidPblancListInfoCnstwk",
            base_params,
            "Construction notice list/sync by registration date",
        ),
        ApiTest(
            "bid_public_construction_basis_amount",
            bid_base_url,
            "getBidPblancListInfoCnstwkBsisAmount",
            base_params,
            "Basis amount enrichment",
        ),
        ApiTest(
            "bid_public_license_limit",
            bid_base_url,
            "getBidPblancListInfoLicenseLimit",
            base_params,
            "License and industry restriction enrichment",
        ),
        ApiTest(
            "bid_public_region_limit",
            bid_base_url,
            "getBidPblancListInfoPrtcptPsblRgn",
            base_params,
            "Eligible region enrichment",
        ),
        ApiTest(
            "bid_public_eorder_attachments",
            bid_base_url,
            "getBidPblancListInfoEorderAtchFileInfo",
            base_params,
            "e-order attachment lookup",
        ),
        ApiTest(
            "pubdata_standard_bid_notice",
            pubdata_base_url,
            "getDataSetOpnStdBidPblancInfo",
            {
                "ServiceKey": service_key,
                "numOfRows": str(args.num_of_rows),
                "pageNo": "1",
                "type": "json",
                "bidNtceBgnDt": f"{args.date}0000",
                "bidNtceEndDt": f"{args.date}2359",
            },
            "Standardized notice data",
        ),
    ]

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    first_notice: dict[str, Any] | None = None

    for test in tests:
        url = build_url(test.base_url, test.operation, test.params)
        started = time.time()
        http_status, raw_text = request_text(url)
        elapsed_ms = int((time.time() - started) * 1000)
        try:
            parsed = parse_response(raw_text)
        except Exception as exc:
            parsed = {"format": "parse_error", "header": {"resultMsg": str(exc)}, "body": {}, "items": [], "total_count": 0}

        items = parsed.get("items", [])
        if test.name == "bid_public_construction_search" and items:
            first_notice = items[0]

        results.append(
            {
                "name": test.name,
                "purpose": test.purpose,
                "operation": test.operation,
                "url_without_key": build_url(test.base_url, test.operation, {**test.params, "ServiceKey": "***"}),
                "http_status": http_status,
                "elapsed_ms": elapsed_ms,
                "format": parsed.get("format"),
                "result_code": result_code(parsed),
                "result_msg": (parsed.get("header") or {}).get("resultMsg", ""),
                "total_count": parsed.get("total_count", 0),
                "item_count": len(items),
                "sample_items": [compact_item(item) for item in items[:3]],
                "attachment_summary": attachment_summary(items),
            }
        )

    if first_notice:
        bid_no = str(first_notice.get("bidNtceNo", ""))
        bid_ord = str(first_notice.get("bidNtceOrd", "000") or "000")
        detail_params = {
            "ServiceKey": service_key,
            "numOfRows": str(args.num_of_rows),
            "pageNo": "1",
            "type": "json",
            "inqryDiv": "2",
            "bidNtceNo": bid_no,
            "bidNtceOrd": bid_ord,
        }
        detail_tests = [
            ApiTest("detail_notice_by_number", bid_base_url, "getBidPblancListInfoCnstwk", detail_params, "Direct notice lookup"),
            ApiTest("detail_basis_amount_by_number", bid_base_url, "getBidPblancListInfoCnstwkBsisAmount", detail_params, "Direct basis amount lookup"),
            ApiTest("detail_license_by_number", bid_base_url, "getBidPblancListInfoLicenseLimit", detail_params, "Direct license lookup"),
            ApiTest("detail_region_by_number", bid_base_url, "getBidPblancListInfoPrtcptPsblRgn", detail_params, "Direct region lookup"),
            ApiTest("detail_eorder_attachment_by_number", bid_base_url, "getBidPblancListInfoEorderAtchFileInfo", detail_params, "Direct e-order attachment lookup"),
        ]
        for test in detail_tests:
            url = build_url(test.base_url, test.operation, test.params)
            started = time.time()
            http_status, raw_text = request_text(url)
            elapsed_ms = int((time.time() - started) * 1000)
            try:
                parsed = parse_response(raw_text)
            except Exception as exc:
                parsed = {"format": "parse_error", "header": {"resultMsg": str(exc)}, "body": {}, "items": [], "total_count": 0}
            items = parsed.get("items", [])
            results.append(
                {
                    "name": test.name,
                    "purpose": test.purpose,
                    "operation": test.operation,
                    "url_without_key": build_url(test.base_url, test.operation, {**test.params, "ServiceKey": "***"}),
                    "http_status": http_status,
                    "elapsed_ms": elapsed_ms,
                    "format": parsed.get("format"),
                    "result_code": result_code(parsed),
                    "result_msg": (parsed.get("header") or {}).get("resultMsg", ""),
                    "total_count": parsed.get("total_count", 0),
                    "item_count": len(items),
                    "sample_items": [compact_item(item) for item in items[:3]],
                    "attachment_summary": attachment_summary(items),
                }
            )

    attachment_download_test = download_test(results)
    output_path = Path(args.output) if args.output else TEMP_DIR / f"nara-api-test-{args.date}-{datetime.now().strftime('%H%M%S')}.json"
    output = {
        "tested_at": datetime.now().isoformat(timespec="seconds"),
        "date": args.date,
        "bid_public_base_url": bid_base_url,
        "pubdata_base_url": pubdata_base_url,
        "results": results,
        "download_test": attachment_download_test,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"NARA_API_TEST date={args.date} output={output_path}")
    for row in results:
        print(
            " | ".join(
                [
                    row["name"],
                    f"http={row['http_status']}",
                    f"code={row['result_code']}",
                    f"total={row['total_count']}",
                    f"items={row['item_count']}",
                    f"attachments={row['attachment_summary']['total']}",
                    f"ms={row['elapsed_ms']}",
                ]
            )
        )

    if attachment_download_test.get("attempted"):
        print(
            " | ".join(
                [
                    "download_test",
                    f"file={attachment_download_test.get('name', '')}",
                    f"http={attachment_download_test.get('http_status', '')}",
                    f"type={attachment_download_test.get('content_type', '')}",
                    f"bytes={attachment_download_test.get('downloaded_bytes', '')}",
                    f"valid_signature={attachment_download_test.get('valid_signature', False)}",
                ]
            )
        )
    else:
        print(f"download_test | skipped | reason={attachment_download_test.get('reason', '')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
