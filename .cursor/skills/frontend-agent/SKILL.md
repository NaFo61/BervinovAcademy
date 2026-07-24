---
name: frontend-agent
description: >-
  Implements Bervinov Academy frontend SPA — React CDN pages, hash routes,
  shared.jsx API helpers, Tailwind. Use when the user asks for frontend, UI,
  React pages, catalog/learn/auth screens, or changes under frontend/.
---

# Frontend agent

You own **frontend only**: `frontend/**`. Do not edit backend or deploy unless the user asks.

## Workflow

1. Read `frontend/src/shared.jsx` and an existing similar page before coding.
2. Implement UI using existing patterns (CDN React, `window` exports, hash routes).
3. Wire routes in `shared.jsx` + `app.jsx`; register scripts in `index.html` for new pages.
4. Call APIs only via `fetchApiJson` / `apiJson` / `fetchApiForm` from `shared.jsx`.
5. Keep mobile + desktop usable; match existing visual language (no Vite migration).
6. Summarize: pages/routes touched, API calls used, how to verify (`npm run dev` on 3000).

## New page checklist

- [ ] `frontend/src/<page>.jsx` exports to `window`
- [ ] Script tag in `frontend/index.html` (`text/babel`)
- [ ] Route in `shared.jsx` `Routes`
- [ ] Render branch in `app.jsx`
- [ ] Uses shared API helpers + existing auth/token flow

## Conventions (enforce)

- Hash routing only (`#/...`)
- Absolute `/api/...` paths
- No parallel fetch/auth layer
- Do not introduce Vite/webpack/TanStack Router for the live SPA

## Out of scope

- Django models/viewsets, migrations, pytest
- `deploy/**`, Docker Hub, CI
- Committing without user ask

## If the API is missing

List required endpoints/fields for the backend agent. Do not invent fake backend files.
