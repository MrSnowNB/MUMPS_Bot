# Dependency Graph Audit — Open Ticket Review

> Authored: 2026-04-11
> Status: **PENDING APPROVAL** — no ticket YAMLs have been changed yet.
> See "Approval Proposal" below for the exact change set awaiting sign-off.

---

## Summary

I audited the open ticket files and the main issue is now clear: the dependency
graph is mostly authored correctly, but it mixes two YAML styles, and that is
what created the earlier confusion. The recent `next_ticket.py` fix addressed
inline-list parsing and output handling, but many tickets are authored with
block-list `depends_on` entries rather than inline lists, so consistency is
still worth enforcing.

---

## Findings

The queue is **not** universally missing dependencies. BOOT, PIPE, and SMOKE
tickets already have explicit inline dependencies:

- `BOOT-T03 -> [BOOT-T01]`
- `PIPE-T01 -> [SMOKE-T01, BOOT-T03]`
- `PIPE-T07 -> [BOOT-T02, PIPE-T01, PIPE-T02, PIPE-T04, PIPE-T05, PIPE-T06]`

Several BUILD, FIX, HARN, MUM, and ROOK tickets also declare dependencies,
but many of those are written in **block-list form** instead of inline form,
which makes the repo harder to audit consistently.

---

## Required Adjustments

### Mandatory — YAML Normalization

Convert every `depends_on` field to a single inline style:

```yaml
# Good
depends_on: [BUILD-T01]
depends_on: [PIPE-T02, PIPE-T03]
depends_on: []
```

This should be applied to **all open ticket YAMLs** so the dependency graph is
visually uniform and easy to diff.

### Optional — Logic Corrections

These tickets are structurally suspicious and should be reviewed before approval
because they are currently root-ready or lightly gated when they may deserve
stronger sequencing:

| Ticket family | Current concern |
|---|---|
| **BUILD-*** | BUILD-T01 is root (fine), but BUILD-T04/T05/T06 depend on tools that Phase 1 currently forbids — these may need re-sequencing or temporary retirement. |
| **FIX-*** | FIX-T02 and FIX-T04 are root tickets; that may be intentional, but they read like post-build integrity checks and may belong after more harness work. |
| **MUM-*** | The chain is partial, but MUM-T05 depends only on MUM-T01 even though its title says it audits completed T01–T04; it should likely depend on MUM-T04 at minimum. |
| **ROOK-*** | ROOK-T07 currently depends on ROOK-T06, but if it emits typed stubs and writes ATA output, it may also need ROOK-T03, ROOK-T04, and ROOK-T05 closed first. |
| **VISTA-T01** | Depends on PIPE-T07 (sensible), but if VistA execution also needs BUILD validation and smoke confirmation, explicit additional dependencies may be warranted. |

---

## Approval Proposal

Recommended two-phase approach:

### Phase A — Normalize YAML Only
No semantic changes. Rewrite every `depends_on` to inline list form across all
open ticket YAMLs.

### Phase B — Correct Dependency Logic
Make the following targeted changes after Phase A:

1. **MUM-T05** — change `depends_on: [MUM-T01]` → `depends_on: [MUM-T04]`
2. **ROOK-T07** — review whether it should depend on `[ROOK-T06]` only, or
   on `[ROOK-T03, ROOK-T04, ROOK-T05, ROOK-T06]`
3. **BUILD-T04 / BUILD-T05 / BUILD-T06** — review whether these should remain
   open in the current phase given the Phase 1 forbidden-tool policy
4. **FIX-T02 / FIX-T04** — confirm root status is intentional; if not,
   add appropriate upstream gates

Tickets to leave unchanged unless stricter gating is requested:
`BOOT-*`, `PIPE-*`, `SMOKE-*`, `HARN-*`

---

## Next Step

**Awaiting approval to proceed.**
If approved, Phase A and Phase B changes will be made in one commit each,
clearly labeled, with no other modifications.
