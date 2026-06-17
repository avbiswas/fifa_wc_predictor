---
phase: 07-insights-scouting
verified: 2026-06-17T20:00:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 7: Insights & Scouting Verification Report

**Phase Goal:** The Insights tab — engine form metrics with a sparkline, plus a scouting report card for each friend.
**Verified:** 2026-06-17T20:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Insights shows engine form: points won, avg per game, spot-on count, scored ratio | ✓ VERIFIED | `InsightsView.swift:23-42` — 4 `MetricTile` instances with values `feed.form.points` (24), `feed.form.avgPoints` (1.5), `feed.form.exact` (4), `feed.form.scored/feed.form.matches` (8/16) |
| 2 | A sparkline shows recent points per pick | ✓ VERIFIED | `InsightsView.swift:48` — `Sparkline(values: feed.form.recentPoints)` inside a `FrostCard` with caption |
| 3 | A scouting card per friend shows tag, blurb, and 3 trait level bars | ✓ VERIFIED | `ScoutCard.swift:27-31` — `SoftPill(text: report.tag)` with color logic; `ScoutCard.swift:34` — `Text(report.blurb)`; `ScoutCard.swift:44-53` — `ForEach(report.traits)` with `TraitLevelBar(level: trait.level)` using 3 capsules filled `Theme.iridLilac` |
| 4 | The Insights tab lists scouting cards sorted by rank | ✓ VERIFIED | `InsightsView.swift:65` — `ForEach(Array(feed.scouting.sorted { $0.rank < $1.rank }.enumerated()), ...)` renders `ScoutCard(report:)` per friend |
| 5 | Tapping a non-you table row opens that friend's scouting card | ✓ VERIFIED | `TableView.swift:54-59` — `.sheet(item: $scouted) { ScoutCard(report:) }` with `.presentationDetents([.medium])`; `TableView.swift:112-116` — `.onTapGesture` sets `scouted` for non-you rows via `scouting.first(where: { $0.name == row.name })` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `EDGE/Sources/Features/Insights/InsightsView.swift` | Engine form metrics + sparkline + scouting list | ✓ VERIFIED | 122 lines. Contains MetricTile (private), LazyVGrid, Sparkline card, takeaway text, Eyebrow("Scouting the field"), ForEach of ScoutCard |
| `EDGE/Sources/Features/Insights/ScoutCard.swift` | Friend scouting card | ✓ VERIFIED | 106 lines. Contains FrostCard wrapper, header (crown/name/rank), SoftPill with tag color logic, blurb, TraitLevelBar (3-capsule, animated) |
| `EDGE/Sources/Features/Shell/RootView.swift` | InsightsView wired into .insights tab | ✓ VERIFIED | `RootView.swift:51` — `case .insights: InsightsView()` — all 4 tabs now host real screens |
| `EDGE/Sources/Features/Table/TableView.swift` | Row tap → ScoutCard sheet | ✓ VERIFIED | `TableView.swift:5` — `@State private var scouted: ScoutReport?`; `TableView.swift:54-59` — `.sheet(item: $scouted)`; `TableView.swift:112-116` — tap gesture on non-you rows |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `InsightsView.swift` | `AppStore.feed.form` | renders form metrics | ✓ WIRED | `InsightsView.swift:11` — `if let feed = store.feed`; lines 23-42 access `feed.form.points`, `.avgPoints`, `.exact`, `.scored`, `.matches`, `.recentPoints` |
| `InsightsView.swift` | `ScoutCard` | lists scouting | ✓ WIRED | `InsightsView.swift:66` — `ScoutCard(report: report)` inside `ForEach(feed.scouting.sorted ...)` |
| `TableView.swift` | `ScoutCard` | row tap presents sheet | ✓ WIRED | `TableView.swift:54-59` — `.sheet(item: $scouted) { ScoutCard(report:) }`; `TableView.swift:112-116` — tap gesture binds `scouted` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `InsightsView.swift` | `feed.form` | `AppStore.feed` | Yes — `Form` struct with `matches`, `points`, `avgPoints`, `exact`, `scored`, `recentPoints` decoded from `SampleFeed.json` | ✓ FLOWING |
| `InsightsView.swift` | `feed.scouting` | `AppStore.feed` | Yes — `[ScoutReport]` with `name`, `rank`, `tag`, `blurb`, `traits` decoded from `SampleFeed.json` | ✓ FLOWING |
| `ScoutCard.swift` | `report.tag` | `ScoutReport.tag` | Yes — populated by JSON decode | ✓ FLOWING |
| `ScoutCard.swift` | `report.traits` | `ScoutReport.traits` | Yes — `[Trait]` with `label`, `value`, `level` populated by JSON decode | ✓ FLOWING |
| `TableView.swift` | `scouted` | `feed.scouting.first(where:)` | Yes — matched by row name from live scouting data | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| InsightsView references form metrics | `grep -c "feed.form\." InsightsView.swift` | 6 occurrences (points, avgPoints, exact, scored, matches, recentPoints) | ✓ PASS |
| ScoutCard references all required fields | `grep -c "report\.\(tag\|blurb\|traits\)" ScoutCard.swift` | 3 occurrences (tag, blurb, traits) | ✓ PASS |
| TraitLevelBar uses 3 segments | `grep "0..<3" ScoutCard.swift` | `ForEach(0..<3, id: \.self)` found | ✓ PASS |
| TraitLevelBar uses iridLilac | `grep "iridLilac" ScoutCard.swift` | `index < level ? Theme.iridLilac : Theme.track` found | ✓ PASS |
| Tag color logic handles chaos/contrarian | `grep -E "chaos|contrarian" ScoutCard.swift` | Both keywords handled in `tagBackground` and `tagForeground` | ✓ PASS |
| TableView sheet binding uses ScoutCard | `grep "ScoutCard(report:" TableView.swift` | `.sheet(item: $scouted) { ScoutCard(report: report)` found | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INSIGHT-01 | 07-01, 07-02 | Insights tab shows engine form metrics + sparkline, and a scouting card per friend (tag, blurb, 3 trait level bars) | ✓ SATISFIED | All 5 truths verified. InsightsView renders form metrics (24/1.5/4/8-of-16) + Sparkline. ScoutCard renders tag pill (color-coded), blurb, 3 TraitLevelBars. Scouting listed in Insights and accessible from Table row tap. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `RootView.swift` | 93-105 | `PlaceholderTab` struct with "coming soon" text | ℹ️ Info | Harmless dead code — struct is private and no longer referenced (replaced by `InsightsView()`). No impact on goal. |

### Human Verification Required

### 1. Visual Fidelity — Metric Tiles

**Test:** Launch app → Insights tab → verify 4 frosted metric tiles display with correct values (24, 1.5, 4, 8/16) and accent coloring (points won + spot-on in green, others in standard text)
**Expected:** Frosted glass tiles with monospaced digits, accent tiles in `Theme.posText` (#1F7A52), non-accent in `Theme.text`
**Why human:** Visual appearance (frosted blur, color accuracy, layout spacing) cannot be verified programmatically

### 2. Visual Fidelity — ScoutCard Trait Level Bars

**Test:** Insights tab → scroll to scouting section → verify each friend's card shows 3 filled capsules per trait (Goals/Draws/Upsets) with iridescent lilac fill
**Expected:** 3 capsule segments per trait, first N filled `Theme.iridLilac`, rest `Theme.track`. Values (High/Rare/Often) shown as text.
**Why human:** Capsule fill animation and visual alignment need human eyes

### 3. Tag Pill Color Coding

**Test:** Insights → scouting → verify "Chaos merchant" tag shows peach (warnBG), "Contrarian" shows purple (actBG), neutral tags show gray
**Expected:** Color-coded pills matching keyword logic
**Why human:** Color accuracy against spec hex values

### 4. Table Row → ScoutCard Sheet

**Test:** Table tab → tap a non-you player row → verify ScoutCard slides up as a medium-detent sheet
**Expected:** Sheet with ScoutCard showing that player's tag, blurb, and trait bars. Tapping your own row does nothing.
**Why human:** Sheet presentation animation and detent behavior

### Gaps Summary

No technical gaps found. All 5 must-have truths are verified against the actual codebase. The implementation matches the ROADMAP success criteria and the UI-SPEC exactly:

1. ✅ Engine form metrics (24 points / 1.5 avg / 4 spot-on / 8-of-16 scored) render in MetricTile grid
2. ✅ Sparkline shows `feed.form.recentPoints` with caption
3. ✅ ScoutCard per friend with tag pill (color-coded), blurb, and 3 trait level bars (iridLilac filled)
4. ✅ Scouting list sorted by rank in Insights tab
5. ✅ Table row tap opens ScoutCard sheet for non-you players

All supporting artifacts (InsightsView.swift, ScoutCard.swift, RootView.swift, TableView.swift) exist, are substantive, are wired, and have real data flowing through them.

**Status is `human_needed` because 4 visual fidelity items require human verification** (frosted glass appearance, trait bar animation, tag pill colors, sheet presentation). Automated checks all pass.

---

_Verified: 2026-06-17T20:00:00Z_
_Verifier: the agent (gsd-verifier)_
