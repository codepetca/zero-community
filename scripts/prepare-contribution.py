#!/usr/bin/env python3
"""Export one allowlisted contribution packet into a new generated directory."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile
import admission


def prepare(root, output, check_report=None):
    source = admission.inspect(root)
    if check_report:
        path = Path(check_report)
        if path.is_symlink() or path.stat().st_size > admission.MAX_FILE_BYTES:
            raise admission.AdmissionError("Unsafe check report")
        report = admission.validate_receipt(admission.parse_json(path.read_bytes()), source["sourceDigest"])
    else:
        report = {"schema": 1, "sourceDigest": source["sourceDigest"], "checks": source["checks"] + [{"id": "behavior-build", "status": "unavailable", "evidence": "No behavior/build receipt supplied; structural export does not execute contributor code."}, {"id": "ai-review", "status": "unavailable", "evidence": "No provider execution configured; advisory only."}], "provenance": {"generator": "prepare-contribution.py schema 1", "scope": "read-only source inspection"}}
    manifest = {key: source[key] for key in ("schema", "sourceDigest", "files", "metadata", "dependencies")}
    manifest["checks"] = report["checks"]
    manifest["provenance"] = {"generator": "prepare-contribution.py schema 1", "sourceManifest": admission.META, "sourceRevision": None, "sourceDigestAlgorithm": "sha256(canonical-json(sorted path+sha256 records))", "scope": "local contribution; authored status is not community approval"}
    contents = {f["path"]: admission.read_owned(Path(root).absolute(), f["path"]) for f in source["files"]}
    if any(admission.digest(contents[f["path"]]) != f["sha256"] for f in source["files"]):
        raise admission.AdmissionError("Source changed while preparing packet")
    output = Path(os.path.abspath(output))
    if output.exists() or output.is_symlink() or any(parent.is_symlink() for parent in output.parents):
        raise admission.AdmissionError("Output must be a new directory without symlink parents; overwrites refused")
    if output == Path(root).absolute() or any(output == Path(root).absolute() / f["path"] for f in source["files"]):
        raise admission.AdmissionError("Output overlaps owned source")
    # Exclusive final directory creation prevents concurrent writers overwriting a packet.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    try:
        (output / "checks").mkdir()
        (output / "packet.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (output / "checks/report.json").write_text(json.dumps(report, indent=2) + "\n")
        contents["packet.json"] = (output / "packet.json").read_bytes()
        contents["checks/report.json"] = (output / "checks/report.json").read_bytes()
        with zipfile.ZipFile(output / "packet.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(contents.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        result = admission.validate_packet(output / "packet.zip")
        (output / "admission-report.json").write_text(json.dumps(result, indent=2) + "\n")
        return {"schema": 1, "sourceDigest": source["sourceDigest"], "packet": str(output / "packet.zip"), "report": str(output / "admission-report.json"), "status": result["status"], "publishAllowed": False}
    except Exception:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-report", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.root, args.output, args.check_report), indent=2))
        return 0
    except (admission.AdmissionError, OSError, ValueError, KeyError, TypeError) as error:
        print("Contribution refused: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
