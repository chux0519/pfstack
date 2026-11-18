# Review rules

Pitfalls we have hit. `R*` rules are checked by `tool/review_lint.py` (run one with
`python3 tool/review_lint.py R01`); `M*` rules are checked by reading.

| Id | Rule | Why (the incident) |
|---|---|---|
| R01 | No real host or user names in tests and fixtures; use `example-*`. | A public export leaked a machine name. |
| R02 | `rm -rf` only as `rm -rf "${VAR:?}"`. | An empty variable must never delete `/`. |
| M01 | Timing claims need a recording cut at stable frames, not one screenshot after the action. | A transient state was reported as a persistent failure. |
| M02 | Build-number bumps go through `tool/next_build.py`, never a blind `sed`. | A sed rewrote a hex id that contained the number. |
