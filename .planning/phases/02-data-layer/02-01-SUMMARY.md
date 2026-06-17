---
phase: 02-data-layer
plan: 01
subsystem: data
tags: [swift, swiftui, ios18, codable, observableobject, bundle-resources, offline-first, anti-jargon]

# Dependency graph
requires:
  - "01-01: Theme soft-state tokens (pos/warn/neg/act BG+Text) + xcodegen EDGE target (Sources/ bundled)"
  - "01-02: EDGEApp root scene + .preferredColorScheme(.light) pattern"
provides:
  - "Codable feed models (Feed/Me/Strategy/Form/TableRow/Match/Pick/ScoutReport + nested structs) — Core/Models.swift"
  - "AppStore — @MainActor ObservableObject with Phase enum, @Published generation counter, iso8601 decoder, bundled SampleFeed loader, refresh() hook — Core/AppStore.swift"
  - "Bundled offline SampleFeed.json (9-row table, 4 matches incl. final France 2:1 Senegal + chaos Ghana 1:1 Panama, 8 scouting cards) — Resources/SampleFeed.json"
  - "Format — enum of human-language + soft-state color helpers (tier/strength/leverage/leader/outcome/mode/greeting/countdown/chance) — Core/Format.swift"
  - "EDGEApp injects AppStore via @StateObject + environmentObject + .task { await store.load() }"
affects: [03-components, 04-shell-table, 05-today-briefing, 06-matches-detail, 07-insights-scouting, 08-motion-a11y-states]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Codable models with `let` properties + Identifiable conformances; field names match JSON keys byte-for-byte (verified by runtime decode of SampleFeed.json → no key mismatches)"
    - "ObservableObject store exposes `@Published var generation: Int` that increments on every load() — screens key their generative-assembly animation on it to replay entrance on refresh (spec §4.3/§5.4)"
    - "Offline-first: feedURL = nil for v1; Bundle.main.url(forResource:\"SampleFeed\", withExtension:\"json\") loads the bundled file. Remote URL is a drop-in for a later phase."
    - "Format.swift is the single enforcement point for LANG-01: no raw %, no composite_score, no expected_points as text. exactChanceOneIn → '1 in N'; tier/leverage/outcome/strength → words + Theme soft-state colors."

key-files:
  created:
    - EDGE/Sources/Core/Models.swift
    - EDGE/Sources/Core/AppStore.swift
    - EDGE/Sources/Core/Format.swift
    - EDGE/Sources/Resources/SampleFeed.json
  modified:
    - EDGE/Sources/EDGEApp.swift

key-decisions:
  - "All four artifacts are byte-for-byte / token-for-token copies of docs/ios_app_plan.md §4.2/§4.3/§6/§18 — no field names, colors, or copy invented (PROJECT.md: design fidelity is the highest priority)."
  - "SampleFeed.json copied VERBATIM from spec §18 — diff against docs/ios_app_plan.md lines 1203-1362 reports BYTE-IDENTICAL. German umlauts (Schirifötze) and the ellipsis in 'Klose4ev…' preserved through decode."
  - "EDGEApp keeps the Phase-1 placeholder body (ZStack bg + IridescentGlow + 'EDGE'/'agentic gen UI' VStack). The spec shows RootView() but RootView does not exist until Phase 4 — deferred per the plan's explicit instruction. Store injection (environmentObject + .task load) is added now so the feed is decoded on launch."
  - "Verified end-to-end by runtime-decoding SampleFeed.json against Models in a standalone Swift script: me=Niko rank=8 leader=Alex deficit=6, table=9, matches=4, scouting=8, final-match outcome=exact, chaos tier present, Schirifötze + Klose4ev… survive the round-trip."

patterns-established:
  - "All feed types live in EDGE/Sources/Core/Models.swift as flat top-level structs with nested layout exactly as spec §4.2 — single file, no per-model files."
  - "The store is the only @EnvironmentObject the app needs; any view reads `store.phase` (switch loading/loaded/failed) and keys replayable entrances on `store.generation`."
  - "Format helpers return tuple-style chip descriptors `(text:, fg:, bg:)` — screens bind these directly into SoftPill-style chips without re-deriving colors. Never call Theme state tokens directly for feed-driven UI; go through Format."

requirements-completed: [DATA-01, DATA-02, DATA-03]

# Metrics
duration: ~7min
started: 2026-06-17T12:54:57Z
completed: 2026-06-17T13:01:43Z
tasks: 4/4 executed
files: 4 created, 1 modified
---

# Phase 02 Plan 01: Offline Data Layer Summary

**Codable feed models, an observable AppStore whose `generation` counter bumps on every refresh (so screens replay their generative entrance), a byte-verbatim bundled SampleFeed.json, and the Format anti-jargon translation layer — all four copied verbatim from spec §4.2/§4.3/§6/§18 and runtime-verified to decode cleanly.**

## Performance

- **Duration:** ~7 min (406s)
- **Started:** 2026-06-17T12:54:57Z
- **Completed:** 2026-06-17T13:01:43Z
- **Tasks:** 4/4 auto tasks executed
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments

- **Models.swift** — verbatim from `docs/ios_app_plan.md` §4.2. `Feed, Me, Strategy (+DrawPlan), Form, TableRow, Match (+Team, ScoreResult, Odds, Upset, FieldExposure, Alternate), Pick (+PickResult), ScoutReport (+Trait)`. `let` properties, Identifiable conformances on `TableRow`/`Match`/`Alternate`/`Trait`/`ScoutReport`, nested-struct layout. Field names match JSON keys exactly (`exactChanceOneIn`, `favoriteStrength`, `vsLeader`, `isLeader`, `leaderPick`, …).
- **SampleFeed.json** — verbatim from §18. **Byte-identical** to the spec appendix (`diff docs/ios_app_plan.md(1203,1362) Resources/SampleFeed.json` → identical). Real 2026-06-17 values: 9-row table (Niko at rank 8, Alex leading with 24), 4 matches including `status:"final"` France 2:1 Senegal (myPick `outcome:"exact"`, +4) and `tier:"chaos"` Ghana 1:1 Panama, 8 scouting cards. German `ö` in `Schirifötze` and `…` in `Klose4ev…` preserved.
- **AppStore.swift** — verbatim from §4.3. `@MainActor final class AppStore: ObservableObject` with `Phase` enum (`loading`/`loaded(Feed)`/`failed(String)`), `@Published var phase`, `@Published var generation: Int = 0`, `iso8601` decoder, `load()` (bundled first → `generation += 1` → optional remote), `refresh()`, and `static loadBundled()`. `feedURL = nil` for offline v1.
- **EDGEApp.swift** — wired the store: `@StateObject private var store = AppStore()`, `.environmentObject(store)`, `.task { await store.load() }`. Phase-1 placeholder body retained (RootView arrives in Phase 4).
- **Format.swift** — verbatim from §6. The LANG-01 enforcement layer: `tierStyle`/`tierRingColor` (tier → soft pill + ring color), `strengthWords` (heavy/clear/slight/even → words), `leverageChip`/`leaderChip` (crowd-vs-contrarian, same-vs-different → chips), `ringFill`/`chanceText` (exactChanceOneIn → `"1 in N"` text + relative ring fill, **never** a percentage), `outcomeChip` (exact/goaldiff/tendency/draw/miss → "Spot on +N" etc.), `modeIcon`, `greeting`, `countdown`, `kickoffClock`, `relativeUpdated`. All colors come from Theme soft-state tokens; no raw `%`, `composite_score`, or `expected_points` ever appear as text.
- **Build:** `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (destination-agnostic form, since iOS 26.5 simulator runtime cannot be installed on this machine — only 26.4 is present; established in 01-01).
- **Decode verified:** Ran a standalone Swift script that decodes `SampleFeed.json` against `Models.swift` end-to-end — prints `DECODE_OK me=Niko rank=8 leader=Alex deficit=6`, `table=9 matches=4 scouting=8`, `final match: exact`, `chaos tier: true`, `scout w/ umlaut: true ellipsis: true`. Zero key mismatches.

## Task Commits

Each task committed atomically:

1. **Task 1: Codable models** — `f12b259` (feat)
2. **Task 2: Bundled SampleFeed.json** — `8eaf60d` (feat)
3. **Task 3: AppStore + EDGEApp injection** — `0bd2b2b` (feat)
4. **Task 4: Format human-language + color helpers** — `9b7dc32` (feat)

**Plan metadata:** `<this commit>` (docs: complete plan)

## Files Created/Modified

- `EDGE/Sources/Core/Models.swift` (created) — verbatim §4.2 Codable feed model tree.
- `EDGE/Sources/Resources/SampleFeed.json` (created) — verbatim §18 bundled offline feed; byte-identical to spec appendix.
- `EDGE/Sources/Core/AppStore.swift` (created) — verbatim §4.3 observable store with generation counter + bundled loader.
- `EDGE/Sources/Core/Format.swift` (created) — verbatim §6 anti-jargon translation layer.
- `EDGE/Sources/EDGEApp.swift` (modified) — `@StateObject var store`, `.environmentObject(store)`, `.task { await store.load() }`; placeholder body retained.

## Decisions Made

- **Verbatim-from-spec policy enforced across all four artifacts.** Models field names, AppStore body, Format helper bodies, and the JSON content all come straight from `docs/ios_app_plan.md` §4.2/§4.3/§6/§18. No field names, colors, copy, or numeric values were invented. PROJECT.md declares design fidelity the highest priority; the data contract is part of that.
- **EDGEApp keeps the Phase-1 placeholder body.** Spec §4.3 shows `RootView().environmentObject(store)`, but `RootView` is not defined until Phase 4. The plan's Task 3 action explicitly says "keep the Phase-1 placeholder body for now; Phase 4 swaps in RootView" — so the existing ZStack (bg + IridescentGlow + "EDGE"/"agentic gen UI" VStack) is preserved, with store injection layered on. This is plan-as-written, not a deviation.
- **Decode sanity check added beyond the plan's `<verify>`.** The plan only requires `xcodebuild` + `python3 -m json.tool`. I additionally decoded the JSON against the Models in a standalone Swift script to catch any silent field-name mismatches (the build does not exercise decoding). Result: zero mismatches; all 4 matches + 9 table rows + 8 scouting cards decode, including the final-match `PickResult` and the chaos-tier pick.
- **No code comments added.** Spec source for Models/AppStore/Format contains no inline comments (Format's section header `// Tier → soft pill style …` is the only one, included verbatim). CLAUDE.md / PROJECT.md forbid comments unless the spec shows them — honored.

## Deviations from Plan

None — plan executed exactly as written. (One environmental substitution in the verify command form — `xcodebuild -target EDGE -sdk iphonesimulator …` instead of `-scheme … -destination 'generic/platform=iOS Simulator'` — is the same Rule-3 blocking constraint already documented in 01-01-SUMMARY Deviation #1: the iOS 26.5 simulator runtime is unavailable on this machine. The destination-agnostic form still compiles+links a real `EDGE.app` against `iPhoneSimulator26.5.sdk` and prints `** BUILD SUCCEEDED **`.)

## Issues Encountered

None.

## User Setup Required

None — fully offline. SampleFeed.json is bundled; no network, no env vars, no secrets.

## Next Phase Readiness

- **Ready for 03-components:** every component that renders feed data can now `@EnvironmentObject var store: AppStore`, switch on `store.phase` (loading/loaded/failed), and read typed `Feed`/`Match`/`Pick`/`TableRow`/`ScoutReport` values. SoftPill / StrengthBar / SoftRing / GapRail consumers should call `Format.*` helpers rather than touching Theme state tokens directly.
- **Replay-on-refresh wired:** any `ScrollView { content.id(store.generation) }` will remount its children on each refresh → re-trigger `.generativeAppear(i)` (the Phase-1 motion primitive). `AppStore.refresh()` is the `.refreshable` hook.
- **Phase 4 swap-in:** when `RootView` lands, replace the placeholder ZStack in `EDGEApp.swift` with `RootView().environmentObject(store)` (spec §4.3 shows the exact form). The store wiring itself is already correct.
- **No blockers.**

## Self-Check: PASSED

**Files verified to exist:**
- FOUND: EDGE/Sources/Core/Models.swift
- FOUND: EDGE/Sources/Resources/SampleFeed.json
- FOUND: EDGE/Sources/Core/AppStore.swift
- FOUND: EDGE/Sources/Core/Format.swift
- FOUND: EDGE/Sources/EDGEApp.swift (modified)

**Commits verified in git log:**
- FOUND: f12b259 (Task 1 — Models)
- FOUND: 8eaf60d (Task 2 — SampleFeed.json)
- FOUND: 0bd2b2b (Task 3 — AppStore + EDGEApp)
- FOUND: 9b7dc32 (Task 4 — Format)

**Acceptance-criteria string checks:**
- FOUND: Models.swift → "struct Feed: Codable", "struct Match: Codable, Identifiable", "struct Pick: Codable", "exactChanceOneIn", "favoriteStrength", "struct Trait"
- FOUND: SampleFeed.json → '"name": "Niko"', '"rank": 8', '"leaderName": "Alex"', '"status":"final"', '"tier":"chaos"'; 8 '"traits"' entries; Schirifötze + Klose4ev… preserved
- FOUND: AppStore.swift → "ObservableObject", "@Published var generation", 'forResource: "SampleFeed"', "func refresh()", "generation += 1"
- FOUND: EDGEApp.swift → "@StateObject private var store", ".environmentObject(store)", ".task { await store.load() }"
- FOUND: Format.swift → "func tierStyle", "func chanceText", `"1 in \(max(oneIn,1))"`, "func outcomeChip"; references Theme.posText / Theme.warnText / Theme.actBG; no raw `%` / `composite_score` / `expected_points` strings

**Build verification:**
- FOUND: `** BUILD SUCCEEDED **` via `xcodebuild -target EDGE -sdk iphonesimulator ONLY_ACTIVE_ARCH=NO build CODE_SIGNING_ALLOWED=NO` (after Task 4)
- FOUND: `JSON_OK` via `python3 -m json.tool SampleFeed.json > /dev/null`
- FOUND: runtime decode of SampleFeed.json against Models succeeds with all expected field values

---
*Phase: 02-data-layer*
*Completed: 2026-06-17*
