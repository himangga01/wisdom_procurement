import json
import unittest

from app.pipelines.corporation_evidence import analyze_corporation_evidence, normalize_business_kind_values


BUSINESS_REGISTRATION_TEXT = """
사업자등록증
( 법인사업자 )
등록번호 : 142-81-28387
법인명(단체명) : 주식회사 온세이엔씨
대표자 : 안영식
개업연월일 : 2010 년 05 월 25 일
법인등록번호 : 134511-0154712
사업장 소재지 : 경기도 성남시 수정구 청계산로 686, 8층 820호
본점 소재지 : 경기도 성남시 수정구 청계산로 686, 8층 820호
사업의 종류 : 업태 건설업
종목 전기공사, 신재생에너지설비설치전문기업
"""

BROKEN_BUSINESS_KIND_OCR_TEXT = """
사업자등록증
등록번호 : 142-81-28387
법인명(단체명) : 주식회사 온세이엔씨
대표자 : 안영식
사업의
종류:
업태
건설업
종목
전기공사,신재생에너지설비설치전문기
업
건설업
일반건축공사업
건설업
전문소방시설공사, 안전시설물설치
건설업
정보통신공사업, 토목공사업
도소매
전기, 소방, 통신자재
도매 및
소매업
컴퓨터 관련 주변기기
도매 및 소매업
산업안전용품
발급사유 : 정정
"""

INLINE_LABEL_BUSINESS_KIND_OCR_TEXT = """
사업자등록증
등록번호 : 142-81-28387
법인명(단체명) : 주식회사 온세이엔씨
사업의 종류 : 업태 건설업 종목 전기공사, 신재생에너지 설비설치전문기
업
업태 도매 및
소매업 종목 컴퓨터 관련 주변기기, 산업안전용품
사업자 단위 과세 적용사업자 여부 : 여( ) 부(V)
"""


class CorporationEvidenceExtractionTests(unittest.TestCase):
    def test_business_registration_rules_extract_core_fields(self) -> None:
        result = analyze_corporation_evidence(BUSINESS_REGISTRATION_TEXT, "사업자등록증.pdf")

        self.assertEqual(result.document_type, "business_registration_certificate")
        self.assertEqual(result.classification_status, "classified")

        fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}
        self.assertEqual(fields["business_registration_number"], "142-81-28387")
        self.assertEqual(fields["name"], "주식회사 온세이엔씨")
        self.assertEqual(fields["representative_name"], "안영식")
        self.assertEqual(fields["corporate_registration_number"], "134511-0154712")
        self.assertEqual(fields["opening_date"], "2010-05-25")
        self.assertIn("경기도 성남시", fields["business_address"])
        self.assertEqual(fields["region"], "경기도 성남시")
        self.assertIn("건설업", fields["business_category"])

    def test_business_registration_rules_clean_broken_kind_table_ocr(self) -> None:
        result = analyze_corporation_evidence(BROKEN_BUSINESS_KIND_OCR_TEXT, "사업자등록증.png")
        fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}

        self.assertEqual(result.document_type, "business_registration_certificate")
        self.assertIn("건설업", fields["business_type"])
        self.assertIn("도매 및 소매업", fields["business_type"])
        self.assertIn("전기공사", fields["business_item"])
        self.assertIn("신재생에너지설비설치전문기업", fields["business_item"])
        self.assertIn("정보통신공사업", fields["business_item"])
        self.assertIn("컴퓨터 관련 주변기기", fields["business_item"])
        self.assertIn("업태:", fields["business_category"])
        self.assertIn("종목:", fields["business_category"])
        for label in ["사업의", "종류", "업태", "종목"]:
            self.assertNotIn(label, fields["business_type"])
            self.assertNotIn(label, fields["business_item"])

    def test_business_registration_rules_clean_inline_kind_labels(self) -> None:
        result = analyze_corporation_evidence(INLINE_LABEL_BUSINESS_KIND_OCR_TEXT, "사업자등록증.png")
        fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}

        self.assertIn("건설업", fields["business_type"])
        self.assertIn("도매 및 소매업", fields["business_type"])
        self.assertIn("전기공사", fields["business_item"])
        self.assertIn("신재생에너지설비설치전문기업", fields["business_item"])
        self.assertIn("컴퓨터 관련 주변기기", fields["business_item"])
        self.assertIn("산업안전용품", fields["business_item"])
        self.assertNotIn("사업자 단위 과세", fields["business_item"])

    def test_llm_business_kind_values_are_sanitized_before_display(self) -> None:
        business_types, business_items = normalize_business_kind_values(
            ["사업의 종류", "업태 건설업", "도매 및\n소매업"],
            [
                "종목 전기공사,신재생에너지설비설치전문기\n업",
                "건설업 정보통신공사업, 토목공사업",
            ],
        )

        self.assertEqual(business_types, ["건설업", "도매 및 소매업"])
        self.assertIn("전기공사", business_items)
        self.assertIn("신재생에너지설비설치전문기업", business_items)
        self.assertIn("정보통신공사업", business_items)
        self.assertIn("토목공사업", business_items)
        self.assertNotIn("종목", ", ".join(business_items))

    def test_unknown_evidence_requires_review(self) -> None:
        result = analyze_corporation_evidence("임의의 회사 소개서입니다.", "intro.pdf")

        self.assertEqual(result.document_type, "unknown")
        self.assertEqual(result.classification_status, "needs_review")
        self.assertEqual(result.candidates, [])

    def test_manual_business_registration_type_still_extracts_candidates(self) -> None:
        result = analyze_corporation_evidence(
            BUSINESS_REGISTRATION_TEXT,
            "unclear.pdf",
            requested_document_type="business_registration_certificate",
        )

        fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}
        self.assertEqual(result.classification_status, "manual")
        self.assertEqual(fields["business_registration_number"], "142-81-28387")

    def test_manual_core_evidence_with_empty_text_does_not_create_static_candidates(self) -> None:
        result = analyze_corporation_evidence(
            "",
            "중소기업확인서.pdf",
            requested_document_type="small_business_confirmation",
        )

        self.assertEqual(result.document_type, "small_business_confirmation")
        self.assertEqual(result.classification_status, "needs_review")
        self.assertEqual(result.candidates, [])
        self.assertTrue(result.warnings)

    def test_small_business_confirmation_extracts_size_and_tags(self) -> None:
        text = """
        중소기업확인서
        기업명 : 주식회사 온세이엔씨
        사업자등록번호 : 142-81-28387
        대표자 : 안영식
        기업규모 : 소기업
        유효기간 : 2026.01.01 ~ 2026.12.31
        """

        result = analyze_corporation_evidence(text, "중소기업확인서.pdf")
        fields = {candidate.field_key: candidate.extracted_value for candidate in result.candidates}

        self.assertEqual(result.document_type, "small_business_confirmation")
        self.assertEqual(fields["company_size_classification"], "소기업")
        self.assertIn("중소기업", json.loads(fields["preference_tags_json"]))
        self.assertIn("중소기업확인서", json.loads(fields["certifications_json"]))

    def test_preference_and_direct_production_documents_extract_profile_candidates(self) -> None:
        women = analyze_corporation_evidence("여성기업확인서\n업체명 : 주식회사 온세이엔씨\n확인번호 : W-1", "여성기업확인서.pdf")
        direct = analyze_corporation_evidence(
            "직접생산확인증명서\n기업명 : 주식회사 온세이엔씨\n세부품명 : 전산업무 개발, 시스템관리\n유효기간 : 2026.01.01 ~ 2026.12.31",
            "직접생산확인증명서.pdf",
        )

        women_fields = {candidate.field_key: candidate.extracted_value for candidate in women.candidates}
        direct_fields = {candidate.field_key: candidate.extracted_value for candidate in direct.candidates}

        self.assertEqual(women.document_type, "women_owned_business_confirmation")
        self.assertIn("여성기업", json.loads(women_fields["preference_tags_json"]))
        self.assertEqual(direct.document_type, "direct_production_confirmation")
        self.assertIn("전산업무 개발", json.loads(direct_fields["direct_production_items_json"]))

    def test_procurement_and_license_documents_extract_status_and_summary(self) -> None:
        procurement = analyze_corporation_evidence(
            "조달청 경쟁입찰참가자격등록증\n업체명 : 주식회사 온세이엔씨\n등록업종 : 전기공사업",
            "경쟁입찰참가자격등록증.pdf",
        )
        license_doc = analyze_corporation_evidence(
            "전기공사업 등록증\n상호 : 주식회사 온세이엔씨\n업종명 : 전기공사업",
            "전기공사업등록증.pdf",
        )

        procurement_fields = {candidate.field_key: candidate.extracted_value for candidate in procurement.candidates}
        license_fields = {candidate.field_key: candidate.extracted_value for candidate in license_doc.candidates}

        self.assertEqual(procurement.document_type, "procurement_registration_certificate")
        self.assertEqual(procurement_fields["procurement_registration_status"], "registered")
        self.assertIn("전기공사업", procurement_fields["license_summary"])
        self.assertEqual(license_doc.document_type, "license_registration_certificate")
        self.assertIn("전기공사업", license_fields["license_summary"])

    def test_credit_rating_and_payment_documents_extract_operational_candidates(self) -> None:
        credit = analyze_corporation_evidence(
            """
            기업신용평가등급확인서
            업체명 : 주식회사 온세이엔씨
            사업자등록번호 : 142-81-28387
            평가등급 : B+
            유효기간 : 2026.01.01 ~ 2026.12.31
            """,
            "기업신용평가등급확인서.pdf",
        )
        tax = analyze_corporation_evidence(
            """
            국세 납세증명서
            상호 : 주식회사 온세이엔씨
            사업자등록번호 : 142-81-28387
            체납액 없음
            유효기간 : 2026.05.31
            """,
            "국세납세증명서.pdf",
        )

        credit_fields = {candidate.field_key: candidate.extracted_value for candidate in credit.candidates}
        tax_fields = {candidate.field_key: candidate.extracted_value for candidate in tax.candidates}

        self.assertEqual(credit.document_type, "credit_rating_certificate")
        self.assertIn("기업신용평가등급 B+", json.loads(credit_fields["certifications_json"]))
        self.assertIn("B+", credit_fields["license_summary"])
        self.assertEqual(tax.document_type, "tax_payment_certificate")
        self.assertIn("체납 없음", tax_fields["license_summary"])

    def test_performance_and_financial_documents_extract_summary_candidates(self) -> None:
        performance = analyze_corporation_evidence(
            """
            실적증명서
            업체명 : 주식회사 온세이엔씨
            사업명 : 미세먼지 저감숲 조성사업
            계약금액 : 120,000,000원
            수행기간 : 2025.01.01 ~ 2025.12.31
            """,
            "실적증명서.pdf",
        )
        financial = analyze_corporation_evidence(
            """
            표준재무제표증명
            상호 : 주식회사 온세이엔씨
            사업자등록번호 : 142-81-28387
            사업연도 : 2025
            """,
            "표준재무제표증명.pdf",
        )

        performance_fields = {candidate.field_key: candidate.extracted_value for candidate in performance.candidates}
        financial_fields = {candidate.field_key: candidate.extracted_value for candidate in financial.candidates}

        self.assertEqual(performance.document_type, "performance_certificate")
        self.assertIn("미세먼지 저감숲", performance_fields["license_summary"])
        self.assertIn("120,000,000", performance_fields["license_summary"])
        self.assertEqual(financial.document_type, "financial_statement_certificate")
        self.assertIn("2025", financial_fields["license_summary"])


if __name__ == "__main__":
    unittest.main()
