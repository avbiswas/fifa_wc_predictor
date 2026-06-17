# Roadmap: EDGE — iOS App

## Overview

Build the EDGE iOS app bottom-up so every phase compiles and runs in the simulator. Start with the
foundation that makes the aesthetic possible (light tokens, the breathing iridescent gradient, the
generative blur-to-focus modifier), then the offline data layer, then the reusable component
library. With those in place, assemble screens in dependency order: the app shell + the simplest
real screen (League Table), then the showcase Today briefing, then Matches + Match Detail, then
Insights + Scouting. Finish with a dedicated motion/accessibility/states pass that hardens the
animations, enforces the no-jargon rule globally, and verifies the full acceptance checklist. The
build order mirrors `docs/ios_app_plan.md` §14 (M0→M7). Design fidelity and the generative
animations are the throughline and the highest-priority success criterion in every phase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation & Living Aesthetic** - Xcode app, light tokens, breathing gradient, generative-appear modifier (completed 2026-06-17)
- [x] **Phase 2: Offline Data Layer** - Codable models, AppStore, bundled SampleFeed.json, Format helpers (completed 2026-06-17)
- [x] **Phase 3: Component Library** - all frosted/ring/bar/pill/button/status components + preview gallery (completed 2026-06-17)
- [x] **Phase 4: App Shell & League Table** - 4-tab frosted shell + the standings screen (completed 2026-06-17)
- [x] **Phase 5: Today Briefing** - the self-assembling showcase home + pull-to-refresh replay (completed 2026-06-17)
- [x] **Phase 6: Matches & Match Detail** - upcoming/results list + the deep match screen with ring morph (completed 2026-06-17)
- [x] **Phase 7: Insights & Scouting** - engine-form metrics + per-friend scouting cards (completed 2026-06-17)
- [ ] **Phase 8: Motion, Accessibility & States** - motion polish, a11y, empty/error states, no-jargon audit, acceptance

## Phase Details

### Phase 1: Foundation & Living Aesthetic
**Goal**: A running iOS 18 light-mode app whose signature aesthetic primitives — the breathing iridescent gradient and the generative blur-to-focus entrance — already work, with all design tokens centralized.
**Depends on**: Nothing (first phase)
**Requirements**: FND-01, FND-02, FND-03, FND-04
**Success Criteria** (what must be TRUE):
  1. App launches in light mode to a screen where the iridescent gradient is **visibly, continuously breathing**
  2. A placeholder element enters with the **blur-to-focus generative** animation on launch
  3. `Theme` and `Font` token files compile and are the only place colors/typography are defined
  4. Project builds with zero warnings on an iOS 18 simulator
**Plans**: 2 plans

Plans:
- [x] 01-01: Create Xcode app + light-mode root + Color/Theme/Typography tokens
- [x] 01-02: IridescentGlow (breathing) + GenerativeAppear modifier + wire into root

### Phase 2: Offline Data Layer
**Goal**: The app decodes the bundled sample feed into typed models with no network, exposes it via an observable store with a refresh-driven generation counter, and provides the human-language Format helpers.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. App decodes `SampleFeed.json` offline and a debug view prints Niko = rank 8, 18 pts, 9 table rows
  2. `AppStore.generation` increments when `refresh()` runs
  3. `Format` converts tier→label+color, leverage/vsLeader→chip, outcome→pill, exact-chance→"1 in N"
**Plans**: 1 plan

Plans:
- [x] 02-01: Models + AppStore + SampleFeed.json (bundled) + Format helpers

### Phase 3: Component Library
**Goal**: Every reusable visual component from the design system exists, animates per spec, and is provable in a preview gallery — the vocabulary every screen will compose.
**Depends on**: Phase 1 (tokens), Phase 2 (Format colors used by some)
**Requirements**: COMP-01, COMP-02, COMP-03
**Success Criteria** (what must be TRUE):
  1. A preview gallery screen renders **every** component correctly on the light canvas
  2. `SoftRing` arc draws on appear; `StrengthBar` and `GapRail` fill/slide on appear
  3. `FrostCard` shows frosted blur + white hairline + soft bluish shadow; `InkButton` is the black pill
**Plans**: 3 plans

Plans:
- [x] 03-01: FrostCard + SoftRing + StrengthBar + GapRail
- [x] 03-02: SoftPill + InkButton/PressScale + MovementArrow + TeamBadge
- [x] 03-03: GeneratedStatus + Sparkline + Eyebrow + ComponentGallery preview

### Phase 4: App Shell & League Table
**Goal**: A 4-tab app shell with the floating frosted tab bar, and the first complete real screen — the League Table — built from real components and data.
**Depends on**: Phase 2 (data), Phase 3 (components)
**Requirements**: NAV-01, TABLE-01
**Success Criteria** (what must be TRUE):
  1. Four tabs (Today/Matches/Table/Insights) switch via a floating frosted bar with a light haptic
  2. The Table lists all 9 players ranked, the user's row highlighted (iridescent), leader crowned
  3. Each row shows a movement arrow (green up / red down / gray none) with the delta number
**Plans**: 2 plans

Plans:
- [x] 04-01: RootView 4-tab shell + floating frosted tab bar + shared gradient
- [x] 04-02: TableView standings (rows, highlight, crown, movement, gap rail header)

### Phase 5: Today Briefing
**Goal**: The showcase home screen that assembles itself — greeting, standing with gap rail, tonight's plan, next-match spotlight — and replays the generative assembly on pull-to-refresh.
**Depends on**: Phase 3 (components), Phase 4 (shell)
**Requirements**: TODAY-01, TODAY-02
**Success Criteria** (what must be TRUE):
  1. Today shows greeting + standing (#8, "6 behind Alex", gap rail) + tonight's plan + next-match spotlight
  2. On open, the screen **assembles top-to-bottom** with the generative stagger
  3. Pull-to-refresh **replays** the assembly and flips the status to "Generating your briefing…"
  4. The next-match spotlight pushes Match Detail when its ink button is tapped
**Plans**: 2 plans

Plans:
- [x] 05-01: Today scaffold — GeneratedStatus, greeting, standing card + gap rail, tonight's plan card
- [x] 05-02: Next-match spotlight + today's-other-picks list + assembly/refresh wiring

### Phase 6: Matches & Match Detail
**Goal**: The Matches tab (Upcoming/Results segmented) and the deep Match Detail screen, including the score-ring shared-element morph and the plain-English breakdown.
**Depends on**: Phase 3 (components), Phase 4 (shell), Phase 5 (detail navigation entry)
**Requirements**: MATCH-01, MATCH-02
**Success Criteria** (what must be TRUE):
  1. Matches shows Upcoming and Results via a segmented control, grouped by matchday
  2. A final match shows the actual score + a soft outcome pill (e.g. "Spot on +4", "Missed")
  3. Tapping a match opens a detail with the ring, 3 reasons, strength bar, "the room", alternates
**Plans**: 2 plans

Plans:
- [x] 06-01: MatchesView (segmented Upcoming/Results) + MatchRowCard
- [x] 06-02: MatchDetailView (hero ring + why + matchup + the room + alternates + news)

### Phase 7: Insights & Scouting
**Goal**: The Insights tab — engine form metrics with a sparkline, plus a scouting report card for each friend.
**Depends on**: Phase 3 (components), Phase 4 (shell)
**Requirements**: INSIGHT-01
**Success Criteria** (what must be TRUE):
  1. Insights shows engine form (24 points / 1.5 avg / 4 spot-on / 8-of-16 scored) + a sparkline
  2. A scouting card per friend shows the tag pill, blurb, and 3 trait level bars (filled = level)
**Plans**: 2 plans

Plans:
- [x] 07-01: InsightsView — form metric tiles + sparkline + takeaway
- [x] 07-02: ScoutCard + scouting list (sorted by rank, tag-colored)

### Phase 8: Motion, Accessibility & States
**Goal**: Harden the experience — finish motion (shared-element morph, haptics, word-build greeting), wire accessibility (Reduce Motion, VoiceOver), add empty/loading/error states, audit the no-jargon rule globally, and verify the full acceptance checklist.
**Depends on**: Phases 5, 6, 7 (all screens exist)
**Requirements**: MOTION-01, LANG-01, A11Y-01, A11Y-02
**Success Criteria** (what must be TRUE):
  1. Match card → detail **ring morphs**; rings/bars/cards animate; tab-switch and card-press haptics fire
  2. **Reduce Motion** snaps all animation to final and pauses the gradient
  3. VoiceOver reads worded labels for rings/bars/table rows
  4. **No raw % / probability / jargon** appears anywhere; empty/loading/error states render gracefully
**Plans**: 2 plans

Plans:
- [x] 08-01: Motion polish — shared-element ring morph, haptics, word-build greeting, press-scale audit
- [ ] 08-02: Accessibility (Reduce Motion + VoiceOver) + empty/loading/error states + no-jargon audit + acceptance pass

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Living Aesthetic | 2/2 | Complete   | 2026-06-17 |
| 2. Offline Data Layer | 1/1 | Complete   | 2026-06-17 |
| 3. Component Library | 3/3 | Complete   | 2026-06-17 |
| 4. App Shell & League Table | 2/2 | Complete   | 2026-06-17 |
| 5. Today Briefing | 2/2 | Complete   | 2026-06-17 |
| 6. Matches & Match Detail | 2/2 | Complete   | 2026-06-17 |
| 7. Insights & Scouting | 2/2 | Complete   | 2026-06-17 |
| 8. Motion, Accessibility & States | 1/2 | In Progress|  |
