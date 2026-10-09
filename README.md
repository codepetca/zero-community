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

The remote hosts source and contribution PRs. Component artifacts and catalogs
remain local prototypes; this is not a configured public Maven repository.

This separate Maven library contains ordinary JavaFX components students can
use without copying component source. Maven owns dependencies. It does not
depend on or bundle Zero's framework. Both examples extend the existing
`zero.SimpleApp`, supplied only by the disposable student starter in the proof.

The first artifact is `school.zero.community:zero-community:0.1.1`, targeting
Java 17 with pinned JavaFX controls 21.0.12. Read the [HealthBar API](docs/HealthBar.md)
and the [component metadata](catalog/components.json). Source is readable under
`src/main/java`. [Adventure](examples/adventure/Main.java) and
[study](examples/study/Main.java) show different app-owned rules using one component.
Actual checks and limitations are recorded in [verification](docs/VERIFICATION.md).

Run local checks with JDK 17+ (a graphical JavaFX session is needed):

```sh
./mvnw -B test
python3 scripts/verify-release-cycle.py --zero-root ../zero
```

The second command builds 0.1.0 from its preserved source and 0.1.1 from current
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

These are experimental local fixtures. Public reuse licensing, artifact distribution location
and named maintainers await owner decisions; `UNLICENSED` records that absence.
No community review or reuse permission is claimed. Wrapper notices
under `.mvn/wrapper` cover upstream wrapper code only. Publishing this source
repository does not publish Maven artifacts or appoint maintainers. Finite checks use synthetic
JavaFX events, with no Robot, forced activation or UI automation. Physical input,
Windows/Linux, editor/native dependency actions and novice trials are untested.

Local preparation and automated admission are documented in
[CONTRIBUTING](docs/CONTRIBUTING.md). Run `python3 scripts/test-admission.py`, then
`python3 scripts/prepare-contribution.py --output .proof/admission/packet-1`.
The packet has source-bound hashes, API/examples/dependencies and check receipts.
Structural checks produce `checked`; independent community acceptance and
distribution remain gated by owner licensing/appointments and trusted review.
The [AI interface](docs/AI-REVIEW.md) is offline, budgeted and advisory.
The PR/push CI has pinned official actions, read-only permissions and no
publishing or AI credentials. It builds/tests with virtual-display JavaFX and
validates a local contribution packet; passing it does not approve a component.
See the verification record for observed runs and platform limitations.
