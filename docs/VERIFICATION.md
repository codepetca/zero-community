# Local proof verification — 2026-10-09

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
