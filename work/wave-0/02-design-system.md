# TASK — wave-0 / 02-design-system

## Goal
Establish the shared Next.js + Tailwind + shadcn design system so every UI task looks coherent (UI/UX 10%).

## Context
- Wave: 0. Disjoint write-set from 00 and 01 — safe to run in parallel.
- Theme: dark, ops-console aesthetic. Severity colour tokens SEV1=red, SEV2=orange, SEV3=amber, SEV4=blue.

## Write-set (ONLY these)
- src/frontend/ui/        (shadcn components, primitives)
- src/frontend/theme/     (tailwind config, tokens, severity palette)
- docs/flows/design-system.md

## Forbid-set
- backend/**, schema/**, docker-compose.yml, feature pages (other waves own those)

## Blast radius
r1.

## Steps
1. Init Next.js 15 app router + Tailwind + shadcn; install base components (button, card, badge, dialog, table, toast).
2. Define severity + status colour tokens and a `<SeverityBadge>` + `<StatusPill>` primitive.
3. Build a component gallery page (`/_gallery`) showing every primitive.
4. Document usage in `docs/flows/design-system.md`.

## Acceptance (PROOF — FM-09)
- Command: `cd src/frontend && npm run build`
- Expected: build succeeds; `/_gallery` renders all primitives with severity colours.

## Report to
`work/reports/wave-0/02-design-system.report.md`
