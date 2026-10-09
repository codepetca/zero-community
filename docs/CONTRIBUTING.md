# Prepare a component contribution

Students own their repositories; coursework links submitted in Pika stay separate.
Community maintainers review component inclusion. The classroom teacher is not the
fallback reviewer when no maintainer is available. Unreviewed contributions wait.

Use ordinary Java objects and explicit method calls. Keep source readable, explain
the public API and errors, and demonstrate reuse in two different apps. Distinct
source examples are a preparation check, not independent proof of usefulness.
Maven dependencies and build plugins must have fixed versions.

`catalog/components.json` is the sole source metadata authority. Its library and
component fields supply the workshop, contribution packet and admission report.
API documentation lives in `docs/<Component>.md`, owned component source under
`src/main/java/zero/community`, tests under the corresponding test package, and
examples at `examples/<app-id>/Main.java`. The first packet has seven owned files:
the POM, metadata, HealthBar source/test/API and the adventure/study apps.

Run the existing Java checks first, then the maintainer preparation checks:

```sh
./mvnw -B test
python3 scripts/test-admission.py
python3 scripts/admission.py inspect --root .
python3 scripts/prepare-contribution.py --root . --output .proof/admission/packet-1
python3 scripts/admission.py validate --packet .proof/admission/packet-1/packet.zip
```

Use a new generated output directory each time. Preparation refuses overwrites.
The graphical Workshop can produce the same schema without installing Python;
Python tools are for maintainer/CI validation. Running a candidate build is an
explicit check task: source inspection never executes contributor code. The
existing release-cycle command verifies actual Maven consumers and compatibility;
its generated repository and catalog remain local under `.proof/`.

Output contains `packet.zip`, `packet.json`, `checks/report.json` and an independent
`admission-report.json`. ZIP entries are exactly the owned source files plus the
packet manifest and check receipt. It excludes credentials, environment files,
caches, targets and arbitrary tree contents. Symlinks, traversal, duplicate entries,
non-owned files and oversized inputs are refused.

Schema 1 `packet.json` carries `sourceDigest`, `files` records (`path`, `sha256`),
the exact source `metadata`, POM-derived `dependencies`, declared `checks` and
`provenance`. The source digest is SHA256 of UTF-8 canonical JSON for the sorted
owned file records: array order by path, object keys `path` then `sha256`, no
whitespace. Source metadata participates in that digest. Packet and check receipt
files are excluded to avoid a digest cycle. New source bytes require a new digest
and new check/review receipts.

Optional `--check-report <receipt.json>` supplies schema 1, the same `sourceDigest`,
`checks` entries with unique `id`, `status` (`passed`, `failed`, `unavailable`) and
string `evidence`, plus a `provenance` object. A stale receipt fails export.
Contributor receipts remain claims. Runtime evidence must identify the actually
tested artifact/version and distinguish it from edited source. Tests of an
installed artifact cannot prove a changed candidate: rebuild the candidate
explicitly or record those checks as unavailable. AI feedback is unavailable by
default and advisory whenever supplied.

A receipt with any failed check produces `changes-required`; validation exits 1.
Export may retain that failed packet for repair feedback. Candidate receipts use
`provenance.testedArtifact` with exact `version`, `sha256`, `sourceBinding` set to
`built-local-candidate`, the same `sourceDigest`, and `kind` (`candidate-class` or
`candidate-jar`). Installed-release receipts use `matched-immutable-source` and
`sourceJarSha256`. These fields are validated claims, never authenticated proof.

Automated structural success produces `checked` with a narrow scope; it does not
change authored metadata into `community-reviewed`. No status field, command flag,
contributor receipt or AI response can self-promote. The CLI has no acceptance or
publishing operation.

For community acceptance, appointed maintainers independently verify build,
behavior, reuse and compatibility for the exact digest, review usefulness and
readability, and record an independent human decision outside the contributor
packet. `admission.acceptance_model` demonstrates this local policy contract in
tests. Its caller must independently authenticate maintainer/reviewer/check-runner
authority; JSON with those names is not authentication. Never obtain trusted policy
from a PR checkout, packet or contributor-controlled flag. The model cannot publish
even when every modeled requirement passes. An authenticated service and release
workflow are separate owner-approved work.

Public reuse licensing, named maintainers and hosting remain owner decisions.
Current `UNLICENSED` and null maintainer prevent acceptance/public distribution.
Wrapper notices only cover upstream wrapper code. Local preparation continues
without inventing a license or appointing anyone.

The CI draft builds/tests and validates a local packet on PR/push with read-only
repository access, no AI secrets and no publishing job. No remote/live CI execution
is configured or observed. Native Windows/Linux input, physical-input usability
and novice/cohort adoption remain untested.
