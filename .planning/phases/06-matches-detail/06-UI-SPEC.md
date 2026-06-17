---
phase: 6
slug: matches-detail
status: draft
shadcn_initialized: false
preset: not applicable (SwiftUI iOS app)
created: 2026-06-17
---

# Phase 6 — UI Design Contract: Matches & Match Detail

> Visual and interaction contract for the Matches tab and Match Detail screen.
> Source of truth: `docs/ios_app_plan.md` §7.3 (Matches), §7.4 (Match Detail), §8 (Motion).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (native SwiftUI) |
| Preset | not applicable |
| Component library | hand-rolled SwiftUI (FrostCard, SoftRing, StrengthBar, etc.) |
| Icon library | SF Symbols |
| Font | SF Pro Display (greeting/hero), SF Pro Text (body/labels) |

---

## Spacing Scale

Declared values (from `Theme.swift`):

| Token | Value | Usage |
|-------|-------|-------|
| s1 | 4px | Icon gaps, inline pill padding |
| s2 | 8px | Compact element spacing, team badge gaps |
| s3 | 12px | Card internal row spacing |
| s4 | 16px | Card padding, horizontal inset |
| s5 | 20px | Between cards (VStack spacing) |
| s6 | 24px | Section padding, top inset |
| s8 | 32px | Bottom safe area padding, major breaks |
| s10 | 40px | Unused in this phase |

Exceptions: TeamBadge sizes vary (36px in detail, 42px in spotlight). SoftRing sizes vary (88px in cards, 108px in detail hero).

---

## Typography

| Role | Font Token | Size | Weight | Usage |
|------|-----------|------|--------|-------|
| Display | `.displayX` | 26pt | medium | Score ring center, actual score in results |
| Title | `.titleX` | 20pt | unused in this phase | — |
| Headline | `.headlineX` | 16pt | medium | Team names, "Why this pick" reasons |
| Body | `.bodyX` | 15pt | regular | Reason text, chance line, room sentence |
| Callout | `.calloutX` | 13pt | regular | Rank numbers, countdown text, meta |
| Eyebrow | `.eyebrowX` | 11pt | medium (tracking 0.6) | Section headers: MATCHDAY, WHY 1:0, THE ROOM |

All numeric values use `.monospacedDigit()`.

---

## Color

| Role | Token | Value | Usage |
|------|-------|-------|-------|
| Dominant (60%) | `Theme.bg` | #FCFCFE | App canvas background |
| Secondary (30%) | `Theme.card` | white @ 0.55 opacity | FrostCard fill (frosted) |
| Accent (10%) | `Theme.spark` | #9B8CF0 | CountdownPill dot, "generating" spark |
| Iridescent | `Theme.irid*` | 5 pastel colors | Gradient glow (faint at top of detail) |

### State Colors (soft pairs — fill + darker same-hue text)

| State | Background | Text | Usage |
|-------|-----------|------|-------|
| Positive (win/exact) | `Theme.posBG` #DDF3E7 | `Theme.posText` #1F7A52 | Outcome pills: "Spot on +4", score color when points > 0 |
| Warning (coin-flip) | `Theme.warnBG` #FBEBD3 | `Theme.warnText` #9A6512 | Thin-edge tier pill, countdown when past |
| Negative (miss/risk) | `Theme.negBG` #FBE3E0 | `Theme.negText` #B5483A | Outcome pill "Missed +0", score color when miss |
| Active (contrarian) | `Theme.actBG` #E7E6FB | `Theme.actText` #5B4FC0 | Leverage chip "Against the room", leader chip, countdown |

Accent reserved for: countdown pill dot, iridescent glow, iridescent expectedPoints bar in alternates, friend dots (onSamePick filled iridescent).

---

## Screens

### Screen 1: MatchesView (§7.3)

**Layout order** (each `.generativeAppear(i)`, i increments):

```
i=0  Title "Matches" (.titleX, ink)
i=1  Frosted Segmented Control [ Upcoming | Results ]
i=2+ Matchday section header (Eyebrow: "MATCHDAY 3 · 17 Jun")
     MatchRowCard ×N (each .generativeAppear(i++))
```

**Content inset:** `.padding(.horizontal, Theme.s4)`, `.padding(.top, Theme.s6)`, `.padding(.bottom, 100)`.

**Background:** `ZStack { Theme.bg.ignoresSafeArea(); IridescentGlow(intensity: 0.35).ignoresSafeArea() }`

#### Segmented Control
- Frosted capsule: `.ultraThinMaterial` + `Theme.hairline` stroke + soft shadow
- Two segments: "Upcoming" and "Results"
- Selected: `Theme.ink` background, white text, `.headlineX`
- Unselected: clear background, `Theme.textDim`, `.calloutX`
- Segments toggle `@State private var showResults: Bool`
- Light haptic on toggle (`UIImpactFeedbackGenerator(.light)`)

#### Matchday Section Headers
- Eyebrow text: "MATCHDAY {n} · {formatted date}"
- Date format: `d MMM` (e.g., "17 Jun")
- Spacing: `Theme.s4` above, `Theme.s2` below

#### MatchRowCard — Upcoming (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ CountdownPill                          [tier SoftPill]
│ [POR] Portugal              [SoftRing 1:0]       88px ring
│ [COD] Congo DR
│ StrengthBar (home/draw/away)
└─────────────────────────────────────────────────┘
```

- **Row 1:** CountdownPill (left) + tier SoftPill (right)
- **Row 2:** TeamBadge(42px) + home name (.headlineX) | SoftRing(88px, center: score .displayX .monospacedDigit)
- **Row 3:** TeamBadge(42px) + away name (.headlineX)
- **Row 4:** StrengthBar (home/draw/away)
- Card spacing: `Theme.s3` between rows
- NavigationLink wrapping: `NavigationLink(value: match.id)` with `.buttonStyle(PressScale())`
- Ring uses `matchedGeometryEffect(id: "ring-\(match.id)", in: namespace)` for shared-element morph

#### MatchRowCard — Results (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ Matchday 3 · 17 Jun                  [Spot on +4]  (soft mint pill)
│ [POR] Portugal  2        your tip 1:0  ✓
│ [COD] Congo DR  0
└─────────────────────────────────────────────────┘
```

- **Row 1:** Eyebrow "Matchday {n} · {date}" (left) + outcome SoftPill via `Format.outcomeChip` (right)
- **Row 2:** TeamBadge(36px) + home name (.headlineX) + actual score (.displayX .monospacedDigit, ink) + pick score (.calloutX, textDim) + checkmark if points > 0
- **Row 3:** TeamBadge(36px) + away name (.headlineX) + actual score
- Score color: `Theme.posText` if any points, `Theme.negText` if miss
- NavigationLink wrapping same as upcoming

#### Empty States

| State | Copy | Icon |
|-------|------|------|
| No results yet | "No results yet — first picks score after kickoff." | `clock` (textMute, 32pt) |
| No upcoming | "All caught up. Next matchday {date}." | `calendar` (textMute, 32pt) |

Empty state renders in a FrostCard with centered VStack, `Theme.s8` vertical padding.

---

### Screen 2: MatchDetailView (§7.4)

**Layout order** (each `.generativeAppear(i)`, i increments from 0):

```
i=0  Hero section (teams + ring + tier + countdown/chance)
i=1  "Why this pick" FrostCard
i=2  "The matchup" FrostCard
i=3  "The room" FrostCard
i=4  "Other scores" FrostCard
i=5  "News" FrostCard (if any news items exist)
```

**Background:** `ZStack { Theme.bg.ignoresSafeArea(); IridescentGlow(intensity: 0.25).ignoresSafeArea() }`

**Navigation:** `.navigationTitle("Matchday {n}")`, `.navigationBarTitleDisplayMode(.inline)`

**Content inset:** `.padding(.horizontal, Theme.s4)`, `.padding(.top, Theme.s6)`, `.padding(.bottom, Theme.s8)`

**Refresh:** `.id(store.generation)` on ScrollView, `.refreshable { await store.refresh() }`

#### Section 0: Hero

```
┌─────────────────────────────────────────────────┐
│ [POR] Portugal  #55                              │
│ [COD] Congo DR  #5                               │
│                                                  │
│              ┌──────────┐                        │
│              │  SoftRing │  108px, morphs in      │
│              │   1:0     │  via matchedGeometry   │
│              └──────────┘                        │
│                                                  │
│ [SoftPill: Coin-flip]  CountdownPill             │
│ "1 in 7 chance it lands exactly."                │
└─────────────────────────────────────────────────┘
```

- **Team rows:** TeamBadge(36px) + name (.headlineX, Theme.text) + rank ("#55", .calloutX, Theme.textDim)
- **SoftRing:** 108px, value from `Format.ringFill(oneIn:)`, color from `Format.tierRingColor`, center = score (.displayX .monospacedDigit)
- **Ring morph:** `matchedGeometryEffect(id: "ring-\(match.id)", in: namespace)` — the ring animates from the tapped card position to the detail hero position
- **Tier pill:** `SoftPill` with `Format.tierStyle(tier, label:)`
- **Countdown/Result:** if upcoming → `CountdownPill(kickoff:)`; if final → outcome SoftPill via `Format.outcomeChip`
- **Chance line:** `Format.chanceText(oneIn:)` → "1 in 7 chance it lands exactly." (.bodyX, Theme.textDim)

#### Section 1: "Why this pick" (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ Eyebrow: WHY 1:0                                 │
│ ✓ Portugal are clear favorites tonight           │
│ ✓ 1:0 is the best-value exact score here         │
│ ✓ Most friends go 2:0 or 2:1 — this buys you    │
│   separation                                     │
└─────────────────────────────────────────────────┘
```

- Eyebrow: "WHY {pick.score}" — uppercase, `.eyebrowX`
- Each reason: `Image(systemName: "checkmark").foregroundStyle(Theme.posText)` + reason text (.bodyX, Theme.text)
- Spacing: `Theme.s2` between reasons
- Reasons stream in: each reason gets its own `.generativeAppear(i)` where i increments (stagger within card)

#### Section 2: "The matchup" (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ StrengthBar (POR / draw / COD)                   │
│ Heavy favorite                                   │
│ ⚠ Form favors Portugal  (only if isUpset)        │
└─────────────────────────────────────────────────┘
```

- `StrengthBar(home:draw:away:homeCode:awayCode:)`
- Strength line: `Format.strengthWords(favoriteStrength)` (.bodyX, Theme.text)
- Upset warning (conditional): if `match.upset.isUpset` → `Image(systemName: "exclamationmark.triangle").foregroundStyle(Theme.negText)` + `match.upset.text` (.bodyX, Theme.negText)

#### Section 3: "The room" (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ Eyebrow: THE ROOM                                │
│ ● ● ● ○ ○ ○ ○ ○  (8 dots, 1 filled iridescent) │
│ Only 1 of 8 friends land here — that's your      │
│ separation.                                      │
│ [Against the room] [Different from Alex]         │
│ Leader's likely tip: 2:1                         │
└─────────────────────────────────────────────────┘
```

- **Eyebrow:** "THE ROOM"
- **FriendDots:** HStack of 8 circles (10px each, spacing 6px). Filled = iridescent gradient (iridBlue→iridLilac). Unfilled = `Theme.track`.
- **Separation sentence:**
  - If `onSamePick < friendsTotal / 2`: "Only {onSame} of {total} friends land here — that's your separation." (.bodyX, Theme.text)
  - If `onSamePick >= friendsTotal / 2`: "{onSame} of {total} friends are on this pick — the room agrees." (.bodyX, Theme.text)
- **Chips row:** leverage SoftPill via `Format.leverageChip` + vsLeader SoftPill via `Format.leaderChip`
- **Leader tip:** "Leader's likely tip: {leaderPick}" (.calloutX, Theme.textDim) — only if `leaderPick` is non-nil

#### Section 4: "Other scores" (FrostCard)

```
┌─────────────────────────────────────────────────┐
│ Eyebrow: OTHER SCORES                            │
│ 2:0  ████████░░  Crowd pick                      │
│ 1:1  ███░░░░░░░  Draw swing                      │
│ 1:0  █████████░  Best value  ← "Your pick" pill   │
└─────────────────────────────────────────────────┘
```

- **Eyebrow:** "OTHER SCORES"
- Each alternate row: score (.headlineX .monospacedDigit) + thin iridescent expectedPoints bar (relative length, no number shown) + note (.calloutX, Theme.textDim)
- **ExpectedPoints bar:** thin capsule (4pt height), `LinearGradient(colors: [Theme.iridBlue, Theme.iridLilac])`, width proportional to `expectedPoints / maxExpectedPoints`
- **Chosen one:** the alternate matching `match.myPick.score` gets a "Your pick" SoftPill (Theme.posBG, Theme.posText) appended right
- Spacing: `Theme.s2` between rows

#### Section 5: "News" (FrostCard, conditional)

```
┌─────────────────────────────────────────────────┐
│ Eyebrow: NEWS                                    │
│ 📰 Portugal expected to rotate two starters      │
└─────────────────────────────────────────────────┘
```

- Only renders if `match.news` is non-empty
- **Eyebrow:** "NEWS"
- Each news item: `Image(systemName: "newspaper").foregroundStyle(Theme.textDim)` + text (.bodyX, Theme.text)
- Spacing: `Theme.s2` between items

---

## Animation Specifications

### Generative Assembly (MatchesView)

| Index | Element | Delay |
|-------|---------|-------|
| 0 | Title "Matches" | 0.12s |
| 1 | Segmented control | 0.205s |
| 2 | First matchday header | 0.29s |
| 3+ | MatchRowCards (sequential) | 0.12 + i×0.085s |

Each element: opacity 0→1, y +16→0, scale .97→1, **blur 9→0**, spring(response:0.75, dampingFraction:0.82).

### Generative Assembly (MatchDetailView)

| Index | Element | Delay |
|-------|---------|-------|
| 0 | Hero (teams + ring + pills) | 0.12s |
| 1 | "Why this pick" card | 0.205s |
| 2 | "The matchup" card | 0.29s |
| 3 | "The room" card | 0.375s |
| 4 | "Other scores" card | 0.46s |
| 5 | "News" card (if present) | 0.545s |

### Why-This-Pick Reason Stagger

Within the "Why this pick" card, each reason bullet gets its own `.generativeAppear`:
- Reason 0: base delay + 0.085s
- Reason 1: base delay + 0.17s
- Reason 2: base delay + 0.255s

### SoftRing Morph (matchedGeometryEffect)

- Source: MatchRowCard in MatchesView or TodayView spotlight
- Destination: MatchDetailView hero
- Shared ID: `"ring-\(match.id)"`
- Namespace: `@Namespace private var ringNamespace` in both source and destination views
- Animation: `.spring(response:0.75, dampingFraction:0.82)` via `.animation(.spring(...), value: namespace)`
- Fallback: if morph is fiddly, use `.scale + opacity + blur` transition (per spec §8.7)

### Ring Draw

- Arc 0→value, `.spring(response:1.0, dampingFraction:0.9)`, delay 0.25s
- Already implemented in `SoftRing.swift`

### StrengthBar Fill

- Width 0→value, `.easeOut(duration:0.8)`, delay 0.2s
- Already implemented in `StrengthBar.swift`

### Press Feedback

- All NavigationLink cards use `.buttonStyle(PressScale())`
- Scale .97 spring(response:0.3, dampingFraction:0.7)

### Replay on Refresh

- ScrollView keyed `.id(store.generation)`
- `.refreshable` bumps generation → remount → full assembly replays

---

## Copywriting Contract

### MatchesView

| Element | Copy |
|---------|------|
| Screen title | "Matches" |
| Segment 1 | "Upcoming" |
| Segment 2 | "Results" |
| Matchday header | "MATCHDAY {n} · {d MMM}" |
| Empty: no results | "No results yet — first picks score after kickoff." |
| Empty: no upcoming | "All caught up. Next matchday {date}." |

### MatchDetailView

| Element | Copy |
|---------|------|
| Nav title | "Matchday {n}" |
| Why eyebrow | "WHY {pick.score}" (e.g., "WHY 1:0") |
| Why reasons | From `match.myPick.reasons[]` — full short sentences |
| The matchup eyebrow | (none — StrengthBar + strength words) |
| Strength words | `Format.strengthWords(favoriteStrength)` → "Heavy favorite" / "Clear favorite" / "Slight edge" / "Even game" |
| Upset text | From `match.upset.text` (e.g., "Form favors Portugal") |
| Room eyebrow | "THE ROOM" |
| Room separation (minority) | "Only {onSame} of {total} friends land here — that's your separation." |
| Room separation (majority) | "{onSame} of {total} friends are on this pick — the room agrees." |
| Leader tip | "Leader's likely tip: {leaderPick}" |
| Other scores eyebrow | "OTHER SCORES" |
| Chosen tag | "Your pick" |
| News eyebrow | "NEWS" |
| Chance line | `Format.chanceText(oneIn:)` → "1 in {n} chance it lands exactly." |

### Outcome Chips (via Format.outcomeChip)

| Outcome | Text | Colors |
|---------|------|--------|
| exact | "Spot on +{points}" | posText / posBG |
| goaldiff | "Right margin +{points}" | posText / posBG |
| tendency | "Right winner +{points}" | posText / posBG |
| draw | "Called the draw +{points}" | posText / posBG |
| miss | "Missed +0" | negText / negBG |

### Destructive Actions

None in this phase. No delete, no irreversible actions.

---

## States

| State | Trigger | Visual |
|-------|---------|--------|
| Loading | `store.phase == .loading` | ProgressView + "Loading your matches…" (bodyX, textDim) centered |
| Loaded (Upcoming) | Matches with status "upcoming" exist | Full list with generative assembly |
| Loaded (Results) | Matches with status "final" exist | Full list with outcome pills |
| Empty (Upcoming) | No upcoming matches | FrostCard with calendar icon + "All caught up. Next matchday {date}." |
| Empty (Results) | No final matches | FrostCard with clock icon + "No results yet — first picks score after kickoff." |
| Error | `store.phase == .failed` | ContentUnavailableView: "Couldn't load matches" + Retry InkButton |

---

## Design Tokens Summary

### Radii Used

| Token | Value | Usage |
|-------|-------|-------|
| `Theme.rSm` | 14pt | (unused in this phase) |
| `Theme.rMd` | 20pt | (unused in this phase) |
| `Theme.rLg` | 26pt | FrostCard corners |
| `Theme.rXl` | 34pt | (unused in this phase) |

### Component Sizes

| Component | Size | Context |
|-----------|------|---------|
| TeamBadge | 42px | Upcoming card, spotlight |
| TeamBadge | 36px | Results card, detail hero |
| SoftRing | 88px | Upcoming card, results card |
| SoftRing | 108px | Detail hero |
| FriendDot | 10px | Room section dots |
| ExpectedPoints bar | 4pt height | Other scores section |

---

## Component Inventory (Existing — Reuse)

| Component | File | Status |
|-----------|------|--------|
| FrostCard | `DesignSystem/Components/FrostCard.swift` | ✅ Exists |
| SoftRing | `DesignSystem/Components/SoftRing.swift` | ✅ Exists |
| StrengthBar | `DesignSystem/Components/StrengthBar.swift` | ✅ Exists |
| CountdownPill | `DesignSystem/Components/CountdownPill.swift` | ✅ Exists |
| TeamBadge | `DesignSystem/Components/TeamBadge.swift` | ✅ Exists |
| SoftPill | `DesignSystem/Components/SoftPill.swift` | ✅ Exists |
| InkButton | `DesignSystem/Components/InkButton.swift` | ✅ Exists |
| PressScale | `DesignSystem/Components/InkButton.swift` | ✅ Exists |
| Eyebrow | `DesignSystem/Typography.swift` | ✅ Exists |
| IridescentGlow | `DesignSystem/Components/IridescentGlow.swift` | ✅ Exists |
| GenerativeAppear | `DesignSystem/Components/GenerativeAppear.swift` | ✅ Exists |
| GeneratedStatus | `DesignSystem/Components/GeneratedStatus.swift` | ✅ Exists |

## Components to Build

| Component | File | Description |
|-----------|------|-------------|
| SegmentedControl | `Features/Matches/SegmentedControl.swift` | Frosted segmented picker (Upcoming/Results) |
| MatchRowCard | `Features/Matches/MatchRowCard.swift` | Upcoming + Results card variants |
| FriendDots | `Features/Matches/FriendDots.swift` | Row of dots for "the room" section |

## Files to Modify

| File | Change |
|------|--------|
| `Features/Matches/MatchDetailView.swift` | Replace stub with full 6-section detail |
| `Features/Shell/RootView.swift` | Wire MatchesView as tab content |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS (no third-party registries — native SwiftUI)

**Approval:** pending
