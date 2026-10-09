# Public release preparation — 2026-10-09

Current source prepares 0.1.2, the first public MIT candidate. It remains
experimental with a null named maintainer. Existing maintain/admin GitHub users
may accept independent source contributions; initial owner release authorization
does not claim that review. No publication or authenticated live contribution
acceptance has occurred during this local implementation.

Local boundary checks: 32 admission tests and 12 public-release/acceptance tests.
Mocks cover maintain/admin vs write/unknown roles, independent author identity,
stale/dismissed/superseded/bot reviews, pagination, CI failure/newer failure,
head races, canonical repository mismatch, dirty source, output overwrite,
license drift, unexpected bundled classes and historical fixtures.

A disposable committed source checkout under `.proof/public-check/source` was
used because implementation edits were uncommitted. Its public preparer passed
two reproducible builds, all three HealthBar checks, canonical MIT bytes in
library/source/API JARs, exact source/POM, no Zero classes, and both actual Maven
consumer apps. The generated manifest is local with null artifact URLs. This is
fixture evidence; after review/commit, regenerate from the actual release commit.

Historical 0.1.1 POM/source/test bytes were copied before the current version and
packaging changed. Historical proof now builds both versions from preserved
`releases/<version>` snapshots. It supports either the old starter SimpleApp path
or the current framework source path, copying core source only into disposable
consumers. Old artifacts/coordinates are never replaced. CI retains read-only
permissions and adds mocked boundaries and inspection of its already-built
licensed artifacts; it does not run live acceptance or publication.

Native physical Windows/Linux input, novice/classroom adoption and the final
public gateway remain outside these checks. Historical proof rerun passed all six install/update/revert consumer checks in
61.11 seconds; both library JAR hashes equal the previously preserved receipts.
Exact byte comparison against base 7c503b3 also confirmed the new 0.1.1 POM,
HealthBar source and test snapshots. Earlier evidence follows.

# Local proof verification — 2026-10-09

## Public source remote and CI — 2026-10-09

Owner authorized source publication to
[codepetca/zero-community](https://github.com/codepetca/zero-community).
Local `main` tracks `origin/main`. First published source-connection commit:
`d66e7cf9e8d7f27da56665fadab6e9f6fc3712b1`.

[GitHub Actions run 37936790362](https://github.com/codepetca/zero-community/actions/runs/37936790362)
completed successfully on Ubuntu 24.04 with Temurin JDK 17. The workflow ran
`xvfb-run -a ./mvnw -B verify`, all 25 Python admission boundary tests,
contribution packet preparation and packet validation. This is automated Linux
virtual-display evidence; it does not verify physical Linux/Windows input or
native VS Code interactions. There is no publishing or AI job.

Coordinator reran all 25 admission tests locally. The initial upload excluded
generated artifacts, caches and packets. A pattern scan of 35 unique tracked
history blobs across four prior commits found no matching credential patterns
or private/build paths; this is a scoped check, not a universal security guarantee.
Catalog, Java source, Maven coordinates and immutable historical fixture bytes
were unchanged by the remote/documentation wiring.

## Previous local release-cycle evidence

Observed on macOS with Homebrew OpenJDK 17.0.14 and pinned JavaFX 21.0.12.
No physical input, UI automation, remote publication or credential changes.

Command: `python3 scripts/verify-release-cycle.py --zero-root /Users/stew/Repos/zero`.

Current library: 3/3 meaningful checks passed (fractions/caption, bounds/independence/reset,
invalid inputs). Historical source rejected by the two fraction scenarios.
Both consumer apps passed install 0.1.0 → update 0.1.1 → revert 0.1.0.
Adventure partial fill: 0 → 0.75 → 0. Study partial fill: 0 → 0.875 → 0.
Actual resolved cache JAR digests match the immutable file repository. Consumers
contain no HealthBar source; release class list contains only HealthBar, no Zero core.

Initial build/cycle: 40.39 seconds. Deterministic repeat: 18.54 seconds, all four
artifact digests matched for each existing version. Final cycle with negative
guards: 20.57 seconds. Differing baseline artifact bytes were rejected
without changing the installed baseline JAR. Generated receipt and distribution
index are `.proof/receipt.json` and `.proof/catalog.json`.

| Version | Library JAR SHA256 |
| --- | --- |
| 0.1.0 | `560f88c6e4dc207202ad526794e2a7e0c2a4dcbdd4d0736f078eb0ccbf13bcb7` |
| 0.1.1 | `ecde77c90e6d01854c5aa89ad099d40ae1714675edfb9343266050d7c626c36e` |

Each version retains its POM, library, source and API JARs plus SHA256/SHA1
sidecars in `.proof/repository/school/zero/community/zero-community/<version>/`.
Public licensing/maintainers/hosting, native editor actions, Windows/Linux,
physical input and novice/cohort usefulness remain unverified. Source revision
is null because the new local repository has no commits. Effective worker
model/configuration and attributable token telemetry are unavailable.

## MIT licensing verification — 2026-10-09

Owner selected MIT for original community code and documentation. Root LICENSE
matches Zero's canonical MIT text byte for byte, copyright 2026 Codepet.
HealthBar metadata now records MIT, retaining experimental status and null
maintainer. Contributions use the same license; upstream wrapper notices remain.
Maintainer appointments, authenticated acceptance and artifact hosting remain gated.

Local checks passed: `python3 scripts/test-admission.py` (32 tests),
`python3 scripts/admission.py inspect --root .`,
`python3 scripts/prepare-contribution.py --root . --output .proof/licensing-2026-10-09/packet-2`,
`python3 scripts/admission.py validate --packet .proof/licensing-2026-10-09/packet-2/packet.zip`,
and `git diff --check`. Generated evidence is ignored under
`.proof/licensing-2026-10-09/`. Packet status is `checked`; `communityReviewed`
and `publishAllowed` are false. Regression tests verify MIT with null maintainer
remains unaccepted and UNLICENSED with otherwise trusted review remains blocked.

Metadata SHA256: `8681d61c115fe81b8b25b6702427f819d0fbcf10da182304cedb87f87424a036`.
Source digest: `5f457df0b1c38f7bd4ad6c2584ef82fa3d40878e215e3fbc463e697f7bcbb517`.
The metadata change invalidates previous source-bound packet/review receipts.
Schema 1 requires root LICENSE whenever any component records MIT, making the
current packet eight owned files. The exact notice bytes and SHA256 participate
in the source digest; missing or symlinked notices and packet/receipt drift are
rejected. Historical UNLICENSED seven-file packets still validate. Current MIT
packets preserve the canonical notice byte for byte. No Java/POM or preserved 0.1.0 source changed, no version or
artifact release was created, and existing generated immutable artifacts were
not rebuilt or replaced by this check. Java behavior was not rerun for this
licensing/documentation change. No current remote CI, native platform or physical
input verification, publication, credential or account changes were performed.
