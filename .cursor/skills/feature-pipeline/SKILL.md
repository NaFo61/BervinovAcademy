---
name: feature-pipeline
description: >-
  Full feature workflow for Bervinov Academy: draft ТЗ, wait for APPROVED, then
  backend → frontend → tests → docs → deploy in order. Use when the user asks
  for a full feature, end-to-end implementation, or ТЗ-first delivery.
---

# Feature pipeline

Orchestrates specialists. Stay in the current phase until the gate passes.

## Phase 0 — Scope

Confirm the feature in 1–2 sentences. If unclear, ask one short question.

## Phase 1 — ТЗ only

Create/update `docs/specs/<slug>.md`:

1. Goal / user value
2. User stories + acceptance criteria
3. API contract (paths, fields, errors)
4. DB / migrations
5. UI (screens, states)
6. Test plan
7. Deploy impact (env, CI, compose) or "none"
8. Out of scope

**STOP.** Do not write product code until the user writes `APPROVED` (or clearly confirms the ТЗ).

## Phase 2 — Backend

Apply skill `backend-agent` against the approved ТЗ. Run focused pytest. Report endpoints ready for UI.

## Phase 3 — Frontend

Apply skill `frontend-agent`. Wire only approved API. Report routes to click-test.

## Phase 4 — Docs

Update only docs that the change requires (spec status, README snippet, API notes). No fluff.

## Phase 5 — Deploy (if needed)

Apply skill `deploy-agent` only if ТЗ marked deploy impact. Prefer `restart.sh` path; never `full-restart` without explicit ask.

## Done checklist

- [ ] Acceptance criteria covered
- [ ] Tests for backend changes
- [ ] Frontend uses shared API helpers
- [ ] No secrets committed
- [ ] Deploy notes (if any) handed to user

Do not commit or push unless the user asks.
