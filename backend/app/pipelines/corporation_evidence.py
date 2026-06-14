import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BUSINESS_REGISTRATION_TYPES = {
    "business_registration_certificate",
    "business_registration_proof",
}

CORE_EVIDENCE_TYPES = {
    "small_business_confirmation",
    "women_owned_business_confirmation",
    "disabled_owned_business_confirmation",
    "direct_production_confirmation",
    "procurement_registration_certificate",
    "license_registration_certificate",
    "tax_payment_certificate",
    "local_tax_payment_certificate",
    "insurance_payment_certificate",
    "credit_rating_certificate",
    "performance_certificate",
    "financial_statement_certificate",
    "gpass_company_certificate",
    "iso_quality_certificate",
    "venture_business_confirmation",
    "innobiz_confirmation",
    "factory_registration_certificate",
    "research_institute_certificate",
    "software_business_certificate",
    "software_quality_certificate",
    "green_technology_certificate",
    "green_product_confirmation",
    "excellent_product_certificate",
    "patent_certificate",
    "copyright_registration_certificate",
    "outdoor_advertising_business_registration",
    "online_sales_business_registration",
    "industry_association_membership",
    "investment_share_certificate",
    "employment_support_approval",
    "insurance_policy_certificate",
    "special_business_license",
    "technology_grade_confirmation",
    "technology_evaluation_excellent_certificate",
}

DOCUMENT_TYPE_CERTIFICATION_LABELS = {
    "small_business_confirmation": "중소기업확인서",
    "women_owned_business_confirmation": "여성기업확인서",
    "disabled_owned_business_confirmation": "장애인기업확인서",
    "direct_production_confirmation": "직접생산확인증명서",
    "procurement_registration_certificate": "나라장터 경쟁입찰참가자격 등록",
    "tax_payment_certificate": "국세 납세증명서",
    "local_tax_payment_certificate": "지방세 납세증명서",
    "insurance_payment_certificate": "4대보험 완납증명서",
    "credit_rating_certificate": "기업신용평가등급확인서",
    "performance_certificate": "실적증명서",
    "financial_statement_certificate": "재무/매출 증빙",
}

DOCUMENT_TYPE_PREFERENCE_TAGS = {
    "small_business_confirmation": "중소기업",
    "women_owned_business_confirmation": "여성기업",
    "disabled_owned_business_confirmation": "장애인기업",
}

DOCUMENT_TYPE_CERTIFICATION_LABELS.update(
    {
        "gpass_company_certificate": "G-PASS기업 지정",
        "iso_quality_certificate": "ISO9001 인증",
        "venture_business_confirmation": "벤처기업확인서",
        "innobiz_confirmation": "기술혁신형중소기업(Inno-Biz) 확인서",
        "factory_registration_certificate": "공장등록증명서",
        "research_institute_certificate": "기업부설연구소 인정서",
        "software_business_certificate": "소프트웨어사업자확인서",
        "software_quality_certificate": "소프트웨어품질인증서",
        "green_technology_certificate": "녹색기술인증서",
        "green_product_confirmation": "녹색기술제품확인서",
        "excellent_product_certificate": "우수제품지정증서",
        "patent_certificate": "특허증",
        "copyright_registration_certificate": "저작권등록증",
        "outdoor_advertising_business_registration": "옥외광고사업 등록증",
        "online_sales_business_registration": "통신판매업신고증",
        "industry_association_membership": "조합원증",
        "investment_share_certificate": "출자증권",
        "employment_support_approval": "고용안정장려금 승인",
        "insurance_policy_certificate": "책임보험가입증명서",
        "special_business_license": "특수 영업/등록/신고증",
        "technology_grade_confirmation": "기술등급확인서",
        "technology_evaluation_excellent_certificate": "기술평가우수기업인증서",
    }
)

DOCUMENT_TYPE_PREFERENCE_TAGS.update(
    {
        "gpass_company_certificate": "G-PASS",
        "venture_business_confirmation": "벤처기업",
        "innobiz_confirmation": "Inno-Biz",
        "green_technology_certificate": "녹색기술",
        "green_product_confirmation": "녹색기술제품",
        "excellent_product_certificate": "우수제품",
        "software_quality_certificate": "소프트웨어품질인증",
        "technology_grade_confirmation": "기술등급",
        "technology_evaluation_excellent_certificate": "기술평가우수기업",
    }
)

EXTENDED_EVIDENCE_CLASSIFICATION_RULES = [
    ("gpass_company_certificate", 0.9, ["g-pass", "gpass", "g-pass기업", "g-pass 기업", "해외조달시장 진출유망기업"]),
    ("iso_quality_certificate", 0.88, ["iso9001", "iso 9001", "품질경영시스템 인증서", "quality management system"]),
    ("venture_business_confirmation", 0.9, ["벤처기업확인서", "벤처기업 확인서"]),
    ("innobiz_confirmation", 0.9, ["기술혁신형중소기업", "기술혁신형 중소기업 확인서", "기술혁신형중소기업확인서", "이노비즈", "inno-biz", "inno biz", "innobiz"]),
    ("factory_registration_certificate", 0.88, ["공장등록증명서", "공장 등록 증명서"]),
    ("research_institute_certificate", 0.88, ["기업부설연구소", "연구소 인정서", "기업부설 연구소"]),
    ("software_business_certificate", 0.88, ["소프트웨어사업자일반현황관리확인서", "소프트웨어사업자 일반현황 관리확인서", "소프트웨어사업자확인서", "소프트웨어사업자", "소프트웨어 사업자", "sw사업자"]),
    ("software_quality_certificate", 0.88, ["소프트웨어품질인증서", "소프트웨어 품질인증", "gs인증", "gs 인증"]),
    ("green_technology_certificate", 0.88, ["녹색기술인증서", "녹색기술 인증"]),
    ("green_product_confirmation", 0.88, ["녹색기술제품확인서", "녹색기술제품 확인"]),
    ("excellent_product_certificate", 0.88, ["우수제품지정증서", "우수제품 지정증서", "조달청장 우수제품"]),
    ("patent_certificate", 0.88, ["특허증", "특허 제", "patent"]),
    ("copyright_registration_certificate", 0.88, ["저작권등록증", "저작권 등록증", "프로그램 등록증"]),
    ("investment_share_certificate", 0.82, ["출자증권", "출자 증권"]),
    ("insurance_policy_certificate", 0.82, ["책임보험가입증명서", "보험가입증명서", "책임보험", "옥외광고업책임보험"]),
    ("outdoor_advertising_business_registration", 0.86, ["옥외광고사업 등록증", "옥외광고업", "옥외광고사업"]),
    ("online_sales_business_registration", 0.86, ["통신판매업신고증", "통신판매업 신고증", "통신판매업"]),
    ("industry_association_membership", 0.82, ["조합원증", "협동조합 조합원", "한국전자산업협동조합"]),
    ("employment_support_approval", 0.82, ["고용안정장려금", "승인통지서"]),
    ("special_business_license", 0.8, ["영업신고증", "등록필증", "건강기능식품영업", "화장품책임판매업"]),
    ("technology_grade_confirmation", 0.84, ["기술등급확인서", "기술 등급 확인서"]),
    ("technology_evaluation_excellent_certificate", 0.84, ["기술평가우수기업인증서", "기술평가 우수기업 인증서", "기술평가우수기업"]),
]

EXTENDED_EVIDENCE_SUBJECT_LABELS = {
    "gpass_company_certificate": ["지정번호", "등급", "기업명"],
    "iso_quality_certificate": ["인증범위", "인증규격", "인증번호"],
    "venture_business_confirmation": ["확인번호", "유형", "기업명"],
    "innobiz_confirmation": ["확인번호", "등급", "기업명"],
    "factory_registration_certificate": ["공장소재지", "업종", "공장명"],
    "research_institute_certificate": ["연구소명", "인정번호", "소재지"],
    "software_business_certificate": ["사업분야", "기업명", "신고번호"],
    "software_quality_certificate": ["제품명", "인증번호", "등급"],
    "green_technology_certificate": ["기술명", "인증번호", "인증명"],
    "green_product_confirmation": ["제품명", "확인번호", "모델명"],
    "excellent_product_certificate": ["제품명", "지정번호", "품명"],
    "patent_certificate": ["발명의 명칭", "특허번호", "등록번호"],
    "copyright_registration_certificate": ["저작물의 명칭", "프로그램 명칭", "등록번호"],
    "outdoor_advertising_business_registration": ["업종", "등록번호", "사업장소재지"],
    "online_sales_business_registration": ["신고번호", "판매방식", "인터넷 도메인"],
    "industry_association_membership": ["조합원명", "회원명", "가입일"],
    "investment_share_certificate": ["출자좌수", "금액", "조합원명"],
    "employment_support_approval": ["지원금", "승인번호", "사업명"],
    "insurance_policy_certificate": ["보험종목", "증권번호", "보험기간"],
    "special_business_license": ["영업의 종류", "업종", "신고번호"],
    "technology_grade_confirmation": ["기술등급", "기술분류", "유효일"],
    "technology_evaluation_excellent_certificate": ["기술명칭", "기술명", "기술등급"],
}

BUSINESS_ITEM_SUBJECT_DOCUMENT_TYPES = {
    "patent_certificate",
    "copyright_registration_certificate",
    "software_business_certificate",
    "software_quality_certificate",
    "green_technology_certificate",
    "green_product_confirmation",
    "excellent_product_certificate",
    "technology_evaluation_excellent_certificate",
}

BUSINESS_ITEM_SUBJECT_LABELS = {
    "patent_certificate": ["발명의 명칭"],
    "copyright_registration_certificate": ["저작물의 명칭", "프로그램 명칭"],
    "software_business_certificate": ["사업분야"],
    "software_quality_certificate": ["제품명", "소프트웨어명"],
    "green_technology_certificate": ["기술명", "인증명"],
    "green_product_confirmation": ["제품명", "모델명"],
    "excellent_product_certificate": ["제품명", "품명"],
    "technology_evaluation_excellent_certificate": ["기술명칭", "기술명"],
}

BUSINESS_TYPE_TOKENS = [
    "도매 및 소매업",
    "제조업",
    "건설업",
    "서비스업",
    "도소매",
    "도매업",
    "소매업",
    "부동산업",
    "운수업",
    "정보통신업",
]

BUSINESS_KIND_STOP_TOKENS = [
    "발급사유",
    "발급일",
    "사업자단위과세",
    "전자세금계산서",
    "성남세무서장",
    "세무서장",
    "국세청",
    "별지출력",
]


@dataclass(frozen=True)
class EvidenceFieldCandidate:
    field_key: str
    field_label: str
    extracted_value: str
    confidence: float
    source_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_key": self.field_key,
            "field_label": self.field_label,
            "extracted_value": self.extracted_value,
            "confidence": self.confidence,
            "source_text": self.source_text,
        }


@dataclass(frozen=True)
class EvidenceExtractionResult:
    document_type: str
    classification_confidence: float
    classification_status: str
    candidates: list[EvidenceFieldCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_type": self.document_type,
            "classification_confidence": self.classification_confidence,
            "classification_status": self.classification_status,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "warnings": self.warnings,
        }


FIELD_LABELS = {
    "name": "법인명",
    "management_group_name": "관리 법인그룹",
    "business_registration_number": "사업자등록번호",
    "representative_name": "대표자명",
    "corporate_registration_number": "법인등록번호",
    "opening_date": "개업연월일",
    "business_address": "사업장 소재지",
    "headquarters_address": "본점 소재지",
    "region": "지역",
    "business_type": "업태",
    "business_item": "종목",
    "business_category": "업종/분류",
    "certifications_json": "인증/확인서",
    "company_size_classification": "기업 규모",
    "preference_tags_json": "우대/제한 태그",
    "direct_production_items_json": "직접생산 품목",
    "license_summary": "면허/등록 요약",
    "procurement_registration_status": "나라장터 등록 상태",
    "evidence_expiry_summary": "증빙 유효기간",
}

STOP_LABELS = [
    "법인명",
    "상호",
    "대표자",
    "개업연월일",
    "법인등록번호",
    "사업장소재지",
    "본점소재지",
    "사업의종류",
    "업태",
    "종목",
    "발급사유",
    "발급일",
    "전자세금계산서",
    "유효기간",
    "확인번호",
    "등록번호",
    "세부품명",
    "세부품명번호",
    "제품명",
    "평가등급",
    "신용등급",
    "계약금액",
    "수행기간",
]


def analyze_corporation_evidence(
    text: str,
    file_name: str = "",
    requested_document_type: str = "auto",
) -> EvidenceExtractionResult:
    normalized = normalize_evidence_text(text)
    detected_type, confidence = classify_evidence_document(normalized, file_name)
    requested_document_type = requested_document_type or "auto"
    if requested_document_type not in {"", "auto"}:
        document_type = requested_document_type
        classification_status = "manual"
        confidence = max(confidence, 0.8)
    else:
        document_type = detected_type
        classification_status = "classified" if detected_type != "unknown" else "needs_review"
    warnings: list[str] = []

    if not normalized:
        warnings.append("문서에서 추출 가능한 텍스트가 없어 자동 후보를 생성하지 않았습니다.")
        return EvidenceExtractionResult(
            document_type=document_type,
            classification_confidence=confidence,
            classification_status="needs_review",
            candidates=[],
            warnings=warnings,
        )

    if document_type in BUSINESS_REGISTRATION_TYPES:
        candidates = extract_business_registration_candidates(normalized)
        if not candidates:
            warnings.append("사업자등록 관련 문서로 보이지만 자동 추출 후보가 없습니다.")
        return EvidenceExtractionResult(
            document_type=document_type,
            classification_confidence=confidence,
            classification_status=classification_status,
            candidates=candidates,
            warnings=warnings,
        )

    if document_type in CORE_EVIDENCE_TYPES:
        candidates = extract_core_evidence_candidates(normalized, document_type)
        if not candidates:
            warnings.append("증빙서류 유형은 확인했지만 자동 추출 후보가 없습니다.")
        return EvidenceExtractionResult(
            document_type=document_type,
            classification_confidence=confidence,
            classification_status=classification_status if candidates else "needs_review",
            candidates=candidates,
            warnings=warnings,
        )

    warnings.append("규칙 기반으로 확정 가능한 법인 기본정보 증빙서류가 아닙니다.")
    return EvidenceExtractionResult(
        document_type=document_type,
        classification_confidence=confidence,
        classification_status="needs_review",
        candidates=[],
        warnings=warnings,
    )


def normalize_evidence_text(text: str) -> str:
    value = (text or "").replace("\x00", "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return "\n".join(line.strip() for line in value.splitlines() if line.strip()).strip()


def classify_evidence_document(text: str, file_name: str = "") -> tuple[str, float]:
    haystack = f"{file_name}\n{text}".lower()
    compact = _compact(haystack)

    if "사업자등록증명" in compact:
        return "business_registration_proof", 0.96
    if "사업자등록증" in compact and ("등록번호" in compact or "사업자등록번호" in compact):
        return "business_registration_certificate", 0.94
    for document_type, rule_confidence, tokens in EXTENDED_EVIDENCE_CLASSIFICATION_RULES:
        if any(token.lower() in haystack for token in tokens):
            return document_type, rule_confidence
    if "직접생산확인증명서" in compact or ("직접생산" in compact and ("세부품명" in compact or "제품명" in compact)):
        return "direct_production_confirmation", 0.9
    if "기업신용평가" in compact or "신용평가등급" in compact or "신용등급확인서" in compact:
        return "credit_rating_certificate", 0.86
    if "중소기업확인서" in compact or ("소기업" in compact and "유효기간" in compact):
        return "small_business_confirmation", 0.92
    if "여성기업확인서" in compact or ("여성기업" in compact and "확인번호" in compact):
        return "women_owned_business_confirmation", 0.92
    if "장애인기업확인서" in compact or ("장애인기업" in compact and "확인번호" in compact):
        return "disabled_owned_business_confirmation", 0.92
    if "경쟁입찰참가자격등록증" in compact or "입찰참가자격등록" in compact:
        return "procurement_registration_certificate", 0.88
    if any(token in compact for token in ("건설업등록증", "전기공사업등록증", "정보통신공사업등록증", "소방시설공사업등록증", "엔지니어링사업자신고증", "산림사업법인등록증", "소프트웨어사업자일반현황관리확인서")):
        return "license_registration_certificate", 0.86
    if "실적증명서" in compact or ("수행실적" in compact and ("계약금액" in compact or "계약기간" in compact)):
        return "performance_certificate", 0.84
    if "국세납세증명" in compact or ("납세증명서" in compact and "국세" in compact):
        return "tax_payment_certificate", 0.84
    if "지방세납세증명" in compact or ("납세증명서" in compact and "지방세" in compact):
        return "local_tax_payment_certificate", 0.84
    if "4대보험완납" in compact or "사회보험료완납" in compact:
        return "insurance_payment_certificate", 0.84
    if "표준재무제표증명" in compact or "부가가치세과세표준증명" in compact or "재무제표증명" in compact:
        return "financial_statement_certificate", 0.82
    if "사업자등록번호" in compact and ("대표자" in compact or "법인명" in compact or "상호" in compact):
        return "business_registration_certificate", 0.84
    return "unknown", 0.0


def extract_business_registration_candidates(text: str) -> list[EvidenceFieldCandidate]:
    candidates: list[EvidenceFieldCandidate] = []

    def add(field_key: str, value: str, confidence: float = 0.88, source_text: str = "") -> None:
        cleaned = _clean_value(value)
        if not cleaned:
            return
        if any(item.field_key == field_key and item.extracted_value == cleaned for item in candidates):
            return
        candidates.append(
            EvidenceFieldCandidate(
                field_key=field_key,
                field_label=FIELD_LABELS.get(field_key, field_key),
                extracted_value=cleaned,
                confidence=confidence,
                source_text=source_text or cleaned,
            )
        )

    registration_number = _find_pattern(
        text,
        r"(?:사업자\s*등록\s*번호|등록\s*번호)\s*[:：]?\s*([0-9]{3}\s*[-]?\s*[0-9]{2}\s*[-]?\s*[0-9]{5})",
    )
    add("business_registration_number", _normalize_registration_number(registration_number), 0.96)

    corporate_registration_number = _find_pattern(
        text,
        r"법인\s*등록\s*번호\s*[:：]?\s*([0-9]{6}\s*[-]?\s*[0-9]{7})",
    )
    add("corporate_registration_number", _normalize_registration_number(corporate_registration_number), 0.94)

    corporation_name = _find_value_after_label(text, ["법인명", "상호"], allow_continuation=False)
    add("name", corporation_name, 0.9)

    representative = _find_value_after_label(text, ["대표자"], allow_continuation=False)
    add("representative_name", representative, 0.9)

    opening_date = _find_value_after_label(text, ["개업연월일"], allow_continuation=False)
    add("opening_date", _normalize_date(opening_date), 0.88, opening_date)

    business_address = _find_value_after_label(text, ["사업장소재지", "사업장 소재지"], allow_continuation=True)
    add("business_address", business_address, 0.86)

    headquarters_address = _find_value_after_label(text, ["본점소재지", "본점 소재지"], allow_continuation=True)
    add("headquarters_address", headquarters_address, 0.84)

    region_source = business_address or headquarters_address
    region = _derive_region(region_source)
    add("region", region, 0.72, region_source)

    refined_business_type, refined_business_item = _extract_business_kind_pair(text)

    business_type = refined_business_type or _find_value_after_label(text, ["업태"], allow_continuation=False)
    business_type = _strip_after_label(business_type, ["종목"])
    add("business_type", business_type, 0.78)

    business_item = refined_business_item or _find_value_after_label(text, ["종목"], allow_continuation=True)
    add("business_item", business_item, 0.72)

    business_category = _format_business_category(business_type, business_item)
    add("business_category", business_category, 0.7)

    return candidates


def extract_core_evidence_candidates(text: str, document_type: str) -> list[EvidenceFieldCandidate]:
    candidates: list[EvidenceFieldCandidate] = []

    def add(field_key: str, value: str, confidence: float = 0.82, source_text: str = "") -> None:
        cleaned = _clean_value(value)
        if not cleaned:
            return
        if any(item.field_key == field_key and item.extracted_value == cleaned for item in candidates):
            return
        candidates.append(
            EvidenceFieldCandidate(
                field_key=field_key,
                field_label=FIELD_LABELS.get(field_key, field_key),
                extracted_value=cleaned,
                confidence=confidence,
                source_text=source_text or cleaned,
            )
        )

    _add_common_identity_candidates(text, add)

    certification_label = DOCUMENT_TYPE_CERTIFICATION_LABELS.get(document_type)
    if certification_label:
        add("certifications_json", _json_list([certification_label]), 0.86, certification_label)

    preference_tag = DOCUMENT_TYPE_PREFERENCE_TAGS.get(document_type)
    if preference_tag:
        add("preference_tags_json", _json_list([preference_tag]), 0.86, preference_tag)

    valid_period = _find_value_after_label(text, ["유효기간", "유효 기간", "확인유효기간"], allow_continuation=False)
    if not valid_period:
        valid_period = _find_pattern(text, r"(\d{4}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}.*?\d{4}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2})")
    add("evidence_expiry_summary", valid_period, 0.72)

    if document_type == "small_business_confirmation":
        size = _detect_company_size(text)
        add("company_size_classification", size, 0.88)

    if document_type == "direct_production_confirmation":
        items = _extract_direct_production_items(text)
        if items:
            add("direct_production_items_json", _json_list(items), 0.86, ", ".join(items))
            add("business_item", ", ".join(items), 0.68)

    if document_type == "procurement_registration_certificate":
        add("procurement_registration_status", "registered", 0.86)
        license_summary = _find_value_after_label(text, ["등록업종", "입찰참가자격", "업종", "물품분류"], True)
        add("license_summary", license_summary, 0.74)

    if document_type == "license_registration_certificate":
        license_summary = _extract_license_summary(text)
        add("license_summary", license_summary, 0.82)
        if license_summary:
            add("certifications_json", _json_list([license_summary]), 0.72)

    if document_type == "credit_rating_certificate":
        grade = _extract_credit_rating_grade(text)
        label = f"기업신용평가등급 {grade}" if grade else "기업신용평가등급확인서"
        add("certifications_json", _json_list([label]), 0.84, label)
        add("license_summary", label, 0.72, label)

    if document_type == "performance_certificate":
        summary = _extract_performance_summary(text)
        add("license_summary", summary, 0.74, summary)

    if document_type in {"tax_payment_certificate", "local_tax_payment_certificate", "insurance_payment_certificate"}:
        status = _extract_payment_status(text, document_type)
        add("license_summary", status, 0.74, status)

    if document_type == "financial_statement_certificate":
        fiscal_year = _find_pattern(text, r"(?:사업연도|귀속연도|회계연도)\s*[:：]?\s*([0-9]{4})")
        summary = f"재무/매출 증빙 {fiscal_year}" if fiscal_year else "재무/매출 증빙"
        add("license_summary", summary, 0.7, summary)

    if document_type in EXTENDED_EVIDENCE_SUBJECT_LABELS:
        label = DOCUMENT_TYPE_CERTIFICATION_LABELS.get(document_type, document_type)
        subject = _extract_extended_evidence_subject(text, document_type)
        summary = f"{label}: {subject}" if subject else label
        add("license_summary", summary, 0.74, summary)
        if document_type in BUSINESS_ITEM_SUBJECT_DOCUMENT_TYPES:
            business_item_subject = _extract_business_item_subject(text, document_type)
            if business_item_subject:
                add("business_item", business_item_subject, 0.68, business_item_subject)

    return candidates


def _add_common_identity_candidates(text: str, add) -> None:
    registration_number = _find_pattern(
        text,
        r"(?:사업자\s*등록\s*번호|사업자번호|등록\s*번호)\s*[:：]?\s*([0-9]{3}\s*[-]?\s*[0-9]{2}\s*[-]?\s*[0-9]{5})",
    )
    add("business_registration_number", _normalize_registration_number(registration_number), 0.94)

    name = _find_value_after_label(text, ["법인명", "기업명", "업체명", "상호", "회사명"], allow_continuation=False)
    add("name", name, 0.84)

    representative = _find_value_after_label(text, ["대표자", "대표자명"], allow_continuation=False)
    add("representative_name", representative, 0.8)


def _detect_company_size(text: str) -> str:
    compact = _compact(text)
    for token in ("소상공인", "소기업", "중기업", "중소기업"):
        if token in compact:
            return token
    return ""


def _extract_direct_production_items(text: str) -> list[str]:
    values: list[str] = []
    for label in ["세부품명", "제품명", "품명", "물품분류명"]:
        value = _find_value_after_label(text, [label], allow_continuation=False)
        value = _strip_after_label(value, ["유효기간", "확인번호", "발급"])
        if value:
            values.extend(_split_items(value))
    return _dedupe(values)


def _extract_extended_evidence_subject(text: str, document_type: str, labels: list[str] | None = None) -> str:
    labels = labels if labels is not None else EXTENDED_EVIDENCE_SUBJECT_LABELS.get(document_type, [])
    for label in labels:
        value = _find_value_after_label(text, [label], allow_continuation=False)
        value = _strip_after_label(value, ["유효기간", "인증기간", "등록일", "발급일", "권리자"])
        if value:
            return value

    pattern = {
        "patent_certificate": r"(?:발명의\s*명칭|명칭)\s*[:：]?\s*(.+)",
        "copyright_registration_certificate": r"(?:저작물의\s*명칭|프로그램\s*명칭|명칭)\s*[:：]?\s*(.+)",
        "software_quality_certificate": r"(?:제품명|소프트웨어명)\s*[:：]?\s*(.+)",
        "green_technology_certificate": r"(?:기술명|인증명)\s*[:：]?\s*(.+)",
        "green_product_confirmation": r"(?:제품명|모델명)\s*[:：]?\s*(.+)",
    }.get(document_type)
    if pattern:
        value = _find_pattern(text, pattern)
        if value:
            return _clean_value(value)
    return ""


def _extract_business_item_subject(text: str, document_type: str) -> str:
    labels = BUSINESS_ITEM_SUBJECT_LABELS.get(document_type)
    if not labels:
        return ""
    return _extract_extended_evidence_subject(text, document_type, labels)


def _extract_license_summary(text: str) -> str:
    for label in ["업종명", "등록업종", "면허명", "등록분야", "전문분야", "공사업의 종류", "산림사업종류", "신고분야"]:
        value = _find_value_after_label(text, [label], allow_continuation=False)
        if value:
            return value
    for token in ["건설업", "전기공사업", "정보통신공사업", "소방시설공사업", "엔지니어링사업자", "산림사업법인", "소프트웨어사업자"]:
        if token in text:
            return token
    return ""


def _extract_credit_rating_grade(text: str) -> str:
    grade = _find_pattern(
        text,
        r"(?:신용평가등급|기업신용등급|신용등급|평가등급)\s*[:：]?\s*([A-D][A-D]?[+\-0]?)",
    )
    return grade.upper()


def _extract_performance_summary(text: str) -> str:
    project = _find_value_after_label(text, ["사업명", "계약명", "용역명", "공사명"], allow_continuation=False)
    amount = _find_value_after_label(text, ["계약금액", "실적금액", "금액"], allow_continuation=False)
    period = _find_value_after_label(text, ["수행기간", "계약기간", "납품기간"], allow_continuation=False)
    pieces = []
    if project:
        pieces.append(project)
    if amount:
        pieces.append(amount)
    if period:
        pieces.append(period)
    return " / ".join(pieces) if pieces else "실적증명서"


def _extract_payment_status(text: str, document_type: str) -> str:
    compact = _compact(text)
    prefix = {
        "tax_payment_certificate": "국세 납세",
        "local_tax_payment_certificate": "지방세 납세",
        "insurance_payment_certificate": "4대보험 완납",
    }.get(document_type, "납부")
    if "체납없" in compact or "체납액없" in compact or "완납" in compact or "해당없음" in compact:
        return f"{prefix}: 체납 없음"
    if "체납" in compact:
        return f"{prefix}: 체납 확인 필요"
    return f"{prefix}: 확인 필요"


def _extract_business_kind_pair(text: str) -> tuple[str, str]:
    section = _business_kind_section(text)
    if not section:
        return "", ""

    business_types: list[str] = []
    business_items: list[str] = []
    for line in _normalize_business_kind_lines(section):
        extracted_type, remainder = _extract_business_type_from_line(line)
        if extracted_type:
            business_types.append(extracted_type)
            if remainder:
                business_items.extend(_split_business_items(remainder))
            continue

        business_items.extend(_split_business_items(line))

    return ", ".join(_dedupe(business_types)), ", ".join(_dedupe(business_items))


def _business_kind_section(text: str) -> str:
    lines = text.splitlines()
    start_index = -1
    for index, line in enumerate(lines):
        compact = _compact(line)
        next_compact = _compact(lines[index + 1]) if index + 1 < len(lines) else ""
        if (
            "사업의종류" in compact
            or compact == "사업의" and next_compact.startswith("종류")
            or compact == "업태"
            or compact.startswith("업태")
        ):
            start_index = index
            break
    if start_index < 0:
        return ""

    section_lines: list[str] = []
    for line in lines[start_index : start_index + 36]:
        compact = _compact(line)
        if section_lines and _is_business_kind_stop_compact(compact):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def _normalize_business_kind_section(section: str) -> str:
    value = section
    value = re.sub(r"전문기\s*\n\s*업", "전문기업", value)
    value = re.sub(r"도매\s*및\s*\n\s*소매업", "도매 및 소매업", value)
    value = re.sub(r"신재생에너지\s*설비", "신재생에너지설비", value)
    value = re.sub(r"([가-힣])\s*,\s*([가-힣])", r"\1, \2", value)
    return value


def _normalize_business_kind_lines(section: str) -> list[str]:
    normalized_section = _normalize_business_kind_section(section)
    lines: list[str] = []
    for raw_line in normalized_section.splitlines():
        line = _clean_business_kind_line(raw_line)
        if not line or _is_business_kind_label(line):
            continue
        if _is_business_kind_stop_line(line):
            break
        if lines and _is_suffix_fragment(line) and not _is_business_type_token(lines[-1]):
            lines[-1] = _clean_value(f"{lines[-1]}{line}")
            continue
        lines.append(line)
    return lines


def _clean_business_kind_line(line: str) -> str:
    cleaned = _clean_value(line)
    cleaned = re.sub(r"^\(?별지\s*출력\)?$", "", cleaned)
    for label in ["사업의 종류", "사업의종류"]:
        cleaned = re.sub(_label_pattern(label) + r"\s*[:：]?", "", cleaned, flags=re.IGNORECASE).strip()
    for label in ["업태", "종목"]:
        pattern = _label_pattern(label)
        cleaned = re.sub(rf"^{pattern}\s*[:：]?", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned


def _is_business_kind_label(line: str) -> bool:
    compact = _compact(line)
    return compact in {"사업의", "종류", "사업의종류", "업태", "종목"}


def _is_business_kind_stop_line(line: str) -> bool:
    return _is_business_kind_stop_compact(_compact(line))


def _is_business_kind_stop_compact(compact: str) -> bool:
    return any(token in compact for token in BUSINESS_KIND_STOP_TOKENS)


def _is_suffix_fragment(line: str) -> bool:
    compact = _compact(line)
    return compact in {"업", "기", "사", "자"}


def _is_business_type_token(value: str) -> bool:
    compact_value = _compact(value)
    return compact_value in {_compact(token) for token in BUSINESS_TYPE_TOKENS}


def _extract_business_type_from_line(line: str) -> tuple[str, str]:
    compact_line = _compact(line)
    for token in BUSINESS_TYPE_TOKENS:
        compact_token = _compact(token)
        if compact_line == compact_token:
            return token, ""
        if compact_line.startswith(compact_token):
            remainder = _remove_compact_prefix(line, compact_token).strip(" :：,/·ㆍ")
            return token, remainder
    return "", line


def _remove_compact_prefix(value: str, compact_prefix: str) -> str:
    compact_seen = ""
    for index, char in enumerate(value):
        if char.isspace():
            continue
        compact_seen += char
        if compact_seen == compact_prefix:
            return value[index + 1 :]
    return value


def _split_business_items(value: str) -> list[str]:
    items: list[str] = []
    for item in re.split(r"[,/·ㆍ]", value):
        cleaned = _clean_value(item)
        for label in ["종목", "업태"]:
            cleaned = re.sub(rf"^{_label_pattern(label)}\s*[:：]?", "", cleaned, flags=re.IGNORECASE).strip()
        if not cleaned:
            continue
        if _is_business_kind_label(cleaned) or _is_business_kind_stop_line(cleaned):
            continue
        if _is_business_type_token(cleaned):
            continue
        items.append(cleaned)
    return items


def normalize_business_kind_values(raw_business_types: Any, raw_business_items: Any) -> tuple[list[str], list[str]]:
    business_types: list[str] = []
    business_items: list[str] = []

    for line in _iter_business_kind_input_lines(raw_business_types):
        extracted_type, remainder = _extract_business_type_from_line(line)
        if extracted_type:
            business_types.append(extracted_type)
            business_items.extend(_split_business_items(remainder))
        else:
            matched_type = _match_business_type_in_line(line)
            if matched_type:
                business_types.append(matched_type)

    for line in _iter_business_kind_input_lines(raw_business_items):
        extracted_type, remainder = _extract_business_type_from_line(line)
        if extracted_type:
            business_types.append(extracted_type)
            if remainder:
                business_items.extend(_split_business_items(remainder))
        else:
            business_items.extend(_split_business_items(line))

    return _dedupe(business_types), _dedupe(business_items)


def _iter_business_kind_input_lines(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            lines.extend(_iter_business_kind_input_lines(item))
        return lines
    if isinstance(value, dict):
        return []

    normalized = _normalize_business_kind_section(str(value))
    lines: list[str] = []
    for raw_line in re.split(r"\n|;", normalized):
        line = _clean_business_kind_line(raw_line)
        if not line or _is_business_kind_label(line) or _is_business_kind_stop_line(line):
            continue
        if lines and _is_suffix_fragment(line) and not _is_business_type_token(lines[-1]):
            lines[-1] = _clean_value(f"{lines[-1]}{line}")
            continue
        lines.append(line)
    return lines


def _match_business_type_in_line(line: str) -> str:
    compact_line = _compact(line)
    for token in BUSINESS_TYPE_TOKENS:
        if compact_line == _compact(token):
            return token
    return ""


def _format_business_category(business_type: str, business_item: str) -> str:
    pieces = []
    if business_type:
        pieces.append(f"업태: {business_type}")
    if business_item:
        pieces.append(f"종목: {business_item}")
    return " / ".join(pieces)


def allowed_profile_update_fields() -> set[str]:
    return set(FIELD_LABELS)


def _find_pattern(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _find_value_after_label(text: str, labels: list[str], allow_continuation: bool) -> str:
    lines = text.splitlines()
    label_patterns = [_label_pattern(label) for label in labels]

    for index, line in enumerate(lines):
        for label_pattern in label_patterns:
            match = re.search(
                rf"{label_pattern}\s*(?:\([^)]*\))?\s*[:：]?\s*(.*)$",
                line,
                flags=re.IGNORECASE,
            )
            if not match:
                continue
            value_parts = [match.group(1).strip()]
            if allow_continuation:
                for next_line in lines[index + 1 : index + 3]:
                    if _line_has_stop_label(next_line):
                        break
                    value_parts.append(next_line.strip())
            return " ".join(part for part in value_parts if part).strip()
    return ""


def _line_has_stop_label(line: str) -> bool:
    compact = _compact(line)
    return any(label in compact for label in STOP_LABELS)


def _strip_after_label(value: str, labels: list[str]) -> str:
    result = value
    for label in labels:
        pattern = _label_pattern(label)
        result = re.split(pattern, result, maxsplit=1)[0]
    return result.strip()


def _label_pattern(label: str) -> str:
    compact_label = _compact(label)
    return r"\s*".join(re.escape(char) for char in compact_label)


def _clean_value(value: str) -> str:
    cleaned = (value or "").strip(" :：\t\n")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([),.])", r"\1", cleaned)
    return cleaned.strip()


def _json_list(values: list[str]) -> str:
    return json.dumps(_dedupe([_clean_value(value) for value in values if _clean_value(value)]), ensure_ascii=False)


def _split_items(value: str) -> list[str]:
    return [_clean_value(item) for item in re.split(r"[,/·ㆍ]", value) if _clean_value(item)]


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _normalize_registration_number(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    if len(digits) == 13:
        return f"{digits[:6]}-{digits[6:]}"
    return _clean_value(value)


def _normalize_date(value: str) -> str:
    cleaned = _clean_value(value)
    if not cleaned:
        return ""
    match = re.search(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", cleaned)
    if match:
        return _format_date(match.group(1), match.group(2), match.group(3))
    match = re.search(r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})", cleaned)
    if match:
        return _format_date(match.group(1), match.group(2), match.group(3))
    return cleaned


def _format_date(year: str, month: str, day: str) -> str:
    try:
        return datetime(int(year), int(month), int(day)).date().isoformat()
    except ValueError:
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _derive_region(address: str) -> str:
    cleaned = _clean_value(address)
    if not cleaned:
        return ""
    parts = cleaned.split()
    if len(parts) >= 2 and (parts[0].endswith(("도", "시")) or parts[0] in {"서울특별시", "부산광역시", "대구광역시"}):
        return " ".join(parts[:2])
    return parts[0] if parts else ""


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def evidence_storage_subdir(corporation_id: int | None = None) -> Path:
    if corporation_id:
        return Path("corporation-evidence") / str(corporation_id)
    return Path("corporation-evidence") / "pending"
