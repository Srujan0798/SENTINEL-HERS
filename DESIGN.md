# DESIGN.md — SENTINEL visual system

> Impeccable init · Spacing, type, color, components.  
> Implement via `src/frontend/src/app/globals.css` + layout fonts.  
> Direction: **Radar Ops Console** — not generic black+neon SaaS.

---

## 1. Design thesis

The UI is a **mission console for production incidents**.  
Signature: **amber phosphor accents + ice data readouts + deep navy void** (radar/flight-deck vernacular), with **SEV1 red only when severity is real**.

Avoid: pure black + acid green templates; cream/serif “editorial AI”; purple gradients.

---

## 2. Color tokens

| Token | Hex | Role |
|-------|-----|------|
| `void` | `#070B14` | App background |
| `panel` | `#0F1629` | Cards / header surfaces |
| `panel-elevated` | `#162038` | Hover / elevated panels |
| `line` | `#243049` | Borders / hairlines |
| `ink` | `#E8EEF9` | Primary text |
| `ink-muted` | `#8B9BB8` | Secondary text |
| `phosphor` | `#E8A838` | Brand accent / primary actions |
| `ice` | `#6EC6FF` | Live data / links / SSE |
| `sev1` | `#FF3B5C` | Destructive / SEV1 only |
| `ok` | `#3DDC97` | Healthy / resolved |
| `warn` | `#F5C542` | SEV2 / warning |

### Mapping to shadcn CSS vars

| shadcn | Token |
|--------|--------|
| `--background` | void |
| `--foreground` | ink |
| `--card` | panel |
| `--primary` | phosphor |
| `--primary-foreground` | `#0B0F1A` |
| `--destructive` | sev1 |
| `--muted-foreground` | ink-muted |
| `--border` / `--input` | line |
| `--ring` | ice |
| `--accent` | panel-elevated |

---

## 3. Typography

| Role | Face | Use |
|------|------|-----|
| **Display / UI** | **Avenir Next / Segoe UI / system UI** | Headings, nav, buttons (no Google Fonts dependency — eternal builds) |
| **Data / mono** | **IBM Plex Mono → SF Mono → Consolas** | Timestamps, IDs, SLA countdown, logs, severity codes |

### Scale (rem @ 16px)

| Name | Size | Weight | Tracking |
|------|------|--------|----------|
| display | 1.75–2rem | 600 | -0.02em |
| title | 1.125–1.25rem | 600 | -0.01em |
| body | 0.875–0.9375rem | 400 | 0 |
| caption | 0.75rem | 500 | 0.04em uppercase for labels |
| mono-sm | 0.75–0.8125rem | 500 | 0 |

---

## 4. Spacing system (4px base)

| Token | px | Use |
|-------|-----|-----|
| `1` | 4 | Icon gaps |
| `2` | 8 | Compact control padding |
| `3` | 12 | Inline clusters |
| `4` | 16 | Card inner (compact) |
| `5` | 20 | — |
| `6` | 24 | Card padding default |
| `8` | 32 | Section gaps |
| `10` | 40 | Page vertical rhythm |
| `12` | 48 | Hero / empty states |

**Rules**
- Page container: `max-width` ~1280px, horizontal padding 16→24  
- Cards: 16–24 padding; gap between cards 16  
- Header height: 56–64px sticky  
- Never stack more than one full-width empty card without an action CTA  

---

## 5. Radius & elevation

| Element | Radius | Shadow |
|---------|--------|--------|
| Buttons / inputs | 6px | none / focus ring ice |
| Cards | 10px | `0 0 0 1px line`, soft glow on hover phosphor/5% |
| Badges / chips | 4px (square-ish ops) or full pill for status | none |
| Dialogs | 12px | deep void shadow |

---

## 6. Components

### Severity chips
- SEV1: sev1 bg / white text, subtle pulse if open  
- SEV2: warn  
- SEV3/4: ice/muted outline  

### SLA
- Within: ice mono countdown  
- Breached: sev1 mono **BREACHED** + remaining negative  

### Cards
- Title: caption uppercase tracking + title weight  
- Prefer dense data over large empty whitespace  

### Login
- Full-bleed void  
- Single card centered  
- Primary CTA: phosphor  
- Demo CTA: high contrast, one click to session  

---

## 7. Motion

| Motion | Spec |
|--------|------|
| SLA tick | 1s update, mono tabular nums |
| SEV1 badge | optional 2s opacity pulse; respect `prefers-reduced-motion` |
| Page load | no long choreography; content visible &lt;100ms after hydrate |
| Hover | border/line → ice 40%, 120ms ease |

---

## 8. Layout wireframe (war room)

```
┌─ SENTINEL ── nav ── SSE ── user ─┐
│ SEV1 title          [SLA mm:ss]   │
│ [Advance] [Assign] [Status]       │
├─────────────┬─────────────────────┤
│ List        │ AI summary / RCA    │
│ incidents   │ Timeline            │
│             │ Tasks               │
│             │ Comms               │
│             │ Chat                │
└─────────────┴─────────────────────┘
```

---

## 9. Accessibility floor

- Focus rings always visible (ice)  
- Contrast body text ≥ 4.5:1 on void  
- Reduced motion: disable pulse  
- Touch targets ≥ 36px on mobile nav  

---

## 10. Do / Don’t

| Do | Don’t |
|----|--------|
| Use phosphor sparingly for primary action | Neon green everywhere |
| Mono for times, IDs, SLA | Decorative serif headings |
| Honest empty states + next action | Fake KPI numbers |
| One signature (radar amber) | Three competing accent colors |

---

## 11. Implementation map

| File | Role |
|------|------|
| `src/frontend/src/app/globals.css` | Tokens + base |
| `src/frontend/src/app/layout.tsx` | Fonts Outfit + IBM Plex Mono |
| `src/frontend/src/app/(dashboard)/layout.tsx` | Shell / nav |
| `src/frontend/src/app/(auth)/login/page.tsx` | Entry experience |
