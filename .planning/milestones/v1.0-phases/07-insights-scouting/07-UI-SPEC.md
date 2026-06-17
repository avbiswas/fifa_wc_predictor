---
phase: 7
slug: insights-scouting
status: draft
shadcn_initialized: false
preset: not applicable — SwiftUI iOS app (no web component library)
created: 2026-06-17
---

# Phase 7: Insights & Scouting — UI Design Contract

> Visual and interaction contract for the Insights tab (engine form metrics + sparkline) and per-friend Scouting cards.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (pure SwiftUI, iOS 18+) |
| Preset | not applicable |
| Component library | custom SwiftUI — `FrostCard`, `SoftPill`, `Sparkline`, `StrengthBar`, `Eyebrow`, `GenerativeAppear` |
| Icon library | SF Symbols (`chart.bar`, `crown.fill`, `sparkles`) |
| Font | SF Pro Display (hero) + SF Pro Text (body/labels) — system default |

**Source files (already implemented):**
- `EDGE/Sources/DesignSystem/Theme.swift` — all color/spacing/radius tokens
- `EDGE/Sources/DesignSystem/Typography.swift` — font tokens + `Eyebrow` view
- `EDGE/Sources/DesignSystem/Components/Sparkline.swift` — bar sparkline
- `EDGE/Sources/DesignSystem/Components/FrostCard.swift` — frosted glass card
- `EDGE/Sources/DesignSystem/Components/SoftPill.swift` — state pill
- `EDGE/Sources/DesignSystem/Components/GenerativeAppear.swift` — blur-to-focus stagger
- `EDGE/Sources/Core/Format.swift` — human-language helpers
- `EDGE/Sources/Core/Models.swift` — `Form`, `ScoutReport`, `ScoutReport.Trait`

---

## Spacing Scale

Declared values (from `Theme.swift` — all multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| `Theme.s1` | 4pt | Inline gaps (trait label to bar, pill icon gap) |
| `Theme.s2` | 8pt | Compact element spacing (metric value to caption, trait row gaps) |
| `Theme.s3` | 12pt | Card internal vertical spacing |
| `Theme.s4` | 16pt | Card padding, horizontal screen inset, default element spacing |
| `Theme.s5` | 20pt | Section spacing (between form card and sparkline card) |
| `Theme.s6` | 24pt | Top padding, section breaks |
| `Theme.s8` | 32pt | Empty state vertical padding |

Exceptions: `3pt` spacing between sparkline bars (spec §5.14, matches existing `Sparkline` component).

---

## Typography

| Role | Font Token | Size | Weight | Line Height | Usage |
|------|-----------|------|--------|-------------|-------|
| Eyebrow | `.eyebrowX` | 11pt | medium (500) | 1.2 | Section headers: "How the picks are doing", "Scouting the field", trait labels |
| Body | `.bodyX` | 15pt | regular (400) | 1.5 | Takeaway line, scout blurb |
| Callout | `.calloutX` | 13pt | regular (400) | 1.4 | Metric captions, sparkline caption, rank/points meta, trait value |
| Headline | `.headlineX` | 16pt | medium (500) | 1.3 | Friend name in ScoutCard |
| Display | `.displayX` | 26pt | medium (500) | 1.2 | Metric tile values (24, 1.5, 4, 8/16) |

All numbers use `.monospacedDigit()` for tabular alignment.

---

## Color

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| Dominant (60%) | `Theme.bg` | `#FCFCFE` | App canvas background |
| Secondary (30%) | `Theme.card` | white @ 0.55 opacity | FrostCard fill (frosted glass) |
| Card hairline | `Theme.hairline` | white @ 0.85 opacity | 1px top-highlight border on cards |
| Card shadow | `Theme.shadow` | `#282A46` @ 0.10 opacity | Soft bluish drop shadow |
| Track | `Theme.track` | `#ECECF1` | Empty trait bars, sparkline zero bars |
| Accent — primary | `Theme.iridLilac` | `#E7CDEE` | Sparkline non-zero bars, filled trait level bars |
| Accent — positive | `Theme.posText` | `#1F7A52` | Highlighted metric values ("24", "4" in accent tiles) |
| Accent — positive bg | `Theme.posBG` | `#DDF3E7` | (not used in this phase) |
| Text primary | `Theme.text` | `#2B2B2E` | Non-accent metric values, scout name, blurb |
| Text dim | `Theme.textDim` | `#9A9AA1` | Eyebrow text, captions, rank/points meta |
| Text mute | `Theme.textMute` | `#BFC0C6` | Dividers, decorative separators |
| Ink | `Theme.ink` | `#161618` | (not used in this phase — reserved for CTAs in other screens) |
| Tag — chaos | `Theme.warnText` / `Theme.warnBG` | `#9A6512` / `#FBEBD3` | Tag pill when tag contains "chaos" |
| Tag — contrarian | `Theme.actText` / `Theme.actBG` | `#5B4FC0` / `#E7E6FB` | Tag pill when tag contains "contrarian" or "away" |
| Tag — neutral | `Theme.textDim` / neutral bg | `#9A9AA1` / `#F0F0F3` | Default tag pill (e.g. "The leader", "Tidy & sharp") |
| Spark | `Theme.spark` | `#9B8CF0` | (used by GeneratedStatus, inherited from parent) |

**Accent reserved for:** metric tile values for "points won" and "spot-on scores" only (the two accent tiles). All other metric values use `Theme.text`. Tag pills use semantic colors based on keyword.

---

## Screen Layout: InsightsView

### Screen Structure

```
ZStack {
    Theme.bg.ignoresSafeArea()
    IridescentGlow(intensity: 0.35).ignoresSafeArea()   // faint — not Today

    NavigationStack {
        ScrollView {
            VStack(alignment: .leading, spacing: Theme.s5) {
                // A) Engine form section
                // B) Scouting section
            }
            .padding(.horizontal, Theme.s4)
            .padding(.top, Theme.s6)
            .padding(.bottom, 100)
        }
        .scrollIndicators(.hidden)
        .id(store.generation)                     // replays assembly on refresh
        .refreshable { await store.refresh() }
        .navigationTitle("Insights")
    }
}
```

### Section A: Engine Form (INSIGHT-01 part A)

**Component order (each `.generativeAppear(i)`, i increments):**

| Index | Component | Content | Sizing |
|-------|-----------|---------|--------|
| 0 | `Eyebrow` | "How the picks are doing · last {N} games" | `.eyebrowX`, `Theme.textDim`, tracking 0.6 |
| 1 | `LazyVGrid(columns: 2, spacing: Theme.s3)` | 4× `MetricTile` (see below) | Grid: 2 columns, 12pt gap |
| 2 | `FrostCard` | `Sparkline` + caption | Full width, `Theme.s4` padding |
| 3 | `Text` (takeaway) | Composed from form data | `.bodyX`, `Theme.text` |

**MetricTile component (private, defined in InsightsView):**

```
┌─────────────────────────┐
│  [caption eyebrow]       │   ← Eyebrow(text:), Theme.textDim
│  [value]                 │   ← .displayX, .monospacedDigit()
└─────────────────────────┘
```

- **Sizing:** `RoundedRectangle(cornerRadius: Theme.rMd)` — 20pt radius
- **Fill:** `.ultraThinMaterial` + `Theme.card` overlay (matches FrostCard pattern)
- **Stroke:** `Theme.hairline`, 1pt
- **Shadow:** `Theme.shadow.opacity(0.10)`, radius 24, y 14 (matches FrostCard)
- **Internal padding:** `Theme.s4` (16pt)
- **Value color:** `Theme.posText` (`#1F7A52`) for accent tiles, `Theme.text` for others

**The 4 metric tiles:**

| Value | Caption | Accent? | Data Source |
|-------|---------|---------|-------------|
| `"\(feed.form.points)"` | "points won" | **yes** — `Theme.posText` | `feed.form.points` → 24 |
| `String(format: "%.1f", feed.form.avgPoints)` | "avg per game" | no — `Theme.text` | `feed.form.avgPoints` → 1.5 |
| `"\(feed.form.exact)"` | "spot-on scores" | **yes** — `Theme.posText` | `feed.form.exact` → 4 |
| `"\(feed.form.scored)/\(feed.form.matches)"` | "games that scored" | no — `Theme.text` | `feed.form.scored`/`feed.form.matches` → 8/16 |

**Sparkline card:**

```
┌─────────────────────────────────────────┐
│ ▂▃▅▂▁▆▂▁▅▂▂▁▆▁▁▁                       │   ← Sparkline(values: feed.form.recentPoints)
│ points per pick, most recent on the right │   ← .calloutX, Theme.textDim
└─────────────────────────────────────────┘
```

- `FrostCard(padding: Theme.s4)`
- Sparkline height: 34pt (fixed, from component)
- Caption: `.calloutX`, `Theme.textDim`, below sparkline with `Theme.s2` spacing

**Takeaway line:**

Compose from data. Example pattern:
```
"Scored in \(feed.form.scored) of \(feed.form.matches) and nailed \(feed.form.exact) exact — steady."
```
- Font: `.bodyX`
- Color: `Theme.text`
- Rule: **no raw probabilities, no "%", no jargon.** This is a plain-English summary.

### Section B: Scouting (INSIGHT-01 part B)

**Component order (continues `.generativeAppear(i)` index from section A):**

| Index | Component | Content |
|-------|-----------|---------|
| 4 | `Eyebrow` | "Scouting the field" |
| 5+ | `ForEach(feed.scouting.sorted { $0.rank < $1.rank })` | `ScoutCard(report:)` per friend |

Each `ScoutCard` gets `.generativeAppear(5 + n)` where `n` is its index in the sorted list.

---

## Component Specification: ScoutCard

### Layout

```
┌───────────────────────────────────────────────┐
│ [👑] UnsPascha              #2 · 23 pts       │
│ [SoftPill: Chaos merchant]                     │
│ "Loves big scorelines and wild results.        │
│  Rarely picks the tidy draws you can copy."    │
│ ─────────────────────────────────────────────  │
│ Goals   [●●○]  High                            │
│ Draws   [●○○]  Rare                            │
│ Upsets  [●●●]  Often                           │
└───────────────────────────────────────────────┘
```

### Container

- **Wrapper:** `FrostCard(padding: Theme.s4)` — frosted glass, 26pt radius, white hairline, bluish shadow
- **Width:** `maxWidth: .infinity` (full screen width minus horizontal inset)

### Header Row

- **Leader crown:** `Image(systemName: "crown.fill")` in `Theme.actText` (`.calloutX`), shown only if `report.isLeader`
- **Name:** `report.name` in `.headlineX`, `Theme.text`
- **Spacer**
- **Meta:** `"#\(report.rank) · \(report.points) pts"` in `.calloutX`, `Theme.textDim`, `.monospacedDigit()`

### Tag Pill

- **Component:** `SoftPill(text: report.tag)`
- **Color logic** (keyword-based on `report.tag.lowercased()`):
  - Contains `"chaos"` → `bg: Theme.warnBG` (`#FBEBD3`), `fg: Theme.warnText` (`#9A6512`)
  - Contains `"contrarian"` or `"away"` → `bg: Theme.actBG` (`#E7E6FB`), `fg: Theme.actText` (`#5B4FC0`)
  - Default → `bg: Color(hex: "F0F0F3")`, `fg: Theme.textDim` (`#9A9AA1`)
- **Position:** below header, `Theme.s2` vertical spacing

### Blurb

- **Text:** `report.blurb`
- **Font:** `.bodyX` (15pt, regular)
- **Color:** `Theme.text`
- **Position:** below tag pill, `Theme.s3` vertical spacing

### Trait Bars

- **Divider:** `Rectangle().fill(Theme.track).frame(height: 1)` above traits, `Theme.s3` spacing
- **For each trait in `report.traits`:**

```
HStack(spacing: Theme.s2) {
    Eyebrow(text: trait.label)         // "Goals", "Draws", "Upsets" — fixed width ~70pt
    TraitLevelBar(level: trait.level)   // 3 segments
    Text(trait.value)                   // "High", "Rare", "Often" — .calloutX, Theme.textDim
}
```

**TraitLevelBar (private, 3-segment):**
- 3 `Capsule` segments in an `HStack(spacing: 3)`
- Each capsule: `width: 18pt`, `height: 7pt`
- First `trait.level` capsules: filled `Theme.iridLilac` (`#E7CDEE`)
- Remaining capsules: filled `Theme.track` (`#ECECF1`)
- **Animation:** bars fill from 0 width with `.easeOut(duration: 0.6).delay(0.15)` (only on appear, respects Reduce Motion)

---

## Animation Specifications

### Generative Appear (stagger order)

All content uses `.generativeAppear(index)` with spring animation:
- **Spring:** `response: 0.75, dampingFraction: 0.82`
- **Base delay:** 0.12s
- **Step:** 0.085s per index
- **Effect:** opacity 0→1, y +16→0, scale 0.97→1, blur 9→0

**InsightsView stagger sequence:**

| Index | Element | Delay |
|-------|---------|-------|
| 0 | Eyebrow "How the picks are doing…" | 0.12s |
| 1 | Metric tiles grid (entire grid as one block) | 0.205s |
| 2 | Sparkline card | 0.29s |
| 3 | Takeaway line | 0.375s |
| 4 | Eyebrow "Scouting the field" | 0.46s |
| 5 | ScoutCard[0] (Alex) | 0.545s |
| 6 | ScoutCard[1] (UnsPascha) | 0.63s |
| 7 | ScoutCard[2] (Toegamorf) | 0.715s |
| ... | ... | +0.085s each |
| 12 | ScoutCard[7] (Katha) | 1.14s |

**Total assembly duration:** ~1.2s (within the spec's 1.2–1.6s target).

### Replay on Refresh

- Content wrapped in `.id(store.generation)` — new generation remounts views → assembly replays
- `.refreshable` calls `store.refresh()` which bumps `generation`
- `GeneratedStatus` (if included) flips to "Generating your briefing…" during refresh

### Trait Level Bar Animation

- 3 capsules per trait
- Fill: `shown ? width : 0` with `.easeOut(duration: 0.6).delay(0.15)`
- Respects `@Environment(\.accessibilityReduceMotion)` — snaps to final if true
- Triggered on card appear (each ScoutCard manages its own state)

### Reduce Motion

- All `.generativeAppear` modifiers check `accessibilityReduceMotion` and snap to final state (no blur, no stagger)
- Trait level bars snap to final width
- Sparkline has no animation (static bars)

---

## Copywriting Contract

### Section Headers

| Element | Copy | Notes |
|---------|------|-------|
| Form eyebrow | "How the picks are doing · last {N} games" | `N = feed.form.matches` (16) |
| Scouting eyebrow | "Scouting the field" | Static |
| Sparkline caption | "points per pick, most recent on the right" | Static |

### Metric Tile Captions

| Tile | Caption | Value Format |
|------|---------|--------------|
| Points | "points won" | `"\(feed.form.points)"` → "24" |
| Average | "avg per game" | `String(format: "%.1f", feed.form.avgPoints)` → "1.5" |
| Exact | "spot-on scores" | `"\(feed.form.exact)" → "4"` |
| Scored | "games that scored" | `"\(feed.form.scored)/\(feed.form.matches)"` → "8/16" |

### Takeaway Line

**Pattern:** Compose a single sentence from the form data. Must be plain English, no jargon.

**Template:**
```
"Scored in \(feed.form.scored) of \(feed.form.matches) and nailed \(feed.form.exact) exact — steady."
```

**Rules:**
- No raw probabilities, no "%", no `composite_score`, no `expected_points`
- Allowed: counts (24, 4, 8/16), points (24), averages (1.5 — this is points-per-game, not a probability)
- Sentence case, ends with em dash + one-word assessment ("steady", "solid", "picking up")

### ScoutCard Copy

| Element | Source | Format |
|---------|--------|--------|
| Friend name | `report.name` | Display as-is |
| Rank + points | `report.rank`, `report.points` | "#2 · 23 pts" |
| Tag | `report.tag` | Display as-is in SoftPill |
| Blurb | `report.blurb` | Display as-is (pre-translated by Python) |
| Trait label | `trait.label` | "Goals", "Draws", "Upsets" |
| Trait value | `trait.value` | "High", "Medium", "Low", "Rare", "Some", "Often" |

### Empty State

If `feed.scouting` is empty (unlikely with bundled data):
- Show a `FrostCard` with `Image(systemName: "sparkles")` (40pt, `Theme.textMute`)
- Text: "No scouting data yet" (`.titleX`, `Theme.text`)
- Subtext: "Reports will appear once the engine has enough matches" (`.bodyX`, `Theme.textDim`)

### Error / Loading State

- **Loading (no feed):** `ProgressView()` + "Loading insights…" (`.bodyX`, `Theme.textDim`)
- **Feed exists but form is zero:** Show metric tiles with "0" values, sparkline with all `Theme.track` bars, takeaway: "First picks are in — check back after kickoff."

---

## Registry Safety

Not applicable — this is a native SwiftUI iOS app with no web component registries.

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| N/A | N/A | N/A |

---

## States

### Loading State

```
ZStack {
    Theme.bg.ignoresSafeArea()
    IridescentGlow(intensity: 0.35).ignoresSafeArea()
    VStack(spacing: Theme.s4) {
        ProgressView()
        Text("Loading insights…")
            .font(.bodyX)
            .foregroundStyle(Theme.textDim)
    }
}
```

### Empty State (no scouting data)

```
FrostCard {
    VStack(spacing: Theme.s4) {
        Image(systemName: "sparkles")
            .font(.system(size: 40))
            .foregroundStyle(Theme.textMute)
        Text("No scouting data yet")
            .font(.titleX)
            .foregroundStyle(Theme.text)
        Text("Reports will appear once the engine has enough matches")
            .font(.bodyX)
            .foregroundStyle(Theme.textDim)
    }
    .frame(maxWidth: .infinity)
    .padding(.vertical, Theme.s8)
}
```

### Error State (hard failure, no data at all)

Handled by `AppStore.Phase.failed` — falls through to the shell's error handling. InsightsView guards on `store.feed` and shows loading state if nil.

---

## Integration Points

### Files to Create

| File | Purpose |
|------|---------|
| `EDGE/Sources/Features/Insights/InsightsView.swift` | Main Insights tab view |
| `EDGE/Sources/Features/Insights/ScoutCard.swift` | Per-friend scouting card component |

### Files to Modify

| File | Change |
|------|--------|
| `EDGE/Sources/Features/Shell/RootView.swift` | Replace `.insights` placeholder with `InsightsView()` |
| `EDGE/Sources/Features/Table/TableView.swift` | Add `.sheet(item:)` for ScoutCard on non-you row tap |

### Data Dependencies

| Data Path | Type | Source |
|-----------|------|--------|
| `store.feed.form` | `Form` | `AppStore.feed.form` — engine metrics |
| `store.feed.form.recentPoints` | `[Int]` | Sparkline data (16 values) |
| `store.feed.scouting` | `[ScoutReport]` | Scouting cards data (8 friends) |
| `store.feed.updatedAt` | `Date` | For GeneratedStatus (if included) |

### Existing Components Used

| Component | File | Usage |
|-----------|------|-------|
| `FrostCard` | `DesignSystem/Components/FrostCard.swift` | Metric tile container, sparkline card, ScoutCard wrapper |
| `Sparkline` | `DesignSystem/Components/Sparkline.swift` | Bar chart of recent points |
| `SoftPill` | `DesignSystem/Components/SoftPill.swift` | Scout tag pill |
| `Eyebrow` | `DesignSystem/Typography.swift` | Section headers, trait labels |
| `IridescentGlow` | `DesignSystem/Components/IridescentGlow.swift` | Background gradient (faint) |
| `GeneratedStatus` | `DesignSystem/Components/GeneratedStatus.swift` | (optional) Spark dot + "Generated just now" |
| `GenerativeAppear` | `DesignSystem/Components/GenerativeAppear.swift` | `.generativeAppear(index)` stagger |

---

## Spec Traceability

| UI-SPEC Section | Spec Reference | Requirement |
|-----------------|----------------|-------------|
| Section A: Engine Form | §7.6 (p.978) | INSIGHT-01 |
| Section B: Scouting | §7.7 (p.978) | INSIGHT-01 |
| Sparkline | §5.14 | COMP-03 |
| FrostCard | §5.5 | COMP-01 |
| SoftPill | §5.9 | COMP-02 |
| GenerativeAppear | §5.4 | FND-04 |
| No-jargon rule | §0, §6 | LANG-01 |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS — all strings defined, no jargon, sentence case
- [ ] Dimension 2 Visuals: PASS — component specs match existing design system
- [ ] Dimension 3 Color: PASS — all tokens from Theme.swift, semantic tag coloring defined
- [ ] Dimension 4 Typography: PASS — all font tokens from Typography.swift
- [ ] Dimension 5 Spacing: PASS — all values from Theme spacing tokens (multiples of 4)
- [ ] Dimension 6 Registry Safety: PASS — not applicable (native SwiftUI)

**Approval:** pending
