# Zero Community

Community source repository: [codepetca/zero-community](https://github.com/codepetca/zero-community).
Part of [Codepet](https://github.com/codepetca), alongside the
[Zero teaching kit](https://github.com/codepetca/zero). Zero owns the framework,
editor extension, student starter and Component Workshop; this repository owns
community component source, examples, metadata and contribution checks.

Clone the repositories as siblings for the existing local Workshop/proof commands:

```sh
git clone https://github.com/codepetca/zero.git
git clone https://github.com/codepetca/zero-community.git
```

The remote hosts source and contribution PRs. Published MIT HealthBar 0.1.2
remains unchanged. The current source prepares a local 0.1.3 library with plain
and segmented health bar alternatives; it has not been published. A prepared
candidate stays local until intentional owner publication and verified readback.
The public catalog and Maven gateway belong to the Zero website integration.
The Workshop integration is included in Zero's published 0.5.0 source; its
separate component kit and Maven artifacts remain local. The source proof below
can be run independently of that editor integration.

This separate Maven library contains ordinary JavaFX components students can
use without copying component source. Maven owns dependencies. It does not
depend on or bundle Zero's framework. Both examples extend the existing
`zero.SimpleApp`, supplied only by the disposable student starter in the proof.

The current local library is `school.zero.community:zero-community:0.1.3`, targeting
Java 17 with pinned JavaFX controls 21.0.12. Read the [HealthBar API](docs/HealthBar.md)
and [SegmentedHealthBar API](docs/SegmentedHealthBar.md), plus the [component metadata](catalog/components.json). Source is readable under
`src/main/java`. [Adventure](examples/adventure/Main.java) and
[study](examples/study/Main.java) show different app-owned rules using one component.
Actual checks and limitations are recorded in [verification](docs/VERIFICATION.md).

Run local checks with JDK 17+ (a graphical JavaFX session is needed):

```sh
./mvnw -B test
python3 scripts/verify-release-cycle.py --zero-root ../zero
```

The second command builds 0.1.0 from its preserved source and 0.1.1 from its preserved
source, attaches source/API JARs, and uses Maven's install-file goal to stage a
local file repository under `.proof/repository`. It runs both consumers through
install → fix → update → revert with exact versions. The first baseline run
occurs before the fix is staged. Each consumer resolves the actual JAR from
the file repository into an isolated dependency cache and checks button/input
behavior, text, numeric fill and JAR origin. It preserves old release hashes.
Immutable existing coordinates are reused only when every built artifact byte
matches; an attempted replacement fails. No personal Maven settings are copied.
The proof also runs current tests against historical source and requires the
fraction regressions to fail, then verifies a different JAR cannot replace 0.1.0.

Generated `.proof/` contains `receipt.json`, `catalog.json` with release SHA256
metadata, `repository/`, `cache/`, `builds/`, and runnable `consumers/`. To run an
example interactively after the proof:

```sh
cd .proof/consumers/adventure
./mvnw -s ../../settings.xml -Dmaven.repo.local=../../cache compile javafx:run
```

The proof finishes with 0.1.0 selected after revert. To select the fix, change the
consumer POM's `zero.community.version` to `0.1.1`, then rebuild. Use fixed versions;
no latest/SNAPSHOT/ranges. Generated files, caches and artifacts stay out of Git.

These are experimental local fixtures. Original code and documentation are licensed
under the [MIT License](LICENSE), copyright 2026 Codepet. Contributions use the
same license; include the copyright and permission notice when reusing substantial
portions. Preserve the upstream wrapper notices under `.mvn/wrapper`; those cover
upstream wrapper code separately. Existing maintain/admin users of the canonical community repository may accept
contributions through independent current-revision GitHub reviews. CI and AI
cannot accept contributions. The initial 0.1.2 component remains experimental
with a null named maintainer under explicit owner release authorization. Publishing this source repository does not publish
Maven artifacts or appoint maintainers. Existing local release fixtures retain
their original bytes; this licensing change creates no artifact version or release.
Finite checks use synthetic
JavaFX events, with no Robot, forced activation or UI automation. Physical input,
Windows/Linux, editor/native dependency actions and novice trials are untested.

Local preparation and automated admission are documented in
[CONTRIBUTING](docs/CONTRIBUTING.md). Run `python3 scripts/test-admission.py`, then
`python3 scripts/prepare-contribution.py --output .proof/admission/packet-1`.
The packet has source-bound hashes, API/examples/dependencies and check receipts.
Structural checks produce `checked`; independent community acceptance and
distribution remain gated by maintainer appointments, trusted review and artifact hosting.
The [AI interface](docs/AI-REVIEW.md) is offline, budgeted and advisory.
The PR/push CI has pinned official actions, read-only permissions and no
publishing or AI credentials. It builds/tests with virtual-display JavaFX and
validates a local contribution packet; passing it does not approve a component.
See the verification record for observed runs and platform limitations.

## Prepare the first public release

Keep 0.1.0 and 0.1.1 as historical local fixtures; their source/POM snapshots and
artifact bytes are preserved. Do not publish the known faulty 0.1.0. Public 0.1.2
keeps the fixed HealthBar API and embeds the canonical MIT notice in its library,
source and API JARs. One public version is sufficient; later real releases enable
public Update/Revert.

From clean committed source, with the sibling Zero checkout:

```sh
python3 scripts/test-public-release.py
python3 scripts/prepare-public-release.py --zero-root ../zero
```

Preparation makes a new ignored `.proof/public/0.1.2/` directory; `--output` may
choose another new directory under `.proof/`. It refuses dirty source, symlinks,
coordinate drift and overwrite. Two clean isolated Maven builds must produce the
same four artifacts; source/POM/license/API bytes and class contents are checked.
Adventure and study resolve the actual JAR through Maven and exercise behavior.
Empty Maven settings and disposable caches avoid personal Maven configuration.
`catalog.json`, `SOURCE.json`, `checks.json`, `SHA256SUMS` and `LICENSE` accompany
the four flat artifacts. The generated catalog records exact source commit/digest,
sizes and hashes; `publication.status` is `local` and asset URLs are null. It never
claims that uploads exist or accepts a contribution. After intentional owner
publication, verified GitHub readback supplies the published URLs to Zero's
single generated public manifest. No publisher or CI write access is added here.

Run the trusted owner-side acceptance helper from maintained source, **never from
a contribution PR checkout**:

```sh
python3 scripts/check-github-acceptance.py --root /path/to/clean/candidate --pull-request 2
```

It uses existing `gh` authentication only for read-only canonical GitHub API calls.
It requires a current-head independent human approval by an existing maintain/admin
user and successful canonical Component checks for that PR revision. Stale,
dismissed, superseded, self, bot, unknown-role or unavailable evidence waits. No
JSON receipt establishes authority; the helper cannot approve, merge or publish.
An owner-authored initial release does not acquire independent community acceptance.

## Local health bar alternatives (0.1.3)

Both `HealthBar` and `SegmentedHealthBar` coexist in the `health-bars` category.
The plain class keeps its existing API and source unchanged. The segmented class
is available only in exact version 0.1.3, with the same constructors, `view`,
`setHealth`, `getHealth` and `getMaximum` methods. Both remain experimental MIT
components with no named maintainer. Contributor metadata can describe category
and exact version availability, but cannot declare recommendation, curation,
acceptance or core promotion. Recommendations belong to the separately reviewed
owner catalog and must name an exact component and library version.

From trusted maintainer source, prepare an uncommitted local working-tree proof:

```sh
python3 scripts/prepare-public-release.py --local-source --zero-root ../zero
node ../zero/scripts/prepare-component-workshop.mjs "$PWD" --local
node ../zero/scripts/run-component-workshop.mjs --check
node ../zero/scripts/package-components.mjs "$PWD" --local-source
```

The first command creates a new `.proof/local/0.1.3/` directory and refuses
overwrite, symlinks or fixed-coordinate drift. It performs two reproducible
builds, checks both classes/source/API/MIT notice and all six JavaFX tests, and
runs two actual Maven consumers. `SOURCE.json` marks `sourceState: working-tree`;
its commit URL identifies the base, while its digest binds the exact declared
working-tree files. This proof is not a clean committed public release candidate.
The default command without `--local-source` retains the clean committed source
guard and writes `.proof/public/<current-version>/`. Neither command publishes.

The Workshop selects either alternative, builds all declared component source
through fixed trusted javac options (never contributor POM/hooks), checks both
components and exports a schema 1 packet binding both classes and their examples.
Existing HealthBar-only 0.1.2 metadata and packets remain supported. Generated
local artifacts and receipt data stay ignored.
