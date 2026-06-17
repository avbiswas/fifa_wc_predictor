---
phase: 05-today-briefing
reviewed: 2026-06-17T20:15:00Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - EDGE/Sources/Features/Today/TodayView.swift
  - EDGE/Sources/DesignSystem/Components/CountdownPill.swift
  - EDGE/Sources/Features/Matches/MatchDetailView.swift
  - EDGE/Sources/Features/Shell/RootView.swift
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-17T20:15:00Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Phase 5 adds the Today briefing screen (upper + lower half), CountdownPill component, MatchDetailView stub, and wires everything into RootView. The implementation is solid overall — correct SwiftUI patterns, proper use of the design system, safe optional handling, and faithful spec compliance for the core Today screen. No critical issues (no crashes, no security concerns, no data loss risks). Three warnings found: one is a spec-deviation where TodayView hardcodes an inline "Why this pick" CTA instead of using the existing `InkButton` component, another is a missing `IridescentGlow` background in `MatchDetailView`, and the third is a timer lifecycle concern in `CountdownPill`. Three informational items flagged for cleanup.

## Warnings

### WR-01: TodayView hardcodes inline InkButton instead of reusing the existing component

**File:** `EDGE/Sources/Features/Today/TodayView.swift:278-291`
**Issue:** The "Why this pick →" CTA is built inline with manual `HStack`, `Text`, `Image`, `Circle`, and `Capsule` styling instead of using the existing `InkButton` component from the design system. The inline code is visually identical to `InkButton` but is a separate code path. This creates duplication — if the InkButton style ever changes (e.g., padding, font, icon size), this CTA will drift out of sync. The spec (§5.10) defines `InkButton` as the canonical black pill CTA component.
**Fix:**
```swift
// Replace lines 278-291 with:
InkButton(title: "Why this pick") {
    // NavigationLink handles navigation via value binding
}
```
However, since this is inside a `NavigationLink(value:)` wrapper, the `InkButton` action closure is unused. A cleaner approach would be to keep the `NavigationLink(value:)` wrapper but apply `.buttonStyle(PressScale())` and use `InkButton` as the label. If the NavigationLink binding prevents using InkButton directly, extract a shared style constant to avoid drift.

### WR-02: MatchDetailView missing IridescentGlow background

**File:** `EDGE/Sources/Features/Matches/MatchDetailView.swift:74`
**Issue:** The spec (§7.4) states: "Faint `IridescentGlow` at top." The current implementation uses a plain `Theme.bg.ignoresSafeArea()` background with no `IridescentGlow`. While this is a stub for Phase 6, the missing glow breaks the opalescent design language and may be forgotten when the full detail is built.
**Fix:**
```swift
// Replace line 74:
.background(Theme.bg.ignoresSafeArea())
// With:
.background {
    ZStack {
        Theme.bg.ignoresSafeArea()
        IridescentGlow(intensity: 0.35).ignoresSafeArea()
    }
}
```

### WR-03: CountdownPill timer fires indefinitely after kickoff

**File:** `EDGE/Sources/DesignSystem/Components/CountdownPill.swift:25-27`
**Issue:** The `Timer.publish(every: 60, ...)` timer starts on appear and never stops, even after `isPast` becomes true (kickoff has passed). While the visual state correctly switches to `warnText`/`warnBG` after kickoff, the timer continues firing every 60 seconds for the lifetime of the view. For a single pill this is negligible, but if many `CountdownPill` instances exist in a list (e.g., MatchesView), each carries its own perpetual timer.
**Fix:**
```swift
.onReceive(Timer.publish(every: 60, on: .main, in: .common).autoconnect()) { date in
    guard !isPast else { return }  // stop updating once past
    now = date
}
```
For a more complete fix, invalidate the timer when `isPast` is true by switching to a conditional `TimelineView` or using `.onReceive` with a `Publishers.Autoconnect` that is conditionally nilled.

## Info

### IN-01: DateFormatter created on every call to Format.kickoffClock

**File:** `EDGE/Sources/Core/Format.swift:59`
**Issue:** `Format.kickoffClock` creates a new `DateFormatter` instance every time it is called. `DateFormatter` is expensive to create. In TodayView, this is called once per render for the spotlight card, so the performance impact is minimal. However, if this helper is used in list rows (e.g., MatchesView), the cost multiplies.
**Fix:**
```swift
private static let clockFormatter: DateFormatter = {
    let f = DateFormatter()
    f.dateFormat = "HH:mm"
    return f
}()
static func kickoffClock(_ d: Date) -> String { clockFormatter.string(from: d) }
```
Same applies to `relativeUpdated` (line 60-62) which creates a `RelativeDateTimeFormatter` on each call.

### IN-02: TodayView greeting animation does not match spec's "word-by-word" flourish

**File:** `EDGE/Sources/Features/Today/TodayView.swift:90-101`
**Issue:** The spec (§7.2 item 2) describes an optional flourish where each word gets its own `.generativeAppear(1 + wordIndex)` for a staggered word-by-word build. The current implementation renders all words in a single `HStack` with one `.generativeAppear(2)`, so they all appear simultaneously. This is functionally correct but misses the intended animation effect.
**Fix:**
```swift
@ViewBuilder
private func greetingWords(_ name: String) -> some View {
    let greeting = Format.greeting(name)
    let words = greeting.split(separator: " ").map(String.init)
    HStack(spacing: 0) {
        ForEach(Array(words.enumerated()), id: \.offset) { index, word in
            Text(word + (index < words.count - 1 ? " " : ""))
                .font(index == words.count - 1 ? .greeting.weight(.medium) : .greeting)
                .foregroundStyle(Theme.text)
                .generativeAppear(2 + index)  // stagger per word
        }
    }
}
```
Note: this changes the index numbering for downstream elements (standing card = 2 + wordCount, etc.), so all subsequent `.generativeAppear` indices would need adjustment.

### IN-03: Minor — trailing period in greeting gets bolded with the name

**File:** `EDGE/Sources/Features/Today/TodayView.swift:97`
**Issue:** `Format.greeting` returns `"Good evening, Niko."` with a trailing period. The greeting word-split logic bolds the last word (`"Niko."`) including the period. This is a cosmetic nit — the period renders in medium weight alongside the name. Barely visible but technically imprecise.
**Fix:** Either strip the trailing period from the greeting format, or apply `.medium` weight only to the name portion by splitting on punctuation. Low priority — the visual difference is minimal at `.greeting` (30pt light) size.

---

_Reviewed: 2026-06-17T20:15:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
