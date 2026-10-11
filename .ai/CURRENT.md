# Current state

Updated 2026-10-10. Canonical repository: `codepetca/zero-community`, branch `main`.
Historical phase instructions are archived in
[the prior handoff](../docs/history/ai-handoff-through-2026-10-10.md).

Community **0.1.3** is published from `7d4fa181d07f320cc4a305f60636e81aab9a9bcb`.
HealthBar and SegmentedHealthBar remain experimental MIT components with no named
maintainer; publication is not independent Community acceptance or core promotion.
See [evidence](../docs/EVIDENCE.md) for public sources, CI and release links.

## Authorized work and ownership

Owner accepted the AI audit fixes. Local branch `codex/ai-flow-hardening` starts at
`f6460f48`. Coordinator owns this snapshot/history/evidence, GitHub main rules and
Git mutations; one Community worker owns admission/acceptance scripts, tests and
contribution docs. No live AI provider, component API change, new release or
credential/account change. Owner now explicitly authorized source PR publication
and merge. Owner subsequently approved both PRs and explicitly requested removal
of GitHub branch protections in both repositories. Authenticated readback confirms
unprotected main branches and empty rulesets; verify final-head CI before merging.

Worker requested GPT-6.1-Sol/high for the bounded CI/authority boundary; effective
configuration/tokens unknown. Weekly24%remaining at start is account-wide;
DeepSeek automatic delegation is paused through2026-12-31.

## Current implementation contract

- AI stays advisory-only. Serialize once and validate exact emitted UTF-8 bytes;
  response schema1 must be an integer, excluding booleans/floats.
- Acceptance helper runs from clean authenticated canonical-main policy source,
  outside the candidate. Candidate workflow/scripts/Maven execution policy must
  match trusted main; changed policy waits for separate human policy review.
- Independent current-head maintain/admin approval is still required. The helper
  remains read-only and cannot merge, publish, recommend or appoint maintainers.
- GitHub main protection was applied, then removed by explicit owner decision.
  CODEOWNERS/main-protection.json do not enforce a gate or authorize restoration.
  Community acceptance-helper requirements are unchanged.

Status: local implementation accepted.39admission and25acceptance/release tests
pass; both initial independent scopes and the targeted correction review complete
with no unresolved blockers. Final decisions refresh PR readiness/reviews/roles;
read-only snapshots do not guarantee atomicity against later changes.
GitHub main protection removal is authenticated readback verified. Source and
CODEOWNERS are published in [Community PR5](https://github.com/codepetca/zero-community/pull/5),
with [Zero PR20](https://github.com/codepetca/zero/pull/20) as the companion.
Recover actual open/merged status from GitHub. Next: final-head CI and
merge both owner-approved source PRs, and verify actual merged state. Do not
re-enable protections without owner authorization. No new release/provider.
Review ledger/limits live in sibling Zero CURRENT.
No live AI, public student acceptance, physical Windows/Linux or novice trial is
claimed. Previous publication authority completed; immutable releases remain intact.
