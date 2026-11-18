# pfstack (potafree stack)

**English** | [中文](README.zh-CN.md)

How we build software with coding agents: **one coordinator sets the direction, agents do the work; every
step leaves evidence, can be resumed and can be rolled back; every pitfall becomes a rule or a test.**

pfstack ships as a Claude Code / Codex skill (`/pfstack`) plus project templates and small tools. It was
distilled on 2026-11-18 from building Shinphony (an iOS / macOS / Windows terminal app, a Go daemon and
Cloudflare Workers). Some ideas come from poteto's pstack (small verifiable units, safe pause and resume,
explain the number); the rest is our own experience.

## One-line install (tell your agent)

> Install the pfstack skill: run `git clone https://github.com/chux0519/pfstack ~/repos/pfstack && bash ~/repos/pfstack/install.sh` (if it is already there, run `bash ~/repos/pfstack/install.sh` to update), then tell me the result.

`install.sh` clones or updates the repo and links `skill/pfstack` into `~/.claude/skills/` (and
`~/.codex/skills/` if `~/.codex/` exists). It is safe to run again.

Then, in any project, say **`/pfstack`** (or "set up pfstack in this project").

---

## 1. Roles: one coordinator, several implementers

| Role | Does | Does not |
|---|---|---|
| Coordinator (the main session) | Talks with the user, writes plans and acceptance criteria, reviews every diff and screenshot, merges, releases; owns shared resources (simulators, devices, production deploys) | Edit the same code an implementer is writing |
| Implementer (a worker: a separate agent in its own terminal) | One task, one branch, one worktree; codes to the plan, runs the lowest evidence tier itself, writes implementation notes | Launch nested agents, touch shared resources, widen the scope, merge or release |

- **Model by difficulty:** mechanical work (renames, copy, renders, test updates, verification runs) → a fast,
  cheap model; cross-cutting design, concurrency, protocols, security, native platform work → the strongest
  model. The plan states the choice.
- **Machine load is capped:** at most 2 workers and 1 simulator at a time; heavy commands under `nice -n 10`;
  caches and temp files on the big disk.
- **Workers are parented to the live session address**, never a copied old one.

## 2. Never lose work: small units, commit, push, leave state

- **Every change goes through a branch and a PR**; the coordinator reviews and merges, then pushes main at once.
- **Implementers finish each small verifiable unit with check → commit → push.** Nothing that took more than a
  few minutes lives only on one machine.
- **Every report and every pause writes `STATE.md`**: done, in progress, next step, open decisions, how to
  verify. A new session (or the machine after a reboot) resumes from it without re-deriving anything.
- Use SSH remotes (an HTTPS keychain can be locked after a reboot).

## 3. Plan first, bounded rounds

- User feedback → the coordinator writes the plan and acceptance criteria → **work starts only after the user
  confirms**. A scope change needs a new confirmation.
- **At most 3 rounds** of implement → accept → review. If P0–P2 issues remain after round 3, stop and let the
  user decide; no round 4, and no renaming the task to reset the count.
- Plans, implementation notes, acceptance and reviews go into `docs/iterations/<id>/round-NN/`, with the exact
  source state that was tested. **An agent saying "done" is not evidence.**

## 4. Evidence tiers: the lowest tier that proves it

| Tier | When | How |
|---|---|---|
| A (default) | Colour, spacing, copy, layout, component swaps | Host-rendered screenshots of the real UI + static analysis + lint + test diff; seconds to minutes |
| B | What A cannot prove: keyboard, timing, animation, WebView, gestures, native features | One device, one theme, the relevant scenes; run by the coordinator |
| C | Once before a store submission or external release | Every device × every theme |

- The plan names the tier for the round; using B needs a reason why A is not enough. What a tier cannot prove is
  listed as "pending C" and never claimed as accepted.
- **Timing issues: record once, then cut frames.** One screenshot after an action is not proof of a failure.
  Scenario scripts print `PHASE` marks; cut frames by mark instead of re-running.
- **Dedicated devices only** (fixed IDs, never "the booted one"); never touch another project's devices; dev
  builds never install over the user's production or beta app (use a separate bundle id).

## 5. One source of truth for design

- `DESIGN.md` is the only standard for visuals and interaction; only the coordinator edits it. New UI uses the
  project's own component layer.
- **Every screenshot gets reviewed** (HIG-style heuristics), with a verdict per image: obvious defects are fixed
  in the same round; advice that conflicts with DESIGN.md is not applied but listed in a "design conflicts"
  table for the user, whose decision is written back into DESIGN.md.
- Spoken user decisions ("diagrams are fine, decoration is not") go into DESIGN.md on the spot, dated.

## 6. Pitfalls become rules

- Each new pitfall → a rule in `docs/review_rules.md`; if it can be checked automatically → a rule in
  `tool/review_lint.py` (each rule runs on its own).
- Every review runs the lint plus the manual checklist.
- Examples from Shinphony: native plugins must be registered; no real host or user names in test data (also
  scanned before any public export); never bump build numbers with a blind `sed` (it once rewrote an id, so
  now a dedicated script does it).

## 7. State invariants + model-based tests (the fix for timing bugs)

- Timing problems (push vs snapshot vs tap vs clock, notifications, trial cadence, …) get **numbered rules
  first, tests second** (A1, LA3, ON7, …).
- A test = a small reference model + seeded random event sequences + every rule checked after every event.
  Seeds are fixed in CI; a failing sequence is shrunk automatically and kept as a named regression case.
- Three layers: pure model test → the real UI driven with fakes (clock, payments, network) → a device
  scenario script (named scenarios + `PHASE` marks, for recording).
- A regression found in the field: new rule id → a case in the generator → a line in the review rules.

## 8. Explain the number before trusting it

- Tests report **only new failures against a baseline** (the test-diff script), so old failures don't drown
  new ones.
- A wall-clock benchmark that fails in the full run is **rerun alone first**; it counts only if it also fails
  alone or a profile shows what got slower, and the explanation goes into the acceptance.
- When an external service errors, first check whether the service is down (e.g. App Store Connect 500/404)
  before "fixing" your own code.

## 9. Layered authorization

- **Standing authorizations** (the user says it once; it is recorded in memory): reviewed security releases,
  beta uploads, deploys of a given service.
- **Ask every time:** store submissions and releases, other production deploys, anything public or hard to undo.
- An authorization never extends to a different context. If the agent's safety mode refuses something, ask the
  user; don't work around it.

## 10. Hygiene (hard rules)

- Never print tokens, passwords or review credentials; read them inside scripts only.
- Redact host and user names in repo copies; fixtures use `example-*` hosts only.
- Delete directories only as `rm -rf "${D:?}"`; look at the target before deleting or overwriting.
- Don't change global toolchains or shared SDKs; ask the user to apply patches.
- Temporary LAN previews serve a copied folder only and are stopped after use; generated HTML always has
  `<meta charset="utf-8">`.

## 11. Scripted release pipeline

- Every outward step is a script that is read-only by default and writes only with explicit flags:
  `prepare (dry run) → --submit → --submit --final`.
- Build-number bumps use a dedicated script (only standalone numbers, never inside hex ids) and retry
  network steps.
- Website and app versions switch on gate variables ("show the new copy once the store shows the new
  version"), so changes can merge early and go live later.
- After a release, verify: live URLs, checksums, reproducible builds, the redaction scan of public exports.

## 12. Talking to the user

- Short replies, **action items first**, a TLDR in the user's language.
- Never predict the result of a background job before it finishes; list exactly what the user needs to do
  and test.
- When the user must run a command themselves, give it as a one-liner they can paste into the session.

---

### Starting a new project (templates in `templates/`)

1. Add `AGENTS.md` (the entry point), `DESIGN.md` (the design standard), `docs/review_rules.md` +
   `tool/review_lint.py`, `docs/design/state_invariants.md`.
2. Add the test-diff baseline script and a host render script (tier A).
3. Fix the IDs of dedicated devices / environments; give dev builds their own bundle id.
4. Decide the standing authorizations and the actions that always need asking; record them.
5. Run the first iteration end to end: plan → confirm → worker → tier A → review → PR merge → STATE.md.

`/pfstack` does steps 1, 3 and 4 for you and records the test baseline.

## Repository layout

```
README.md                         this file (English)
README.zh-CN.md                   Chinese version
install.sh                        clone/update + link the skill
templates/AGENTS.md               project entry point: roles, workflow, hard rules
templates/DESIGN.md               skeleton of the design source of truth
templates/docs/review_rules.md    review rules (manual + automatic)
templates/docs/design/state_invariants.md   invariant template (rule ids + event alphabet)
templates/docs/iterations/_example/         plan / implementation / acceptance / STATE templates
templates/tool/review_lint.py     rule-registry lint (each rule runs alone)
templates/tool/test_diff.sh       report only new failures against a baseline
templates/tool/next_build.py      build-number bump that never touches hex ids
templates/tool/model_check.py     tiny model-based testing harness: seeds, generator, per-step checks, shrinking
templates/tool/spawn_worker.sh    start an implementer worker in hc
skill/pfstack/                    the Claude Code / Codex skill (init / check / update) + CLI script
```

## Usage

**Recommended: the skill.** Install once (see above); it works in every project.

In a new project say `/pfstack` (or "set up pfstack in this project"). It lists the files it will add → asks,
in one message, for the project name, devices, authorizations, names that must never appear, and the test
command → copies the templates and fills the placeholders → creates `CLAUDE.md` (`@AGENTS.md`) → runs the
lint and records the test baseline → commits on a `pfstack-init` branch and asks before pushing. In an
existing project, `/pfstack check` lists what is missing and `/pfstack update` brings in newer templates
without overwriting your edits.

**Or use the CLI directly:**

```sh
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py init <dir> [--dry-run]
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py check <dir>
python3 ~/repos/pfstack/skill/pfstack/scripts/pfstack.py update <dir>
```

## License

MIT © 2026 Potafree LLC
