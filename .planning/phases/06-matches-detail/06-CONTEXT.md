# Phase 6: Matches & Match Detail - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

The Matches tab (Upcoming/Results segmented) and the deep Match Detail screen, including the score-ring shared-element morph and the plain-English breakdown. This phase delivers the match browsing and detail viewing experience.

</domain>

<decisions>
## Implementation Decisions

### Matches List Layout
- Segmented control: frosted segmented control at top, "Upcoming" and "Results" tabs (per spec §7.3)
- Match grouping: group by matchday with section headers (per spec)
- Upcoming card layout: CountdownPill + team badges + SoftRing + StrengthBar + tier pill (per spec)
- Results card layout: ring → big actual score + outcome chip via Format.outcomeChip (per spec)

### Match Detail Screen
- Hero section: teams + ranks, SoftRing morphs in via matchedGeometryEffect, tier pill + countdown, chance text (per spec §7.4)
- "Why this pick" section: FrostCard with eyebrow "WHY 1:0", reasons with soft check icons, staggered animation (per spec)
- "The room" section: FriendDots row (8 dots, onSamePick filled iridescent) + separation sentence + leverage/leader chips (per spec)
- Other scores section: alternates rows with score + iridescent expectedPoints bar + note, chosen one tagged "Your pick" (per spec)

### Navigation & States
- Match detail navigation: push via NavigationStack from both Today spotlight and Matches list (per spec)
- Back button style: back chevron with title "Matchday {n}" (per spec)
- Empty states: "No results yet — first picks score after kickoff." / "All caught up. Next matchday {date}." (per spec)
- Shared element transition: SoftRing morphs via matchedGeometryEffect(id:"ring-{id}") from tapped card (per spec §7.4)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FrostCard` for card containers
- `SoftRing` for score visualization (will be used for matchedGeometryEffect)
- `StrengthBar` for home/draw/away strength
- `CountdownPill` (just created in Phase 5)
- `TeamBadge` for team logos
- `SoftPill` for tier/outcome pills
- `InkButton` with `PressScale` for CTAs
- `Format` helpers for human-language conversion (outcomeChip, chanceText)
- `GenerativeAppear` modifier (`.generativeAppear(index:)`)
- `MatchDetailView` stub (created in Phase 5)

### Established Patterns
- `@EnvironmentObject var store: AppStore` for data access
- `Theme` for all styling tokens
- `.generativeAppear(index)` for staggered entrance animations
- `NavigationStack` with `.navigationDestination` for push navigation
- `FrostCard { }` wrapper for card containers
- Section headers with `.eyebrowX` font

### Integration Points
- `RootView.swift` — needs MatchesView wired in (replace placeholder)
- `AppStore.feed` — provides `matches` array
- `MatchDetailView` — stub exists, needs full implementation
- `TodayView.swift` — already pushes MatchDetailView via NavigationLink

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches matching the spec.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
