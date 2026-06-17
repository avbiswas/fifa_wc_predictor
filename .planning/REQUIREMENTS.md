# Requirements: EDGE — iOS App

**Defined:** 2026-06-17
**Core Value:** On open, in one glance, Niko knows what to tip tonight and why — in plain language — in a UI that needs no manual.

> Source of truth for all implementation detail: `docs/ios_app_plan.md`. Each requirement cites the
> section that pins it down. Requirements are deliberately observable/testable so the verifier can
> confirm them.

## v1 Requirements

### Foundation

- [x] **FND-01**: App "EDGE" builds and launches on iOS 18 in **light mode only** (spec §2)
- [x] **FND-02**: Design tokens (colors, spacing, radii, typography) exist in one place — `Theme`/`Font` — and are the only color/font source (spec §5.1, §5.2)
- [x] **FND-03**: The iridescent gradient background renders and **continuously breathes** (blobs drift/scale via `TimelineView`) (spec §5.3)
- [x] **FND-04**: Any view can enter with the **generative blur-to-focus stagger** via a reusable `.generativeAppear(index:)` modifier (spec §5.4)

### Data

- [x] **DATA-01**: App decodes the bundled `SampleFeed.json` into typed `Codable` models with **zero network**, exposing Niko = rank 8 / 18 pts and 9 table rows (spec §4.1, §4.2, §18)
- [x] **DATA-02**: A single `AppStore` (`ObservableObject`) exposes the feed and a `generation` counter that **increments on refresh** (spec §4.3)
- [x] **DATA-03**: `Format` helpers convert tier/leverage/outcome/strength to words + soft colors and exact-chance to "1 in N" (spec §6)

### Components

- [x] **COMP-01**: `FrostCard`, `SoftRing` (draws on appear), `StrengthBar` (fills on appear), `GapRail` (marker slides in) render per spec (§5.5–5.8)
- [x] **COMP-02**: `SoftPill`, `InkButton` (+`PressScale`), `MovementArrow`, `TeamBadge` render per spec (§5.9–5.12)
- [x] **COMP-03**: `GeneratedStatus` (pulsing spark), `Sparkline`, `Eyebrow` render per spec (§5.13–5.15)

### Navigation

- [x] **NAV-01**: A 4-tab shell with a **floating frosted tab bar** switches Today / Matches / Table / Insights, with a light haptic on switch (spec §7.1)

### League Table

- [x] **TABLE-01**: The Table tab lists all 9 players ranked, **highlights the user's row** (iridescent), crowns the leader, and shows a movement arrow per row (spec §7.5)

### Today Briefing

- [x] **TODAY-01**: Today shows greeting + standing (rank, "6 behind Alex", gap rail), tonight's plan, and the next-match spotlight (spec §7.2)
- [x] **TODAY-02**: Today **assembles itself** top-to-bottom on open and **replays the assembly on pull-to-refresh** (status flips to "Generating your briefing…") (spec §7.2, §8)

### Matches & Detail

- [ ] **MATCH-01**: The Matches tab shows **Upcoming** and **Results** in a segmented control; results show the actual score + a soft outcome pill (Spot on +4 / Missed) (spec §7.3, §11)
- [ ] **MATCH-02**: Tapping a match opens a **detail** with the score ring, 3 plain-English reasons, the matchup strength bar, "the room" leverage view, and alternate scores (spec §7.4)

### Insights & Scouting

- [x] **INSIGHT-01**: The Insights tab shows engine form metrics (24 / 1.5 / 4 / 8-of-16) + a sparkline, and a **scouting card per friend** (tag, blurb, 3 trait level bars) (spec §7.6, §7.7)

### Human Language (cross-cutting)

- [x] **LANG-01**: **No raw probability, "%", `composite_score`, or `expected_points`** appears as text anywhere; every number is a word, ring, bar, or soft-colored pill (spec §0, §6) — audited globally in Phase 8

### Motion & Accessibility

- [ ] **MOTION-01**: Rings draw, bars/rails fill, cards stagger, and the match card → detail **ring morphs** (matchedGeometry); tab-switch and card-press haptics fire (spec §8)
- [x] **A11Y-01**: **Reduce Motion** snaps every animation to final state and pauses the gradient; VoiceOver reads worded labels for rings/bars/rows (spec §9)
- [x] **A11Y-02**: Loading / per-section empty / offline-fallback / hard-error states render gracefully and never block when any data exists (spec §10)

## v2 Requirements

### Live Data
- **LIVE-01**: App fetches a fresh `app_feed.json` from a URL and falls back to bundled data offline
- **LIVE-02**: A `scripts/build_app_feed.py` pipeline generates the feed from the engine reports (spec §16)

### Enhancements
- **ENH-01**: Match-detail share sheet
- **ENH-02**: Home-screen widget showing standing + next pick
- **ENH-03**: Push notification before each kickoff ("pick locks in 30 min")

## Out of Scope

| Feature | Reason |
|---------|--------|
| Dark mode | Aesthetic is light; dark dilutes fidelity |
| Chat / Ask bar | User chose structured dashboard, not conversational |
| Auth / accounts | Single-user personal app; no need |
| In-app 3D scene | Marketing-only; evoked via gradient + frosted depth |
| Third-party packages / Swift Charts | Keep dependency-free; viz hand-rolled for control |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FND-01 | Phase 1 | Complete |
| FND-02 | Phase 1 | Complete |
| FND-03 | Phase 1 | Complete |
| FND-04 | Phase 1 | Complete |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 2 | Complete |
| DATA-03 | Phase 2 | Complete |
| COMP-01 | Phase 3 | Complete |
| COMP-02 | Phase 3 | Complete |
| COMP-03 | Phase 3 | Complete |
| NAV-01 | Phase 4 | Complete |
| TABLE-01 | Phase 4 | Complete |
| TODAY-01 | Phase 5 | Complete |
| TODAY-02 | Phase 5 | Complete |
| MATCH-01 | Phase 6 | Pending |
| MATCH-02 | Phase 6 | Pending |
| INSIGHT-01 | Phase 7 | Complete |
| MOTION-01 | Phase 8 | Pending |
| LANG-01 | Phase 8 | Complete |
| A11Y-01 | Phase 8 | Complete |
| A11Y-02 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-17*
*Last updated: 2026-06-17 after Phase 05 completion*
