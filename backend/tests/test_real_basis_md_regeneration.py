from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import fitz


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "scripts" / "regenerate-real-basis-document-md.py"


def load_regeneration_module():
    spec = importlib.util.spec_from_file_location("real_basis_md_regeneration", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load regeneration script: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RealBasisMdRegenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.regen = load_regeneration_module()

    def test_table_to_markdown_escapes_cells_and_preserves_rows(self) -> None:
        markdown = self.regen.table_to_markdown(
            [
                ["세부품명", "생산시설"],
                ["검사|설비", "1\n2"],
            ]
        )

        self.assertIn("| 세부품명 | 생산시설 |", markdown)
        self.assertIn("| 검사\\|설비 | 1<br>2 |", markdown)
        self.assertEqual(len(self.regen.markdown_table_rows(markdown)), 2)

    def test_logical_page_regions_split_after_first_page(self) -> None:
        doc = fitz.open()
        try:
            page = doc.new_page(width=842, height=594)
            first_regions = self.regen.logical_page_regions(page, 1)
            second_regions = self.regen.logical_page_regions(page, 2)
        finally:
            doc.close()

        self.assertEqual(len(first_regions), 1)
        self.assertEqual(first_regions[0]["area"], "전체")
        self.assertEqual(len(second_regions), 2)
        self.assertEqual([region["area"] for region in second_regions], ["좌측", "우측"])

    def test_markdown_table_count_detects_separator_lines(self) -> None:
        markdown = """
| A | B |
| --- | --- |
| 1 | 2 |

not a table

| C | D |
| --- | --- |
| 3 | 4 |
"""
        self.assertEqual(self.regen.markdown_table_count(markdown), 2)
        self.assertEqual(len(self.regen.markdown_table_rows(markdown)), 4)


if __name__ == "__main__":
    unittest.main()

