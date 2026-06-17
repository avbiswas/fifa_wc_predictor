---
phase: 06-matches-detail
reviewed: 2026-06-17T16:45:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - EDGE/Sources/Features/Matches/MatchRowCard.swift
  - EDGE/Sources/Features/Matches/MatchesView.swift
  - EDGE/Sources/Features/Matches/MatchDetailView.swift
  - EDGE/Sources/Features/Shell/RootView.swift
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-06-17T16:45:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the Matches tab and Match Detail screen implementation (Phase 06, plans 01+02). The code is well-structured, follows SwiftUI patterns, and closely adheres to the spec in `docs/ios_app_plan.md` §7.3/§7.4. The design system components (FrostCard, SoftRing, CountdownPill, etc.) are used correctly. No force unwraps, no hardcoded secrets, no unsafe data handling.

One critical issue found: status branching in `MatchRowCard` uses a fallthrough `else` instead of explicitly checking for `"final"`, which could silently show incorrect content if the data model ever includes statuses beyond "upcoming" and "final". Three warnings around repeated `DateFormatter` allocation and a spec deviation in the empty state message. Two informational items for dead code and fragile string comparisons.

Cross-file analysis confirms that `MatchesView`'s filtering (`status == "upcoming"` / `status == "final"`) protects `MatchRowCard` from receiving unexpected statuses in the current data flow — but the component itself is not defensive. The `animIndex` variable mutation inside the `@ViewBuilder` closure in `MatchesView` is correct (synchronous evaluation during view construction). The `GeometryReader` usage in `MatchDetailView` for alternate score bars is properly bounded. The `matchedGeometryEffect` ring morph from the spec is deferred (spec allows fallback), using `generativeAppear` instead.

## Critical Issues

### CR-01: Status branching fallthrough in MatchRowCard

**File:** `EDGE/Sources/Features/Matches/MatchRowCard.swift:9-12`
**Issue:** The body uses `if match.status == "upcoming" { upcomingContent } else { finalContent }`. Any status that isn't `"upcoming"` — including potential future values like `"live"`, `"postponed"`, or `"suspended"` — would silently render as final score content with potentially stale or nil data. While `MatchesView` currently filters to only pass `"upcoming"` or `"final"` matches, the component itself is not defensive and will produce wrong output if used elsewhere or if the data model changes.
**Fix:**
```swift
// In MatchRowCard.swift, lines 9-12:
if match.status == "upcoming" {
    upcomingContent
} else if match.status == "final" {
    finalContent
} else {
    // Fallback: show basic matchup info without score/outcome
    upcomingContent // or a dedicated "live" variant
}
```

## Warnings

### WR-01: DateFormatter allocated on every render in MatchRowCard

**File:** `EDGE/Sources/Features/Matches/MatchRowCard.swift:134-137`
**Issue:** `formatDate(_:)` creates a new `DateFormatter()` on every call. `DateFormatter` is expensive to allocate and this function is called during every view body evaluation (potentially on every frame during scroll). This degrades rendering performance, especially in a list of many match cards.
**Fix:**
```swift
// Replace the instance method with a static cached formatter:
private static let dayMonthFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "d MMM"
    return f
}()

private func formatDate(_ date: Date) -> String {
    Self.dayMonthFormatter.string(from: date)
}
```

### WR-02: DateFormatter allocated on every render in MatchesView

**File:** `EDGE/Sources/Features/Matches/MatchesView.swift:148-153`
**Issue:** Same pattern as WR-01. `formatMatchdayDate(_:)` creates a new `DateFormatter()` on every call, which happens for each matchday section header during view evaluation.
**Fix:**
```swift
// Replace with a static cached formatter:
private static let matchdayDateFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "d MMM"
    return f
}()

private func formatMatchdayDate(_ date: Date?) -> String {
    guard let date else { return "" }
    return Self.matchdayDateFormatter.string(from: date)
}
```

### WR-03: Empty state message missing next matchday date (spec deviation)

**File:** `EDGE/Sources/Features/Matches/MatchesView.swift:165-166`
**Issue:** The spec (§7.3) requires: `"All caught up. Next matchday {date}."` — but the implementation shows just `"All caught up."` without the next matchday date. This removes useful context that tells the user when to check back. The `upcomingMatches` data is available to compute the next kickoff date.
**Fix:**
```swift
// Compute the next matchday date from upcoming matches:
Text(showResults
    ? "No results yet — first picks score after kickoff."
    : {
        let nextDate = feed.matches
            .filter { $0.status == "upcoming" }
            .sorted { $0.kickoff < $1.kickoff }
            .first?.kickoff
        if let nextDate {
            return "All caught up. Next matchday \(formatMatchdayDate(nextDate))."
        }
        return "All caught up."
    }())
```

## Info

### IN-01: Unused Seg enum in MatchesView

**File:** `EDGE/Sources/Features/Matches/MatchesView.swift:7-10`
**Issue:** The `Seg` enum (`case upcoming = "Upcoming"`, `case results = "Results"`) is defined but never referenced. The segmented control uses a `showResults` boolean instead. This is dead code that may confuse future maintainers into thinking there's a typed segment model.
**Fix:** Remove the unused enum, or refactor the segmented control to use `Seg` instead of a raw boolean:
```swift
// Option A: Remove the dead code
// (delete lines 7-10)

// Option B: Use Seg for the segmented control
@State private var selectedSegment: Seg = .upcoming
```

### IN-02: String-based status comparisons throughout codebase

**File:** `EDGE/Sources/Features/Matches/MatchRowCard.swift:9`, `MatchesView.swift:125,131`, `MatchDetailView.swift:99`
**Issue:** Status is compared as raw strings (`"upcoming"`, `"final"`) across 4 files. The `Match` model in `Models.swift` defines `status` as `String`. If the JSON contract ever changes status values (e.g., `"live"` instead of `"in_progress"`), every comparison must be found and updated manually. This is fragile but consistent with the current data model.
**Fix:** Consider adding a computed property or enum to `Match`:
```swift
extension Match {
    enum Status: String { case upcoming, final, live, postponed }
    var matchStatus: Status { Status(rawValue: status) ?? .upcoming }
}
```

---

_Reviewed: 2026-06-17T16:45:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
