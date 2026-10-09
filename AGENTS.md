# Zero community

Read [.ai/CURRENT.md](.ai/CURRENT.md) and [README.md](README.md) before edits.
This is an ordinary Java 17 / JavaFX Maven library, independent of Zero core.
Keep explicit object updates and the API readable. One writer per component.
Pin dependencies, preserve reproducible release fixtures, and exclude builds.
Local implementation does not authorize pushes, publication, account changes,
remote creation or deployment. Licensing and maintainers await owner decisions.
Run the relevant checks in README and `git diff --check` before handoff; report
native/platform and physical-input gaps accurately.

Contribution preparation uses scripts/admission.py and
scripts/prepare-contribution.py; run scripts/test-admission.py for boundary changes.
Keep schema 1 and canonical digest consistent with Zero's graphical Workshop.
Do not execute scripts from contributor-controlled source roots in a beginner UI.
Metadata is derived from catalog/components.json, never a second authored catalog.
Contributor statuses, receipts and AI responses cannot establish review authority.
Trusted maintainer policy must be authenticated outside packets/PR checkouts.
CI must remain read-only, without AI secrets, write credentials or publication.
