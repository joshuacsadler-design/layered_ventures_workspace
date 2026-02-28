# workflow (global)

## core behavior
- automation-first: always look for ways to remove manual steps
- premium output: clean structure, deterministic pipelines, professional artifacts
- transparency: no false promises; verify when possible

## code change workflow (non-negotiable)
For ANY code edit request:
1) provide full-file paste of every modified file (no partial diffs)
2) include a git command chain for commit + push
3) verify/test each change before moving to the next change
4) keep changes minimal and scoped to the stated objective

## determinism + drift control
- originals are immutable (create new versions, never silently replace)
- no silent drift: changes must be logged as new events/versions
- prefer append-only logs and versioned constants for policies/rules

