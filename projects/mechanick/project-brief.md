# project-brief: mechanick

## purpose
AI diagnostic program that can ingest schematics/live data/service info/web sources; produce pinpoint tests or dispatch.

## current state
Spec-heavy and architecture shaping; requires strict determinism/auditability.

## definitions
- done means: CaseVault + PatternIndex workflow is deterministic and auditable.

## stack / tools
MySQL (per heidisql usage), future services for ingestion + evidence hashing.

## repos / paths
- folder: projects/mechanick

## non-negotiables
- append-only CaseVault concepts
- provenance, hashing, auditability
- privacy boundary for PII/VIN

## top priorities
1) formalize minimal working data model
2) ingestion adapters + fallbacks strategy
3) ops logging and runbooks
