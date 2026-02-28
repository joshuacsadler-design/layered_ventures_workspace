# LV Operator Framework — Hardening Plan v1 (A)

## Goal
Make continuity + orchestration verifiable, tamper-evident, and self-repairable.

## A1) Registry validation (non-fatal)
Validate at runtime:
- file exists + parseable JSON
- version present
- projects[] array present
- each project has: id, path, enabled (bool), type
- enabled projects resolve to existing paths

Output:
- warnings into ops logs
- snapshot.json includes validation result summary

## A2) Tamper evidence
Already present:
- registry_hash in snapshot

Add:
- snapshot_hash (sha256 of snapshot.json)
- prev_snapshot_hash in new snapshot
- chain_valid boolean

No secrets stored.

## A3) Self-repair hints
If task missing or wrong:
- write REPAIR.md into ops/ops/logs/capsule_tick_all/latest/
- include exact installer command:
  pwsh -NoProfile -ExecutionPolicy Bypass -File <ops>\tools\install_lv_capsule_tasks.ps1 -LvRoot <lv_root>

## Definition of Done
- Any operator can prove system integrity from disk alone.
- Drift produces explicit artifacts (already).
- Repair steps are printed and written to disk.

--- end ---
