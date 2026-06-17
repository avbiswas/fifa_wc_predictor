---
phase: 8
slug: motion-a11y-states
status: draft
created: 2026-06-17
---

# Phase 8 — Motion, Accessibility & States: UI Design Contract

> Visual and interaction contract for the final polish phase. Covers motion hardening, accessibility, graceful states, and the no-jargon audit. Source of truth: `docs/ios_app_plan.md` §8, §9, §10.

---

## Design System

| Property | Value |
|----------|-------|
| Platform | iOS 18+, SwiftUI |
| Appearance | Light mode only |
| Component library | Hand-rolled (FrostCard, SoftRing, StrengthBar, GapRail, etc.) |
| Icon library | SF Symbols |
| Font | SF Pro Display (greeting/hero), SF Pro Text (body/labels) |
| Design tokens | `Theme.swift`, `Typography.swift` |

---

## 1. Motion Specifications

### 1.1 Generative Assembly (exists — verify & harden)

The signature animation. Every screen element enters with blur-to-focus + rise + scale + fade, staggered top-to-bottom.

| Parameter | Value | Source |
|-----------|-------|--------|
| Spring response | 0.75s | spec §5.4 |
| Damping fraction | 0.82 | spec §5.4 |
| Base delay | 0.12s | spec §5.4 |
| Step delay | 0.085s per index | spec §5.4 |
| Blur radius | 9pt → 0pt | spec §5.4 |
| Scale | 0.97 → 1.0 | spec §5.4 |
| Offset Y | 16pt → 0pt | spec §5.4 |
| Total assembly time | ~1.2–1.6s | spec §8 |

**Current state:** GenerativeAppear modifier exists. Already wired on all screens with `.generativeAppear(i)`.

**Action required:** Verify all screens use incrementing indices. Confirm `.id(store.generation)` replays assembly on refresh. No code changes expected unless gaps found.

### 1.2 Word-Build Greeting (exists — verify)

| Parameter | Value | Source |
|-----------|-------|--------|
| Split | By word | spec §8, item 4 |
| Each word | `.generativeAppear(1 + wordIndex)` | spec §8 |
| Name weight | `.medium` on last word | spec §7.2 |

**Current state:** `TodayView.greetingWords()` splits greeting into words. Currently uses a single `.generativeAppear(2)` on the HStack wrapper, not per-word.

**Action required:** Refactor `greetingWords()` so each `Text(word)` gets its own `.generativeAppear(1 + wordIndex)` for word-by-word assembly. The name word (last) gets `.greeting.weight(.medium)`.

### 1.3 Shared-Element Ring Morph (NEW)

| Parameter | Value | Source |
|-----------|-------|--------|
| Effect | `matchedGeometryEffect` | spec §8, item 7 |
| ID pattern | `"ring-\(match.id)"` | spec §8 |
| Shared namespace | `@Namespace private var ns` | spec §8 |
| Transition | Ring scales/positions from card to detail hero | spec §8 |
| Fallback | `.scale + opacity + blur` if fiddly | spec §8 |

**Action required — Plan 08-01:**

1. Add `@Namespace private var ns` to `MatchesView`.
2. On `MatchRowCard`'s `SoftRing`: `.matchedGeometryEffect(id: "ring-\(match.id)", in: ns)`.
3. On `MatchDetailView`'s hero `SoftRing`: `.matchedGeometryEffect(id: "ring-\(match.id)", in: ns)`.
4. Wrap the `NavigationLink` destination with the namespace so the effect spans push.
5. Test: tap a match card → ring should morph smoothly from card position to detail hero center.
6. If `matchedGeometryEffect` proves unreliable across NavigationStack push, fall back to a `.scale(1.1) + .opacity + .blur(4)` transition on the ring with a matched `.spring` timing.

### 1.4 Haptic Feedback (exists — audit & extend)

| Trigger | Haptic Style | Source |
|---------|-------------|--------|
| Tab switch | `UIImpactFeedbackGenerator(.light)` | spec §8, item 10 |
| Card/button press | `UIImpactFeedbackGenerator(.light)` | spec §8, item 8 |
| Segmented control switch | `UIImpactFeedbackGenerator(.light)` | spec §8 |
| "Spot on" result open | `UINotificationFeedbackGenerator(.success)` | spec §9 |

**Current state:**
- Tab switch: ✅ `RootView` line 63
- Segmented control: ✅ `MatchesView` lines 91, 95
- Card press: ✅ via `PressScale()` button style on NavigationLinks
- Spot-on success: ❌ Missing

**Action required:**
1. Add `UINotificationFeedbackGenerator(style: .success).notificationOccurred(.success)` when opening a match detail where `match.myPick.result?.outcome == "exact"`.
2. Audit all `PressScale()` usages — confirm every tappable card/button uses it.
3. Add haptic to `InkButton` action (currently relies on `PressScale` only — add explicit light impact in the action closure).

### 1.5 Press-Scale Audit

| Element | PressScale? | Status |
|---------|-------------|--------|
| InkButton | ✅ via `ButtonStyle(PressScale())` | Already wired |
| Today spotlight NavigationLink | ✅ `.buttonStyle(PressScale())` | Already wired |
| Today other-picks NavigationLink | ✅ `.buttonStyle(PressScale())` | Already wired |
| Matches match cards NavigationLink | ✅ `.buttonStyle(PressScale())` | Already wired |
| Tab bar buttons | ❌ `.buttonStyle(.plain)` | Needs PressScale |
| Segmented control buttons | ❌ `.buttonStyle(.plain)` | Needs PressScale |
| Table row taps (ScoutCard sheet) | Check if present | Audit needed |

**Action required:** Add `PressScale()` to tab bar buttons and segmented control buttons. Audit table row interactions.

### 1.6 Ring & Bar Draw Animations (exists — verify)

| Component | Animation | Delay | Source |
|-----------|-----------|-------|--------|
| SoftRing | `.spring(response: 1.0, damping: 0.9)` | 0.25s | spec §5.6 |
| StrengthBar | `.easeOut(0.8)` | 0.2s | spec §5.7 |
| GapRail | `.spring(response: 1.0, damping: 0.9)` | 0.3s | spec §5.8 |
| Sparkline | No draw animation (instant) | — | spec §5.14 |

**Current state:** All components have draw animations with `@Environment(\.accessibilityReduceMotion)` checks.

**Action required:** Verify animations match spec parameters exactly. No changes expected.

### 1.7 Reduce Motion Handling (exists — verify)

Every animated component already checks `@Environment(\.accessibilityReduceMotion)` and snaps to final state.

| Component | Reduce Motion Behavior | Status |
|-----------|----------------------|--------|
| IridescentGlow | `TimelineView(paused: reduceMotion)` | ✅ |
| GenerativeAppear | `shown = true` immediately | ✅ |
| SoftRing | `animated = v` immediately | ✅ |
| StrengthBar | `shown = true` immediately | ✅ |
| GapRail | `p = frac` immediately | ✅ |
| GeneratedStatus | `pulse = true` immediately | ✅ |
| ScoutCard trait bars | `shown = true` immediately | ✅ |

**Action required:** Verify in simulator with Reduce Motion enabled. Confirm gradient pauses, all animations snap, no visual glitches.

---

## 2. Accessibility Specifications

### 2.1 VoiceOver Labels

Every ring, bar, and interactive element needs a plain-language accessibility label. No jargon, no raw numbers — words only.

| Component | accessibilityLabel | accessibilityValue | accessibilityHint |
|-----------|-------------------|-------------------|-------------------|
| SoftRing (match) | "Pick: \(score)" | "\(tierLabel), \(chanceText)" | "Double-tap for match details" |
| SoftRing (detail hero) | "Your pick: \(score)" | "\(tierLabel), \(chanceText)" | None |
| StrengthBar | "\(homeCode) vs \(awayCode)" | "\(strengthWords)" | None |
| GapRail | "Your standing" | "\(mine) points, \(deficit) behind \(leaderName)" | None |
| MovementArrow | "Position change" | "Up \(abs(move))" / "Down \(abs(move))" / "No change" | None |
| MatchRowCard (upcoming) | "\(home) vs \(away)" | "Kickoff \(countdown), \(tierLabel)" | "Double-tap for match details" |
| MatchRowCard (final) | "\(home) \(homeScore) – \(away) \(awayScore)" | "\(outcomeLabel), \(points) points" | "Double-tap for match details" |
| SoftPill (outcome) | None needed — text is readable | — | — |
| TeamBadge | "\(teamName)" | None | None |
| TableView row | "Rank \(rank), \(name)" | "\(points) points, \(movement)" | "Double-tap for scouting report" (if not me) |
| Sparkline | "Points history" | "\(values.count) games" | None |
| GeneratedStatus | "Generation status" | "Generated \(relativeTime)" / "Generating" | None |

**Action required — Plan 08-02:**

1. Add `.accessibilityLabel()` and `.accessibilityValue()` to `SoftRing`, `StrengthBar`, `GapRail`, `MovementArrow`, `MatchRowCard`, `TeamBadge`, `Sparkline`, `GeneratedStatus`.
2. Use `Format` helpers for all values — no raw numbers.
3. Group `MatchRowCard` content with `.accessibilityElement(children: .combine)` for a single coherent VoiceOver readout.
4. Group `TableView` rows similarly.
5. Ensure `NavigationLink` destinations are announced with `.accessibilityHint`.

### 2.2 Color Contrast (verify AA)

| Pair | FG | BG | Ratio (approx) | Passes AA? |
|------|----|----|----------------|------------|
| Body text on canvas | `#2B2B2E` | `#FCFCFE` | ~15.5:1 | ✅ |
| Dim text on canvas | `#9A9AA1` | `#FCFCFE` | ~3.5:1 | ⚠️ Non-essential only |
| Mute text on canvas | `#BFC0C6` | `#FCFCFE` | ~2.2:1 | ❌ Decorative only |
| posText on posBG | `#1F7A52` | `#DDF3E7` | ~5.2:1 | ✅ |
| warnText on warnBG | `#9A6512` | `#FBEBD3` | ~4.1:1 | ✅ |
| negText on negBG | `#B5483A` | `#FBE3E0` | ~4.5:1 | ✅ |
| actText on actBG | `#5B4FC0` | `#E7E6FB` | ~5.0:1 | ✅ |
| White on ink | `#FFFFFF` | `#161618` | ~16.5:1 | ✅ |

**Rules:**
- `Theme.textMute` — use ONLY for decorative/dead elements (orbs, dividers). Never for essential content.
- `Theme.textDim` — acceptable for supplementary info (captions, meta). Not for primary content.
- All state pill pairs (pos/warn/neg/act) pass AA at normal text sizes.

**Action required:** Audit all views. If `textMute` is used for any essential information, swap to `textDim` minimum.

### 2.3 Touch Targets

| Element | Minimum Size | Current | Action |
|---------|-------------|---------|--------|
| InkButton | 44pt height | 46pt (13+13+20 padding) | ✅ OK |
| Tab bar button | 44pt | 56pt container | ✅ OK |
| Segmented control | 44pt | ~36pt ⚠️ | Increase padding |
| SoftPill (if tappable) | 44pt | ~26pt | Wrap in 44pt hit area |
| NavigationLink cards | 44pt | Variable | ✅ OK (cards are large) |
| TeamBadge | 44pt | 32–42pt | Use 42pt minimum |

**Action required:**
1. Increase segmented control vertical padding to ensure ≥ 44pt tap area.
2. If any `SoftPill` is interactive (e.g., filter chips), ensure `.contentShape(Rectangle())` with 44pt min frame.
3. Confirm `TeamBadge` minimum size is 42pt (already at spec minimum).

---

## 3. State Specifications

### 3.1 Loading State

**Pattern:** Light canvas + breathing glow + soft skeleton or ProgressView.

| Screen | Current Loading | Improve? |
|--------|----------------|----------|
| Today | `ProgressView()` + "Loading your briefing…" | Add skeleton shimmer |
| Matches | `ProgressView()` + "Loading your matches…" | Add skeleton shimmer |
| Table | Check current state | Standardize |
| Insights | `ProgressView()` + "Loading insights…" | Add skeleton shimmer |
| MatchDetail | No loading (pushed with data) | N/A |

**Spec (§10):** "Light canvas + breathing glow + a soft skeleton."

**Action required — Plan 08-02:**

1. Create a `SkeletonCard` component: a `FrostCard` with 3–4 `RoundedRectangle` placeholders in `Theme.track` with a subtle shimmer animation (left-to-right gradient sweep, respects Reduce Motion).
2. Replace bare `ProgressView()` loading states with skeleton layout matching the screen's structure.
3. Keep `IridescentGlow` visible during loading (already present).

### 3.2 Empty States

| Screen | Condition | Empty State Content | Icon |
|--------|-----------|-------------------|------|
| Today | No upcoming matches | "No matches today" + "Next up soon" | `calendar` |
| Today | No matches at all | "No matches scheduled" + "Check back later" | `calendar.badge.clock` |
| Matches (Upcoming) | No upcoming | "All caught up." + "Next matchday soon." | `checkmark.circle` |
| Matches (Results) | No results | "No results yet — first picks score after kickoff." | `clock` |
| Table | No data | "No standings yet" + "League updates after matchday 1" | `trophy` |
| Insights | No scouting | "No scouting reports yet" | `chart.bar` |
| MatchDetail | N/A (always has data) | N/A | N/A |

**Current state:**
- Today: ✅ Has `emptyStateCard` with calendar icon + "No matches today" / "Next up soon"
- Matches: ✅ Has `emptyState` with contextual copy
- Table: ⚠️ Check — may not have empty state
- Insights: ⚠️ Check — may not have empty state

**Spec copy (§10):** "Friendly one-liners with a soft SF Symbol in `textMute`."

**Action required:**
1. Verify `TableView` has an empty state for no data.
2. Verify `InsightsView` has an empty state for no scouting data.
3. All empty states use the pattern: `FrostCard` → icon (32pt, `textMute`) → title (`.headlineX`, `text`) → subtitle (`.bodyX`, `textDim`).
4. Center content vertically with `.padding(.vertical, Theme.s8)`.

### 3.3 Error States

| Condition | Behavior | Copy |
|-----------|----------|------|
| Remote fetch fails, bundled exists | Show bundled silently | Optional: "Offline — showing saved data" pill under GeneratedStatus |
| Hard failure (no data) | Show `ContentUnavailableView` | "Couldn't load your league" + Retry InkButton |
| Decode error | Show hard failure | "Something went wrong" + Retry InkButton |

**Spec (§10):** "Never block if any data exists."

**Action required — Plan 08-02:**

1. In `AppStore`, distinguish between `.loaded(Feed)` (from bundled) and `.loadedLive(Feed)` (from network). When network fails but bundled succeeds, set a flag `isOffline: Bool`.
2. In `GeneratedStatus`, when `isOffline`, show a tiny "offline" `SoftPill` in `warnBG`/`warnText` next to the spark dot.
3. For hard failure (`.failed`), show a full-screen state:
   ```
   ZStack {
       Theme.bg + IridescentGlow(intensity: 0.2)
       VStack(spacing: Theme.s4) {
           Image(systemName: "wifi.slash")
               .font(.system(size: 48))
               .foregroundStyle(Theme.textMute)
           Text("Couldn't load your league")
               .font(.titleX)
               .foregroundStyle(Theme.text)
           Text("Check your connection and try again.")
               .font(.bodyX)
               .foregroundStyle(Theme.textDim)
           InkButton(title: "Retry") { Task { await store.load() } }
               .frame(maxWidth: 200)
       }
   }
   ```
4. Apply `.generativeAppear(0)` to the error state for graceful entrance.

### 3.4 State Transitions

| From | To | Animation |
|------|----|-----------|
| Loading → Loaded | Content assembles | `.generativeAppear` stagger |
| Loaded → Refreshing | Status flips to "Generating…" | Crossfade |
| Refreshing → Loaded | Assembly replays | `.id(store.generation)` remount |
| Any → Error | Error state appears | `.generativeAppear(0)` |
| Error → Retry → Loading | Loading state returns | Crossfade |

**Action required:** Ensure `AppStore.phase` transitions drive correct UI states. No additional animation code needed — existing patterns handle this.

---

## 4. No-Jargon Audit Checklist

The hard rule: **No raw probability, "%", `composite_score`, or `expected_points` appears as text anywhere.**

### 4.1 Forbidden Patterns (grep audit)

Run across all `.swift` files in `EDGE/Sources/`:

| Pattern | Context | Allowed? |
|---------|---------|----------|
| `%` as text | Any `Text()` literal | ❌ Forbidden |
| `probability` | Any user-visible string | ❌ Forbidden |
| `composite_score` | Any user-visible string | ❌ Forbidden |
| `expected_points` / `expectedPoints` | As text label | ❌ Forbidden |
| `expectedPoints` | As bar length parameter | ✅ OK (internal) |
| `p=` or `p_` | Any user-visible string | ❌ Forbidden |
| Raw decimal like `0.74` | As text | ❌ Forbidden |
| `0.74` as odds | Internal model field | ✅ OK (never shown) |

### 4.2 Allowed Numeric Displays

| What | How Shown | Example |
|------|----------|---------|
| Scoreline | Text, monospacedDigit | `1:0` |
| Points | Text with `+` prefix | `+4` |
| Rank | Text with `#` prefix | `#8` |
| Gap | Worded | `6 points behind Alex` |
| Exact chance | Worded | `1 in 7` |
| Friend count | Worded | `1 of 8 friends` |
| expectedPoints | Bar length only | Thin iridescent bar, no number |
| Odds (home/draw/away) | Bar segments only | StrengthBar, no percentages |
| avgPoints | Text (it's already human) | `1.5 avg per game` |

### 4.3 Audit Targets

| File | What to Check | Status |
|------|--------------|--------|
| `TodayView.swift` | No raw % in greeting, standing, plan, spotlight | Audit |
| `MatchesView.swift` | No raw % in match cards, segmented content | Audit |
| `MatchDetailView.swift` | No raw % in hero, why, matchup, room, alternates | Audit |
| `TableView.swift` | No raw % in standings rows | Audit |
| `InsightsView.swift` | No raw % in form metrics, sparkline | Audit |
| `ScoutCard.swift` | No raw % in scouting blurbs, traits | Audit |
| `MatchRowCard.swift` | No raw % in upcoming/final cards | Audit |
| `Format.swift` | All helpers return words, not numbers | Audit |

**Action required — Plan 08-02:**

1. `grep -rn "Text.*%" EDGE/Sources/` — flag any percentage literals.
2. `grep -rn "expected_points\|composite_score\|probability" EDGE/Sources/` — flag any jargon.
3. `grep -rn "Text.*0\\.[0-9]" EDGE/Sources/` — flag raw decimals in Text() contexts.
4. For each flag: replace with worded equivalent using `Format` helpers.
5. Verify `Format.swift` — `chanceText(oneIn:)` returns "1 in N", not "N%". ✅ Already correct.
6. Verify `Format.swift` — `strengthWords(_:)` returns words, not numbers. ✅ Already correct.

---

## 5. Acceptance Criteria

All of the following must be TRUE for Phase 8 to be complete:

### Motion (MOTION-01)

- [ ] Match card → detail **ring morphs** via `matchedGeometryEffect` (or documented fallback)
- [ ] Rings draw, bars/rails fill, cards stagger per spec parameters
- [ ] Tab-switch haptic fires (`.light`)
- [ ] Card-press haptic fires (via `PressScale`)
- [ ] Segmented-control haptic fires (`.light`)
- [ ] "Spot on" result detail opens with success haptic (`.success`)
- [ ] Greeting builds **word-by-word** (each word its own `.generativeAppear`)
- [ ] Pull-to-refresh **replays** the full assembly
- [ ] All interactive elements have `PressScale` feedback

### Accessibility (A11Y-01, A11Y-02)

- [ ] **Reduce Motion** snaps every animation to final state and pauses gradient
- [ ] VoiceOver reads worded labels for rings ("Pick 1:0, coin-flip, lands about 1 in 7")
- [ ] VoiceOver reads worded labels for bars ("Portugal heavy favorite")
- [ ] VoiceOver reads worded labels for gap rail ("18 points, 6 behind Alex")
- [ ] VoiceOver reads worded labels for table rows ("Rank 8, Niko, 18 points, up 1")
- [ ] All text contrast passes WCAG AA (no `textMute` on essentials)
- [ ] All interactive elements have ≥ 44pt touch targets
- [ ] Segmented control has ≥ 44pt tap area

### States (A11Y-02)

- [ ] Loading shows skeleton layout with breathing gradient (not bare ProgressView)
- [ ] Today empty: "No matches today" with calendar icon
- [ ] Matches empty: contextual copy per segment
- [ ] Table empty: "No standings yet"
- [ ] Insights empty: "No scouting reports yet"
- [ ] Remote-fail-with-bundled: silent fallback + optional "offline" pill
- [ ] Hard failure: "Couldn't load your league" + Retry InkButton

### No-Jargon (LANG-01)

- [ ] Zero instances of `%` in any `Text()` view
- [ ] Zero instances of `probability`, `composite_score`, `expected_points` in user-visible strings
- [ ] Zero raw decimals (e.g., `0.74`) shown as text
- [ ] All numeric displays use approved formats (scoreline, +points, #rank, "1 in N", gap words)
- [ ] `Format.swift` helpers produce only worded output

### Visual Polish

- [ ] App looks **light & opalescent** on every screen
- [ ] Near-white canvas, frosted cards with white hairlines, soft bluish shadows
- [ ] One black CTA pill per context, only soft pastel state colors
- [ ] Gradient breathing is visible (Today strong, others faint)
- [ ] No visual glitches during Reduce Motion

---

## 6. File Inventory

### Files to Modify

| File | Changes |
|------|---------|
| `Features/Today/TodayView.swift` | Word-by-word greeting refactor, skeleton loading, VoiceOver labels |
| `Features/Matches/MatchesView.swift` | `@Namespace` for ring morph, skeleton loading, PressScale on seg buttons |
| `Features/Matches/MatchRowCard.swift` | `matchedGeometryEffect` on ring, VoiceOver labels |
| `Features/Matches/MatchDetailView.swift` | `matchedGeometryEffect` on ring, success haptic, VoiceOver labels |
| `Features/Table/TableView.swift` | Empty state, VoiceOver labels on rows |
| `Features/Insights/InsightsView.swift` | Empty state, skeleton loading, VoiceOver labels |
| `Features/Insights/ScoutCard.swift` | VoiceOver labels |
| `Features/Shell/RootView.swift` | PressScale on tab buttons |
| `DesignSystem/Components/SoftRing.swift` | VoiceOver label/value |
| `DesignSystem/Components/StrengthBar.swift` | VoiceOver label/value |
| `DesignSystem/Components/GapRail.swift` | VoiceOver label/value |
| `DesignSystem/Components/MovementArrow.swift` | VoiceOver label/value |
| `DesignSystem/Components/GeneratedStatus.swift` | VoiceOver label, offline pill support |
| `DesignSystem/Components/Sparkline.swift` | VoiceOver label |

### Files to Create

| File | Purpose |
|------|---------|
| `DesignSystem/Components/SkeletonCard.swift` | Shimmer placeholder for loading states |

---

## 7. Plan Split

### Plan 08-01: Motion Polish

**Scope:** Shared-element ring morph, haptics, word-build greeting, press-scale audit.

| Task | Detail |
|------|--------|
| Ring morph | `@Namespace` + `matchedGeometryEffect` on card → detail ring |
| Word-build greeting | Refactor `greetingWords()` for per-word `.generativeAppear` |
| Haptic audit | Add success haptic for "Spot on" results, verify all triggers |
| Press-scale audit | Add `PressScale` to tab buttons and segmented control |
| Ring/bar verify | Confirm animation parameters match spec §5.6–5.8 |

### Plan 08-02: Accessibility, States & No-Jargon

**Scope:** VoiceOver labels, Reduce Motion verify, empty/loading/error states, no-jargon audit, acceptance pass.

| Task | Detail |
|------|--------|
| VoiceOver | Add labels to all components and interactive elements |
| Reduce Motion | Verify in simulator, fix any gaps |
| Skeleton loading | Create `SkeletonCard`, replace bare ProgressViews |
| Empty states | Verify all screens have proper empty states |
| Error states | Implement hard-failure screen with Retry button |
| Offline pill | Add "offline" indicator in GeneratedStatus |
| No-jargon audit | Grep for forbidden patterns, fix any violations |
| Touch targets | Verify ≥ 44pt on all interactive elements |
| Contrast audit | Verify no `textMute` on essentials |
| Acceptance pass | Run through all acceptance criteria |

---

## Checker Sign-Off

- [ ] Motion: PASS
- [ ] Accessibility: PASS
- [ ] States: PASS
- [ ] No-Jargon: PASS
- [ ] Visual Polish: PASS

**Approval:** pending
