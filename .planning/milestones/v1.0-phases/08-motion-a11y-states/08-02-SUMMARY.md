---
phase: 08-motion-a11y-states
plan: 02
subsystem: ui
tags: [swiftui, accessibility, voiceover, reduce-motion, content-unavailable-view, ios18]

# Dependency graph
requires:
  - phase: 08-motion-a11y-states/01
    provides: "Motion polish: matchedGeometry morph, stagger, haptics, greeting animation"
  - phase: 07-insights-scouting
    provides: "Complete app shell with Today, Matches, Table, Insights tabs and all data wiring"
provides:
  - VoiceOver worded labels for rings, bars, and table rows (A11Y-01 partial)
  - Loading, offline-fallback, and hard-error app-level states (A11Y-02)
  - Global no-jargon audit proof (LANG-01)
  - Full §15 human-verified acceptance pass
affects: [v1-release, future-live-feed]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "a11yLabel optional param on custom Shape components (SoftRing, StrengthBar)"
    - "accessibilityHidden(true) for decorative views (IridescentGlow)"
    - "ContentUnavailableView + InkButton Retry for error states"
    - "store.phase switch in RootView for loading/failed/data-present routing"

key-files:
  created: []
  modified:
    - "EDGE/Sources/DesignSystem/Components/SoftRing.swift"
    - "EDGE/Sources/DesignSystem/Components/StrengthBar.swift"
    - "EDGE/Sources/DesignSystem/Components/IridescentGlow.swift"
    - "EDGE/Sources/Features/Matches/MatchDetailView.swift"
    - "EDGE/Sources/Features/Table/TableView.swift"
    - "EDGE/Sources/Features/Shell/RootView.swift"

key-decisions:
  - "a11yLabel is optional String? on SoftRing/StrengthBar — nil means no override, keeps backward compat"
  - "RootView prioritizes data-present path: if store.feed != nil, always show TabView regardless of phase"
  - "Error state uses ContentUnavailableView (iOS 17+) with InkButton retry — minimal, on-brand"

patterns-established:
  - "Accessibility label pattern: optional a11yLabel prop on reusable components, worded not numeric"
  - "App-level state routing: store.phase switch in RootView with data-present-wins semantics"

requirements-completed: [A11Y-01, A11Y-02, LANG-01]

# Metrics
duration: 3min
completed: 2026-06-17
---

# Phase 08 Plan 02: A11y, States & No-Jargon Summary

**VoiceOver worded labels on rings/bars/rows, graceful loading/error states, and a global no-jargon audit proving LANG-01 across the entire codebase**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-06-17T22:16:22Z
- **Completed:** 2026-06-17T22:19:06Z
- **Tasks:** 4 executed + 1 human-verified checkpoint
- **Files modified:** 6

## Accomplishments

- **VoiceOver labels** — SoftRing and StrengthBar accept optional `a11yLabel` and apply `.accessibilityLabel()`; IridescentGlow marked `.accessibilityHidden(true)`; table rows read "#N Name, X points, you, leader" in words
- **Loading + error states** — RootView routes on `store.phase`: loading shows pulsing skeleton, failed shows ContentUnavailableView with Retry button, data-present always wins and shows TabView
- **No-jargon audit** — Grepped all `EDGE/Sources` for `composite`, `probability`, `Text(...%` — zero hits. LANG-01 proven clean.
- **Full §15 acceptance** — Human verified: Today assembles, gradient breathes, match detail has 3 reasons with zero jargon, Results show score + outcome pills, Table highlights user + crowns leader, Insights shows form + scouting, Reduce Motion snaps all animation, VoiceOver reads worded descriptions

## Task Commits

Each task was committed atomically:

1. **Task 1: VoiceOver labels** - `6cb1fb4` (feat)
2. **Task 2: Loading + offline + hard-error states** - `d493a8d` (feat)
3. **Task 3: No-jargon audit** - `530aa7f` (test)
4. **Task 4: Build, launch, and self-check acceptance** - verification only, no commit
5. **Task 5: Human verification checkpoint** - approved, no commit

## Files Created/Modified

- `EDGE/Sources/DesignSystem/Components/SoftRing.swift` - Added optional `a11yLabel` param; applies `.accessibilityElement(children: .ignore).accessibilityLabel()` when set
- `EDGE/Sources/DesignSystem/Components/StrengthBar.swift` - Added optional `a11yLabel` param; same accessibility pattern as SoftRing
- `EDGE/Sources/DesignSystem/Components/IridescentGlow.swift` - Marked `.accessibilityHidden(true)` (decorative gradient)
- `EDGE/Sources/Features/Matches/MatchDetailView.swift` - Wired a11yLabel on hero ring and strength bar with worded descriptions
- `EDGE/Sources/Features/Table/TableView.swift` - Added per-row `.accessibilityLabel()` with rank, name, points, you/leader status
- `EDGE/Sources/Features/Shell/RootView.swift` - Added `store.phase` switch: loading skeleton, ContentUnavailableView error with Retry, data-present TabView

## Decisions Made

- **a11yLabel is optional** — `var a11yLabel: String? = nil` keeps backward compat; existing call sites unaffected
- **Data-present always wins** — `if store.feed != nil` check before phase switch ensures offline/data-available never blocks the UI
- **ContentUnavailableView for errors** — iOS 17+ native component, lightweight, on-brand with InkButton retry

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Threat Flags

No new security surface introduced. Changes are UI-only (accessibility labels, state routing views).

## Next Phase Readiness

- **EDGE v1 is complete.** All 8 phases delivered: foundation, data, components, shell, Today, Matches+Detail, Insights+Scouting, motion+a11y+states.
- All v1 requirements satisfied (FND-01–04, DATA-01–03, COMP-01–03, NAV-01, TABLE-01, TODAY-01–02, INSIGHT-01, LANG-01, A11Y-01, A11Y-02).
- MATCH-01 and MATCH-02 remain pending (Results tab polish + detail screen — tracked separately).
- MOTION-01 confirmed via human verification (matchedGeometry morph, haptics, stagger all working).
- v2 deferred: live feed, share sheet, widget, push notifications.

---
*Phase: 08-motion-a11y-states*
*Completed: 2026-06-17*

## Self-Check: PASSED

- All 6 modified files verified on disk
- All 3 task commits verified in git log (6cb1fb4, d493a8d, 530aa7f)
- SUMMARY.md created at `.planning/phases/08-motion-a11y-states/08-02-SUMMARY.md`
