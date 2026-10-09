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
from unittest.mock import patch
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

    def pom_insert(self, xml):
        path = self.root / "pom.xml"
        path.write_text(path.read_text().replace("</project>", xml + "</project>"))

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

    def test_mit_packet_preserves_canonical_license_and_hash(self):
        source = admission.inspect(self.root)
        expected = (ROOT / "LICENSE").read_bytes()
        self.assertEqual(len(source["files"]), 8)
        self.assertIn({"path": "LICENSE", "sha256": admission.digest(expected)}, source["files"])
        with zipfile.ZipFile(self.packet()) as archive:
            self.assertEqual(archive.read("LICENSE"), expected)
        self.assertEqual(admission.validate_packet(self.work / "packet/packet.zip")["sourceDigest"], source["sourceDigest"])

    def test_mit_missing_license_rejected(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_mit_missing_packet_license_rejected(self):
        packet = self.packet()
        self.mutate_zip(packet, lambda c: c.pop("LICENSE"))
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)

    def test_mit_license_symlink_rejected(self):
        path = self.root / "LICENSE"
        path.unlink()
        path.symlink_to(ROOT / "LICENSE")
        with self.assertRaises(admission.AdmissionError):
            admission.inspect(self.root)

    def test_mit_license_drift_rejected(self):
        source = admission.inspect(self.root)
        receipt = self.work / "license-receipt.json"
        receipt.write_text(json.dumps({"schema": 1, "sourceDigest": source["sourceDigest"], "checks": [], "provenance": {"generator": "fixture"}}))
        packet = self.packet()
        self.mutate_zip(packet, lambda c: c.update({"LICENSE": c["LICENSE"] + b"\nchanged notice\n"}))
        with self.assertRaises(admission.AdmissionError):
            admission.validate_packet(packet)
        path = self.root / "LICENSE"
        path.write_bytes(path.read_bytes() + b"\nchanged notice\n")
        self.assertNotEqual(admission.inspect(self.root)["sourceDigest"], source["sourceDigest"])
        with self.assertRaises(admission.AdmissionError):
            prepare.prepare(self.root, self.work / "stale-license", receipt)

    def test_historical_unlicensed_seven_file_packet_validates(self):
        self.metadata(lambda m: m["components"][0].update(license="UNLICENSED"))
        (self.root / "LICENSE").unlink()
        source = admission.inspect(self.root)
        self.assertEqual(len(source["files"]), 7)
        packet = self.packet()
        with zipfile.ZipFile(packet) as archive:
            self.assertNotIn("LICENSE", archive.namelist())
        self.assertEqual(admission.validate_packet(packet)["status"], "checked")

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

    def test_mit_without_maintainer_never_accepted(self):
        report = admission.validate_packet(self.packet())
        self.assertEqual(report["metadata"]["components"][0]["license"], "MIT")
        self.assertNotIn("Owner-approved reuse licensing required", report["publishBlockers"])
        modeled = admission.acceptance_model(report, {})
        self.assertNotIn("Owner-approved reuse licensing required", modeled["blockers"])
        self.assertIn("Appointed component maintainer required", modeled["blockers"])
        self.assertFalse(modeled["communityReviewed"])
        self.assertFalse(modeled["publishAllowed"])

    def test_unlicensed_with_trusted_review_never_accepted(self):
        self.metadata(lambda m: m["components"][0].update(license="UNLICENSED", maintainer="maintainer"))
        report = admission.validate_packet(self.packet())
        policy = {"maintainers": ["maintainer"], "reviewers": ["reviewer"], "checkRunners": ["trusted-runner"], "verifiedChecks": [{"runner": "trusted-runner", "sourceDigest": report["sourceDigest"], "passedChecks": ["build", "behavior", "reuse", "compatibility"]}], "independentApprovals": [{"reviewer": "reviewer", "author": "contributor", "decision": "approve", "kind": "human-community-review", "sourceDigest": report["sourceDigest"]}]}
        modeled = admission.acceptance_model(report, policy)
        self.assertEqual(modeled["blockers"], ["Owner-approved reuse licensing required"])
        self.assertIn("Owner-approved reuse licensing required", report["publishBlockers"])
        self.assertFalse(modeled["communityReviewed"])
        self.assertFalse(modeled["publishAllowed"])

    def test_ai_response_has_no_acceptance_authority(self):
        source = admission.inspect(self.root)
        response = {"schema": 1, "sourceDigest": source["sourceDigest"], "advisory": True, "findings": []}
        self.assertEqual(admission.validate_ai(response, source)["acceptanceEffect"], "none")
        response["approve"] = True
        with self.assertRaises(admission.AdmissionError):
            admission.validate_ai(response, source)

    def test_unsupported_maven_profiles_rejected_without_activation(self):
        original = (self.root / "pom.xml").read_text()
        for active in ("true", "false"):
            with self.subTest(activeByDefault=active):
                (self.root / "pom.xml").write_text(original)
                self.pom_insert('<profiles><profile><id>tools</id><activation><activeByDefault>' + active + '</activeByDefault></activation><dependencies><dependency><groupId>example</groupId><artifactId>tool</artifactId><version>LATEST</version></dependency></dependencies><build><plugins><plugin><artifactId>tool-plugin</artifactId><version>RELEASE</version></plugin></plugins></build></profile></profiles>')
                with self.assertRaisesRegex(admission.AdmissionError, "profiles"):
                    admission.inspect(self.root)

    def test_unsupported_maven_parent_management_and_extensions(self):
        original = (self.root / "pom.xml").read_text()
        fixtures = {
            "parent": '<parent><groupId>example</groupId><artifactId>parent</artifactId><version>1.0</version></parent>',
            "dependencyManagement": '<dependencyManagement><dependencies><dependency><groupId>example</groupId><artifactId>tool</artifactId><version>1.0</version></dependency></dependencies></dependencyManagement>',
            "pluginManagement": '<build><pluginManagement><plugins><plugin><artifactId>tool-plugin</artifactId><version>1.0</version></plugin></plugins></pluginManagement></build>',
            "build extensions": '<build><extensions><extension><groupId>example</groupId><artifactId>extension</artifactId><version>1.0</version></extension></extensions></build>',
            "plugin extensions": '<build><plugins><plugin><artifactId>extension-plugin</artifactId><version>1.0</version><extensions>true</extensions></plugin></plugins></build>',
        }
        for label, xml in fixtures.items():
            with self.subTest(unsupported=label):
                (self.root / "pom.xml").write_text(original)
                # Insert into the existing build rather than creating duplicate builds.
                if xml.startswith("<build>"):
                    xml = xml[len("<build>"):-len("</build>")]
                    path = self.root / "pom.xml"
                    path.write_text(path.read_text().replace("</build>", xml + "</build>"))
                else:
                    self.pom_insert(xml)
                with self.assertRaisesRegex(admission.AdmissionError, label):
                    admission.inspect(self.root)

    def test_nested_plugin_dependency_versions_pinned_and_recorded(self):
        original = (self.root / "pom.xml").read_text()
        for version in ("LATEST", "RELEASE", "1.0-SNAPSHOT", "[1.0,2.0)", "${missing}"):
            with self.subTest(version=version):
                xml = '<dependencies><dependency><groupId>example.tools</groupId><artifactId>compiler-helper</artifactId><version>' + version + '</version></dependency></dependencies>'
                (self.root / "pom.xml").write_text(original.replace("</plugin>", xml + "</plugin>", 1))
                with self.assertRaisesRegex(admission.AdmissionError, "exact pinned version"):
                    admission.inspect(self.root)
        xml = '<dependencies><dependency><groupId>example.tools</groupId><artifactId>compiler-helper</artifactId><version>${junit.version}</version></dependency></dependencies>'
        (self.root / "pom.xml").write_text(original.replace("</plugin>", xml + "</plugin>", 1))
        source = admission.inspect(self.root)
        self.assertEqual(source["dependencies"][-1], {"groupId": "example.tools", "artifactId": "compiler-helper", "version": "5.11.4", "scope": "plugin", "plugin": {"groupId": "org.apache.maven.plugins", "artifactId": "maven-clean-plugin", "version": "3.2.0"}})
        report = admission.validate_packet(self.packet())
        self.assertEqual(report["sourceDigest"], source["sourceDigest"])

    def test_ai_request_rejects_actual_second_read_drift(self):
        original_read = admission.read_owned
        reads = 0
        def drift(root, name):
            nonlocal reads
            if name == "src/main/java/zero/community/HealthBar.java":
                reads += 1
                if reads == 2:
                    path = root / name
                    path.write_bytes(path.read_bytes() + b"\n// changed between inspect and bundle\n")
            return original_read(root, name)
        with patch.object(admission, "read_owned", side_effect=drift):
            with self.assertRaisesRegex(admission.AdmissionError, "Source changed while preparing AI request"):
                admission.ai_request(self.root)
        self.assertEqual(reads, 2)

    def test_pom_leaf_and_property_whitespace_normalized(self):
        path = self.root / "pom.xml"
        original = path.read_text()
        xml = '<dependencies><dependency><groupId> example.tools </groupId><artifactId> compiler-helper </artifactId><version> ${junit.version} </version></dependency></dependencies>'
        text = original.replace("</plugin>", xml + "</plugin>", 1)
        text = text.replace('<junit.version>5.11.4</junit.version>', '<junit.version>\n 5.11.4 \n</junit.version>')
        text = text.replace('<groupId>school.zero.community</groupId>', '<groupId> school.zero.community </groupId>')
        text = text.replace('<version>3.2.0</version>', '<version> 3.2.0 </version>')
        path.write_text(text)
        source = admission.inspect(self.root)
        self.assertEqual(source["dependencies"][-1], {"groupId": "example.tools", "artifactId": "compiler-helper", "version": "5.11.4", "scope": "plugin", "plugin": {"groupId": "org.apache.maven.plugins", "artifactId": "maven-clean-plugin", "version": "3.2.0"}})
        self.assertEqual(admission.validate_packet(self.packet())["sourceDigest"], source["sourceDigest"])

    def test_ai_request_text_matches_every_declared_digest(self):
        request = admission.ai_request(self.root)
        for file in request["files"]:
            self.assertEqual(admission.digest(file["text"].encode("utf-8")), file["sha256"])

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
