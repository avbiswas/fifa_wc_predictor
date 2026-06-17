# Phase 7: Insights & Scouting - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

The Insights tab — engine form metrics with a sparkline, plus a scouting report card for each friend. This phase delivers the analytics and opponent intelligence view.

</domain>

<decisions>
## Implementation Decisions

### Insights Tab Layout
- Engine form metrics: 4 metric tiles (24 points, 1.5 avg, 4 spot-on, 8-of-16 scored) + sparkline (per spec §7.6)
- Sparkline visualization: bar chart with Theme.iridLilac for non-zero, Theme.track for zero (per spec §5.14)
- Takeaway text: "Engine form" eyebrow + one-line takeaway (per spec)
- Layout structure: VStack with metrics card + sparkline card + scouting list (per spec)

### Scouting Cards
- Scouting card layout: tag pill (colored by tag type) + blurb + 3 trait level bars (filled = level) (per spec §7.7)
- Card sorting: sorted by rank (per spec)
- Tag pill colors: use Format.tagColor for each tag type (per spec)
- Trait level bars: 3 bars per trait, filled to level (per spec)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FrostCard` for card containers
- `Sparkline` component (created in Phase 3, spec §5.14)
- `SoftPill` for tag pills
- `StrengthBar` (can be adapted for trait level bars)
- `Format` helpers for human-language conversion
- `GenerativeAppear` modifier (`.generativeAppear(index:)`)
- `AppStore` with `feed.form` and `feed.table` data

### Established Patterns
- `@EnvironmentObject var store: AppStore` for data access
- `Theme` for all styling tokens
- `.generativeAppear(index)` for staggered entrance animations
- `FrostCard { }` wrapper for card containers
- `.eyebrowX` font for section headers

### Integration Points
- `RootView.swift` — needs InsightsView wired in (replace placeholder)
- `AppStore.feed` — provides `form` (engine metrics) and `table` (player data for scouting)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches matching the spec.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
