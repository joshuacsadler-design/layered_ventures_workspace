# decision-log

## 2026-02-28
- decision: lv_ops is the shared operational brain used by every project UI.
  reason: continuity + auditability without relying on chat history.
  scope: global

- decision: global naming is linux-safe lowercase with hyphen/underscore only.
  reason: cross-platform stability and automation friendliness.
  scope: global

- decision: code edits require full-file pastes + git commit/push chain + verification.
  reason: prevent partial edits and regression drift.
  scope: global

