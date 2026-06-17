# Phase 5: Today Briefing - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

The showcase home screen that assembles itself — greeting, standing with gap rail, tonight's plan, next-match spotlight — and replays the generative assembly on pull-to-refresh. This is the "wow" screen that must look stunning and be instantly understandable on open.

</domain>

<decisions>
## Implementation Decisions

### Greeting & Header Assembly
- Greeting word-by-word animation — split into words, each `.generativeAppear` for a word-by-word build (per spec §8)
- GeneratedStatus position: top-left, above greeting (per spec §7.2)
- Date label: show "Wed, 17 Jun" in `.callout`, dim (per spec)
- IridescentGlow intensity: full 1.0 intensity concentrated on top third (per spec)

### Standing Card & Tonight's Plan
- Standing card layout: Eyebrow "YOUR POSITION" + orb, rank "#8 of 9", "6 points behind Alex", GapRail, tiebreaker pill (per spec)
- Tonight's plan card structure: Eyebrow + icon, strategy.headline (title), strategy.subtitle (body), divider, drawPlan row with reason (per spec)
- GapRail animation: rail fills + marker slides in on appear (per spec §5.7)
- Missing plan data: show "No matches today — next on {date}" with soft iridescent calendar glyph (per spec empty state)

### Next Match Spotlight & Other Picks
- Spotlight card content: Eyebrow "NEXT UP · 17:00 · CountdownPill", team badges with SoftRing, StrengthBar, tier/room pills, InkButton "Why this pick →" (per spec)
- InkButton navigation: push MatchDetail via NavigationStack (per spec)
- Today's other picks: compact rows with TeamBadge home, score, TeamBadge away, tier dot (per spec §7.2.6)
- Refresh behavior: pull-to-refresh replays assembly, flips status to "Generating your briefing…" (per spec §8)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppStore` with `@Published var generation: Int` for refresh tracking
- `FrostCard` for card containers
- `GapRail` for standing gap visualization
- `GeneratedStatus` for spark dot + "Generated just now" status
- `GenerativeAppear` modifier (`.generativeAppear(index:)`)
- `SoftRing` for score visualization
- `StrengthBar` for home/draw/away strength
- `InkButton` with `PressScale` for CTAs
- `TeamBadge` for team logos
- `SoftPill` for tier/outcome pills
- `Format` helpers for human-language conversion
- `IridescentGlow` for gradient background

### Established Patterns
- `@EnvironmentObject var store: AppStore` for data access
- `Theme` for all styling tokens (colors, spacing, radii, typography)
- `.generativeAppear(index)` for staggered entrance animations
- `.refreshable { await store.refresh() }` for pull-to-refresh
- `store.generation` as `.id()` to trigger re-render on refresh
- `FrostCard { }` wrapper for card containers
- Navigation via `NavigationStack` and `.navigationTitle()`

### Integration Points
- `RootView.swift` — currently shows `PlaceholderTab` for `.today`; needs to be replaced with `TodayView`
- `AppStore.feed` — provides `Feed` data including `me`, `strategy`, `form`, `table`, `matches`
- `Feed` models in `Models.swift` — `me`, `strategy`, `form`, `table`, `matches` arrays

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches matching the spec.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
