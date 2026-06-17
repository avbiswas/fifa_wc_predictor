---
phase: 08-motion-a11y-states
plan: 01
subsystem: ui
tags: [swiftui, ios18, haptics, animation, navigation-transition, matched-geometry]

# Dependency graph
requires:
  - phase: 06-matches-detail
    provides: MatchDetailView with full detail layout
  - phase: 05-today-briefing
    provides: TodayView with spotlight and greeting
provides:
  - iOS 18 zoom navigation transition (card → detail morph)
  - Success haptic feedback on "Spot on" results
  - Word-by-word greeting animation
affects: [08-motion-a11y-states]

# Tech tracking
tech-stack:
  added: [navigationTransition(.zoom), matchedTransitionSource, UINotificationFeedbackGenerator]
  patterns: [per-word generativeAppear stagger, namespace-based zoom transitions]

key-files:
  created: []
  modified:
    - EDGE/Sources/Features/Matches/MatchesView.swift
    - EDGE/Sources/Features/Matches/MatchDetailView.swift
    - EDGE/Sources/Features/Today/TodayView.swift

key-decisions:
  - "Used iOS 18 navigationTransition(.zoom) instead of matchedGeometryEffect for cross-push morph (reliable across NavigationStack)"
  - "Added optional ns parameter to MatchDetailView to keep it working in previews when namespace is nil"
  - "Used helper extension applyZoomTransition(ns:matchID:) for clean conditional zoom modifier"

patterns-established:
  - "Namespace-based zoom transitions: @Namespace on source view, passed to destination via parameter"
  - "Per-word generativeAppear: split text into words, each with .generativeAppear(base + index)"

requirements-completed: [MOTION-01]

# Metrics
duration: 6min
completed: 2026-06-17
---

# Phase 8 Plan 01: Motion Polish Summary

**iOS 18 zoom morph from match cards to detail, success haptic on exact-score results, and word-by-word greeting assembly animation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-17T20:04:35Z
- **Completed:** 2026-06-17T20:11:04Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Zoom navigation transition wired across MatchesView, TodayView → MatchDetailView using iOS 18 APIs
- Success haptic fires when opening a "Spot on" (exact) result detail
- Greeting animates word-by-word with proper stagger sequencing

## Task Commits

Each task was committed atomically:

1. **Task 1: Zoom transition (card → detail morph)** - `b3e3a14` (feat)
2. **Task 2: Success haptic on Spot-on result** - `97bab4d` (feat)
3. **Task 3: Word-by-word greeting build** - `d574239` (feat)

## Files Created/Modified
- `EDGE/Sources/Features/Matches/MatchesView.swift` - Added @Namespace and matchedTransitionSource on match card NavigationLinks, pass ns to detail
- `EDGE/Sources/Features/Matches/MatchDetailView.swift` - Added ns parameter, applyZoomTransition helper, success haptic on appear
- `EDGE/Sources/Features/Today/TodayView.swift` - Added @Namespace and matchedTransitionSource on spotlight/picks, per-word greeting stagger, shifted all animation indices

## Decisions Made
- Used iOS 18 `navigationTransition(.zoom(sourceID:in:))` instead of `matchedGeometryEffect` for the cross-push morph — the latter does NOT animate across NavigationStack pushes reliably
- Made `ns` parameter optional on MatchDetailView with a `@ViewBuilder` helper extension to keep previews working
- Greeting words use base index 2 (after date label at 1), subsequent cards shifted to maintain sequential top-to-bottom stagger

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed animation index collision between greeting words and standing card**
- **Found during:** Task 3 (Word-by-word greeting build)
- **Issue:** Greeting "Good evening, Niko." = 3 words using indices 2-4, but standing card was also at index 4
- **Fix:** Shifted standing card to 5, plan to 6, spotlight to 7, picks to 8-9+ to maintain sequential stagger
- **Files modified:** EDGE/Sources/Features/Today/TodayView.swift
- **Verification:** Grep confirmed non-overlapping generativeAppear indices
- **Committed in:** d574239 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Index collision fix was necessary for correct stagger animation. No scope creep.

## Issues Encountered
- iOS 26.5 simulator runtime not installed in Xcode environment — could not run xcodebuild verification. Code verified via grep for acceptance criteria patterns instead.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Motion layer complete (MOTION-01): zoom morph, haptics, word-build greeting
- Ready for Plan 08-02: Accessibility, States & No-Jargon audit

---
*Phase: 08-motion-a11y-states*
*Completed: 2026-06-17*

## Self-Check: PASSED

- All 3 modified files exist
- All 3 task commits found (b3e3a14, 97bab4d, d574239)
- MatchesView: @Namespace + matchedTransitionSource ✓
- TodayView: @Namespace + matchedTransitionSource (2 occurrences) ✓
- MatchDetailView: ns param + navigationTransition + UINotificationFeedbackGenerator + outcome=="exact" ✓
- TodayView: per-word generativeAppear(2 + index) ✓
