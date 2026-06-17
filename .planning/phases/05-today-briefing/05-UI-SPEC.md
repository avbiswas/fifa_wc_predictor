---
phase: 5
slug: today-briefing
status: draft
shadcn_initialized: false
preset: not applicable
created: 2026-06-17
---

# Phase 5 — UI Design Contract: Today Briefing

> Visual and interaction contract for the self-assembling Today screen. Source of truth: `docs/ios_app_plan.md` §7.2 + §8.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (native SwiftUI) |
| Preset | not applicable |
| Component library | none (hand-rolled design system) |
| Icon library | SF Symbols |
| Font | SF Pro Display (greeting/hero) + SF Pro Text (body/labels) |

---

## Spacing Scale

Declared values (from `Theme.swift`):

| Token | Value | Usage |
|-------|-------|-------|
| s1 | 4pt | Icon gaps, inline pill padding |
| s2 | 8pt | Compact element spacing, pill internals |
| s3 | 12pt | Small card internal gaps |
| s4 | 16pt | Default card padding, horizontal screen margin |
| s5 | 20pt | Between cards, eyebrow-to-content gap |
| s6 | 24pt | Section-level padding |
| s8 | 32pt | Major section breaks |
| s10 | 40pt | Page-level top padding |

Exceptions: none

---

## Typography

| Token | Font | Size | Weight | Usage in Phase 5 |
|-------|------|------|--------|------------------|
| `.greeting` | SF Pro Display | 30pt | light (300) | "Good evening, Niko." |
| `.heroLight` | SF Pro Display | 48pt | light (300) | "#8" rank in standing card |
| `.displayX` | SF Pro Display | 26pt | medium (500) | SoftRing center score (1:0) |
| `.titleX` | SF Pro Text | 20pt | medium (500) | `strategy.headline` in plan card |
| `.headlineX` | SF Pro Text | 16pt | medium (500) | Team names in spotlight, friend names |
| `.bodyX` | SF Pro Text | 15pt | regular (400) | `strategy.subtitle`, reasons, blurbs |
| `.calloutX` | SF Pro Text | 13pt | regular (400) | Date label, "Generated just now", meta text |
| `.eyebrowX` | SF Pro Text | 11pt | medium (500) | "YOUR POSITION", "TONIGHT'S PLAN", "NEXT UP" — tracking 0.6 |

---

## Color

### Surface Hierarchy

| Role | Token | Value | Usage |
|------|-------|-------|-------|
| Canvas (60%) | `Theme.bg` | `#FCFCFE` | Full-screen background |
| Card (30%) | `Theme.card` | white @ 55% opacity | FrostCard frosted fill |
| Hairline | `Theme.hairline` | white @ 85% opacity | 1px card border top-highlight |
| Track | `Theme.track` | `#ECECF1` | GapRail track, ring track |
| Shadow | `Theme.shadow` | `#282A46` @ 10% | Card soft shadow |

### Text Hierarchy

| Role | Token | Value | Usage |
|------|-------|-------|-------|
| Primary | `Theme.text` | `#2B2B2E` | Body text, rank, team names |
| Dim | `Theme.textDim` | `#9A9AA1` | Eyebrow labels, date, meta |
| Muted | `Theme.textMute` | `#BFC0C6` | Draw label in StrengthBar |
| Ink | `Theme.ink` | `#161618` | InkButton fill, strong emphasis |

### Iridescent Palette (gradient + accents)

| Token | Value | Usage |
|-------|-------|-------|
| `Theme.iridBlue` | `#B9C9F2` | GapRail fill gradient start, IridescentGlow blob |
| `Theme.iridLilac` | `#E7CDEE` | GapRail fill gradient end, IridescentGlow blob |
| `Theme.iridBlush` | `#F6D4DC` | IridescentGlow blob |
| `Theme.iridPeach` | `#F8E7C8` | IridescentGlow blob |
| `Theme.iridMint` | `#CBEBD9` | IridescentGlow blob |
| `Theme.spark` | `#9B8CF0` | GeneratedStatus spark dot, GapRail marker stroke |

### Soft State Pairs (pastel fill + darker same-hue text)

| State | BG | Text | Usage |
|-------|----|------|-------|
| Positive | `Theme.posBG` `#DDF3E7` | `Theme.posText` `#1F7A52` | Tier "strong"/"normal" pills |
| Warning | `Theme.warnBG` `#FBEBD3` | `Theme.warnText` `#9A6512` | Tier "thin_edge" / Coin-flip pill |
| Negative | `Theme.negBG` `#FBE3E0` | `Theme.negText` `#B5483A` | Tier "wild_card" pill |
| Active | `Theme.actBG` `#E7E6FB` | `Theme.actText` `#5B4FC0` | "Against the room" leverage pill |

---

## Screen Layout — TodayView

### Container Structure

```
ZStack {
    Theme.bg.ignoresSafeArea()
    IridescentGlow(intensity: 1.0).ignoresSafeArea()    // full intensity, concentrated top-third
    ScrollView {
        VStack(alignment: .leading, spacing: Theme.s5) { // 20pt between cards
            // ... sections below ...
        }
        .padding(.horizontal, Theme.s4)                  // 16pt side margins
        .padding(.top, Theme.s6)                         // 24pt top
        .padding(.bottom, Theme.s8)                      // 32pt bottom (clear tab bar)
    }
    .id(store.generation)                                 // replays assembly on refresh
    .refreshable { await store.refresh() }
}
```

### Section Order (each `.generativeAppear(index)`)

| Index | Section | Component | Key Data |
|-------|---------|-----------|----------|
| 0 | GeneratedStatus | `GeneratedStatus(updatedAt:)` | `feed.updatedAt` |
| 1 | Date label | `Text` `.calloutX`, `Theme.textDim` | `Date()` formatted "Wed, 17 Jun" |
| 2 | Greeting | `Text` `.greeting`, split word-by-word | `Format.greeting("Niko")` |
| 3 | Standing card | `FrostCard` | `feed.me` |
| 4 | Tonight's plan card | `FrostCard` | `feed.strategy` |
| 5 | Next match spotlight | `FrostCard` | `feed.matches.first { $0.status == "upcoming" }` |
| 6+ | Today's other picks | Compact rows | `feed.matches.dropFirst().filter { $0.status == "upcoming" }` |

### Section 0 — GeneratedStatus

```
Position: top-left of VStack, index 0
Component: GeneratedStatus(updatedAt: feed.updatedAt, generating: isRefreshing)
  - Spark dot: 7pt circle, Theme.spark, pulsing easeInOut(1.2s) repeatForever
  - Text: "Generated just now" in .calloutX, Theme.textDim
  - When refreshing: "Generating your briefing…" in .calloutX, Theme.textDim
```

### Section 1 — Date Label

```
Position: index 1
Content: "Wed, 17 Jun" (or current date)
Font: .calloutX
Color: Theme.textDim
Alignment: .leading
```

### Section 2 — Greeting

```
Position: index 2
Content: Format.greeting("Niko") → "Good evening, Niko."
Font: .greeting (30pt, light)
Color: Theme.text
Word-by-word build: split by " ", each word gets .generativeAppear(2 + wordIndex)
  - "Good" at index 2
  - "evening," at index 3
  - "Niko." at index 4
  - (greeting words use same base/step as standard appear)
```

### Section 3 — Standing Card

```
Position: index 3 (or after greeting words complete)
Component: FrostCard(padding: Theme.s4)

┌─────────────────────────────────────────────────┐
│ Eyebrow "YOUR POSITION"              [iridescent orb 12pt] │
│                                                   │
│ #8  of 9                                          │ ← #8 in .heroLight, "of 9" in .bodyX, Theme.textDim
│                                                   │
│ 6 points behind Alex                              │ ← .bodyX, Theme.text
│                                                   │
│ GapRail(mine: 18, leader: 24, leaderName: "Alex") │ ← rail fills + marker slides in
│                                                   │
│ [SoftPill "ties · matchday wins"]                 │ ← Theme.actBG / Theme.actText
└─────────────────────────────────────────────────┘

Layout:
- Eyebrow + orb: HStack, orb = 12pt circle with LinearGradient(iridBlue→iridLilac)
- Rank line: HStack { "#8" .heroLight .monospacedDigit() + " of 9" .bodyX .textDim }
- Deficit line: Text .bodyX Theme.text
- GapRail: full-width, 6pt capsule track, iridescent fill, 14pt marker circle with spark stroke
- Tiebreaker pill: SoftPill(text: "ties · matchday wins") at bottom
```

### Section 4 — Tonight's Plan Card

```
Position: index 4
Component: FrostCard(padding: Theme.s4)

┌─────────────────────────────────────────────────┐
│ Eyebrow "TONIGHT'S PLAN"        [SF Symbol icon] │
│                                                   │
│ Chasing the lead                                  │ ← .titleX, Theme.ink
│                                                   │
│ Calculated risks to close a 6-point gap           │ ← .bodyX, Theme.textDim
│                                                   │
│ ──────────────────────────────────────────────── │ ← Divider, Theme.track
│                                                   │
│ ◐ 3 draws planned                                 │ ← .bodyX, Theme.text
│   "Nobody here backs draws — so a draw that       │ ← .calloutX, Theme.textDim
│    lands gains on everyone"                        │
└─────────────────────────────────────────────────┘

Layout:
- Eyebrow: HStack { Eyebrow("TONIGHT'S PLAN") + Spacer + Image(Format.modeIcon(strategy.mode)) }
  - Icon: .calloutX, Theme.textDim
- Headline: Text(strategy.headline).font(.titleX).foregroundStyle(Theme.ink)
- Subtitle: Text(strategy.subtitle).font(.bodyX).foregroundStyle(Theme.textDim)
- Divider: Rectangle().fill(Theme.track).frame(height: 1)
- Draw plan row: HStack {
    Image(systemName: "circle.lefthalf.filled") → .calloutX, Theme.textDim
    Text("\(strategy.drawPlan.planned) draws planned") → .bodyX, Theme.text
  }
- Draw reason: Text(strategy.drawPlan.reason).font(.calloutX).foregroundStyle(Theme.textDim)
```

### Section 5 — Next Match Spotlight

```
Position: index 5
Component: FrostCard(padding: Theme.s4)

┌─────────────────────────────────────────────────┐
│ Eyebrow "NEXT UP" · "17:00" · [CountdownPill]    │
│                                                   │
│ [POR] Portugal           [SoftRing: 1:0]          │ ← TeamBadge(42pt) + SoftRing
│ [COD] Congo DR                                   │ ← TeamBadge(42pt)
│                                                   │
│ StrengthBar(home: 0.74, draw: 0.20, away: 0.06)  │ ← fills on appear
│                                                   │
│ [SoftPill "Coin-flip"] [SoftPill "Against the room"] │
│                                                   │
│ InkButton "Why this pick →"                       │ → pushes MatchDetail
└─────────────────────────────────────────────────┘

Layout:
- Eyebrow row: HStack {
    Eyebrow("NEXT UP")
    Text(" · ").font(.eyebrowX).foregroundStyle(Theme.textMute)
    Text(Format.kickoffClock(match.kickoff)).font(.eyebrowX).foregroundStyle(Theme.textDim)
    Text(" · ").font(.eyebrowX).foregroundStyle(Theme.textMute)
    CountdownPill(to: match.kickoff)                    // NEW component — see below
  }

- Matchup row: HStack(alignment: .center) {
    VStack(alignment: .leading, spacing: Theme.s2) {
      HStack { TeamBadge(code: match.home.code) + Text(match.home.name) .headlineX }
      HStack { TeamBadge(code: match.away.code) + Text(match.away.name) .headlineX }
    }
    Spacer()
    SoftRing(
      value: Format.ringFill(oneIn: match.myPick.exactChanceOneIn),
      color: Format.tierRingColor(match.myPick.tier),
      size: 88
    ) {
      Text(match.myPick.score).font(.displayX).monospacedDigit()
    }
  }

- StrengthBar: StrengthBar(
    home: match.odds.home, draw: match.odds.draw, away: match.odds.away,
    homeCode: match.home.code, awayCode: match.away.code
  )

- Pills row: HStack(spacing: Theme.s2) {
    SoftPill(
      text: Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel).text,
      bg: Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel).bg,
      fg: Format.tierStyle(match.myPick.tier, label: match.myPick.tierLabel).fg
    )
    SoftPill(
      text: Format.leverageChip(match.myPick.leverage).text,
      bg: Format.leverageChip(match.myPick.leverage).bg,
      fg: Format.leverageChip(match.myPick.leverage).fg,
      systemImage: Format.leverageChip(match.myPick.leverage).icon
    )
  }

- InkButton: InkButton(title: "Why this pick", systemImage: "arrow.right") {
    // push MatchDetail via NavigationStack path binding
  }
```

### Section 6+ — Today's Other Picks

```
Position: index 6, 7, ... (one per remaining upcoming match)
Component: plain row (no FrostCard), inside a VStack

For each match at array index n:
  .generativeAppear(6 + n)

Row layout:
┌─────────────────────────────────────────────────┐
│ [TeamBadge home 32pt]  "POR"  1:0  "COD"  [TeamBadge away 32pt]  ● tier │
└─────────────────────────────────────────────────┘

- HStack(spacing: Theme.s3) {
    TeamBadge(code: m.home.code, size: 32)
    Text(m.home.code).font(.calloutX).foregroundStyle(Theme.text)
    Text(m.myPick.score).font(.headlineX).monospacedDigit().foregroundStyle(Theme.text)
    Text(m.away.code).font(.calloutX).foregroundStyle(Theme.text)
    TeamBadge(code: m.away.code, size: 32)
    Spacer()
    Circle().fill(Format.tierRingColor(m.myPick.tier)).frame(width: 8, height: 8)  // tier dot
  }
  .padding(.vertical, Theme.s2)

Tap → pushes MatchDetail
```

---

## New Components Required

### CountdownPill (not yet implemented)

```
Purpose: Compact time-until-kickoff indicator
Props: to: Date
Layout:
  - HStack(spacing: 4) {
      Image(systemName: "clock").font(.system(size: 9, weight: .semibold))
      Text(Format.countdown(to: date)).font(.eyebrowX)
    }
    .foregroundStyle(Theme.actText)
    .padding(.horizontal, 8).padding(.vertical, 4)
    .background(Capsule().fill(Theme.actBG))

Behavior:
  - Updates text every 60s via TimelineView or Timer
  - When kickoff passed: text = "Kicking off", bg = Theme.warnBG, fg = Theme.warnText
```

---

## Animation Specifications

### Generative Assembly (§8)

| Parameter | Value |
|-----------|-------|
| Spring response | 0.75 |
| Spring damping | 0.82 |
| Base delay | 0.12s |
| Step per index | 0.085s |
| Blur start | 9pt → 0pt |
| Y offset start | +16pt → 0pt |
| Scale start | 0.97 → 1.0 |

**Stagger order (indices → delays):**

| Index | Element | Delay |
|-------|---------|-------|
| 0 | GeneratedStatus | 0.120s |
| 1 | Date label | 0.205s |
| 2 | "Good" | 0.290s |
| 3 | "evening," | 0.375s |
| 4 | "Niko." | 0.460s |
| 5 | Standing card | 0.545s |
| 6 | Plan card | 0.630s |
| 7 | Spotlight card | 0.715s |
| 8+ | Other picks | 0.800s + 0.085s each |

Total assembly: ~1.2–1.6s (within spec target)

### Sub-animations (within cards, on appear)

| Element | Animation | Delay | Duration |
|---------|-----------|-------|----------|
| GapRail fill | spring(response: 1.0, damping: 0.9) | 0.3s | ~0.8s |
| GapRail marker | spring(response: 1.0, damping: 0.9) | 0.3s | ~0.8s |
| SoftRing arc | spring(response: 1.0, damping: 0.9) | 0.25s | ~1.0s |
| StrengthBar fill | easeOut(duration: 0.8) | 0.2s | 0.8s |
| GeneratedStatus pulse | easeInOut(duration: 1.2).repeatForever | on appear | ∞ |

### Refresh Replay

```
Trigger: .refreshable { await store.refresh() }
Mechanism: store.generation increments → .id(store.generation) remounts ScrollView
  → all .generativeAppear modifiers reset → assembly replays
Status flip: GeneratedStatus shows "Generating your briefing…" during refresh
  → reverts to "Generated just now" when store.phase updates
```

### Reduce Motion

All animations check `@Environment(\.accessibilityReduceMotion)`:
- `.generativeAppear`: snaps to final state immediately (shown = true)
- GapRail/SoftRing/StrengthBar: snaps to final values
- IridescentGlow: paused (TimelineView respects reduceMotion)
- GeneratedStatus pulse: snaps to visible (pulse = true)

---

## Copywriting Contract

### Dynamic Text (computed from data)

| Element | Source | Example Output |
|---------|--------|----------------|
| Greeting | `Format.greeting("Niko")` | "Good evening, Niko." |
| Date | `Date()` formatted | "Wed, 17 Jun" |
| Rank line | `feed.me` | "#8 of 9" |
| Deficit line | `feed.me` | "6 points behind Alex" |
| Strategy headline | `feed.strategy.headline` | "Chasing the lead" |
| Strategy subtitle | `feed.strategy.subtitle` | "Calculated risks to close a 6-point gap" |
| Draw plan | `feed.strategy.drawPlan` | "3 draws planned" |
| Draw reason | `feed.strategy.drawPlan.reason` | "Nobody here backs draws — so a draw that lands gains on everyone" |
| Mode icon | `Format.modeIcon(strategy.mode)` | "scope" (controlled_attack) |
| Kickoff time | `Format.kickoffClock(match.kickoff)` | "17:00" |
| Countdown | `Format.countdown(to: match.kickoff)` | "in 2h 30m" |
| Tier label | `Format.tierStyle(tier, label)` | "Coin-flip" |
| Leverage | `Format.leverageChip(leverage)` | "Against the room" |
| Chance text | `Format.chanceText(oneIn:)` | "1 in 7" |
| Tiebreaker | `feed.me.tiebreaker` | "ties · matchday wins" |

### Static Text (hardcoded in view)

| Element | Copy |
|---------|------|
| Eyebrow: standing | "YOUR POSITION" |
| Eyebrow: plan | "TONIGHT'S PLAN" |
| Eyebrow: spotlight | "NEXT UP" |
| Rank suffix | "of 9" (from `feed.me.playersCount`) |
| Deficit suffix | "points behind" |
| InkButton CTA | "Why this pick" |
| InkButton icon | "arrow.right" |
| Separator | " · " (between eyebrow elements) |
| Draw plan prefix | "draws planned" |

### Empty State

```
Condition: no upcoming matches in feed.matches
Layout: FrostCard {
  VStack(spacing: Theme.s4) {
    Image(systemName: "calendar")
      .font(.system(size: 40))
      .foregroundStyle(Theme.textMute)
    Text("No matches today")
      .font(.titleX)
      .foregroundStyle(Theme.text)
    Text("Next on \(nextMatchDate)")
      .font(.bodyX)
      .foregroundStyle(Theme.textDim)
  }
  .frame(maxWidth: .infinity)
  .padding(.vertical, Theme.s8)
}
```

### Error State

```
Condition: AppStore.phase == .failed
Layout: ContentUnavailableView {
  Label("Couldn't load your league", systemImage: "wifi.slash")
} description: {
  Text("Check your connection and try again.")
} actions: {
  InkButton(title: "Retry") { Task { await store.refresh() } }
}
```

---

## Design Tokens Summary (all from Theme.swift)

### Radii Used

| Token | Value | Usage |
|-------|-------|-------|
| `Theme.rLg` | 26pt | FrostCard corner radius |
| `Theme.rMd` | 20pt | (available) |
| `Theme.rSm` | 14pt | (available) |

### Spacing Used

| Context | Token | Value |
|---------|-------|-------|
| Card padding | `Theme.s4` | 16pt |
| Between cards | `Theme.s5` | 20pt |
| Card top padding | `Theme.s6` | 24pt |
| Bottom clearance | `Theme.s8` | 32pt |
| Horizontal margin | `Theme.s4` | 16pt |
| Pill internal H | 9pt | (SoftPill default) |
| Pill internal V | 5pt | (SoftPill default) |
| Element gaps | `Theme.s2` | 8pt |

---

## Component Inventory — Phase 5 Usage

| Component | Status | Used In |
|-----------|--------|---------|
| `FrostCard` | ✅ exists | Standing card, plan card, spotlight card, empty state |
| `GeneratedStatus` | ✅ exists | Top of screen (index 0) |
| `IridescentGlow` | ✅ exists | Background, intensity: 1.0 |
| `GenerativeAppear` | ✅ exists | All sections |
| `GapRail` | ✅ exists | Standing card |
| `SoftRing` | ✅ exists | Spotlight card (match score) |
| `StrengthBar` | ✅ exists | Spotlight card |
| `SoftPill` | ✅ exists | Tier pill, leverage pill, tiebreaker pill |
| `InkButton` | ✅ exists | "Why this pick" CTA |
| `PressScale` | ✅ exists | InkButton style |
| `TeamBadge` | ✅ exists | Spotlight + other picks |
| `Eyebrow` | ✅ exists | Section headers |
| `Format` | ✅ exists | All computed text |
| `AppStore` | ✅ exists | Data source, refresh, generation |
| `CountdownPill` | ❌ NEW | Spotlight eyebrow — must be created |

---

## States

### Loading State

```
Condition: AppStore.phase == .loading
Behavior: Show breathing IridescentGlow on Theme.bg canvas
  + light skeleton shimmer (optional — near-instant decode means this barely shows)
```

### Loaded State (default)

```
Condition: AppStore.phase == .loaded(feed)
Behavior: Full generative assembly as described above
```

### Refreshing State

```
Condition: .refreshable is active
Behavior: 
  - GeneratedStatus text → "Generating your briefing…"
  - On completion: generation increments → assembly replays
  - Status reverts to "Generated just now"
```

### Empty State (no upcoming matches)

```
Condition: feed.matches.filter { $0.status == "upcoming" }.isEmpty
Behavior: Show standing card + plan card, then empty-state FrostCard for spotlight section
```

### Error State (hard failure)

```
Condition: AppStore.phase == .failed
Behavior: ContentUnavailableView with retry InkButton
  (only shown if no data at all — if bundled data exists, show that silently)
```

---

## Integration Points

### Files to Create

| File | Purpose |
|------|---------|
| `EDGE/Sources/Features/Today/TodayView.swift` | Main Today screen view |
| `EDGE/Sources/DesignSystem/Components/CountdownPill.swift` | New: time-until-kickoff pill |

### Files to Modify

| File | Change |
|------|--------|
| `EDGE/Sources/Features/Shell/RootView.swift` | Replace `PlaceholderTab` for `.today` with `TodayView()` |

### Data Dependencies

| Data | Path | Usage |
|------|------|-------|
| `feed.updatedAt` | `AppStore.feed.updatedAt` | GeneratedStatus timestamp |
| `feed.me` | `AppStore.feed.me` | Standing card (rank, points, deficit, leader) |
| `feed.strategy` | `AppStore.feed.strategy` | Plan card (headline, subtitle, drawPlan, mode) |
| `feed.matches` | `AppStore.feed.matches` | Spotlight + other picks (filtered by status=="upcoming") |
| `store.generation` | `AppStore.generation` | `.id()` for refresh replay |
| `store.refresh()` | `AppStore.refresh()` | Pull-to-refresh action |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS (no third-party)

**Approval:** pending

---

*Generated: 2026-06-17*
*Source: docs/ios_app_plan.md §7.2, §5, §8 + existing Theme/Typography/Components*
