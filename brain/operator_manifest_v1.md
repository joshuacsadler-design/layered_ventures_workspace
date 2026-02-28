# Layered Ventures — Operator Manifest v1.0

## 1. Authority Structure
Layered Ventures (LV) is an Operator-Governed Multi-Entity Infrastructure System.
Primary Operator: Joshua Sadler
All AI outputs are advisory unless committed into repository state.

## 2. System Philosophy
1. Determinism over convenience
2. Infrastructure before expansion
3. Automation over repetition
4. Versioned truth over conversational memory
5. Security before exposure

## 3. Canonical Sources of Truth
- workspace/projects/projects-registry.json
- ops/capsules/* (latest per project)
- workspace/brain/operator_manifest_v1.md
- git history per repository

If conflict occurs: Git + manifest override conversation.

## 4. Capsule Protocol
Autosave interval: 5 minutes
Scheduler: schtasks
Universal runner: lv_capsule_tick_all.ps1
Capsules are append-only and immutable once committed.

## 5. Operator Boot Sequence
1. Read operator_manifest_v1.md
2. Read projects-registry.json
3. Read active capsule
4. Confirm objective
5. Proceed

## 6. Framework Intent Declaration
Layered Ventures is both an operating entity and a reference implementation of the LV Operator Framework.

Infrastructure must be:
- Portable
- Parameterized
- Environment-agnostic
- Reproducible on blank machine

## 7. Template Extraction Rules
Before feature maturity:
- Decouple from personal identity
- Remove machine-bound logic
- Make config-driven
- Document boundaries

If it cannot be cleanly reinstalled on a blank machine, it is not complete.

--- End of Manifest v1 ---
