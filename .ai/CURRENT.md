# Current state — 2026-10-09

Local component lifecycle proof; no public repository or release configured.
One library: `school.zero.community:zero-community:0.1.1` with ordinary
`zero.community.HealthBar`. Java 17, JavaFX controls 21.0.12.
Canonical source is under `src/main/java`; 0.1.0's known fractional-fill bug is
preserved under `releases/0.1.0`. The API is compatible across both versions.
`catalog/components.json` is the sole component discovery metadata source.
Examples consume the Maven artifact; Zero's SimpleApp is copied only into ignored
disposable proof apps, never into the library or release artifacts.
Generated `.proof/` contains local repository/cache/consumers and receipts.
Experimental, UNLICENSED; no community-review or distribution-permission claim.
Checks and commands: [README](../README.md). No credentials or external service
configuration. Windows/Linux, physical input and cohort adoption remain untested.

Phase 3 local preparation: schema 1 packet/admission scripts, negative boundary
tests, source-bound offline AI interface, contributing docs and read-only
pinned-action CI draft. Sole metadata remains catalog/components.json.
Generated packets use .proof/admission, disjoint from phase 1 release artifacts.
Acceptance model demonstrates separately trusted independent human approval and
source-bound checks; CLI cannot accept or publish. Missing license, appointments,
authenticated service and public hosting remain gated. CI has not run on GitHub.
Live AI execution remains deferred.

Observed local admission proof: 19 boundary tests, Python export and independent
Python validation of the Java Workshop ZIP share source digest
`d123308f8274e0f2dbd62d9da78ebd91ef731b0d2e427f74a0988d1073c7f8cf`.
Offline AI bundle/response validation passed. Evidence: ignored
`.proof/admission/verification.json` and `boundary-tests.txt`. Java/library source,
release fixtures, release-cycle script and phase 1 artifacts were not edited.
