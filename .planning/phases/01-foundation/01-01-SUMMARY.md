---
phase: 01-foundation
plan: 01
subsystem: infra
tags: [swift, swiftui, ios18, xcodegen, design-system, design-tokens]

# Dependency graph
requires: []
provides:
  - "EDGE.xcodeproj — xcodegen-generated iOS 18 SwiftUI app target, light-mode-locked"
  - "Color(hex:) initializer (DesignSystem/ColorHex.swift)"
  - "Theme tokens — surfaces, text, iridescent palette, soft-state pairs, spacing, radii (DesignSystem/Theme.swift)"
  - "Typography scale — 8 font tokens + Eyebrow view (DesignSystem/Typography.swift)"
  - "Minimal @main app entry rendering Theme.bg + 'EDGE' in .heroLight, .preferredColorScheme(.light)"
affects: [01-02, 02-foundation, 03-designsystem-components, 04-shell, 05-today, 06-matches, 07-table, 08-insights]

# Tech tracking
tech-stack:
  added: [Swift 5.9, SwiftUI (iOS 18+), xcodegen 2.45.4, Xcode 26.5]
  patterns:
    - "Single source of truth for colors/fonts: Theme.swift + Typography.swift only — no hardcoded colors anywhere else"
    - "xcodegen owns EDGE.xcodeproj; project.yml is the source of truth (the .xcodeproj is gitignored and regenerated)"
    - "Sources rooted at EDGE/Sources/ with DesignSystem/ subdir (spec §2 layout, with Color+Hex → ColorHex rename to avoid '+' in paths)"

key-files:
  created:
    - EDGE/project.yml
    - EDGE/Sources/DesignSystem/ColorHex.swift
    - EDGE/Sources/DesignSystem/Theme.swift
    - EDGE/Sources/DesignSystem/Typography.swift
    - EDGE/Sources/EDGEApp.swift
  modified:
    - .gitignore

key-decisions:
  - "Sources rooted at EDGE/Sources/ (not EDGE/ root) per plan; Color+Hex.swift renamed to ColorHex.swift to avoid '+' in file paths (spec §2 names preserved otherwise)"
  - "EDGE.xcodeproj/ is gitignored — regenerable from project.yml via `xcodegen generate`. Only project.yml + Sources/ are committed."
  - "Verify command substituted: `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build` instead of plan's `-scheme ... -destination 'generic/platform=iOS Simulator'` — see Deviations"

patterns-established:
  - "Design tokens live ONLY in Theme.swift / Typography.swift (FND-01, FND-02)"
  - "Color hex values are non-negotiable — copy verbatim from docs/ios_app_plan.md §5.1; never invent or 'improve'"
  - "App is light-mode-locked at two layers: INFOPLIST_KEY_UIUserInterfaceStyle=Light (OS-level) + .preferredColorScheme(.light) (SwiftUI-level)"

requirements-completed: [FND-01, FND-02]

# Metrics
duration: ~10min
completed: 2026-06-17
---

# Phase 01 Plan 01: Foundation (App Scaffold + Design Tokens) Summary

**Buildable iOS 18 SwiftUI app (xcodegen-owned) with verbatim-from-spec Theme + Typography token layer and a light-locked `@main` entry — every later phase composes from these tokens.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-17T14:08Z
- **Completed:** 2026-06-17T14:20Z
- **Tasks:** 3/3
- **Files modified:** 6 (5 created, 1 modified)

## Accomplishments

- `EDGE/project.yml` defines the iOS 18.0, iPhone-only, light-mode-locked SwiftUI app target; `xcodegen generate` produces `EDGE.xcodeproj` cleanly.
- All design tokens copied **verbatim** from `docs/ios_app_plan.md` §5.1 (Theme + Color+Hex) and §5.2 (Typography + Eyebrow). The 6 iridescent hexes, 4 soft-state pairs, spacing s1..s10, and radii rSm..rXl are pinned to the spec.
- Minimal `@main EDGEApp` renders `ZStack { Theme.bg.ignoresSafeArea(); Text("EDGE").heroLight }` with `.preferredColorScheme(.light)` — a temporary placeholder that plan 01-02 replaces with the iridescent gradient + generative entrance.
- `xcodebuild` reports **`** BUILD SUCCEEDED **`** with zero code warnings for the simulator SDK.

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold the xcodegen iOS app project** — `97aee4c` (feat)
2. **Task 2: Color(hex:) + Theme tokens (light palette)** — `61053aa` (feat)
3. **Task 3: Typography tokens + minimal light app entry** — `d4acab4` (feat)

**Plan metadata:** `<this commit>` (docs: complete plan)

## Files Created/Modified

- `EDGE/project.yml` — xcodegen spec: iOS 18.0, SwiftUI, `INFOPLIST_KEY_UIUserInterfaceStyle: Light`, bundle `com.niko.edge.app`, single-target iPhone app, generated Info.plist.
- `EDGE/Sources/DesignSystem/ColorHex.swift` — `extension Color { init(hex:) }` via `Scanner.scanHexInt64` (verbatim from spec §5.1, file renamed from `Color+Hex.swift` to avoid `+` in paths).
- `EDGE/Sources/DesignSystem/Theme.swift` — `enum Theme`: surfaces (bg `FCFCFE`, card, hairline, track `ECECF1`, shadow `282A46`), text (text `2B2B2E`, textDim `9A9AA1`, textMute `BFC0C6`, ink `161618`), iridescent palette (iridBlue `B9C9F2`, iridLilac `E7CDEE`, iridBlush `F6D4DC`, iridPeach `F8E7C8`, iridMint `CBEBD9`, spark `9B8CF0`), 4 soft-state pairs, spacing s1..s10, radii rSm..rXl.
- `EDGE/Sources/DesignSystem/Typography.swift` — `extension Font` (greeting 30/.light, heroLight 48/.light, displayX 26/.medium, titleX 20/.medium, headlineX 16/.medium, bodyX 15/.regular, calloutX 13/.regular, eyebrowX 11/.medium) + `Eyebrow` view.
- `EDGE/Sources/EDGEApp.swift` — temporary `@main` `WindowGroup { ZStack { Theme.bg.ignoresSafeArea(); Text("EDGE").font(.heroLight).foregroundStyle(Theme.text) }.preferredColorScheme(.light) }`.
- `.gitignore` — added `EDGE/*.xcodeproj/`, `EDGE/DerivedData/`, `EDGE/build/`, `xcuserdata/`, `*.xcuserstate` so `project.yml` stays the source of truth.

## Decisions Made

- **Source layout:** rooted at `EDGE/Sources/` (per plan) rather than `EDGE/` root; preserves spec §2 directory names otherwise. `Color+Hex.swift` → `ColorHex.swift` (plan-mandated rename to avoid `+` in paths).
- **`.xcodeproj` is gitignored** (regenerated via `xcodegen generate`). Only `project.yml` + `Sources/` are committed. This keeps the plan's `files_modified` list authoritative and avoids committing regenerable artifacts.
- **Verify command substitution** (see Deviations): used `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build` instead of the plan's `-scheme ... -destination 'generic/platform=iOS Simulator'` form because the matching iOS 26.5 simulator runtime cannot be installed on this machine.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Substituted the plan's `xcodebuild ... -scheme ... -destination 'generic/platform=iOS Simulator'` verify command**
- **Found during:** Task 2 (first build attempt) and Task 3 (final build verification)
- **Issue:** The plan's exact verify command requires the iOS 26.5 simulator runtime to be installed (the Xcode 26.5 SDK is `iphonesimulator26.5`). On this machine, only the **iOS 26.4** simulator runtime is installed and the 26.5 runtime **cannot be installed**: `xcodebuild -downloadPlatform iOS` fails with `"Insufficient space available. Requires 8,49 GB"` (only ~3.0 GB free on `/`). xcodebuild therefore reports `"Supported platforms for the buildables in the current scheme is empty"` / `"Unable to find a destination matching ... 'generic/platform=iOS Simulator'"` for every destination variant tried (`generic`, `name=iPhone 17`, `OS=26.4`, by UDID, with `SUPPORTED_PLATFORMS` set, with an explicit shared scheme).
- **Fix:** Verified build using the destination-agnostic form `xcodebuild -project EDGE.xcodeproj -target EDGE -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=NO build`, which compiles + links the real `EDGE.app` binary against `iPhoneSimulator26.5.sdk` without needing a deployable simulator runtime. This produces a true `** BUILD SUCCEEDED **` (Task 3's hard acceptance criterion).
- **Files modified:** none (project.yml left spec-exact; the SUPPORTED_PLATFORMS + schemes block I tried during debugging was reverted before commit because it did not solve the destination-resolution issue).
- **Verification:** `** BUILD SUCCEEDED **` printed; `EDGE.app` produced under `EDGE/build/Debug-iphonesimulator/EDGE.app`; Swift sources compile with zero warnings.
- **Committed in:** N/A (verification-only deviation; no source changes).
- **Forward note for future executors (plans 01-02 onward):** Use the same `-target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build` form until the iOS 26.5 simulator runtime is installed (free up ≥9 GB on `/` then `xcodebuild -downloadPlatform iOS`). After that, the plan's `-scheme ... -destination 'generic/platform=iOS Simulator'` form should work as written.

**2. [Rule 3 - Blocking] `.gitignore` updated to exclude generated Xcode artifacts**
- **Found during:** Task 1 (after first `xcodegen generate`)
- **Issue:** `xcodegen generate` writes `EDGE/EDGE.xcodeproj/` and `xcodebuild` writes `EDGE/build/`, `EDGE/DerivedData/`. Without gitignore rules these would appear as untracked noise on every task and risk being accidentally staged.
- **Fix:** Added `EDGE/*.xcodeproj/`, `EDGE/DerivedData/`, `EDGE/build/`, `xcuserdata/`, `*.xcuserstate` to `.gitignore`. Now only `EDGE/project.yml` + `EDGE/Sources/**` are tracked — `project.yml` is the regenerable source of truth.
- **Files modified:** `.gitignore`
- **Verification:** `git status --short` after each `xcodegen generate` shows only intended source files.
- **Committed in:** `97aee4c` (Task 1 commit; the `.gitignore` edit was grouped with `project.yml` since both establish the EDGE project scaffolding).

---

**Total deviations:** 2 auto-fixed (2 blocking / Rule 3)
**Impact on plan:** No scope creep. Source code is byte-for-byte the spec; only the verification *command form* and `.gitignore` hygiene differ, both forced by this machine's environment (missing 26.5 sim runtime + disk-space constraint).

## Issues Encountered

- **iOS 26.5 simulator runtime not installed.** Root cause: `xcodebuild -downloadPlatform iOS` fails with `"Insufficient space available. Requires 8,49 GB"`; only ~3.0 GB free on `/`. Worked around via destination-agnostic build (see Deviation #1). Not blocking for plan completion; **is** blocking for any plan that needs to actually *launch* the app in a simulator (none in 01-01 — that's a Phase 4+ concern).
- **xcodebuild auto-generated scheme reports "supported platforms empty"** for the EDGE target. xcodegen does not emit `SUPPORTED_PLATFORMS` or an explicit shared scheme by default. I tested adding both — they did not solve the destination-resolution problem (the real blocker is the missing runtime, not the scheme), so I reverted them to keep `project.yml` spec-exact. If a future executor wants IDE-friendly schemes, add a `schemes:` block to `project.yml` — it's a harmless improvement, just not needed for headless `xcodebuild -target` builds.

## User Setup Required

None — no external service configuration required. The app is fully offline, no API keys, no backend.

## Next Phase Readiness

- **Ready for 01-02 (IridescentGlow + GenerativeAppear):** Theme.swift exposes `iridBlue/Lilac/Blush/Peach/Mint/spark` exactly as `IridescentGlow.swift` (spec §5.3) expects them. Typography.swift exposes `.greeting`/`.heroLight` ready for the Today hero. EDGEApp.swift's body is the documented replacement point ("plan 01-02 replaces the body with the gradient + generative entrance").
- **Ready for all later phases:** every color/font must come from Theme.swift / Typography.swift (FND-01, FND-02). The token names are stable.
- **One environmental caveat for future executors:** use `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build` (not the plan's `-scheme ... -destination` form) until the iOS 26.5 simulator runtime is installed. Documented above under Deviation #1.
- **No blockers** for proceeding to plan 01-02.

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: EDGE/project.yml
- FOUND: EDGE/Sources/DesignSystem/ColorHex.swift
- FOUND: EDGE/Sources/DesignSystem/Theme.swift
- FOUND: EDGE/Sources/DesignSystem/Typography.swift
- FOUND: EDGE/Sources/EDGEApp.swift

**Commits verified in git log:**
- FOUND: 97aee4c (Task 1)
- FOUND: 61053aa (Task 2)
- FOUND: d4acab4 (Task 3)

**Build verification:**
- FOUND: `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO ONLY_ACTIVE_ARCH=NO build` (clean rebuild from `rm -rf build EDGE.xcodeproj && xcodegen generate && xcodebuild ...`)

---
*Phase: 01-foundation*
*Completed: 2026-06-17*
