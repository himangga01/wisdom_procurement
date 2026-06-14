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

    def test_extended_evidence_document_types_are_classified_separately(self) -> None:
        cases = [
            ("G-PASS기업 지정서\n기업명 : 테스트 법인", "G-PASS기업 지정서.pdf", "gpass_company_certificate"),
            ("ISO9001 인증서\n인증범위 : 소프트웨어 개발", "ISO9001 인증서.pdf", "iso_quality_certificate"),
            ("벤처기업확인서\n기업명 : 테스트 법인", "벤처기업확인서.pdf", "venture_business_confirmation"),
            ("Inno-Biz 확인서\n등급 : A", "Inno-Biz 확인서.pdf", "innobiz_confirmation"),
            ("기술혁신형 중소기업 확인서\n확인번호 : INNO-1", "기술혁신형 중소기업 확인서.pdf", "innobiz_confirmation"),
            ("공장등록증명서\n공장소재지 : 경기도 성남시", "공장등록증명서.pdf", "factory_registration_certificate"),
            ("기업부설연구소 인정서\n연구소명 : 테스트 연구소", "기업부설연구소 인정서.pdf", "research_institute_certificate"),
            ("소프트웨어사업자확인서\n사업분야 : 컴퓨터 관련 서비스", "소프트웨어사업자확인서.pdf", "software_business_certificate"),
            ("소프트웨어사업자일반현황관리확인서\n사업분야 : 컴퓨터 관련 서비스", "소프트웨어사업자일반현황관리확인서.pdf", "software_business_certificate"),
            ("소프트웨어품질인증서\n제품명 : 조달 분석 시스템", "GS인증서.pdf", "software_quality_certificate"),
            ("녹색기술인증서\n기술명 : 저전력 제어 기술", "녹색기술인증서.pdf", "green_technology_certificate"),
            ("녹색기술제품확인서\n제품명 : 친환경 제어기", "녹색기술제품확인서.pdf", "green_product_confirmation"),
            ("우수제품지정증서\n제품명 : 스마트 조달 단말", "우수제품지정증서.pdf", "excellent_product_certificate"),
            ("특허증\n발명의 명칭 : 스마트 조달 분석 장치", "특허증.pdf", "patent_certificate"),
            ("저작권등록증\n저작물의 명칭 : 조달 분석 프로그램", "저작권등록증.pdf", "copyright_registration_certificate"),
            ("옥외광고사업 등록증\n업종 : 옥외광고업", "옥외광고사업 등록증.pdf", "outdoor_advertising_business_registration"),
            ("통신판매업신고증\n판매방식 : 인터넷", "통신판매업신고증.pdf", "online_sales_business_registration"),
            ("조합원증\n조합원명 : 테스트 법인", "조합원증.pdf", "industry_association_membership"),
            ("출자증권\n출자좌수 : 10좌", "출자증권.pdf", "investment_share_certificate"),
            ("고용안정장려금 승인서\n사업명 : 고용지원", "고용안정장려금 승인서.pdf", "employment_support_approval"),
            ("책임보험가입증명서\n보험종목 : 영업배상책임보험", "책임보험가입증명서.pdf", "insurance_policy_certificate"),
            ("건강기능식품영업신고증\n업종 : 특수 영업", "특수 영업 신고증.pdf", "special_business_license"),
            ("기술등급확인서\n기술등급 : T-2", "기술등급확인서.pdf", "technology_grade_confirmation"),
            ("기술평가우수기업인증서\n기술명칭 : 전자칠판 제조 기술", "기술평가우수기업인증서.pdf", "technology_evaluation_excellent_certificate"),
        ]

        for text, file_name, expected_type in cases:
            with self.subTest(expected_type=expected_type):
                result = analyze_corporation_evidence(text, file_name)
                self.assertEqual(result.document_type, expected_type)
                self.assertEqual(result.classification_status, "classified")
                self.assertTrue(result.candidates)

    def test_extended_evidence_candidates_map_to_review_safe_profile_fields(self) -> None:
        patent = analyze_corporation_evidence(
            "특허증\n발명의 명칭 : 스마트 조달 분석 장치\n등록번호 : 10-1234567",
            "특허증.pdf",
        )
        green = analyze_corporation_evidence(
            "녹색기술인증서\n기술명 : 저전력 제어 기술\n인증번호 : GT-1",
            "녹색기술인증서.pdf",
        )
        factory = analyze_corporation_evidence(
            "공장등록증명서\n공장소재지 : 경기도 성남시\n업종 : 전기장비 제조",
            "공장등록증명서.pdf",
        )
        gpass = analyze_corporation_evidence(
            "G-PASS기업 지정서\n지정번호 : GP-1\n기업명 : 테스트 법인",
            "G-PASS기업 지정서.pdf",
        )
        association = analyze_corporation_evidence(
            "조합원증\n조합원명 : 테스트 법인\n가입일 : 2026.01.01",
            "조합원증.pdf",
        )
        software_business = analyze_corporation_evidence(
            "소프트웨어사업자일반현황관리확인서\n신고번호 : SW-1\n사업분야 : 컴퓨터 관련 서비스",
            "소프트웨어사업자일반현황관리확인서.pdf",
        )
        software_business_without_field = analyze_corporation_evidence(
            "소프트웨어사업자일반현황관리확인서\n신고번호 : SW-2\n기업명 : 테스트 법인",
            "소프트웨어사업자일반현황관리확인서.pdf",
        )

        patent_fields = {candidate.field_key: candidate.extracted_value for candidate in patent.candidates}
        green_fields = {candidate.field_key: candidate.extracted_value for candidate in green.candidates}
        factory_fields = {candidate.field_key: candidate.extracted_value for candidate in factory.candidates}
        gpass_fields = {candidate.field_key: candidate.extracted_value for candidate in gpass.candidates}
        association_fields = {candidate.field_key: candidate.extracted_value for candidate in association.candidates}
        software_business_fields = {candidate.field_key: candidate.extracted_value for candidate in software_business.candidates}
        software_business_without_field_fields = {
            candidate.field_key: candidate.extracted_value for candidate in software_business_without_field.candidates
        }

        self.assertIn("특허증", json.loads(patent_fields["certifications_json"]))
        self.assertIn("스마트 조달 분석 장치", patent_fields["license_summary"])
        self.assertEqual(patent_fields["business_item"], "스마트 조달 분석 장치")
        self.assertIn("녹색기술", json.loads(green_fields["preference_tags_json"]))
        self.assertIn("저전력 제어 기술", green_fields["license_summary"])
        self.assertIn("공장등록증명서", json.loads(factory_fields["certifications_json"]))
        self.assertIn("경기도 성남시", factory_fields["license_summary"])
        self.assertNotIn("business_item", factory_fields)
        self.assertIn("GP-1", gpass_fields["license_summary"])
        self.assertNotIn("business_item", gpass_fields)
        self.assertIn("테스트 법인", association_fields["license_summary"])
        self.assertNotIn("business_item", association_fields)
        self.assertEqual(software_business_fields["business_item"], "컴퓨터 관련 서비스")
        self.assertIn("소프트웨어사업자확인서", software_business_without_field_fields["license_summary"])
        self.assertNotIn("business_item", software_business_without_field_fields)

    def test_demo_pdf_specific_document_type_precedence(self) -> None:
        direct_production = analyze_corporation_evidence(
            """
            직접생산확인증명서
            세부품명 : 동영상제작서비스
            중소기업제품 구매촉진 및 판로지원에 관한 법률
            """,
            "20250226_(주)벡트_직생(동영상제작).pdf",
        )
        credit_rating = analyze_corporation_evidence(
            """
            기업신용평가등급 확인서
            조달청 및 공공기관 제출용
            본 기업신용평가등급은 중소기업 심사용으로 활용됩니다.
            """,
            "기업신용평가등급확인서_벡트.pdf",
        )
        insurance_policy = analyze_corporation_evidence(
            """
            책임보험가입증명서
            옥외광고업책임보험
            옥외광고사업 신규등록 처리사항
            """,
            "옥외광고업책임보험가입증명서.pdf",
        )
        investment_share = analyze_corporation_evidence(
            """
            출자증권
            한국전자산업협동조합
            출자좌수 : 10좌
            """,
            "출자증권_한국전자산업협동조합.pdf",
        )

        self.assertEqual(direct_production.document_type, "direct_production_confirmation")
        self.assertEqual(credit_rating.document_type, "credit_rating_certificate")
        self.assertEqual(insurance_policy.document_type, "insurance_policy_certificate")
        self.assertEqual(investment_share.document_type, "investment_share_certificate")


if __name__ == "__main__":
    unittest.main()
