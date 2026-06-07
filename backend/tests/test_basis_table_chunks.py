import unittest

from app.pipelines.basis_document import (
    basis_page_ranges,
    basis_search_score,
    page_for_offset,
    split_basis_tables_into_row_chunks,
)
from app.services.basis_rule_candidates import basis_rule_candidate_match_score


class BasisTableChunkTests(unittest.TestCase):
    def test_split_basis_tables_into_row_chunks_preserves_table_metadata(self) -> None:
        chunks = split_basis_tables_into_row_chunks(
            {
                "engine": "opendataloader-pdf",
                "tables": [
                    {
                        "table_id": "p120-t2",
                        "source_engine": "opendataloader-pdf",
                        "page_number": 120,
                        "bbox": [41.8, 66.9, 380.7, 424.6],
                        "headers": ["항목", "내용", "비고"],
                        "rows": [
                            {"row_index": 1, "cells": ["항목", "내용", "비고"]},
                            {
                                "row_index": 2,
                                "cells": ["생산시설", "절단기 천공기 용접기", "임차보유 인정하지 않음"],
                                "bbox": [10, 20, 30, 40],
                            },
                        ],
                    }
                ],
            },
            start_index=5,
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_index"], 5)
        self.assertEqual(chunks[0]["page_start"], 120)
        self.assertIn("생산시설", chunks[0]["chunk_text"])
        self.assertIn("절단기", chunks[0]["chunk_text"])
        self.assertEqual(chunks[0]["metadata"]["chunk_type"], "table_row")
        self.assertEqual(chunks[0]["metadata"]["table_id"], "p120-t2")
        self.assertEqual(chunks[0]["metadata"]["row_index"], 2)
        self.assertEqual(chunks[0]["metadata"]["column_headers"], ["항목", "내용", "비고"])

    def test_table_row_chunks_do_not_shift_columns_when_header_is_blank(self) -> None:
        chunks = split_basis_tables_into_row_chunks(
            {
                "engine": "opendataloader-pdf",
                "tables": [
                    {
                        "table_id": "p10-t1",
                        "page_number": 10,
                        "headers": ["", "세부품명", "직접생산 기준"],
                        "rows": [
                            {"cells": ["", "세부품명", "직접생산 기준"]},
                            {"cells": ["1", "도로표지판", "절단기와 용접기를 보유"]},
                        ],
                    }
                ],
            }
        )

        self.assertEqual(chunks[0]["metadata"]["column_headers"], ["", "세부품명", "직접생산 기준"])
        self.assertIn("col_1: 1", chunks[0]["chunk_text"])
        self.assertIn("세부품명: 도로표지판", chunks[0]["chunk_text"])
        self.assertIn("직접생산 기준: 절단기와 용접기를 보유", chunks[0]["chunk_text"])
        self.assertEqual(chunks[0]["metadata"]["row_index"], 2)

    def test_basis_page_ranges_use_explicit_offsets_from_pdf_reader(self) -> None:
        text = "first page\n\nsecond page"
        ranges = basis_page_ranges(
            {
                "pages": [
                    {"page_number": 1, "char_count": 10, "char_start": 0, "char_end": 10},
                    {"page_number": 2, "char_count": 11, "char_start": 12, "char_end": len(text)},
                ]
            },
            text,
        )

        self.assertEqual(page_for_offset(ranges, text.index("second")), 2)

    def test_basis_search_score_counts_unique_query_tokens_not_repetition(self) -> None:
        query_tokens = {"direct", "production", "certificate"}

        repeated_one_token = {"direct": 12}
        balanced_match = {"direct": 1, "production": 1}

        self.assertLess(basis_search_score(query_tokens, repeated_one_token), basis_search_score(query_tokens, balanced_match))
        self.assertLessEqual(basis_search_score(query_tokens, repeated_one_token), 1)

    def test_rule_candidate_score_does_not_reward_repeated_single_token(self) -> None:
        requirement = {
            "required_value": "direct production certificate",
            "source_text": "",
            "required_evidence_types": [],
            "requirement_type": "required_document",
        }
        repeated_candidate = {
            "condition_text": "direct direct direct direct direct direct direct",
            "target_scope": "",
            "required_evidence_types": [],
            "related_profile_fields": [],
            "rule_type": "basis_rule",
            "confidence": 0,
        }
        balanced_candidate = {
            "condition_text": "direct production certificate",
            "target_scope": "",
            "required_evidence_types": [],
            "related_profile_fields": [],
            "rule_type": "basis_rule",
            "confidence": 0,
        }

        self.assertLess(
            basis_rule_candidate_match_score(requirement, repeated_candidate),
            basis_rule_candidate_match_score(requirement, balanced_candidate),
        )


if __name__ == "__main__":
    unittest.main()
