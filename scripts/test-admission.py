#!/usr/bin/env python3
"""Behavior tests for the contribution/admission boundary; no external services."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
import admission

spec = importlib.util.spec_from_file_location("prepare", Path(__file__).with_name("prepare-contribution.py"))
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
ROOT = Path(__file__).resolve().parents[1]


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name).resolve()
        self.root = self.work / "source"
        self.root.mkdir()
        for name in admission.declarations(admission.parse_json((ROOT / admission.META).read_bytes())):
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)

    def tearDown(self):
        self.temp.cleanup()

    def metadata(self, edit):
        path = self.root / admission.META
        value = json.loads(path.read_text())
        edit(value)
        path.write_text(json.dumps(value))

    def packet(self):
        output = self.work / "packet"
        prepare.prepare(self.root, output)
        return output / "packet.zip"

    def mutate_zip(self, path, edit):
        with zipfile.ZipFile(path) as archive:
            contents = {name: archive.read(name) for name in archive.namelist()}
        edit(contents)
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in contents.items():
                archive.writestr(name, data)

    def test_positive_cli_roundtrip_and_no_environment_leak(self):
        (self.root / ".env").write_text("private-token=do-not-export")
        output = self.work / "generated"
        result = subprocess.run([sys.executable, str(ROOT / "scripts/prepare-contribution.py"), "--root", str(self.root), "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = subprocess.run([sys.executable, str(ROOT / "scripts/admission.py"), "validate", "--packet", str(output / "packet.zip")], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        report = json.loads(checked.stdout)
        self.assertEqual(report["status"], "checked")
        self.assertFalse(report["communityReviewed"])
        self.assertFalse(report["publishAllowed"])
        with zipfile.ZipFile(output / "packet.zip") as archive:
            self.assertNotIn(".env", archive.namelist())
        self.assertEqual(report["sourceDigest"], admission.inspect(self.root)["sourceDigest"])

    def test_missing_docs(self):
        (self.root / "docs/HealthBar.md").unlink()
        with self.assertRaises(admission.AdmissionError):
            self.packet()

    def test_missing_or_duplicate_reuse(self):
        self.metadata(lambda m: m["components"][0].update(examples=m["components"][0]["examples"][:1]))
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_identical_examples_not_reuse(self):
        shutil.copyfile(self.root / "examples/adventure/Main.java", self.root / "examples/study/Main.java")
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_stale_check_report(self):
        report = {"schema": 1, "sourceDigest": admission.inspect(self.root)["sourceDigest"], "checks": [], "provenance": {"generator": "fixture"}}
        receipt = self.work / "receipt.json"
        receipt.write_text(json.dumps(report))
        with (self.root / "src/main/java/zero/community/HealthBar.java").open("a") as source:
            source.write("\n// changed after checks\n")
        with self.assertRaises(admission.AdmissionError):
            prepare.prepare(self.root, self.work / "stale", receipt)

    def test_failed_declared_check_blocks_checked_status(self):
        source = admission.inspect(self.root)
        receipt = self.work / "failed-checks.json"
        receipt.write_text(json.dumps({"schema": 1, "sourceDigest": source["sourceDigest"], "checks": [{"id": "fractional-fill", "status": "failed", "evidence": "Observed 0 rather than 0.875"}], "provenance": {"generator": "fixture"}}))
        output = self.work / "failed-packet"
        prepare.prepare(self.root, output, receipt)
        report = admission.validate_packet(output / "packet.zip")
        self.assertEqual(report["status"], "changes-required")
        self.assertFalse(admission.acceptance_model(report, {})["communityReviewed"])
        result = subprocess.run([sys.executable, str(ROOT / "scripts/admission.py"), "validate", "--packet", str(output / "packet.zip")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "changes-required")

    def test_symlink_owned_file(self):
        path = self.root / "docs/HealthBar.md"
        path.unlink()
        path.symlink_to(ROOT / "docs/HealthBar.md")
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_symlink_output_parent(self):
        alias = self.work / "alias"
        alias.symlink_to(self.work, target_is_directory=True)
        with self.assertRaises(admission.AdmissionError):
            prepare.prepare(self.root, alias / "packet")

    def test_overwrite_refused_and_original_retained(self):
        packet = self.packet()
        original = packet.read_bytes()
        with self.assertRaises(admission.AdmissionError):
            prepare.prepare(self.root, packet.parent)
        self.assertEqual(original, packet.read_bytes())

    def test_path_traversal_zip(self):
        packet = self.packet()
        self.mutate_zip(packet, lambda c: c.update({"../escape.txt": b"x"}))
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)

    def test_non_owned_zip_file(self):
        packet = self.packet()
        self.mutate_zip(packet, lambda c: c.update({"src/main/java/student/Private.java": b"x"}))
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)

    def test_metadata_cannot_declare_outside_owned_source(self):
        self.metadata(lambda m: m["components"][0]["examples"][0].update(path="../private.java"))
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_authored_review_status_cannot_self_promote(self):
        self.metadata(lambda m: m["components"][0].update(status="community-reviewed", license="MIT", maintainer="maintainer"))
        report = admission.validate_packet(self.packet())
        self.assertFalse(report["communityReviewed"])
        forged = admission.acceptance_model(report, {"maintainers": ["maintainer"], "reviewers": ["contributor"], "independentApprovals": [{"reviewer": "contributor", "author": "contributor", "decision": "approve", "kind": "human-community-review", "sourceDigest": report["sourceDigest"]}]})
        self.assertFalse(forged["communityReviewed"])
        self.assertFalse(forged["publishAllowed"])

    def test_trusted_policy_local_model_source_binding(self):
        self.metadata(lambda m: m["components"][0].update(license="MIT", maintainer="maintainer"))
        report = admission.validate_packet(self.packet())
        policy = {"maintainers": ["maintainer"], "reviewers": ["reviewer"], "checkRunners": ["trusted-runner"], "verifiedChecks": [{"runner": "trusted-runner", "sourceDigest": report["sourceDigest"], "passedChecks": ["build", "behavior", "reuse", "compatibility"]}], "independentApprovals": [{"reviewer": "reviewer", "author": "contributor", "decision": "approve", "kind": "human-community-review", "sourceDigest": report["sourceDigest"]}]}
        modeled = admission.acceptance_model(report, policy)
        self.assertTrue(modeled["communityReviewed"])
        self.assertFalse(modeled["publishAllowed"])
        policy["independentApprovals"][0]["sourceDigest"] = "0" * 64
        self.assertFalse(admission.acceptance_model(report, policy)["communityReviewed"])

    def test_no_license_or_maintainer_never_accepted(self):
        report = admission.validate_packet(self.packet())
        self.assertFalse(admission.acceptance_model(report, {})["communityReviewed"])

    def test_ai_response_has_no_acceptance_authority(self):
        source = admission.inspect(self.root)
        response = {"schema": 1, "sourceDigest": source["sourceDigest"], "advisory": True, "findings": []}
        self.assertEqual(admission.validate_ai(response, source)["acceptanceEffect"], "none")
        response["approve"] = True
        with self.assertRaises(admission.AdmissionError):
            admission.validate_ai(response, source)

    def test_ai_stale_digest_and_budget_rejected(self):
        source = admission.inspect(self.root)
        response = {"schema": 1, "sourceDigest": "0" * 64, "advisory": True, "findings": []}
        with self.assertRaises(admission.AdmissionError):
            admission.validate_ai(response, source)
        response["sourceDigest"] = source["sourceDigest"]
        response["findings"] = [{"path": "pom.xml", "severity": "warning", "message": "x"}] * 13
        with self.assertRaises(admission.AdmissionError):
            admission.validate_ai(response, source)

    def test_candidate_receipt_is_bound_but_never_authority(self):
        source = admission.inspect(self.root)
        receipt = {"schema": 1, "sourceDigest": source["sourceDigest"], "checks": [{"id": "fractional-fill", "status": "passed", "evidence": "candidate rebuilt locally"}], "provenance": {"generator": "fixture", "testedArtifact": {"version": "0.1.1", "sha256": "f" * 64, "sourceBinding": "built-local-candidate", "kind": "candidate-class", "sourceDigest": source["sourceDigest"]}}}
        self.assertEqual(admission.validate_receipt(receipt, source["sourceDigest"]), receipt)
        receipt["provenance"]["testedArtifact"]["sourceDigest"] = "0" * 64
        with self.assertRaises(admission.AdmissionError):
            admission.validate_receipt(receipt, source["sourceDigest"])

    def test_duplicate_zip_and_changed_bytes_refused(self):
        packet = self.packet()
        self.mutate_zip(packet, lambda c: c.update({"pom.xml": c["pom.xml"] + b"\n"}))
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)
        packet.unlink()
        shutil.rmtree(packet.parent)
        packet = self.packet()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(packet, "a") as archive:
                archive.writestr("packet.json", "{}")
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)


if __name__ == "__main__":
    unittest.main(verbosity=2)
