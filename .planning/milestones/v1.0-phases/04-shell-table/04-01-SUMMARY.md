---
phase: 04-shell-table
plan: 01
subsystem: ui
tags: [swiftui, ios18, tabbar, navigation, haptics, frosted-glass]

requires:
  - phase: 01-foundation
    provides: Theme tokens, AppStore + Feed models, EDGEApp scaffold
  - phase: 03-components
    provides: IridescentGlow, FrostCard, GenerativeAppear component vocabulary
provides:
  - "RootView: 4-tab app shell (Today / Matches / Table / Insights)"
  - "Custom floating frosted capsule tab bar with light haptic + spring"
  - "Shared IridescentGlow behind all tabs (strong on Today, faint elsewhere)"
  - "AppStore.feed convenience accessor (Feed? from .loaded phase)"
  - "Tab enum (CaseIterable, titled, SF Symbol icons)"
affects: [04-02-table, 05-today-briefing, 06-matches-detail, 07-insights-scouting]

tech-stack:
  added: []
  patterns:
    - "Shell pattern: ZStack(bg + glow) → TabView(selection:) → .safeAreaInset(.bottom) for floating bar"
    - "System tab bar hidden via .toolbar(.hidden, for: .tabBar); custom bar replaces it"
    - "Per-tab gradient intensity: 1.0 active Today, 0.35 elsewhere — single living aesthetic across tabs"
    - "Haptic + spring on tab switch (UIImpactFeedbackGenerator(style: .light))"

key-files:
  created:
    - EDGE/Sources/Features/Shell/RootView.swift
  modified:
    - EDGE/Sources/EDGEApp.swift

key-decisions:
  - "Floating frosted bar uses Capsule (not RoundedRectangle) per §7.1 — matches the spec's 'frosted capsule' description"
  - "Selected item renders as Label (icon+title) in Theme.ink; unselected renders icon-only in Theme.textMute — asymmetry signals selection without a separate highlight chip"
  - "Tab content is PlaceholderTab (FrostCard '<Title> — coming soon'); real screens land in later phases (TableView in 04-02, Today in 05, etc.)"
  - "ComponentGallery.swift kept intact as a debug preview surface — not deleted, just no longer the app root"

patterns-established:
  - "AppStore.feed: Feed? convenience — every screen reads the feed via @EnvironmentObject store + store.feed"
  - "Tab enum is the single source of truth for tab identity (title + SF Symbol icon)"
  - "Tab switch = haptic + spring animation; UIImpactFeedbackGenerator(style: .light) is the standard 'tap selected' haptic"

requirements-completed: [NAV-01]

duration: 8min
completed: 2026-06-17
---

# Phase 04 Plan 01: App Shell Summary

**4-tab RootView shell with a floating frosted capsule tab bar (Today/Matches/Table/Insights), shared breathing IridescentGlow behind every tab, light haptic + spring on switch — now the EDGE app root.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-17T15:25Z
- **Completed:** 2026-06-17T15:33Z
- **Tasks:** 3
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- **RootView shell created** with 4 tabs (`Tab` enum) and a shared `IridescentGlow` that breathes behind all tabs — strong (intensity 1.0) on Today, faint (0.35) elsewhere, so the living aesthetic persists across navigation
- **Custom floating frosted capsule tab bar** per spec §7.1: `.ultraThinMaterial` + `Theme.hairline` border + soft `Theme.shadow.opacity(0.10)`, ~56pt tall, ~12pt bottom inset; selected item shows icon+title in `Theme.ink`, others show icon-only in `Theme.textMute`
- **Light haptic + spring** fires on every tab switch via `UIImpactFeedbackGenerator(style: .light).impactOccurred()` and `.spring(response: 0.4, dampingFraction: 0.75)`
- **App root swapped** from `ComponentGallery` → `RootView()` in `EDGEApp.swift`, preserving the `.environmentObject(store)` / `.preferredColorScheme(.light)` / `.task { await store.load() }` chain
- **`AppStore.feed` convenience** added so every screen can read `store.feed` (returns `Feed?` from `.loaded` phase)
- **System tab bar hidden** via `.toolbar(.hidden, for: .tabBar)` — the custom bar fully replaces it

## Task Commits

Each task was committed atomically:

1. **Task 1: Tab enum + store.feed convenience + shell scaffold** — `6f14f86` (feat)
2. **Task 2: Floating frosted tab bar + haptic** — `3a154a2` (feat)
3. **Task 3: Make RootView the app root** — `6ee306c` (feat)

## Files Created/Modified

- `EDGE/Sources/Features/Shell/RootView.swift` — **created.** `AppStore.feed` extension + `Tab` enum + `RootView` (ZStack bg+glow, TabView with `.toolbar(.hidden, for: .tabBar)`, `.safeAreaInset(.bottom)` floating bar) + private `PlaceholderTab` (FrostCard "<Title> — coming soon")
- `EDGE/Sources/EDGEApp.swift` — **modified.** `WindowGroup` content swapped from `ComponentGallery()` → `RootView()`; env+scheme+load chain preserved

## Decisions Made

- **Capsule, not RoundedRectangle** for the bar — spec §7.1 explicitly calls it a "frosted capsule", and the ASCII art shows rounded pill ends
- **Label for selected, Image-only for unselected** — the asymmetry itself signals selection; no need for an extra highlight/indicator chip that would clutter the bar
- **`guard tab != t else { return }` before haptic** — prevents redundant haptic + animation when re-tapping the active tab
- **PlaceholderTab kept simple** — no `.navigationTitle`/toolbar; lets the IridescentGlow and FrostCard speak for themselves, matching the §7 preamble ("Every screen: `ZStack { Theme.bg.ignoresSafeArea(); IridescentGlow(…); ScrollView { … } }`")
- **`Theme.s5` horizontal padding inside the HStack, `Theme.s4` outside** — tighter internal spacing keeps the four icons visually grouped, while the outer padding gives the capsule breathing room from the screen edges

## Deviations from Plan

None — plan executed exactly as written. All three acceptance-criteria grep checks passed on the first build, and the build succeeded on the first attempt for every task.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. The shell reads from the bundled `SampleFeed.json` via `AppStore.load()` (offline-first, demoable).

## Next Phase Readiness

- **Shell is ready** for all downstream screen plans
- **04-02 (Table)** can swap `PlaceholderTab(tab: .table)` → `TableView()` inside `RootView`'s `NavigationStack`
- **05 (Today)**, **06 (Matches/Detail)**, **07 (Insights/Scout)** do the same for their respective tabs
- The `store.feed` accessor is the canonical way for tab content to read the loaded feed
- `ComponentGallery.swift` remains available as a debug/preview surface — not wired into the app anymore but still in the bundle

## Self-Check: PASSED

- ✅ `EDGE/Sources/Features/Shell/RootView.swift` exists (created)
- ✅ `EDGE/Sources/EDGEApp.swift` contains `RootView()` and `.environmentObject(store)`
- ✅ Commit `6f14f86` found (Task 1)
- ✅ Commit `3a154a2` found (Task 2)
- ✅ Commit `6ee306c` found (Task 3)
- ✅ `** BUILD SUCCEEDED **` confirmed across all 3 task builds
- ✅ Acceptance-criteria greps all matched: `enum Tab`, `toolbar(.hidden, for: .tabBar)`, `IridescentGlow(intensity: tab == .today ? 1.0 : 0.35`, `var feed: Feed?`, `@EnvironmentObject var store: AppStore`, `safeAreaInset(edge: .bottom)`, `UIImpactFeedbackGenerator(style: .light)`, `ultraThinMaterial`
- ✅ STATE.md / ROADMAP.md NOT modified (per instructions)

---
*Phase: 04-shell-table*
*Completed: 2026-06-17*
