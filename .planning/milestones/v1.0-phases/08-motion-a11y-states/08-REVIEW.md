---
phase: 08-motion-a11y-states
reviewed: 2026-06-17T23:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - EDGE/Sources/Features/Today/TodayView.swift
  - EDGE/Sources/Features/Matches/MatchesView.swift
  - EDGE/Sources/Features/Matches/MatchRowCard.swift
  - EDGE/Sources/Features/Matches/MatchDetailView.swift
  - EDGE/Sources/Features/Shell/RootView.swift
  - EDGE/Sources/DesignSystem/Components/SoftRing.swift
  - EDGE/Sources/DesignSystem/Components/StrengthBar.swift
  - EDGE/Sources/DesignSystem/Components/IridescentGlow.swift
  - EDGE/Sources/Features/Table/TableView.swift
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-06-17T23:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed all 9 source files modified during Phase 8 (Motion Polish + A11y/States). The implementation is solid overall — zoom transitions, haptics, word-by-word greeting, VoiceOver labels, Reduce Motion handling, and loading/error states all follow the spec. The Reduce Motion wiring is consistent across `IridescentGlow`, `SoftRing`, `StrengthBar`, and `GapRail`. The no-jargon audit holds: no raw probabilities or percentages leak into the UI.

Two warnings found: two `StrengthBar` instances in `MatchRowCard` and `TodayView` are missing their `a11yLabel` parameter, violating the spec requirement that all bars get worded VoiceOver labels. The remaining findings are minor code quality items.

## Warnings

### WR-01: StrengthBar missing a11yLabel in MatchRowCard (upcoming variant)

**File:** `EDGE/Sources/Features/Matches/MatchRowCard.swift:60-66`
**Issue:** The `StrengthBar` in the upcoming match card is created without an `a11yLabel`. When `a11yLabel` is `nil`, the `A11yBarLabel` modifier does nothing — VoiceOver will read the raw team code labels ("POR", "draw", "BRA") instead of a worded description. Spec §9 requires all bars get plain labels like "Portugal heavy favorite."
**Fix:**
```swift
StrengthBar(
    home: match.odds.home,
    draw: match.odds.draw,
    away: match.odds.away,
    homeCode: match.home.code,
    awayCode: match.away.code,
    a11yLabel: "\(Format.strengthWords(match.favoriteStrength)): \(match.favorite)."
)
```

### WR-02: StrengthBar missing a11yLabel in TodayView spotlight card

**File:** `EDGE/Sources/Features/Today/TodayView.swift:263-269`
**Issue:** Same as WR-01. The spotlight card's `StrengthBar` has no `a11yLabel`, so VoiceOver reads raw team codes instead of the spec-required worded description.
**Fix:**
```swift
StrengthBar(
    home: match.odds.home,
    draw: match.odds.draw,
    away: match.odds.away,
    homeCode: match.home.code,
    awayCode: match.away.code,
    a11yLabel: "\(Format.strengthWords(match.favoriteStrength)): \(match.favorite)."
)
```

## Info

### IN-01: Dead code — PlaceholderTab struct

**File:** `EDGE/Sources/Features/Shell/RootView.swift:164-177`
**Issue:** `PlaceholderTab` is defined but never instantiated anywhere. It appears to be a leftover from early development before all tabs were implemented. Dead code adds maintenance burden and confuses readers.
**Fix:** Remove the `PlaceholderTab` struct entirely.

### IN-02: Fragile mutable animIndex in MatchesView ForEach

**File:** `EDGE/Sources/Features/Matches/MatchesView.swift:39-54`
**Issue:** `var animIndex` is declared as a local variable and mutated during `@ViewBuilder` evaluation inside nested `ForEach` loops. While this works because SwiftUI evaluates the body synchronously, it's an unusual pattern that's fragile — any SwiftUI rendering change (lazy evaluation, body re-evaluation order) could break the stagger sequence.
**Fix:** Consider computing indices from enumerated offsets instead of mutable state:
```swift
// Compute flat indices before the ForEach
let flatIndices: [(matchday: Int, match: Match, animIndex: Int)] = {
    var result: [(Int, Match, Int)] = []
    var idx = 2
    for group in grouped {
        idx += 1 // section header
        for match in group.matches {
            result.append((group.matchday, match, idx))
            idx += 1
        }
    }
    return result
}()
```
This is informational — the current code works correctly.

### IN-03: GeometryReader per-row in alternates section

**File:** `EDGE/Sources/Features/Matches/MatchDetailView.swift:251-259`
**Issue:** Each alternate score row allocates its own `GeometryReader` to compute bar width. `GeometryReader` is intended for layout containers, not per-item sizing. With many alternates, this creates unnecessary layout work.
**Fix:** Wrap the entire alternates `VStack` in a single `GeometryReader` at the parent level and pass the width down. This is a minor optimization — the current approach is functionally correct.

---

_Reviewed: 2026-06-17T23:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
