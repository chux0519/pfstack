---
name: pfstack
description: Set up or check potafree stack (pfstack) agent-development practices in a project. Use when the user says "pfstack", "/pfstack", "set up pfstack", "按 pfstack 开始", or starts a new project and wants the AGENTS.md / DESIGN.md / review rules / state invariants / iteration workflow / lint and test-diff tooling. Subcommands - init (default in a project without AGENTS.md), check (default when AGENTS.md exists), update (pull newer templates without overwriting edits).
---

# pfstack

The practices are in `../../README.md` relative to this file (the pfstack repo; `README.zh-CN.md` is the Chinese version). Templates are in
`../../templates/`. Read the README once before acting, then follow the subcommand below.
Talk to the user in their language; short, action items first.

## init — set up a project

1. Confirm the target directory (default: current working directory) is a git repo. If not, ask before
   `git init`.
2. Run `python3 <skill>/scripts/pfstack.py init <dir> --dry-run` and show the user the file list. Files that
   already exist are never overwritten (reported as "kept").
3. Ask the user, in one message, only what you cannot infer from the repo:
   - project name and one-line purpose;
   - platforms and the dedicated devices / environments (simulator UDIDs, staging URLs), if any;
   - standing authorizations (what may be done without asking) and what must always be asked;
   - names that must never appear in the repo (machine names, user names, internal domains);
   - the test command and how a failing test line looks (offer a guess from package.json / pubspec / go.mod
     / pyproject).
4. Run `python3 <skill>/scripts/pfstack.py init <dir>` to copy the templates, then fill the `<placeholders>`
   in AGENTS.md, DESIGN.md §1, `tool/review_lint.py` FORBIDDEN_NAMES and `tool/test_diff.sh` defaults with the
   answers. Create `CLAUDE.md` containing `@AGENTS.md` if it does not exist (append the line if it exists).
5. Run `python3 tool/review_lint.py` and `bash tool/test_diff.sh --update` on a clean tree to record the
   baseline (ask first if the test suite is slow or touches anything external).
6. Run `check`, commit on a branch `pfstack-init`, and offer to push and open a PR. Never push without a yes.
7. Tell the user how to start the first iteration: "按 pfstack 开始：先写计划给我确认".

## check — what is missing or drifted

Run `python3 <skill>/scripts/pfstack.py check <dir>` and report its list: missing files, placeholders still
unfilled, CLAUDE.md not importing AGENTS.md, lint or baseline missing, iterations without STATE.md. Offer to
fix each item; fix nothing without asking.

## update — newer templates

`python3 <skill>/scripts/pfstack.py update <dir>` writes `<file>.pfstack-new` beside every template file that
changed upstream and differs locally. Show the diffs, merge with the user, delete the `.pfstack-new` files.

## Rules while using this skill
- Never overwrite an existing file without showing the diff and getting a yes.
- Never print secrets; never put real host or user names into templates or examples.
- `rm` only as `rm -rf "${VAR:?}"`.
