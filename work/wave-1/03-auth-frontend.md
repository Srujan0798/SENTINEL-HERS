# TASK — wave-1 / 03-auth-frontend

## Goal
Login/logout UI + protected routing + role-aware nav, on the wave-0 design system.

## Context
- Wave: 1. Depends on wave-0 (design system) + consumes auth API contract.

## Write-set (ONLY these)
- src/frontend/app/(auth)/
- src/frontend/lib/auth.ts

## Forbid-set
- backend/**, src/frontend/ui/ (design-system primitives are frozen — consume, don't edit)

## Blast radius
r1.

## Steps
1. Login + register pages using shadcn primitives.
2. `lib/auth.ts`: token store, refresh, `useUser()` hook with role.
3. Route guard: unauthenticated → redirect `/login`; role-gated nav items hidden for viewer.

## Acceptance (PROOF — FM-09)
- Command: `cd src/frontend && npx playwright test e2e/login.spec.ts`
- Expected: login → dashboard redirect passes; protected route blocks logged-out user.

## Report to
`work/reports/wave-1/03-auth-frontend.report.md`
