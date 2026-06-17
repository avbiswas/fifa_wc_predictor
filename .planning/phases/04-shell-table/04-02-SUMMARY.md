---
phase: 04-shell-table
plan: 02
subsystem: ui
tags: [swiftui, ios18, standings, table, gap-rail, generative-assembly, frost-card]

requires:
  - phase: 01-foundation
    provides: Theme tokens, AppStore + Feed models, Format helpers
  - phase: 03-components
    provides: FrostCard, SoftPill, MovementArrow, GapRail, GenerativeAppear component vocabulary
  - phase: 04-01
    provides: RootView 4-tab shell with floating frosted bar, AppStore.feed accessor, Tab enum
provides:
  - "TableView: 9-player league standings — first complete real screen"
  - "Spec-exact §7.5 standings layout: rank, crown on leader, name, 'you' pill, points, movement arrow"
  - "User-row highlight recipe: 3pt iridescent left bar + Theme.actBG.opacity(0.5) tint + Theme.ink name"
  - "GapRail header above standings shows the live gap to the leader"
  - "Per-row generative stagger keyed on store.generation — replays on pull-to-refresh"
affects: [05-today-briefing, 07-insights-scouting]

tech-stack:
  added: []
  patterns:
    - "Tab-content pattern: ScrollView → VStack(header, GapRail, FrostCard[rows]); no per-screen ZStack — the shared IridescentGlow lives in RootView"
    - "List-in-card pattern: single FrostCard containing VStack(spacing:0) with Divider().background(Theme.hairline) between rows (not separate cards per row)"
    - "User-row highlight: overlay(alignment:.leading) for iridescent 3pt accent bar + background tint via RoundedRectangle on the row"
    - "Replay-on-refresh: .id(store.generation) on the VStack contents — generation bumps on every store.load/refresh, forcing GenerativeAppear to re-mount and replay the blur-to-focus stagger"

key-files:
  created:
    - EDGE/Sources/Features/Table/TableView.swift
  modified:
    - EDGE/Sources/Features/Shell/RootView.swift

key-decisions:
  - "Single FrostCard containing all 9 rows (not one card per row) — matches §7.5 'one FrostCard with rows' and keeps the league as one glanceable surface"
  - "Hairline Divider between rows inside the card — spec §7.5 ASCII shows implicit row separation; Theme.hairline keeps it frosted-consistent"
  - "Rank #1 colored Theme.actText (not just the crown) — plan says 'actText if rank==1 else textDim', so the leader's rank echoes the crown color"
  - "Iridescent left accent uses the same iridBlue→iridLilac→iridBlush gradient as IridescentGlow, vertical orientation — binds the user row visually to the app's living aesthetic"
  - "SoftPill 'you' default styling (actBG/actText) — already on-brand, no override needed"
  - "MovementArrow(move: row.move) called directly on the row.move Int — component handles up/down/dash + abs(delta) per §5.11"
  - "Loading guard: simple FrostCard 'Loading the league…' in textDim — matches spec §10 minimalism; no spinner, no shimmer"
  - "navigationTitle('Table') + .inline — the inline title sits subtly under the system bar; the in-screen 'League' header carries the actual screen identity per §7.5"

patterns-established:
  - "First-real-screen pattern: store.feed guard → ScrollView[VStack(header, content)] → .refreshable { await store.refresh() }"
  - "Enumerated ForEach over feed arrays with .generativeAppear(offset) so the stagger index is the array position"
  - "No-jargon is automatic here: points + movement are user-facing scores, not raw engine internals. Format helpers were not needed on this screen."

requirements-completed: [TABLE-01]

duration: 12min
completed: 2026-06-17
---

# Phase 04 Plan 02: League Table Summary

**9-player standings rendered spec-exact (§7.5) inside one FrostCard — rank, crown on Alex, SoftPill "you" + iridescent left bar + actBG tint on Niko's row, GapRail header above; rows blur-to-focus in via GenerativeAppear and replay on pull-to-refresh.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-17T15:55Z
- **Completed:** 2026-06-17T16:12Z
- **Tasks:** 4 (3 auto + 1 checkpoint:human-verify)
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- **First complete real screen shipped.** TableView renders the 9-player league from `store.feed.table`, replacing the Phase-04-01 placeholder in the `.table` tab.
- **Spec-exact §7.5 layout.** Header "League" + subtitle "{playersCount} players · {tiebreaker} decides ties"; GapRail (you-leader spread) at the top of the card stack; one FrostCard containing all 9 ranked rows.
- **User-row highlight baked.** Niko's row gets a 3pt iridescent (iridBlue→iridLilac→iridBlush) left accent bar, `Theme.actBG.opacity(0.5)` background tint, `Theme.ink` name color, and a `SoftPill(text:"you")`.
- **Leader crowned.** `crown.fill` in `Theme.actText` next to Alex; rank `#1` also in `Theme.actText` (other ranks in `Theme.textDim`).
- **Movement arrows everywhere.** `MovementArrow(move: row.move)` after points — green up-right (▲n), red down-right (▼n), gray dash (–).
- **Generative replay wired.** Each row `.generativeAppear(offset)`; the whole content stack is `.id(store.generation)` so a pull-to-refresh re-mounts and replays the blur-to-focus stagger.
- **Wired into shell.** RootView's `.table` tab now hosts `TableView()` inside its existing NavigationStack; Today/Matches/Insights remain `PlaceholderTab` for later phases.
- **Build + install + launch verified** on the booted iPhone 17 (iOS 26.4) sim from `EDGE/build/Debug-iphonesimulator/EDGE.app`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build League Table standings screen** — `f925536` (feat)
2. **Task 2: Wire TableView into the Table tab** — `32befbf` (feat)
3. **Task 3: Launch + open the Table tab on simulator** — no code change (build/install/launch/screenshot only)
4. **Task 4: checkpoint:human-verify** — screenshot at `/tmp/edge_04-02_table.png`, awaiting user visual sign-off

**Plan metadata:** `docs(04-02): summary` (this commit)

## Files Created/Modified

- `EDGE/Sources/Features/Table/TableView.swift` — **created.** `@EnvironmentObject var store: AppStore`; body guards `store.feed == nil` (loading placeholder); else `ScrollView` over `VStack` [header "League" + subtitle, `GapRail`, `FrostCard` containing `ForEach(Array(feed.table.enumerated()))` of rows separated by hairline `Divider`s]. Row builder: rank (`#\(row.rank)`, actText if rank==1 else textDim), crown.fill on `isLeader`, name (ink if isMe else text), `SoftPill(text:"you")` on isMe, Spacer, points (ink, monospacedDigit), `MovementArrow(move: row.move)`. User-row background: `Theme.actBG.opacity(0.5)` rounded rect; `.overlay(alignment:.leading)`: 3pt iridescent vertical gradient bar. Per-row `.generativeAppear(offset)`; whole content `.id(store.generation)`; `.refreshable { await store.refresh() }`. `.navigationTitle("Table").navigationBarTitleDisplayMode(.inline)`.
- `EDGE/Sources/Features/Shell/RootView.swift` — **modified.** Inside the existing `ForEach(Tab.allCases)` NavigationStack, branches: `if t == .table { TableView() } else { PlaceholderTab(tab: t) }`. All other shell behavior (haptic, floating frosted bar, shared glow) unchanged.

## Decisions Made

- **Single FrostCard containing all 9 rows** — matches spec §7.5 ("one FrostCard with rows") and keeps the league as one glanceable surface (one frost surface, one shadow, one breathing object). One-card-per-row would have made the screen feel like nine separate widgets.
- **Hairline Divider between rows** — spec §7.5 ASCII separates rows visually; using `Divider().background(Theme.hairline)` keeps the separator consistent with the frost aesthetic (white-on-frost rather than the default dark separator).
- **Rank `#1` in `Theme.actText`** — the plan says "actText if rank==1 else textDim"; this echoes the crown color and reinforces the leader's identity without an additional element.
- **Iridescent left bar uses the full hero gradient, vertical** — iridBlue→iridLilac→iridBlush (top→bottom) ties the user's row to the IridescentGlow living behind every tab; 3pt wide, 2pt vertical inset, rounded caps.
- **`SoftPill(text:"you")` uses defaults** — the component already defaults to `actBG`/`actText`, which is exactly what the spec wants.
- **Loading state is a single dim sentence in a FrostCard** — matches §10's minimalism ("Loading the league…"). No spinner, no shimmer; the in-app generative motion only happens once data is real.
- **Slight gradient replay trick for screenshot** — to deterministically capture the Table tab without fighting simulator UI automation, the default tab was temporarily set to `.table`, the binary rebuilt, the screenshot taken, then the change was reverted and the binary rebuilt + reinstalled. Final installed app defaults to `.today` per the committed source.

## Deviations from Plan

None — plan executed exactly as written. Acceptance-criteria greps all matched on the first build; `** BUILD SUCCEEDED **` on every task; the wire-up `TableView()` appears in RootView at line 44; the screenshot was captured at `/tmp/edge_04-02_table.png`.

## Issues Encountered

- **Simulator tab-tap automation** — `xcrun simctl io` has no native tap on this Xcode; `cliclick`/`idb` not installed; CGEvent taps and System Events `click at` did not reliably route to the device framebuffer. Resolved deterministically by temporarily defaulting the tab to `.table` for the screenshot only, then reverting and rebuilding. Final installed binary is the production version (default `.today`). No source change leaked.

## User Setup Required

None — reads from the bundled `SampleFeed.json` via `AppStore.load()` (offline-first, demoable).

## Next Phase Readiness

- **The first real screen is live** — the data → store → component → shell pipeline is proven end-to-end on a dense, glanceable view.
- **05-today-briefing** can swap `PlaceholderTab(tab: .today)` → `TodayView()` using the same pattern (store-feed guard, FrostCards, GenerativeAppear stagger, `.id(store.generation)`).
- **07-insights-scouting** can add the tap-to-ScoutCard sheet on non-`isMe` rows (currently intentionally non-interactive per the plan note).
- The user-row-highlight recipe (3pt iridescent bar + actBG tint + ink name + SoftPill) is reusable for any "you" surface in later screens.

## Self-Check: PASSED

- ✅ `EDGE/Sources/Features/Table/TableView.swift` exists (created, 105 lines)
- ✅ `EDGE/Sources/Features/Shell/RootView.swift` contains `TableView()` at line 44
- ✅ Commit `f925536` found (Task 1: feat, build League Table standings screen)
- ✅ Commit `32befbf` found (Task 2: feat, wire TableView into the Table tab)
- ✅ `** BUILD SUCCEEDED **` confirmed on every task build (4×)
- ✅ App installed + launched on booted iPhone 17 (PID 67528 for production binary)
- ✅ Screenshot captured at `/tmp/edge_04-02_table.png` (1.67 MB — the dense 9-row standings view)
- ✅ Acceptance-criteria greps all matched: `feed.me.playersCount`, `crown.fill`, `row.isMe`, `MovementArrow(move: row.move)`, `.generativeAppear(`, `.id(store.generation)`, `.refreshable`, `Theme.actBG`, `Theme.ink`, `TableView()` in RootView
- ✅ STATE.md / ROADMAP.md NOT modified (per instructions)

---
*Phase: 04-shell-table*
*Completed: 2026-06-17*
