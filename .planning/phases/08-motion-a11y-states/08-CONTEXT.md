# Phase 8: Motion, Accessibility & States - Context

**Gathered:** 2026-06-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden the experience — finish motion (shared-element morph, haptics, word-build greeting), wire accessibility (Reduce Motion, VoiceOver), add empty/loading/error states, audit the no-jargon rule globally, and verify the full acceptance checklist. This is the polish and quality phase.

</domain>

<decisions>
## Implementation Decisions

### Motion Polish
- Shared-element ring morph: implement matchedGeometryEffect for ring from card → detail (per spec §8)
- Haptic feedback: tab-switch + card-press haptics (per spec §8)
- Word-build greeting: split greeting into words, each with .generativeAppear (per spec §8)
- Press-scale audit: audit all interactive elements for press-scale feedback (per spec)

### Accessibility
- Reduce Motion: snap all animations to final state, pause gradient (per spec §9)
- VoiceOver: read worded labels for rings/bars/table rows (per spec §9)
- Color contrast: ensure all text meets AA contrast ratios (per spec)
- Touch targets: all interactive elements ≥ 44pt (per iOS guidelines)

### States & No-Jargon Audit
- Empty/loading/error states: graceful states for each screen (per spec §10)
- No-jargon audit: global audit — no raw %, probability, composite_score, expected_points as text (per spec §0)
- Error recovery: retry buttons on error states, offline fallback (per spec §10)
- State transitions: smooth transitions between states (per spec)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- All existing components (FrostCard, SoftRing, StrengthBar, GapRail, etc.)
- GenerativeAppear modifier (`.generativeAppear(index:)`)
- Format helpers for human-language conversion
- AppStore with feed data
- IridescentGlow for gradient background

### Established Patterns
- `@EnvironmentObject var store: AppStore` for data access
- `Theme` for all styling tokens
- `.generativeAppear(index)` for staggered entrance animations
- `UIImpactFeedbackGenerator` for haptics (already used in RootView)
- `accessibilityReduceMotion` check for motion preferences

### Integration Points
- All existing screens (Today, Matches, Table, Insights, MatchDetail)
- All existing components
- AppStore for data loading states

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches matching the spec.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
