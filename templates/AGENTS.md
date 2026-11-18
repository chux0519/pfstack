# Agent notes for <project>

Practices: pfstack (potafree stack). Read this file first; details live in the linked docs.

## Roles
- **Coordinator** (main session): talks with the user, writes plans and acceptance criteria, reviews every diff
  and screenshot, merges, releases. Owns shared resources: <simulators / devices / production deploys>.
- **Implementers** (workers in hc): one task = one branch = one worktree = one writer. They code, run tier A,
  write implementation notes. They never launch other agents, touch shared resources, merge or release.
- Launch: `tool/spawn_worker.sh <name> <worktree> [sonnet]`. Model by difficulty: mechanical work → a fast
  model; design, concurrency, protocol, security, native → the strongest model. State the choice in the plan.
- Machine load: at most 2 workers and 1 <simulator>; heavy commands run with `nice -n 10`.

## Never lose work
- Every change goes through a branch and a PR; the coordinator merges and pushes main right away.
- Implementers: each small verifiable unit ends in check → commit → push. Nothing older than a few minutes
  lives only on this machine.
- Every report and every pause writes `docs/iterations/<id>/round-NN/STATE.md` (done, in progress, next,
  open decisions, how to verify).

## Plan first, bounded rounds
- Plan + acceptance criteria → user confirms → implement. Scope changes need a new confirmation.
- At most 3 implement → accept → review rounds per iteration; then stop and ask the user.
- An agent saying "done" is not evidence. Record the exact source state that was tested.

## Evidence tiers
- **A (default):** host-rendered screenshots + analyze + lint + test diff.
- **B:** one device / one theme / relevant scenes, only when A cannot prove it (keyboard, timing, webview,
  gestures, native). Coordinator only. Timing issues: record once, cut frames at PHASE marks.
- **C:** full matrix once before a store submission or external release.
- Use dedicated devices only (<UDIDs>), never `booted`. Dev builds use their own bundle id.

## Design
- [DESIGN.md](DESIGN.md) is the single source of truth; only the coordinator edits it.
- Every screenshot gets a review; obvious defects are fixed in the same round; advice that conflicts with
  DESIGN.md goes to the user as a "design conflicts" table.

## Rules, invariants, numbers
- New pitfall → a rule in [docs/review_rules.md](docs/review_rules.md), and in `tool/review_lint.py` if it can
  be checked automatically. Every review runs `python3 tool/review_lint.py`.
- Timing / state bugs → a numbered rule in [docs/design/state_invariants.md](docs/design/state_invariants.md)
  first, then a model-based test (`tool/model_check.py` pattern), then a named regression case.
- Only new failures count (`tool/test_diff.sh`). A wall-clock benchmark that fails in the full run is rerun
  alone before it counts.

## Authorizations
- Standing (no need to ask): <e.g. reviewed security releases, beta uploads, deploys of service X>.
- Always ask: store submissions and releases, other production deploys, anything public or hard to undo.
- An authorization never extends to a different context. If the tool refuses an action, ask; don't work around.

## Hard rules
- Never print tokens, passwords or review credentials; read them inside scripts only.
- Fixtures use `example-*` hosts only; no real host or user names in the repo or public exports.
- `rm -rf "${D:?}"` form only; look before deleting or overwriting.
- Don't change global toolchains or shared SDKs; ask the user to apply patches.
- Temporary LAN previews serve a copied folder only and are stopped after use; generated HTML has
  `<meta charset="utf-8">`.
- Replies to the user: short, action items first, in the user's language.
