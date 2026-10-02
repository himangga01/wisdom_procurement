import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

try:
    from app.pipelines.hwp_engine import HwpEngine, HwpEngineError
except ImportError:
    HwpEngine = None
    HwpEngineError = RuntimeError


FAKE_CLI = r'''
import json, pathlib, sys, time
mode, args = sys.argv[1], sys.argv[2:]
if args == ["--version"]:
    print("rhwp v0.8.6"); sys.exit(0)
if mode == "timeout": time.sleep(5)
if mode == "failure": print("private document content", file=sys.stderr); sys.exit(1)
if args[0] == "export-text":
    if mode == "malformed": print("not JSON"); sys.exit(0)
    payload = {"schemaVersion":"1.0","source":args[1],"pageCount":2,
        "truncated": mode == "truncated", "omittedCount": 12 if mode == "truncated" else 0,
        "pages":[{"page":0,"text":"입찰참가자격: 사업자등록증"},
                 {"page":1,"text":"제출기한: 2026-10-15"}]}
    if mode == "empty": payload["pages"] = [{"page":0,"text":""}]; payload["pageCount"]=1
    if mode == "wrong_schema": payload["schemaVersion"]="9.0"
    if mode == "text_changed" and pathlib.Path(args[1]).stem == "output":
        payload["pages"][0]["text"]="입찰참가자격: 변경된 내용"
    data = pathlib.Path(args[1]).read_bytes()
    if b"\nFAKE_EDIT=" in data:
        edit = json.loads(data.split(b"\nFAKE_EDIT=",1)[1].decode("utf-8"))
        payload["pages"][0]["text"] = payload["pages"][0]["text"].replace(edit["find"],edit["replace"])
        if mode == "edit_corrupted": payload["pages"][0]["text"] += " 관련 없는 변조"
    print(json.dumps(payload, ensure_ascii=False)); sys.exit(0)
if args[:2] == ["edit","replace-text"]:
    out = pathlib.Path(args[args.index("-o")+1])
    edit = {"find":args[args.index("--find")+1],"replace":args[args.index("--replace")+1]}
    if mode != "no_match": out.write_bytes(pathlib.Path(args[2]).read_bytes()+b"\nFAKE_EDIT="+json.dumps(edit).encode("utf-8"))
    print(json.dumps({"schemaVersion":"1.0","source":args[2],"find":"x","replace":"y",
        "caseSensitive":True,"dryRun":False,"replacedCount":0 if mode=="no_match" else 1,
        "output":str(out),"outputFormat":"hwp5"})); sys.exit(0)
if args[0] == "convert":
    pathlib.Path(args[2]).write_bytes(pathlib.Path(args[1]).read_bytes()); sys.exit(0)
raise SystemExit(2)
'''


class HwpEngineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(HwpEngine, "The service needs a real RHWP read/write adapter")
        self.tmp = tempfile.TemporaryDirectory(prefix="wisdom-hwp-unit-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "입찰 양식.hwp"
        self.source.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"synthetic fixture")
        self.cli = self.root / "fake_cli.py"
        self.cli.write_text(FAKE_CLI, encoding="utf-8")

    def engine(self, mode="normal", timeout=10):
        return HwpEngine(command=[sys.executable, str(self.cli), mode], timeout_seconds=timeout)

    def test_read_preserves_page_order_and_korean_text(self):
        result = self.engine().read(self.source)
        self.assertEqual(result.text, "입찰참가자격: 사업자등록증\n\n제출기한: 2026-10-15")
        self.assertEqual(result.metadata["page_count"], 2)
        self.assertEqual([p["page_number"] for p in result.metadata["pages"]], [1, 2])
        self.assertFalse(result.metadata["needs_ocr"])

    def test_write_preserves_original_and_produces_a_distinct_file(self):
        before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        output = self.root / "result.hwp"
        result = self.engine().write(self.source, output, find="사업자등록증", replace="법인등기부등본")
        self.assertEqual(result.replaced_count, 1)
        self.assertTrue(output.exists())
        self.assertNotEqual(output.read_bytes(), self.source.read_bytes())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), before)

    def test_same_source_destination_is_rejected(self):
        with self.assertRaises(HwpEngineError):
            self.engine().write(self.source, self.source)
        self.assertTrue(self.source.exists())

    def test_existing_destination_is_not_overwritten(self):
        output = self.root / "existing.hwp"
        output.write_bytes(b"keep this file")
        with self.assertRaises(HwpEngineError):
            self.engine().write(self.source, output)
        self.assertEqual(output.read_bytes(), b"keep this file")

    def test_invalid_signature_is_rejected_before_processing(self):
        self.source.write_bytes(b"this is not HWP")
        with self.assertRaises(HwpEngineError):
            self.engine().read(self.source)

    def test_truncated_and_empty_extraction_are_not_successes(self):
        for mode in ("truncated", "empty", "wrong_schema", "malformed"):
            with self.subTest(mode=mode), self.assertRaises(HwpEngineError):
                self.engine(mode).read(self.source)

    def test_timeout_is_bounded_and_does_not_change_source(self):
        before = self.source.read_bytes()
        with self.assertRaises(HwpEngineError) as caught:
            self.engine("timeout", timeout=0.05).read(self.source)
        self.assertEqual(caught.exception.code, "hwp_timeout")
        self.assertEqual(self.source.read_bytes(), before)

    def test_cli_failure_does_not_expose_document_content(self):
        with self.assertRaises(HwpEngineError) as caught:
            self.engine("failure").read(self.source)
        self.assertNotIn("private document content", str(caught.exception))

    def test_no_match_does_not_create_or_claim_an_edited_output(self):
        output = self.root / "absent.hwp"
        with self.assertRaises(HwpEngineError) as caught:
            self.engine("no_match").write(self.source, output, find="x", replace="y")
        self.assertEqual(caught.exception.code, "hwp_no_matches")
        self.assertFalse(output.exists())

    def test_serializer_text_changes_are_rejected_before_output_publication(self):
        output = self.root / "should-not-exist.hwp"
        before = self.source.read_bytes()
        with self.assertRaises(HwpEngineError) as caught:
            self.engine("text_changed").write(self.source, output)
        self.assertEqual(caught.exception.code, "hwp_text_verification_failed")
        self.assertFalse(output.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_edit_serializer_unrelated_changes_are_not_trusted_as_baseline(self):
        output = self.root / "corrupted-edit.hwp"
        with self.assertRaises(HwpEngineError) as caught:
            self.engine("edit_corrupted").write(self.source, output, find="사업자등록증", replace="법인등기부등본")
        self.assertEqual(caught.exception.code, "hwp_edit_verification_failed")
        self.assertFalse(output.exists())

    def test_missing_engine_reports_setup_required(self):
        engine = HwpEngine(command=[str(self.root / "missing-rhwp.exe")])
        self.assertFalse(engine.status()["available"])
        with self.assertRaises(HwpEngineError) as caught:
            engine.read(self.source)
        self.assertEqual(caught.exception.code, "needs_hwp_setup")


class HwpNativeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(HwpEngine)
        self.source = Path(__file__).parent / "fixtures" / "hwp" / "synthetic.hwp"
        self.engine = HwpEngine()
        if not self.engine.status()["available"]:
            self.skipTest("Install the pinned RHWP CLI for native round-trip checks")

    def test_native_delete_all_text_can_export_without_claiming_analysis_text(self):
        original = self.source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "cleared.hwp"
            try:
                self.engine.write(self.source, output, find=self.engine.read(self.source).text, replace="")
            except HwpEngineError as exc:
                self.fail(f"Valid empty-body export must be allowed: {exc.code}")
            self.assertTrue(output.is_file())
            with self.assertRaises(HwpEngineError) as caught:
                self.engine.read(output)
            self.assertEqual(caught.exception.code, "hwp_insufficient_text")
        self.assertEqual(self.source.read_bytes(), original)

    def test_native_hwp_to_hwpx_to_hwp_preserves_text_and_original(self):
        original = self.source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            hwpx = Path(tmp) / "converted.hwpx"
            hwp = Path(tmp) / "converted.hwp"
            self.engine.write(self.source, hwpx)
            self.engine.write(hwpx, hwp)
            for path in (self.source, hwpx, hwp):
                text = self.engine.read(path).text
                self.assertIn("입찰참가자격: 사업자등록증", text)
                self.assertIn("RHWP_TEST_ORIGINAL", text)
        self.assertEqual(self.source.read_bytes(), original)

    def test_native_replace_changes_saved_text_without_mutating_original(self):
        original = self.source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "changed.hwpx"
            result = self.engine.write(self.source, output, find="RHWP_TEST_ORIGINAL", replace="변경된_검증_문자열")
            self.assertEqual(result.replaced_count, 1)
            text = self.engine.read(output).text
            self.assertIn("변경된_검증_문자열", text)
            self.assertNotIn("RHWP_TEST_ORIGINAL", text)
        self.assertEqual(self.source.read_bytes(), original)

    def test_common_parser_recognizes_both_hangul_formats(self):
        from app.pipelines.parser import extract_document
        for suffix in ("hwp", "hwpx"):
            with self.subTest(suffix=suffix):
                try:
                    parsed = extract_document(self.source.with_suffix("." + suffix))
                except ValueError as exc:
                    self.fail(f"Common parser must accept {suffix}: {exc}")
                self.assertEqual(parsed.kind, suffix)
                self.assertEqual(parsed.metadata["engine"], "rhwp")
                self.assertIn("입찰참가자격: 사업자등록증", parsed.text)

    def test_short_native_hwp_text_does_not_run_image_ocr(self):
        from app.pipelines.ocr import run_ocr_if_needed
        result = run_ocr_if_needed("짧은 한글", self.source, "hwp", {"engine": "rhwp", "needs_ocr": False})
        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.text, "짧은 한글")


if __name__ == "__main__":
    unittest.main()
