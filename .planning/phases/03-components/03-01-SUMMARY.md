---
phase: 03-components
plan: 01
subsystem: ui
tags: [swift, swiftui, ios18, design-system, data-viz, animation, accessibility, reduce-motion]

# Dependency graph
requires:
  - "01-01: Theme tokens (card/hairline/track/shadow/iridBlue/iridLilac/spark/textMute/s2/s4/rLg) + Color(hex:) initializer"
  - "01-02: Components/ directory + generative-motion vocabulary (these components compose with GenerativeAppear/IridescentGlow in later phases)"
provides:
  - "FrostCard<Content> — frosted glass container (.ultraThinMaterial + Theme.card overlay + 1pt Theme.hairline strokeBorder + soft Theme.shadow)"
  - "SoftRing<Center> — track + tier-colored arc that draws on appear (spring 1.0/0.9 delay 0.25), Reduce-Motion-safe, custom @ViewBuilder center"
  - "StrengthBar — pastel 1X2 home/draw/away capsule bar that fills on appear (easeOut 0.8 delay 0.2), Reduce-Motion-safe, eyebrow labels"
  - "GapRail — you->leader timeline rail (iridescent iridBlue->iridLilac fill + white Theme.spark-stroked marker) that slides on appear (spring 1.0/0.9 delay 0.3), Reduce-Motion-safe, leaderName param"
affects: [03-02, 04-shell, 05-today, 06-matches, 07-table, 08-insights]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural data-viz components are hand-rolled with Shape/Capsule/Circle/LinearGradient only — no third-party packages, no Charts framework (PROJECT.md constraint)"
    - "Every animated component reads @Environment(\\.accessibilityReduceMotion) and snaps to its final state when true — Reduce-Motion-safe is a non-negotiable component contract"
    - "Components consume ONLY Theme tokens (card/hairline/track/shadow/iridBlue/iridLilac/spark/text/textDim/textMute) + the two spec-mandated inline hexes (StrengthBar sage 9DBBA9 / blue A9C2E6). No hardcoded colors elsewhere."
    - "Source for each component is byte-for-byte docs/ios_app_plan.md §5.5-§5.8 (inline // comments preserved verbatim — CLAUDE.md allows comments the spec shows)"

key-files:
  created:
    - EDGE/Sources/DesignSystem/Components/FrostCard.swift
    - EDGE/Sources/DesignSystem/Components/SoftRing.swift
    - EDGE/Sources/DesignSystem/Components/StrengthBar.swift
    - EDGE/Sources/DesignSystem/Components/GapRail.swift
  modified: []

key-decisions:
  - "All four component bodies are verbatim copies of docs/ios_app_plan.md §5.5-§5.8 — corner radii, blur material, stroke widths, shadow radii/opacity, gradient stops, animation curves (spring 1.0/0.9 vs easeOut 0.8), delays (0.25/0.2/0.3), and Reduce-Motion snap branches all match the spec exactly. PROJECT.md makes design fidelity the highest priority; these four are the load-bearing visual vocabulary of every screen."
  - "GapRail: added `let leaderName: String` parameter and replaced the spec's placeholder expression `\\(/* leaderName passed in */ \"leader\")` with `\\(leaderName)` — exactly as the plan's Task 4 action mandated. Everything else in GapRail is byte-verbatim from §5.8. No other component required a deviation."
  - "Inline `// soft sage (home)`, `// gray (draw)`, `// soft blue (away)`, `// soft, not neon`, `// 18, 24` comments are kept because they appear in the spec source — CLAUDE.md's 'no comments unless the spec shows them' rule is honored."

patterns-established:
  - "Animated-on-appear contract: `@State private var animated: …` + `.onAppear { if reduceMotion { animated = final; return }; withAnimation(curve) { animated = final } }`. Every future data-viz component that animates in (FriendDots, InsightRing, etc.) should follow this shape."
  - "Soft shadow contract: `shadow(color: <tint>.opacity(0.10-0.25), radius: small, y: small)` — never a hard neon glow. PROJECT.md design doctrine."

requirements-completed: [COMP-01]

# Metrics
duration: ~5min
started: 2026-06-17T14:40Z
completed: 2026-06-17T14:45Z
tasks: 4/4
files: 4 created, 0 modified
---

# Phase 03 Plan 01: Structural Data-Viz Components (FrostCard / SoftRing / StrengthBar / GapRail) Summary

**Four hand-rolled SwiftUI data-viz components — the frosted glass surface plus the three animated feed-visuals (drawing ring, pastel 1X2 bar, you->leader timeline) — copied byte-for-byte from spec §5.5-§5.8, all building clean and Reduce-Motion-safe.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-17T14:40Z
- **Completed:** 2026-06-17T14:45Z
- **Tasks:** 4/4 auto tasks executed
- **Files modified:** 4 (4 created, 0 modified)

## Accomplishments

- **FrostCard** — verbatim §5.5. `.ultraThinMaterial` background + `Theme.card` fill overlay + `RoundedRectangle(... Theme.rLg, .continuous)` with a 1pt `Theme.hairline` strokeBorder + `.shadow(color: Theme.shadow.opacity(0.10), radius: 24, x: 0, y: 14)`. Default padding `Theme.s4`, radius `Theme.rLg`, `@ViewBuilder var content`. The frosted container every screen composes inside.
- **SoftRing** — verbatim §5.6. `Theme.track` circle + a tier-colored `Circle().trim(from: 0, to: animated)` arc with `.round` line caps, rotated `-90°`, soft `.shadow(color: color.opacity(0.25), radius: 6)` (soft, not neon), and a `@ViewBuilder center`. On appear, animates 0->clamped value via `.spring(response: 1.0, dampingFraction: 0.9).delay(0.25)`; under `accessibilityReduceMotion` snaps immediately. Defaults: lineWidth 8, size 108.
- **StrengthBar** — verbatim §5.7. `GeometryReader` HStack of three capsule segments — home `Color(hex:"9DBBA9")` (soft sage), draw `Theme.textMute`, away `Color(hex:"A9C2E6")` (soft blue) — widths animate from 0 via `.easeOut(duration: 0.8).delay(0.2)` (snap under Reduce Motion). Eyebrow labels `homeCode / "draw" / awayCode`. Height 8.
- **GapRail** — verbatim §5.8 + plan-mandated `leaderName` param. `Theme.track` rail, iridescent fill `LinearGradient([Theme.iridBlue, Theme.iridLilac])` to `mine/leader` fraction, white marker circle (stroked `Theme.spark`, lineWidth 2) sliding to that fraction via `.spring(response: 1.0, dampingFraction: 0.9).delay(0.3)` (snap under Reduce Motion). Labels `"\(mine) you"` / `"\(leader) \(leaderName)"`, `.monospacedDigit()`.
- **Build:** `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (destination-agnostic form established in 01-01; iOS 26.5 simulator runtime unavailable on this machine, only 26.4 present).

## Task Commits

Each task was committed atomically:

1. **Task 1: FrostCard frosted glass container** — `ad75e58` (feat)
2. **Task 2: SoftRing drawing ring** — `09951ec` (feat)
3. **Task 3: StrengthBar pastel 1X2 bar** — `d7fd412` (feat)
4. **Task 4: GapRail you->leader timeline** — `6fcc7f6` (feat)

**Plan metadata:** `<this commit>` (docs: complete plan)

## Files Created/Modified

- `EDGE/Sources/DesignSystem/Components/FrostCard.swift` (created) — verbatim §5.5 frosted glass surface: ultraThinMaterial + Theme.card + Theme.hairline + Theme.shadow(0.10).
- `EDGE/Sources/DesignSystem/Components/SoftRing.swift` (created) — verbatim §5.6 drawing ring with custom @ViewBuilder center, soft shadow, spring-on-appear, Reduce-Motion-safe.
- `EDGE/Sources/DesignSystem/Components/StrengthBar.swift` (created) — verbatim §5.7 three-capsule pastel 1X2 bar with eyebrow labels, easeOut-on-appear, Reduce-Motion-safe.
- `EDGE/Sources/DesignSystem/Components/GapRail.swift` (created) — verbatim §5.8 you->leader timeline rail with iridescent fill + sliding marker, plus plan-mandated `leaderName: String` parameter.

## Decisions Made

- **Byte-verbatim-from-spec policy enforced across all four components.** Corner radii, blur material, stroke widths, shadow radii/opacity, gradient stops, animation curves (spring 1.0/0.9 vs easeOut 0.8), delays (0.25/0.2/0.3), and Reduce-Motion snap branches all match `docs/ios_app_plan.md` §5.5-§5.8 exactly. No values invented. PROJECT.md makes design fidelity the highest priority; these four are the vocabulary every later screen composes.
- **GapRail `leaderName` param wired into the label.** The spec snippet's trailing-label expression `\(/* leaderName passed in */ "leader")` was a placeholder. The plan's Task 4 action explicitly mandated adding a `leaderName: String` parameter and replacing the placeholder with it — so the label now renders `"\(leader) \(leaderName)"` (e.g. "24 Alex"). This is plan-as-written, not a deviation.
- **Inline spec comments preserved.** `// soft sage (home)`, `// gray (draw)`, `// soft blue (away)` (StrengthBar), `// soft, not neon` (SoftRing), `// 18, 24` (GapRail) all appear in the spec source and are kept verbatim. CLAUDE.md / PROJECT.md forbid comments unless the spec shows them — honored.
- **No code added beyond the spec bodies.** No `#Preview` blocks (spec does not show them for these components; sibling plan 03-02 or a later preview-gallery phase may add them), no extra modifiers, no convenience initializers. Adding them now would risk drift from spec values.

## Deviations from Plan

None — plan executed exactly as written. The only environmental substitution is the verify-command form: `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` instead of the plan's `xcodebuild -project EDGE.xcodeproj -scheme EDGE -destination 'generic/platform=iOS Simulator' build CODE_SIGNING_ALLOWED=NO`. This is the same Rule-3 blocking constraint already documented in 01-01-SUMMARY Deviation #1 (iOS 26.5 simulator runtime cannot be installed on this machine — only 26.4 is present; `xcodebuild -downloadPlatform iOS` fails with "Insufficient space available. Requires 8,49 GB"). The destination-agnostic form still compiles+links a real `EDGE.app` against `iPhoneSimulator26.5.sdk` and prints `** BUILD SUCCEEDED **`.

## Issues Encountered

None.

## User Setup Required

None — pure structural view components. No external services, no env vars, no secrets.

## Next Phase Readiness

- **Ready for 03-02 (sibling — SoftPill / chips / cards / dots):** SoftPill can pair `Format.tierStyle` / `Format.leverageChip` / `Format.leaderChip` / `Format.outcomeChip` (all return `(text, fg, bg)` tuples) directly into a chip view. The `.foregroundStyle` / `.background` soft-state token contract is already in Theme.
- **Ready for 04-shell:** `FrostCard` is the card surface every screen wraps content in. Shell/RootView (Phase 4) can use it immediately.
- **Ready for 05-today:** `GapRail` is the standing-card timeline (you->leader); `SoftRing` is the next-match spotlight's exact-chance ring (consumes `Format.ringFill` + `Format.tierRingColor`); `StrengthBar` is the matchup bar (consumes Match.odds home/draw/away). All three key their entrance on `store.generation` via the Phase-1 `GenerativeAppear` primitive so a pull-to-refresh replays the assembly.
- **Replay-on-refresh contract:** the components read their initial state in `.onAppear`, so wrapping a parent in `ScrollView { content.id(store.generation) }` (per spec §5.4) will remount them and replay each animation on every `store.refresh()`. No component-internal change needed.
- **No blockers.**

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: EDGE/Sources/DesignSystem/Components/FrostCard.swift
- FOUND: EDGE/Sources/DesignSystem/Components/SoftRing.swift
- FOUND: EDGE/Sources/DesignSystem/Components/StrengthBar.swift
- FOUND: EDGE/Sources/DesignSystem/Components/GapRail.swift

**Commits verified in git log:**
- FOUND: ad75e58 (Task 1 — FrostCard)
- FOUND: 09951ec (Task 2 — SoftRing)
- FOUND: d7fd412 (Task 3 — StrengthBar)
- FOUND: 6fcc7f6 (Task 4 — GapRail)

**Acceptance-criteria string checks:**
- FOUND: FrostCard.swift → "ultraThinMaterial", "Theme.hairline", "Theme.shadow.opacity(0.10)"
- FOUND: SoftRing.swift → "trim(from: 0, to: animated)", "accessibilityReduceMotion", "dampingFraction: 0.9", "color.opacity(0.25)"
- FOUND: StrengthBar.swift → 'Color(hex: "9DBBA9")', 'Color(hex: "A9C2E6")', "accessibilityReduceMotion"
- FOUND: GapRail.swift → "Theme.iridBlue", "Theme.spark", "accessibilityReduceMotion", "leaderName"

**Build verification:**
- FOUND: `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (after Task 4)

**Scope boundary respected:**
- Only the 4 plan-listed files created. Sibling plan 03-02's files (SoftPill etc.) NOT touched. STATE.md / ROADMAP.md / REQUIREMENTS.md NOT modified (per orchestrator instruction).

---
*Phase: 03-components*
*Completed: 2026-06-17*
