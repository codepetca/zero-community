# Prepare a component contribution

Students own their repositories; coursework links submitted in Pika stay separate.
Propose community changes through a fork and pull request to
[codepetca/zero-community](https://github.com/codepetca/zero-community).
Framework, editor and Workshop changes belong in
[codepetca/zero](https://github.com/codepetca/zero).
Community maintainers review component inclusion. The classroom teacher is not the
fallback reviewer when no maintainer is available. Unreviewed contributions wait.

Use ordinary Java objects and explicit method calls. Keep source readable, explain
the public API and errors, and demonstrate reuse in two different apps. Distinct
source examples are a preparation check, not independent proof of usefulness.
Maven dependencies and build plugins must have fixed versions.

Schema 1 accepts a standalone POM with direct dependencies and build plugins.
Parents, profiles (active or inactive), dependency/plugin management and build or
plugin extensions are unsupported and fail admission. Admission inspects XML
without executing Maven or resolving an effective POM. Explicit plugin dependencies
must also have exact versions; their packet dependency records use `scope: plugin`
and a `plugin` object identifying the owning plugin's coordinates and version.

`catalog/components.json` is the sole source metadata authority. Its library and
component fields supply the workshop, contribution packet and admission report.
API documentation lives in `docs/<Component>.md`, owned component source under
`src/main/java/zero/community`, tests under the corresponding test package, and
examples at `examples/<app-id>/Main.java`. The current MIT packet has eight owned
files: root LICENSE, the POM, metadata, HealthBar source/test/API and the
adventure/study apps. Schema 1 requires root LICENSE whenever any component
records MIT; its bytes and hash participate in the source digest. Existing
UNLICENSED seven-file packets still validate, without acquiring reuse permission.

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

Schema fields must be the JSON integer `1`; booleans, floats and strings fail
source, packet, receipt and AI validation.

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

Original code and documentation are licensed under the [MIT License](../LICENSE),
copyright 2026 Codepet, by owner decision on 2026-10-09. Contributions use the
same MIT license. Reuse must retain the copyright and permission notice in copies
or substantial portions. Preserve upstream notices under `.mvn/wrapper`, which
cover wrapper code separately. Current HealthBar metadata records `MIT`, remains
`experimental` and has a null maintainer. Named maintainers, authenticated
community acceptance and artifact hosting remain gated; MIT reuse permission
does not appoint a maintainer or approve a component. This change does not replace
existing immutable Maven artifacts or create a version/release.

CI builds/tests and validates a local packet on PR/push with read-only
repository access, no AI secrets and no publishing job. Source hosting does not
configure a public artifact service or authenticated acceptance service.
Native Windows/Linux input, physical-input usability
and novice/cohort adoption remain untested.

## Authenticated maintainer decision

Owner policy for public contributions: existing `maintain`/`admin` users of
`codepetca/zero-community` are the allowed acceptors. Use the normal fork and source
PR workflow above. Uploading a Workshop packet is preparation; a source PR lets
GitHub's read-only checks build and inspect the proposed source. Passing checks,
a contributor's authored status and AI feedback never accept it.

The maintained `scripts/check-github-acceptance.py` is an owner-side read-only
bridge to GitHub's authenticated reviews and repository roles. Run the helper
from a clean owner checkout at the authenticated canonical GitHub `main` SHA,
pointing `--root` at a separate clean candidate checkout and `--pull-request` at
its canonical PR number. The helper authenticates its own checkout revision using
the read-only GitHub branch API; a dirty, stale or noncanonical helper checkout
fails closed. The PR must target canonical `main`. It fetches all review pages,
uses the effective decision for each reviewer, and requires an independent
`APPROVED` review on the exact current head. `role_name` must be `maintain` or
`admin`; the legacy `permission: write` is insufficient. The reviewer must be a
User account distinct from the PR author, with matching role API identity.
Canonical Component checks must pass for the same head and PR, and a newer failed
or incomplete run supersedes an older success. Before relying on CI, the helper
compares every tracked path, Git mode, object type and blob hash under `scripts/`,
`.github/workflows/` and `.mvn/`, plus `mvnw`, `mvnw.cmd` and `pom.xml`, against
that trusted `main` checkout. Changed, added, removed or mode-changed policy files
keep the contribution waiting even with green CI and a qualified human approval.
Policy changes require a separate owner policy review and merge; component
acceptance can only follow against the resulting authenticated `main` policy.
A PR changing this helper cannot use its own changed code to acquire acceptance,
including the initial hardening PR. This check never executes candidate scripts.
Re-reading canonical main, both clean checkout revisions, policy trees and the
PR head/base/digest catches changes during the check. After reading CI, the helper
refreshes effective reviews and qualified role identities and checks that the PR
is still open and ready for review. Reported decisions use this final readback.
These bounded read-only API calls provide a snapshot, not an atomic guarantee
against later changes. Unavailable role/review/CI evidence waits.
A current-head effective changes request by another qualified maintainer blocks
acceptance even when an approval exists; stale/unqualified requests are not authority.
The owner is responsible for human review; automation must not post approvals.

The helper reports `accepted` only for authenticated maintainer review plus CI
with unchanged execution policy. Human usefulness/readability review remains
required. Separate release artifact checks and an intentional owner publication are still
required. `publishAllowed` always remains false. No flags, local JSON authority,
AI secret, CI write permission, automatic merge or publisher are introduced.
The earlier `acceptance_model` remains a local policy demonstration, not this
live authenticated bridge. Initial experimental 0.1.2 publication under the
owner's explicit authorization does not claim independent community acceptance.

## Alternatives and catalog authority

Use an optional `category` slug to group alternatives and optional `versions`
containing distinct exact library versions that actually include the class.
Include the current library version; omit `versions` for older metadata whose
component is available in every listed release. Plain and segmented health bars
share `health-bars`, while SegmentedHealthBar begins at 0.1.3. Every component
declares its own API documentation, meaningful tests and two distinct app examples;
all declared files participate in one canonical schema 1 digest.

Contributor source metadata cannot declare recommendation or curation fields.
Those belong to the separately owner-reviewed public catalog, tied to an exact
component and library version. Packet receipts, CI and AI confer no recommendation,
community acceptance, named maintainer appointment or Zero core promotion.

## Required GitHub merge gate

Canonical main requires an up-to-date PR, one current human approval, resolved
review conversations and the GitHub Actions `check` result. Stale approvals are
dismissed and the latest push must be approved by someone else. Rules apply to
administrators without review bypass, force push or branch deletion. Code owners
are existing human maintainers; AI feedback cannot supply a GitHub human approval.
The owner-side acceptance helper is still a separate read-only check, not an
automatic merge or publication service. Policy-changing PRs use human policy
review; component acceptance follows only against authenticated main policy.
