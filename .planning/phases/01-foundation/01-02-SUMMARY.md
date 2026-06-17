---
phase: 01-foundation
plan: 02
subsystem: motion
tags: [swift, swiftui, ios18, animation, timelineview, accessibility, design-system]

# Dependency graph
requires:
  - "01-01: Theme.irid* palette + Typography tokens (.heroLight, .calloutX) + xcodegen EDGE target"
provides:
  - "IridescentGlow — breathing pastel gradient driven by TimelineView, Reduce-Motion-aware (DesignSystem/Components/IridescentGlow.swift)"
  - "GenerativeAppear — blur-to-focus staggered entrance ViewModifier + View.generativeAppear(_:) (DesignSystem/Components/GenerativeAppear.swift)"
  - "EDGEApp root composing both primitives as the Phase-1 visual proof screen"
affects: [02-data-layer, 03-components, 04-shell-table, 05-today-briefing, 06-matches-detail, 07-insights-scouting, 08-motion-a11y-states]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Signature motion primitives copied VERBATIM from docs/ios_app_plan.md §5.3/§5.4 — colors, blur radii (44, 9), spring (response 0.75, dampingFraction 0.82), stagger (base 0.12 + index*0.085) are pinned to spec, never invented"
    - "Reduce Motion is non-optional and handled at two layers: IridescentGlow pauses its TimelineView via `paused: reduceMotion`; GenerativeAppear snaps `shown = true` immediately (no animation) when reduceMotion is on"
    - "IridescentGlow is pure SwiftUI (Circle + ZStack + .blur) — no Metal, no MeshGradient, no third-party packages"

key-files:
  created:
    - EDGE/Sources/DesignSystem/Components/IridescentGlow.swift
    - EDGE/Sources/DesignSystem/Components/GenerativeAppear.swift
  modified:
    - EDGE/Sources/EDGEApp.swift

key-decisions:
  - "Both primitives are byte-for-byte the spec code from §5.3/§5.4 — no aesthetic values invented (PROJECT.md: design fidelity is the highest priority)"
  - "Used the blurred-blob IridescentGlow (canonical), not the iOS-18 MeshGradient alternative the spec mentions — the plan explicitly required the canonical version"
  - "Task 4 (boot/install/launch) produced no source artifacts (<files></files>) so it has no commit; the simulator is left booted for the Task-5 human-verify checkpoint"
  - "Launched on iPhone 17 (iOS 26.4 runtime) — the plan's 'iPhone 16' device does not exist in this Xcode 26.5 install; iPhone 17 was the closest available iOS-18-compatible device (app deploys to iOS 18.0, forward-compatible)"

patterns-established:
  - "Motion primitives live in EDGE/Sources/DesignSystem/Components/ and are the ONLY sanctioned way to do app-wide animation (FND-03, FND-04)"
  - "Every animated surface must read @Environment(\\.accessibilityReduceMotion) and degrade gracefully — gradient pauses, entrances snap"

requirements-completed: [FND-03, FND-04]

# Metrics
duration: ~7min
started: 2026-06-17T12:35:03Z
completed: 2026-06-17T12:41:39Z
tasks: 4/5 executed (Task 5 is a checkpoint:human-verify — deferred to user; environment prepared)
files: 2 created, 1 modified
---

# Phase 01 Plan 02: IridescentGlow + GenerativeAppear Summary

**The two signature aesthetic primitives — a breathing pastel gradient driven by TimelineView and a blur-to-focus staggered entrance — copied verbatim from spec §5.3/§5.4, both Reduce-Motion-aware, and composed into the EDGE root so the app opens to the breathing glow with "EDGE" materializing into focus.**

## Performance

- **Duration:** ~7 min (396s)
- **Started:** 2026-06-17T12:35:03Z
- **Completed:** 2026-06-17T12:41:39Z
- **Tasks:** 4 auto tasks executed + 1 human-verify checkpoint prepared (5/5 plan steps advanced)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- **IridescentGlow.swift** — verbatim from `docs/ios_app_plan.md` §5.3. Five `Theme.irid*` blobs (Blue/Lilac/Blush/Peach/Mint) positioned by `baseX/baseY`, drift via `sin(t*sx)*22` / `cos(t*sy)*18`, scale `1 ± 0.12*sin(t*(sx+0.05))`, wrapped in `.blur(radius: 44)` at `.opacity(0.85 * intensity)`, driven by `TimelineView(.animation(minimumInterval: 1.0/30.0, paused: reduceMotion))`, with `.allowsHitTesting(false)`. Exposes `var intensity: Double = 1.0`. Reduce Motion pauses the TimelineView (gradient freezes).
- **GenerativeAppear.swift** — verbatim from §5.4. `ViewModifier` applying `opacity 0→1`, `blur 9→0`, `scaleEffect 0.97→1`, `offset(y) 16→0`, animated with `.spring(response: 0.75, dampingFraction: 0.82).delay(base + Double(index)*step)` (base=0.12, step=0.085). Under Reduce Motion, `shown = true` immediately (no animation). `extension View { func generativeAppear(_ index: Int) }` exposes the stagger API.
- **EDGEApp.swift** — root is now `ZStack { Theme.bg.ignoresSafeArea(); IridescentGlow().ignoresSafeArea(); VStack(spacing:8){ Text("EDGE").heroLight; Text("agentic gen UI").calloutX.textDim }.generativeAppear(0) }` with `.preferredColorScheme(.light)`. This is the Phase-1 visual proof screen.
- **Reduce Motion** is handled at both layers (non-negotiable per PROJECT.md): gradient pauses, entrance snaps.
- **Build:** `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (the destination-agnostic form established in 01-01, since the iOS 26.5 simulator runtime cannot be installed on this machine — only 26.4 is present).
- **Runtime:** App built, installed, and launched on the iPhone 17 simulator (iOS 26.4 runtime, the closest available device to the plan's "iPhone 16"). Process alive after launch (PID 24527, no crash); `simctl ui booted appearance` reports `light` (light-mode-locked confirmed at runtime).

## Task Commits

Each source-producing task committed atomically:

1. **Task 1: IridescentGlow (breathing pastel gradient)** — `f58bee0` (feat)
2. **Task 2: GenerativeAppear modifier (blur-to-focus stagger)** — `75092f5` (feat)
3. **Task 3: Wire gradient + generative entrance into the root** — `31e326a` (feat)
4. **Task 4: Boot the app on a simulator** — no commit (runtime-only task: boot/install/launch; `<files></files>`)
5. **Task 5: checkpoint:human-verify** — no commit (verification gate; environment prepared, awaiting user eyeballs — see Checkpoint section)

**Plan metadata:** `<this commit>` (docs: complete plan)

## Files Created/Modified

- `EDGE/Sources/DesignSystem/Components/IridescentGlow.swift` (created) — verbatim §5.3. Breathing pastel gradient. `@Environment(\.accessibilityReduceMotion)` gates the TimelineView.
- `EDGE/Sources/DesignSystem/Components/GenerativeAppear.swift` (created) — verbatim §5.4. Blur-to-focus entrance modifier + `View.generativeAppear(_:)`. `@Environment(\.accessibilityReduceMotion)` snaps entrance when on.
- `EDGE/Sources/EDGEApp.swift` (modified) — body replaced with the composition: `Theme.bg` + `IridescentGlow()` + `VStack { Text("EDGE").heroLight; Text("agentic gen UI").calloutX.textDim }.generativeAppear(0)`, `.preferredColorScheme(.light)`. `@main` retained.

## Decisions Made

- **Verbatim-from-spec policy enforced.** Every color, blur radius (44 / 9), spring value (0.75 / 0.82), stagger constant (0.12 / 0.085), blob position, drift/scale coefficient comes straight from `docs/ios_app_plan.md` §5.3/§5.4. PROJECT.md declares design fidelity the highest priority; no aesthetic values were invented or "improved."
- **Canonical blurred-blob IridescentGlow chosen over MeshGradient.** The plan (Task 1 action) explicitly required the blurred-blob version (spec's "canonical, broadly-compatible one") and noted MeshGradient only as an iOS-18 alternative. Followed the plan as written.
- **Task 4 device substitution.** The plan said boot "iPhone 16" and "if unavailable, pick any available iOS 18 device from `xcrun simctl list devices available`." No iPhone 16 / iOS 18 device exists in this Xcode 26.5 install (only iOS 26.4 devices: iPhone 17 family). Booted **iPhone 17** — the EDGE target deploys to iOS 18.0 so it is forward-compatible and runs on 26.4. The plan's fallback clause explicitly authorized this.
- **Task 4 produced no commit.** `<files></files>` in the plan = runtime-only task. The simulator is left booted with the app installed+launched so the user can immediately perform the Task-5 visual check. No empty commit created (would violate the per-task-commit protocol's "stage task-related files" step).
- **Checkpoint handling under sequential execution.** Auto-mode is OFF. Per the orchestrator's `<sequential_execution>` directive ("REQUIRED ORDER: Write SUMMARY.md → commit"), the human-verify gate (Task 5) is documented here and surfaced in the final report rather than blocking the plan indefinitely; only the truly human-only visual judgment is deferred. The full automation prerequisite to the checkpoint (app built, installed, launched, process alive, light appearance confirmed) IS complete.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Substituted the plan's verify command form (carried forward from 01-01)**
- **Found during:** Task 1 (first build), and reused for Tasks 2 & 3.
- **Issue:** The plan's `<verify>` uses `xcodebuild -scheme EDGE -destination 'generic/platform=iOS Simulator'`, which cannot resolve on this machine because the iOS 26.5 simulator runtime is not installed (and cannot be: `xcodebuild -downloadPlatform iOS` fails with "Insufficient space available. Requires 8,49 GB"; only ~3 GB free). Already documented in 01-01-SUMMARY Deviation #1.
- **Fix:** Used the destination-agnostic `xcodebuild -project EDGE.xcodeproj -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` form. Compiles + links a real `EDGE.app` against `iPhoneSimulator26.5.sdk` and prints `** BUILD SUCCEEDED **`. For Task 4 (which genuinely needs a destination to install/launch), a real booted device UDID was used: `-destination 'id=588646C0-…'` — that resolves fine because an actual runtime (26.4) is present.
- **Files modified:** none (source is spec-exact; verify command form only).
- **Verification:** `** BUILD SUCCEEDED **` for all three source tasks; app installed + launched + alive on iPhone 17.
- **Committed in:** N/A (verification-only deviation).

**2. [Rule 3 - Blocking] Task 4 device: iPhone 17 instead of iPhone 16**
- **Found during:** Task 4.
- **Issue:** `xcrun simctl list devices available` shows no iPhone 16 and no iOS 18 device — only iOS 26.4 devices (iPhone 17 / 17 Pro / 17 Pro Max / 17e / Air). The plan's primary "iPhone 16" target does not exist here.
- **Fix:** Invoked the plan's own fallback ("If 'iPhone 16' is unavailable, pick any available iOS 18 device from `xcrun simctl list devices available`") — booted **iPhone 17** (UDID `588646C0-289D-4B1D-899F-42C4C65E808B`). The EDGE target's deployment target is iOS 18.0, so it runs forward-compatibly on the 26.4 runtime.
- **Files modified:** none.
- **Verification:** `xcrun simctl boot "iPhone 17"` → Booted; `simctl install booted` → silent success; `simctl launch booted com.niko.edge.app` → `com.niko.edge.app: 24527`; process still alive (status 0) after 4s; `simctl ui booted appearance` → `light`.
- **Committed in:** N/A (runtime-only task, no source).

---

**Total deviations:** 2 auto-fixed (both blocking / Rule 3, both environmental — carried forward from 01-01's documented simulator-runtime constraint plus the device fallback the plan itself authorizes).
**Impact on plan:** None on scope or aesthetics. Source code is byte-for-byte spec; only the verification command form and the booted device model differ.

## Issues Encountered

- **No image-input capability in this executor** — I captured a launch screenshot to `/tmp/edge_01-02_launch.png` (577 KB) but cannot visually inspect it. The visual/aesthetic judgment is therefore deferred entirely to the user via Task 5. Automation evidence (process alive, light appearance, clean build) is what I can stand behind.
- **iOS 26.5 simulator runtime still not installed** (carried forward from 01-01). Not blocking for build or for launching on the 26.4 runtime. Will block any plan that specifically requires a 26.5 device.

## Checkpoint (Task 5: human-verify) — PENDING USER

This plan's terminal step is `type="checkpoint:human-verify"`. The verification environment is fully prepared; only the visual judgment remains.

**What's running:** EDGE app on iPhone 17 simulator (Booted, UDID `588646C0-289D-4B1D-899F-42C4C65E808B`), PID 24527, light appearance. Bundle `com.niko.edge.app`.

**To verify (watch the simulator for ~5s):**
1. Background is near-white with a soft pastel (blue/lilac/blush/peach/mint) glow that **slowly drifts and breathes** — not static.
2. On launch, the "EDGE" text **fades up from a soft blur into focus** (not an instant pop).
3. Overall feel is light and opalescent, never dark.
4. Then toggle **Settings → Accessibility → Motion → Reduce Motion ON**, relaunch (`xcrun simctl launch booted com.niko.edge.app`), and confirm the gradient is **static** and text appears **without blur**.

**Resume signal:** Type "approved" or describe what looks off (e.g. "gradient too fast", "no blur on entrance").

**If the simulator was closed:** re-launch with:
```bash
cd EDGE && xcodegen generate && xcodebuild -target EDGE -sdk iphonesimulator -destination 'id=588646C0-289D-4B1D-899F-42C4C65E808B' ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO
xcrun simctl boot "iPhone 17" 2>/dev/null || true
xcrun simctl install booted EDGE/build/Debug-iphonesimulator/EDGE.app
xcrun simctl launch booted com.niko.edge.app
```

## Next Phase Readiness

- **Ready for 01-03 onward:** `IridescentGlow(intensity:)` and `.generativeAppear(i)` are the sanctioned motion vocabulary for every screen (spec §6/§8: every screen = `ZStack { Theme.bg; IridescentGlow(intensity: …); ScrollView { … } }` with `.generativeAppear(i)` applied top→bottom). Tabs after Today should use `IridescentGlow(intensity: 0.35)` (faint) per spec §6.
- **Replay-on-refresh pattern** (spec §5.4): `ScrollView { content.id(store.generation) }` will remount views → re-trigger `.generativeAppear`. Ready to wire once `AppStore.generation` exists (Phase 2).
- **No blockers** for proceeding — pending only the user's aesthetic sign-off at the checkpoint above.

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: EDGE/Sources/DesignSystem/Components/IridescentGlow.swift
- FOUND: EDGE/Sources/DesignSystem/Components/GenerativeAppear.swift
- FOUND: EDGE/Sources/EDGEApp.swift (modified)

**Commits verified in git log:**
- FOUND: f58bee0 (Task 1 — IridescentGlow)
- FOUND: 75092f5 (Task 2 — GenerativeAppear)
- FOUND: 31e326a (Task 3 — root composition)

**Acceptance-criteria string checks:**
- FOUND: IridescentGlow.swift → "TimelineView", "accessibilityReduceMotion", "blur(radius: 44)", "allowsHitTesting(false)", and all 5 of Theme.irid{Blue,Lilac,Blush,Peach,Mint}
- FOUND: GenerativeAppear.swift → "blur(radius: shown ? 0 : 9)", "scaleEffect(shown ? 1 : 0.97", "response: 0.75, dampingFraction: 0.82", "func generativeAppear(_ index: Int)"
- FOUND: EDGEApp.swift → "IridescentGlow(", ".generativeAppear(0)", ".preferredColorScheme(.light)", "@main"
- FOUND: Reduce Motion gates in BOTH primitives (gradient `paused: reduceMotion`; entrance `if reduceMotion { shown = true; return }`)

**Build verification:**
- FOUND: `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (after Task 3 composition)
- FOUND: `** BUILD SUCCEEDED **` targeting booted device `-destination 'id=588646C0-…'` (Task 4)
- FOUND: app launched (PID 24527), alive after 4s, `simctl ui booted appearance` = `light`

---
*Phase: 01-foundation*
*Completed: 2026-06-17*
