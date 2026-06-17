# EDGE — iOS App

## What This Is

EDGE is a light, opalescent iOS app (SwiftUI, iOS 18+) that turns the KickTipp exploit engine's
JSON into a glanceable, **self-assembling** dashboard for winning Niko's 9-person World Cup 2026
prediction league. It shows where Niko stands, what to tip tonight and *why* in plain language,
what already happened (scores + points), and how to beat each specific friend. v1 runs **fully
offline** from a bundled `SampleFeed.json`.

The complete, implementation-ready specification lives at **`docs/ios_app_plan.md`** — it is the
single source of truth for the data contract, design system (with full SwiftUI component code),
human-language rules, screens, and motion. This milestone packages that spec into executable GSD
phases.

## Core Value

On open, in one glance, Niko knows exactly what to tip tonight and why — in plain language —
inside a UI so beautiful and self-explanatory it needs no manual. **If everything else fails, the
Today screen must look stunning and be instantly understandable.**

## Requirements

### Validated

(None yet — ship to validate)

### Active

<!-- Hypotheses until shipped. Full testable list in REQUIREMENTS.md. -->

- [ ] App launches offline (bundled JSON), light-mode, with the iridescent gradient breathing
- [ ] Every screen assembles itself with the generative blur-to-focus stagger
- [ ] Four tabs — Today, Matches, Table, Insights — plus a pushed Match Detail
- [ ] Every number is shown as a word, ring, bar, or soft-colored pill (no raw %, no jargon)
- [ ] Design + motion match the "agentic gen UI" aesthetic exactly (the top priority)

### Out of Scope

- Live/remote data feed — deferred to v2; v1 ships the bundled `SampleFeed.json` (keeps the app
  simple, testable, and demoable with zero backend).
- Chat / Ask bar / conversational navigation — user chose "aesthetic + animations only" on a
  structured 4-tab dashboard.
- Dark mode — the aesthetic is light; building dark would dilute fidelity.
- 3D rendered scene inside the app — that's marketing; we evoke it with the gradient + frosted depth.
- The Python `build_app_feed.py` pipeline — spec'd in `docs/ios_app_plan.md` §16 for a later milestone.
- Auth, push notifications, settings, sharing, widgets — not needed for v1.

## Context

- **Source of truth:** `docs/ios_app_plan.md` (this repo). Every phase references it by section.
- **Aesthetic reference:** glebich "agentic gen UI" concept (light, opalescent, frosted glass,
  thin type, generative self-assembly motion, single black CTA pill). We could not fetch the
  source video (paywalled) — the aesthetic is derived from supplied frames and pinned exactly in
  the spec's design system (§5) and motion (§8).
- **Real data baked into the sample:** current league has Niko 8th of 9 (18 pts), leader Alex
  (24 pts), 9 players; tonight has 12 matches; engine form is 24 pts / 1.5 avg / 4 exact in 16.
- **Executor calibration:** plans are written so a low-capability coding model (e.g. Haiku) can
  execute each task with zero ambiguity — concrete file paths, exact code references into the
  spec, and grep-verifiable acceptance criteria.
- **Location:** the app is a new greenfield Xcode project in the `EDGE/` subdirectory of this repo
  (the rest of the repo is the Python engine that produces the data; it is not a build dependency).

## Constraints

- **Tech stack**: Swift 5.9+, SwiftUI, **iOS 18.0+**, **light mode only**. No third-party packages.
  Icons = SF Symbols. All data-viz (rings, bars, gradient) hand-rolled with `Shape`/`Canvas`/
  `TimelineView`. — Matches the spec; keeps it dependency-free and fully controllable.
- **Design fidelity**: the opalescent aesthetic + the generative animations are the **highest
  priority** and must match `docs/ios_app_plan.md` §1/§5/§8 exactly. — This is the whole point.
- **Data**: v1 reads only the bundled `SampleFeed.json`; no network calls. — Offline-first, demoable.
- **No-jargon rule**: no raw probabilities, "%", `composite_score`, or `expected_points` as text
  anywhere. — Core UX doctrine (spec §0/§6).
- **Tooling**: Xcode build/run + simulator. Plans must remain valid for `/gsd-execute-phase`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Light, opalescent "agentic gen UI" aesthetic (not dark) | Corrected from glebich reference frames; this is the look the user wants | — Pending |
| Scope = aesthetic + animations on a structured 4-tab dashboard (no chat/Ask bar) | User choice; keeps dense data glanceable while keeping the wow motion | — Pending |
| iOS 18 minimum (MeshGradient + modern APIs), blurred-blob fallback documented | Mesh gradient nails the opal look; 2026 baseline is safe | — Pending |
| v1 data = bundled SampleFeed.json; live feed deferred | Zero backend → simple, testable, perfect for handoff to a small model | — Pending |
| App lives in `EDGE/` subdir of the Python repo | Keeps engine + app together; app is greenfield, not coupled to Python | — Pending |
| Author all plans at Opus fidelity rather than via cold sub-agents | Spec is complete in-context; maximizes per-phase detail for a Haiku executor | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-17 after initialization*
