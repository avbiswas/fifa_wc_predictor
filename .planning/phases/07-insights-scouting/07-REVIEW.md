---
phase: 07-insights-scouting
reviewed: 2026-06-17T20:15:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - EDGE/Sources/Features/Insights/InsightsView.swift
  - EDGE/Sources/Features/Insights/ScoutCard.swift
  - EDGE/Sources/Features/Table/TableView.swift
  - EDGE/Sources/Features/Shell/RootView.swift
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-06-17T20:15:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 7 (Insights & Scouting) implemented `InsightsView` with engine-form metric tiles, sparkline, and takeaway text, plus `ScoutCard` with keyword-colored tag pills, trait level bars, and sheet presentation from `TableView`. All 4 app tabs now host real screens.

The implementation is clean, follows existing design system patterns (FrostCard, SoftPill, Eyebrow, generativeAppear), and the code is well-organized. No security issues or crash-prone patterns found. Two warnings relate to spec compliance: the tag pill color logic adds an "away" keyword not specified in §7.7, and the neutral fallback uses a hardcoded color instead of a Theme token.

## Warnings

### WR-01: Tag pill color logic adds "away" keyword not in spec

**File:** `EDGE/Sources/Features/Insights/ScoutCard.swift:64`
**Issue:** Spec §7.7 line 1002 defines exactly two keyword-to-color mappings: `chaos→warn, contrarian→active, default→neutral`. The implementation adds `|| lower.contains("away")` as a third trigger for the accent color. The 07-02-SUMMARY claims this "matches spec §7.7" — it does not. While the sample data includes "Away-backer" as a tag, the spec doesn't specify it should get accent coloring. This is a reasonable extension but should be documented as a deliberate spec deviation, not presented as compliance.

**Fix:** Either remove the "away" keyword to match the spec exactly:
```swift
private var tagBackground: Color {
    let lower = report.tag.lowercased()
    if lower.contains("chaos") {
        return Theme.warnBG
    } else if lower.contains("contrarian") {
        return Theme.actBG
    }
    return Theme.track  // or a dedicated neutral token
}
```
Or update the spec §7.7 to document the three-keyword mapping if the extension is intentional.

### WR-02: Neutral tag fallback uses hardcoded hex instead of Theme token

**File:** `EDGE/Sources/Features/Insights/ScoutCard.swift:67`
**Issue:** The default/neutral tag background returns `Color(hex: "F0F0F3")` — a magic number that's close to but distinct from `Theme.track` (`#ECECF1`). This breaks the pattern where all colors come from the Theme enum. If the theme changes, this color won't update.

**Fix:** Use a Theme token for the neutral fallback:
```swift
return Theme.track  // #ECECF1 — closest Theme token for neutral pill background
```
Or add a dedicated `Theme.neutralBG` token if the slightly different shade is intentional.

## Info

### IN-01: PlaceholderTab dead code in RootView

**File:** `EDGE/Sources/Features/Shell/RootView.swift:93-106`
**Issue:** The `PlaceholderTab` struct is no longer referenced after InsightsView replaced the `.insights` placeholder. The 07-01-SUMMARY acknowledges this as "harmless dead code." It's a minor clutter item.

**Fix:** Remove the unused struct to keep the file clean:
```swift
// Delete lines 93-106 (the entire PlaceholderTab struct)
```

### IN-02: TraitLevelBar has no bounds validation on level

**File:** `EDGE/Sources/Features/Insights/ScoutCard.swift:88-105`
**Issue:** The `TraitLevelBar` renders `ForEach(0..<3)` and fills segments where `index < level`. If `level` is 0, all segments show as track (correct). If `level` > 3, all segments fill (acceptable visual fallback). No crash risk, but the implicit contract that `level` is 0–3 is not enforced. Sample data only contains levels 1–3.

**Fix:** Optional defensive clamp for robustness:
```swift
let clamped = min(max(level, 0), 3)
// Then use clamped instead of level in the fill condition
```

### IN-03: Divider coloring uses .background() instead of .foregroundStyle()

**File:** `EDGE/Sources/Features/Table/TableView.swift:30`
**Issue:** `Divider().background(Theme.hairline)` applies a background color behind the divider, but SwiftUI's `Divider()` inherits its color from the environment's foreground style. The `.background()` modifier may not visually color the divider as intended. This is a pre-existing pattern (not introduced by Phase 7) but worth noting.

**Fix:** Use `.foregroundStyle()` to color the divider:
```swift
Divider().foregroundStyle(Theme.hairline)
```

---

_Reviewed: 2026-06-17T20:15:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
