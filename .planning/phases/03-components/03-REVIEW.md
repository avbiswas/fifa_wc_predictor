---
phase: 03-components
reviewed: 2026-06-17T16:05:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - EDGE/Sources/DesignSystem/Components/FrostCard.swift
  - EDGE/Sources/DesignSystem/Components/SoftRing.swift
  - EDGE/Sources/DesignSystem/Components/StrengthBar.swift
  - EDGE/Sources/DesignSystem/Components/GapRail.swift
  - EDGE/Sources/DesignSystem/Components/SoftPill.swift
  - EDGE/Sources/DesignSystem/Components/InkButton.swift
  - EDGE/Sources/DesignSystem/Components/MovementArrow.swift
  - EDGE/Sources/DesignSystem/Components/TeamBadge.swift
  - EDGE/Sources/DesignSystem/Components/GeneratedStatus.swift
  - EDGE/Sources/DesignSystem/Components/Sparkline.swift
  - EDGE/Sources/Features/Shell/ComponentGallery.swift
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-17T16:05:00Z
**Depth:** standard
**Files Reviewed:** 11 (10 components + ComponentGallery)
**Status:** issues_found

## Summary

All 10 components in `EDGE/Sources/DesignSystem/Components/` plus the `ComponentGallery` preview surface were reviewed at standard depth. Cross-referenced byte-for-byte against `docs/ios_app_plan.md` §5.5–§5.14, against the project's stated constraints (PROJECT.md / CLAUDE.md), and against the implementer's self-declared contracts in the phase SUMMARYs.

**High-level:** the implementation is faithful to the spec source — every value (corner radius, blur material, stroke width, shadow radii/opacity, gradient stops, spring/easeOut parameters, delays, Reduce-Motion snap branches present in §5.6–5.8) matches §5 verbatim. No hardcoded colors outside the two spec-mandated inline hexes (`9DBBA9`, `A9C2E6`). No raw probabilities surfaced as text. Theme tokens are consumed consistently.

**However**, the implementer's stated policy of "byte-verbatim from spec" propagated two real spec-source defects into shipped code, and one of them violates the project's self-declared "non-negotiable" accessibility contract. The spec's prose (§8.11, §9) explicitly promises "every animated component checks `accessibilityReduceMotion` and snaps to the final state (no blur, no stagger; gradient paused). **Already wired in the component code above.**" — but §5.13's source omits that wiring, and `GeneratedStatus.swift` ships without it. This is exactly the kind of spec-internal contradiction that byte-verbatim copying cannot catch and that adversarial review exists to surface.

The other notable issue is shared by `StrengthBar` and `GapRail`: their proportion math (`total * p` per segment, `mine/leader` fraction) doesn't account for inter-segment spacing or clamp at the upper bound, producing real visual defects when probabilities sum to ~1.0 (always — they're probabilities) or when a player overtakes the leader (a real game state). Both are spec-source bugs copied verbatim.

No security findings — pure offline SwiftUI, no I/O, no network, no untrusted input. No-jargon rule honored across all components.

---

## Critical Issues

### CR-01: GeneratedStatus pulse animation ignores Reduce Motion — spec §8.11/§9 contract violation

**File:** `EDGE/Sources/DesignSystem/Components/GeneratedStatus.swift:5-13`
**Issue:**

`GeneratedStatus` is the "agentic motif" — a `Theme.spark` 7pt dot that pulses `scaleEffect 0.8↔1.2` + `opacity 0.5↔1` via `.easeInOut(duration: 1.2).repeatForever(autoreverses: true)`, fired unconditionally in `.onAppear`. The component reads **no** `@Environment(\.accessibilityReduceMotion)` value and has **no** branch to snap to a final state when the user has enabled Reduce Motion. The pulse runs forever.

This violates three layers of explicit project contract:

1. **Spec `docs/ios_app_plan.md:1031-1032` (§8.11):** *"Reduce Motion: **every animated component** checks `accessibilityReduceMotion` and snaps to the final state (no blur, no stagger; gradient paused). **Already wired in the component code above.**"* — the spec's prose claims the wiring is done; the §5.13 source (and the shipped file) omits it. This is an internal spec contradiction.
2. **Spec `docs/ios_app_plan.md:1048` (§9):** *"Reduce Motion: assembly + breathing + draws all snap to final (see §8.11)."*
3. **Phase SUMMARY `.planning/phases/03-components/03-01-SUMMARY.md:23`:** *"Every animated component reads `@Environment(\.accessibilityReduceMotion)` and snaps to its final state when true — Reduce-Motion-safe is a **non-negotiable component contract**."* This claim is project-wide and is FALSE for `GeneratedStatus`.

The three sibling components (`SoftRing`, `StrengthBar`, `GapRail`) all correctly honor the contract via the canonical `if reduceMotion { … = final; return }; withAnimation(…) { … = final }` pattern. `GeneratedStatus` is the one outlier.

**Why severity = Critical:** `GeneratedStatus` is not a one-shot entrance animation — it is a *forever-looping* pulse that lives permanently at the top of the Today screen (spec §7.2, §8.5). Forever-looping motion is the worst-case pattern for users with vestibular disorders and is precisely the case Apple's Reduce Motion setting exists to disable. The component will appear in every session, every screen refresh, indefinitely, with no user recourse. Shipping this is an accessibility regression that affects real users — not a stylistic preference.

The byte-verbatim-from-spec policy is the proximate cause, but PROJECT.md makes design fidelity paramount *and* CLAUDE.md requires "Reduce Motion where spec indicates" — the spec indicates it (twice), the spec source just fails to implement it. The reviewer's job is to catch that contradiction, not propagate it.

**Fix:**

```swift
import SwiftUI
struct GeneratedStatus: View {
    let updatedAt: Date
    var generating: Bool = false
    @State private var pulse = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion   // ← add
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(Theme.spark).frame(width: 7, height: 7)
                .scaleEffect(pulse ? 1.2 : 0.8).opacity(pulse ? 1 : 0.5)
                .onAppear {
                    if reduceMotion { pulse = true; return }              // ← snap to final state
                    withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
                        pulse = true
                    }
                }
            Text(generating ? "Generating your briefing…" : "Generated \(Format.relativeUpdated(updatedAt))")
                .font(.calloutX).foregroundStyle(Theme.textDim)
        }
    }
}
```

Also update `03-01-SUMMARY.md` and `03-03-SUMMARY.md` to either (a) remove the over-broad "every animated component" claim, or (b) note this fix as a deliberate deviation from §5.13 source to honor §8.11 prose.

---

## Warnings

### WR-01: GapRail marker + gradient fill overflow when `mine ≥ leader` (no clamp on `frac`)

**File:** `EDGE/Sources/DesignSystem/Components/GapRail.swift:7,15,19`
**Issue:**

```swift
private var frac: CGFloat { leader <= 0 ? 0 : CGFloat(mine)/CGFloat(leader) }
```

`frac` is not clamped to `[0, 1]`. Three real-world cases break the layout:

| State | `frac` | Result |
|---|---|---|
| `mine == leader` (player tied with leader) | `1.0` | Marker center lands at right edge of track; right half of 14pt marker (7pt) hangs off the rail |
| `mine > leader` (player overtook leader — a *normal* mid-league state) | `> 1.0` | Gradient `Capsule` width `geo.size.width * p` exceeds track width (visible overflow past the right edge of the rail); marker offset `geo.size.width * p - 7` is off the right edge of the card |
| `mine < 0` (defensive — shouldn't happen but `Int` permits it) | `< 0` | Gradient `Capsule` width is negative → SwiftUI clamps to 0; marker offset `-7` puts marker off the *left* edge |

The gallery demo (`mine: 18, leader: 24` → `frac = 0.75`) doesn't exercise this, but the component is reused on the Table screen (spec §7.4 line 975) and the standing card (spec §7.2 line 891) where standings fluctuate round-by-round. A player who overtakes the leader mid-league will see a broken GapRail with no error path.

The spec source (§5.8 line 605) has the identical defect — `GeneratedStatus` and `GapRail` are both cases where byte-verbatim copying propagated a spec-source bug into shipped code. Because the implementer modified this file (adding `leaderName`) and shipped it as a production-ready primitive, they own this defect.

**Fix:**

```swift
private var frac: CGFloat {
    guard leader > 0 else { return 0 }
    return min(1, max(0, CGFloat(mine) / CGFloat(leader)))
}
```

Note: if `mine == leader` semantically means "you are the leader", callers will likely want a different affordance entirely (a crown, a "you lead by X" label) rather than a marker pinned to the right edge. That is a design decision for the consuming screen — but the component itself must not silently overflow.

---

### WR-02: StrengthBar segment widths don't subtract inter-segment spacing → proportions render off

**File:** `EDGE/Sources/DesignSystem/Components/StrengthBar.swift:9-15,24-26`
**Issue:**

```swift
GeometryReader { geo in
    HStack(spacing: 3) {
        seg(home, Color(hex: "9DBBA9"), geo.size.width)   // each seg gets the FULL width
        seg(draw, Theme.textMute,       geo.size.width)
        seg(away, Color(hex: "A9C2E6"), geo.size.width)
    }
}.frame(height: 8)

private func seg(_ p: Double, _ c: Color, _ total: CGFloat) -> some View {
    Capsule().fill(c).frame(width: shown ? max(4, total * p) : 0)
}
```

Each segment's width is `geo.size.width * p`, and the three widths plus `2 × 3pt` HStack spacing sum to:

```
W·home + W·draw + W·away + 6pt = W·(home + draw + away) + 6pt
```

For the gallery's POR/COD demo (`home: 0.74, draw: 0.20, away: 0.06`), `home + draw + away = 1.0`, so the HStack content width is `W + 6pt` — a **6pt horizontal overflow** that SwiftUI resolves by either clipping at the FrostCard edge or extending into the right padding, slightly compressing/distorting the visual proportions.

Worse cases:
- **Probabilities that don't sum to exactly 1.0** (the realistic case — oddses rounded to 2 decimals like `0.34/0.33/0.34 = 1.01`): overflow grows beyond 6pt.
- **Very weak outcomes** (e.g., `away = 0.02`): the `max(4, ...)` clamp forces a 4pt minimum width, further distorting proportions. Three minimum-4pt segments + 6pt spacing = 18pt floor even when probabilities are vanishingly small.

Spec-verbatim (§5.7 line 589-591 has the identical formula). The gallery demo IS affected — anyone scrolling the ComponentGallery sees slightly compressed sage/gray/blue segments vs. the design intent.

**Fix:** subtract the spacing from the available width before computing per-segment widths:

```swift
GeometryReader { geo in
    let spacing: CGFloat = 3
    let usable = max(0, geo.size.width - spacing * 2)   // account for 2 gaps between 3 segments
    HStack(spacing: spacing) {
        seg(home, Color(hex: "9DBBA9"), usable)
        seg(draw, Theme.textMute,       usable)
        seg(away, Color(hex: "A9C2E6"), usable)
    }
}.frame(height: 8)
```

(If exact-proportion rendering matters more than minimum-visibility, also drop the `max(4, …)` floor or reduce it to `max(1, …)`.)

---

## Info

### IN-01: Sparkline uses `ForEach(values.indices, id: \.self)` — positional identity

**File:** `EDGE/Sources/DesignSystem/Components/Sparkline.swift:8`
**Issue:**

`ForEach(values.indices, id: \.self)` uses index position as identity. This is conceptually correct for Sparkline (position = which pick in the recent-points trend), so value-only updates render fine. But it's an Apple-documented anti-pattern when the underlying array can change length, and the consuming screen (Insights, spec §7.5 line 983) will pass a `recentPoints` array that grows over time. Consider `Array(values.enumerated()).map(IdentifiedValue.init)` for explicit clarity. Spec-verbatim.
**Fix:** Optional — current pattern works for all expected mutations. If refactor desired:

```swift
private struct Bar: Identifiable { let id: Int; let value: Int }
// ...
ForEach(values.indices.map { Bar(id: $0, value: values[$0]) }) { bar in
    RoundedRectangle(cornerRadius: 2)
        .fill(bar.value == 0 ? Theme.track : Theme.iridLilac)
        .frame(height: max(2, geo.size.height * CGFloat(bar.value) / CGFloat(maxV)))
}
```

### IN-02: Animated components don't replay when their inputs change after `.onAppear`

**File:** `EDGE/Sources/DesignSystem/Components/SoftRing.swift:20-24`, `StrengthBar.swift:19-22`, `GapRail.swift:28-31`
**Issue:**

All three read their initial value in `.onAppear` only. If a parent passes new `value` / `home,draw,away` / `mine,leader` without remounting the view, the new state renders without re-animating. The spec's stated replay contract (spec §5.4, §8.5: `ScrollView { content.id(store.generation) }`) handles this by remounting — so this is intentional — but a `.onChange(of: value)` would make each component self-contained and remove a footgun for future callers who forget to remount.
**Fix:** Optional. Add `.onChange(of: value) { … }` clauses mirroring the `.onAppear` body if self-contained replay is desired.

### IN-03: GeneratedStatus `withAnimation { … repeatForever }` is the less-robust SwiftUI pulse idiom

**File:** `EDGE/Sources/DesignSystem/Components/GeneratedStatus.swift:10`
**Issue:**

`withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) { pulse = true }` inside `.onAppear` works in practice, but the more reliable iOS-18 idiom is `.animation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true), value: pulse)` attached to the dot. Some SwiftUI versions are flaky about `withAnimation + repeatForever` transaction chaining on first appear. Spec-verbatim — affects robustness, not correctness today.
**Fix:** When CR-01 is addressed, prefer:

```swift
Circle().fill(Theme.spark).frame(width: 7, height: 7)
    .scaleEffect(pulse ? 1.2 : 0.8).opacity(pulse ? 1 : 0.5)
    .animation(reduceMotion ? nil : .easeInOut(duration: 1.2).repeatForever(autoreverses: true), value: pulse)
    .onAppear { pulse = true }
```

### IN-04: ComponentGallery has no `#if DEBUG` guard — will be dead code after Phase 4

**File:** `EDGE/Sources/Features/Shell/ComponentGallery.swift:1-80` (and `EDGEApp.swift:9`)
**Issue:**

Plan 03-03 SUMMARY states Phase 4 swaps `ComponentGallery()` for `RootView` in `EDGEApp.swift`. Once that happens, `ComponentGallery.swift` becomes unreferenced release-build dead code (still compiled, still ships in the binary). Plan-mandated so INFO, but the gallery is a QA surface and should be wrapped in `#if DEBUG` so it can't ship.
**Fix:** Wrap the entire file body in `#if DEBUG` / `#endif`. (Or delete it once Phase 4 lands.)

### IN-05: `ComponentGallery` evaluates `Date.now` on every body recomputation

**File:** `EDGE/Sources/Features/Shell/ComponentGallery.swift:64-65`
**Issue:**

`GeneratedStatus(updatedAt: .now)` re-evaluates `.now` each time the gallery's body recomputes. The gallery is currently stateless so this rarely fires, but the "Generated just now" text is pinned to whatever `.now` was at last render and never updates. Real consuming screens (Phase 5) will pass `store.updatedAt`. INFO — only matters if the gallery is reused as a long-running screen.
**Fix:** For the gallery only — pass a fixed `Date(timeIntervalSince1970: …)` literal, or accept the staleness.

---

_Reviewed: 2026-06-17T16:05:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
