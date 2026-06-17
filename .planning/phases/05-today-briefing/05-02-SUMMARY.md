---
phase: 05-today-briefing
plan: 02
subsystem: ui
tags: [swiftui, generative-appear, spotlight, countdown, match-detail, navigation, refresh-replay]

# Dependency graph
requires:
  - phase: 05-today-briefing
    plan: 01
    provides: TodayView scaffold (status, greeting, standing, plan cards)
  - phase: 03-components
    provides: SoftRing, StrengthBar, SoftPill, Eyebrow, FrostCard, InkButton
provides:
  - CountdownPill (frosted countdown capsule)
  - MatchDetailView stub (Phase 6 replaces)
  - Spotlight + picks list + navigation in TodayView
  - Refresh replays assembly with generating status
affects: [06-matches-detail]

# Tech tracking
tech-stack:
  added: []
  patterns: [NavigationLink(value:) with String IDs, CountdownPill with Format.countdown, pull-to-refresh generating state flip]

key-files:
  created:
    - EDGE/Sources/DesignSystem/Components/CountdownPill.swift
    - EDGE/Sources/Features/Matches/MatchDetailView.swift
  modified:
    - EDGE/Sources/Features/Today/TodayView.swift

key-decisions:
  - "NavigationLink uses String values (match.id) rather than Match: Hashable conformance"
  - "MatchDetailView is a stub; Phase 06-02 replaces it with full detail screen"
  - "Generating state toggles on refresh start/end and passes to GeneratedStatus"
  - "Empty state shows a FrostCard with calendar glyph when no upcoming matches"

patterns-established:
  - "NavigationLink(value: String) + .navigationDestination(for: String.self) pattern"
  - "CountdownPill as reusable frosted capsule for countdowns"
  - "Spotlight card pattern: FrostCard with eyebrow, countdown, teams, ring, strength bar, tier/leverage pills, ink CTA"

requirements-completed: [TODAY-01, TODAY-02]

# Metrics
duration: 3min
completed: 2026-06-17
---

# Phase 5 Plan 02: Today Briefing Lower Half Summary

**CountdownPill component, next-match spotlight with pick ring + strength bar, today's other picks list, navigation to match detail stub, and refresh replays assembly with generating status**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-17T16:57:47Z
- **Completed:** 2026-06-17T17:00:19Z
- **Tasks:** 5 (+ 1 human-verify checkpoint)
- **Files modified:** 3

## Accomplishments

- Created CountdownPill — a frosted Capsule with ultraThinMaterial, Theme.spark dot, and monospaced countdown text
- Created MatchDetailView stub with team badges, pick score ring, tier pill, and "Full detail in Phase 6" note
- Added next-match spotlight to TodayView: FrostCard with eyebrow, countdown, teams, SoftRing, StrengthBar, tier/leverage pills, and "Why this pick →" ink CTA
- Added today's other picks list with NavigationLink rows showing teams, score, and tier dot
- Added .navigationDestination(for: String.self) routing match IDs to MatchDetailView
- Wired pull-to-refresh with generating state flip — "Generating your briefing…" shows during refresh
- Full assembly replay on refresh via .id(store.generation) remount
- Launched on simulator and verified via human checkpoint — APPROVED

## Task Commits

Each task was committed atomically:

1. **Task 1: CountdownPill component** - `c6d96c4` (feat)
2. **Task 2: MatchDetailView stub** - `f25c3f8` (feat)
3. **Task 3: Spotlight + other picks + navigation** - `da2f19f` (feat)
4. **Task 4: Refresh replays assembly + generating status** - `63779f1` (feat)
5. **Task 5: Launch Today on simulator** - (verified, no separate commit)
6. **Task 6: Human verification checkpoint** - APPROVED

## Files Created/Modified

- `EDGE/Sources/DesignSystem/Components/CountdownPill.swift` — Frosted countdown capsule (created)
- `EDGE/Sources/Features/Matches/MatchDetailView.swift` — Match detail stub for navigation (created)
- `EDGE/Sources/Features/Today/TodayView.swift` — Spotlight, picks list, navigation, refresh replay (modified)

## Decisions Made

- NavigationLink uses String values (match.id) rather than making Match conform to Hashable — simpler, no coupling
- MatchDetailView is explicitly a stub; Phase 06-02 will replace it with the full detail screen using the same initializer signature
- Empty state for no upcoming matches uses a FrostCard with calendar glyph — matches the opalescent design system
- Generating state is a simple @State bool that flips on refresh start/end

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Known Stubs

- `MatchDetailView` is a stub showing teams + ring + "Full detail in Phase 6". Phase 06-02 replaces with full implementation.

## Next Phase Readiness

- Today screen is fully complete: upper half (status, greeting, standing, plan) + lower half (spotlight, picks list)
- Self-assembly animation and refresh replay working end-to-end
- Navigation to MatchDetailView stub ready — Phase 06-02 replaces with full detail
- CountdownPill available as reusable component for Phase 06 matches screen

## Self-Check: PASSED

- ✅ CountdownPill.swift exists
- ✅ MatchDetailView.swift exists
- ✅ TodayView.swift modified
- ✅ Commit c6d96c4 found (Task 1)
- ✅ Commit f25c3f8 found (Task 2)
- ✅ Commit da2f19f found (Task 3)
- ✅ Commit 63779f1 found (Task 4)
- ✅ SUMMARY.md exists

---

*Phase: 05-today-briefing*
*Completed: 2026-06-17*
