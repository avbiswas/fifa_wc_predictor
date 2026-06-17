# EDGE — iOS App Build Plan

> A bright, opalescent, self-assembling iOS companion for the KickTipp exploit engine.
> Working name: **EDGE**.
> Visual language is modelled on the **"agentic gen UI"** aesthetic: a soft, light, almost
> 3D-clay studio feel; a single **iridescent pastel gradient** that slowly breathes; **frosted
> glass** cards; **thin** typography; one **black pill** for primary actions; and motion where
> the interface **generates itself** — content materializes with a blur-to-focus stagger.
> **Scope decision:** apply this aesthetic + these animations to a **structured 4-tab dashboard**
> (no chat / no Ask bar). Keep it glanceable.
>
> This document is written so a low-level coding LLM (e.g. Haiku) can implement each section
> verbatim. **Build order is §14. Start there.**

---

## 0. TL;DR — what we are building

A 4-tab SwiftUI app (iOS 18+, light) that turns the engine's JSON into a glanceable, premium
dashboard that *assembles itself* on screen. It answers four questions instantly:

1. **Where do I stand?** (rank, gap to leader, the plan for tonight)
2. **What do I tip, and why — in plain words?** (per-match pick + 3 human reasons)
3. **What already happened?** (results + points I scored — soft green/red)
4. **How do I beat these specific people?** (scouting reports on each friend)

**Hard rules (design doctrine):**
- **No raw percentages, no "confidence 67%", no jargon.** Translate every number into a word, a
  soft-colored pill, a bar, or a ring. "1 in 7", "heavy favorite", "against the room" — never "p=0.146".
- **Understand at a glance.** Eyebrow label + one big thing + supporting chips. No card needs a paragraph.
- **Light & opalescent.** Near-white surfaces, one iridescent pastel gradient as the hero color
  moment, frosted-glass cards, **thin** type. Saturated color is rare; state colors are *soft*
  (pastel fills with a darker same-hue text). Primary actions are a single **black pill**.
- **It generates itself.** On open (and on pull-to-refresh) the screen assembles: elements fade
  up from a soft blur into focus, staggered top-to-bottom, while the gradient breathes. Rings and
  bars draw. This motion is the product's signature — treat it as a feature, not decoration.

---

## 1. The aesthetic (reference: glebich "agentic gen UI" — aesthetic & motion only)

Mood words: **light, opalescent, calm, weightless, expensive, alive.**

The reference is a soft 3D studio (matte off-white, fluted columns, floating sculptural blobs,
reflective podium) holding a phone whose UI is **bright and milky**, with a central **iridescent
mesh gradient** (periwinkle → lilac → blush → peach → mint), **frosted glass** cards, thin gray
typography, and a black CTA pill. The interface **builds itself** in response to the user — a
greeting fades in, a card materializes with the details streaming in, a timeline draws.

We bring the *UI aesthetic and the motion* into the app. We do **not** render a 3D scene inside
the app (that's marketing) — instead we evoke it with: a white canvas, the breathing iridescent
glow, frosted depth, soft diffuse shadows, and the generative assembly animation.

Signature elements we build:
- **Iridescent breathing gradient** (`IridescentGlow`) — the soul; soft pastel blobs that drift,
  scale, and rotate forever. Strong on Today, faint at the top of other tabs.
- **Generative assembly** (`.generativeAppear(index:)`) — every element enters with
  opacity + rise + scale + **blur-to-focus**, staggered. Replays on refresh.
- **Frosted glass cards** (`FrostCard`) — translucent white + blur + 1px white hairline + soft
  bluish shadow, 26pt radius.
- **Soft rings** that draw on appear; **pastel segmented bars**; **timeline rails** that fill.
- **Soft state pills** (mint / peach / rose / periwinkle) — never neon.
- **Black pill** (`InkButton`) for the one primary action per context.
- **A "generated just now" status** with a pulsing spark dot (the agentic motif, kept as the
  refresh affordance).

---

## 2. Tech stack & architecture

- **Language/UI:** Swift 5.9+, SwiftUI. **Target: iOS 18.0+** (for `MeshGradient`; a blurred-blob
  fallback is given so iOS 17 works too). **Light appearance** — set
  `.preferredColorScheme(.light)` at the root (the aesthetic is light; do not build dark mode).
- **No third-party packages.** Pure SwiftUI. Icons = SF Symbols. Rings/bars/gradients hand-rolled
  with `Shape`/`Canvas`/`TimelineView` (do NOT use Swift Charts).
- **Fonts:** system **SF Pro Display** for big/greeting text at **light** weight; **SF Pro Text**
  for body/labels. Numbers use `.monospacedDigit()`.
- **State:** `ObservableObject` + `@Published` + `@StateObject`/`@EnvironmentObject`. One store: `AppStore`.
- **Data:** a single `app_feed.json` (schema §4). Ships **bundled** (`SampleFeed.json`) so it runs
  fully offline; optionally fetches a fresh copy from a URL. `Codable`.
- **Navigation:** `TabView` (4 tabs) with a **custom floating frosted tab bar**; match detail is
  pushed inside a `NavigationStack` per tab.
- **Pattern:** MVVM-light. Models = `Codable` structs. Views are pure functions of state.

### Project file structure (create exactly this)

```
EDGE/
├─ EDGEApp.swift                      // @main, injects AppStore, .preferredColorScheme(.light)
├─ Resources/
│  └─ SampleFeed.json                 // bundled fixture (full sample in §18)
├─ Core/
│  ├─ AppStore.swift                  // ObservableObject: load + decode + state + generation id
│  ├─ Models.swift                    // all Codable structs (§4.2)
│  └─ Format.swift                    // human-language + visual mapping helpers (§6)
├─ DesignSystem/
│  ├─ Theme.swift                     // light tokens (§5.1)
│  ├─ Typography.swift                // light font scale (§5.2)
│  ├─ Color+Hex.swift                 // Color(hex:)
│  └─ Components/
│     ├─ IridescentGlow.swift         // breathing pastel gradient (§5.3)  ★
│     ├─ GenerativeAppear.swift       // blur-to-focus stagger modifier (§5.4)  ★
│     ├─ FrostCard.swift              // frosted glass card (§5.5)
│     ├─ SoftRing.swift               // drawing ring (§5.6)
│     ├─ StrengthBar.swift            // pastel 1X2 bar (§5.7)
│     ├─ GapRail.swift                // 18—•—24 timeline rail (§5.8)
│     ├─ SoftPill.swift              // state chips (§5.9)
│     ├─ InkButton.swift              // black primary pill (§5.10)
│     ├─ MovementArrow.swift          // ▲▼ (§5.11)
│     ├─ TeamBadge.swift              // circular monogram (§5.12)
│     ├─ GeneratedStatus.swift        // spark dot + "generated just now" (§5.13)
│     ├─ Sparkline.swift              // tiny bars (§5.14)
│     └─ Eyebrow.swift                // small label (§5.15)
├─ Features/
│  ├─ Shell/RootView.swift            // TabView + floating frosted bar (§7.1)
│  ├─ Today/TodayView.swift           // §7.2
│  ├─ Matches/MatchesView.swift       // §7.3
│  ├─ Matches/MatchRowCard.swift
│  ├─ Matches/MatchDetailView.swift   // §7.4
│  ├─ Table/TableView.swift           // §7.5
│  ├─ Insights/InsightsView.swift     // §7.6
│  └─ Insights/ScoutCard.swift        // §7.7
└─ Assets.xcassets                    // app icon only; colors live in Theme.swift
```

---

## 3. Data flow

```
existing Python reports                 (new, spec only — §16, do NOT build in this task)
reports/leverage_tip_sheet.json  ─┐     scripts/build_app_feed.py
data/kicktipp/rounds.local.json  ─┼──►  merges + TRANSLATES to human strings  ──►  app_feed.json
reports/kicktipp_optimizer_       ─┘                                                    │
   backtest.json                                                                        ▼
                                            iOS app: AppStore.load()  ◄── bundled SampleFeed.json (offline)
                                                                      ◄── optional GET <feedURL> (fresh)
```

The feed is **pre-translated**: Python produces human-ready strings (`tierLabel`, `reasons[]`,
`favoriteStrength`, scouting `blurb`). The iOS app owns only **visual mapping** (which soft color,
ring fill, arrow). §6 gives iOS-side fallbacks. **For THIS task the app reads the bundled
`SampleFeed.json` (§18) and must run + look finished with zero backend.**

---

## 4. The data contract — `app_feed.json`

### 4.1 Schema (annotated)

```jsonc
{
  "updatedAt": "2026-06-17T06:52:11Z",
  "season": "World Cup 2026",
  "me": {
    "name": "Niko", "rank": 8, "points": 18, "playersCount": 9,
    "leaderName": "Alex", "leaderPoints": 24, "deficit": 6, "tiebreaker": "matchday wins"
  },
  "strategy": {
    "mode": "controlled_attack",
    "headline": "Chasing the lead",
    "subtitle": "Calculated risks to close a 6-point gap",
    "drawPlan": { "planned": 3, "reason": "The field forgets draws" }
  },
  "form": {
    "matches": 16, "points": 24, "avgPoints": 1.5, "exact": 4, "scored": 8, "blanked": 8,
    "recentPoints": [2,0,4,2,0,3,2,0,4,2,2,0,3,0,0,0]
  },
  "table": [
    { "rank":1, "name":"Alex", "points":24, "move":3, "isMe":false, "isLeader":true },
    { "rank":8, "name":"Niko", "points":18, "move":1, "isMe":true,  "isLeader":false }
    // move: positions gained(+)/lost(-) since last matchday; 0 = none
  ],
  "matches": [
    {
      "id":"760435", "kickoff":"2026-06-17T17:00:00Z", "matchday":3, "status":"upcoming",
      "home": { "name":"Portugal", "code":"POR", "rank":55 },
      "away": { "name":"Congo DR", "code":"COD", "rank":5 },
      "result": null,                                   // when final: { "home":2, "away":0 }
      "myPick": {
        "score":"1:0",
        "tier":"thin_edge",                             // strong | normal | thin_edge | chaos
        "tierLabel":"Coin-flip",
        "leverage":"contrarian",                        // crowd | contrarian
        "vsLeader":"different",                         // same | different
        "exactChanceOneIn":7,
        "expectedPoints":1.87,                          // bar length only, never shown as text
        "reasons":[
          "Portugal are clear favorites tonight",
          "1:0 is the best-value exact score here",
          "Most friends go 2:0 or 2:1 — this buys you separation"
        ],
        "result": null                                  // when final: { "points":4, "outcome":"exact" }
      },
      "odds": { "home":0.74, "draw":0.20, "away":0.06 },
      "favorite": "Portugal",
      "favoriteStrength": "heavy",                       // heavy | clear | slight | even
      "upset": { "isUpset": false, "text": "Form favors Portugal" },
      "fieldExposure": { "friendsTotal": 8, "onSamePick": 1, "leaderPick": "2:1" },
      "alternates": [
        { "score":"1:0", "expectedPoints":1.87, "note":"Best value" },
        { "score":"2:0", "expectedPoints":1.87, "note":"Crowd pick" },
        { "score":"1:1", "expectedPoints":0.57, "note":"Draw swing" }
      ],
      "news": [ "Portugal expected to rotate two starters" ]
    }
  ],
  "scouting": [
    {
      "name":"UnsPascha", "rank":2, "points":23, "isLeader":false,
      "tag":"Chaos merchant",
      "blurb":"Loves big scorelines and wild results. Rarely picks the draws you can copy.",
      "traits":[
        { "label":"Goals","value":"High","level":3 },
        { "label":"Draws","value":"Rare","level":1 },
        { "label":"Upsets","value":"Often","level":3 }
      ]
    }
  ]
}
```

### 4.2 Swift models (`Core/Models.swift`) — implement verbatim

```swift
import Foundation

struct Feed: Codable {
    let updatedAt: Date
    let season: String
    let me: Me
    let strategy: Strategy
    let form: Form
    let table: [TableRow]
    let matches: [Match]
    let scouting: [ScoutReport]
}
struct Me: Codable {
    let name: String; let rank: Int; let points: Int; let playersCount: Int
    let leaderName: String; let leaderPoints: Int; let deficit: Int; let tiebreaker: String
}
struct Strategy: Codable {
    let mode: String; let headline: String; let subtitle: String; let drawPlan: DrawPlan
    struct DrawPlan: Codable { let planned: Int; let reason: String }
}
struct Form: Codable {
    let matches: Int; let points: Int; let avgPoints: Double
    let exact: Int; let scored: Int; let blanked: Int; let recentPoints: [Int]
}
struct TableRow: Codable, Identifiable {
    var id: String { name }
    let rank: Int; let name: String; let points: Int; let move: Int; let isMe: Bool; let isLeader: Bool
}
struct Match: Codable, Identifiable {
    let id: String; let kickoff: Date; let matchday: Int; let status: String
    let home: Team; let away: Team; let result: ScoreResult?
    let myPick: Pick; let odds: Odds; let favorite: String; let favoriteStrength: String
    let upset: Upset; let fieldExposure: FieldExposure; let alternates: [Alternate]; let news: [String]
    struct Team: Codable { let name: String; let code: String; let rank: Int }
    struct ScoreResult: Codable { let home: Int; let away: Int }
    struct Odds: Codable { let home: Double; let draw: Double; let away: Double }
    struct Upset: Codable { let isUpset: Bool; let text: String }
    struct FieldExposure: Codable { let friendsTotal: Int; let onSamePick: Int; let leaderPick: String? }
    struct Alternate: Codable, Identifiable { var id: String { score }
        let score: String; let expectedPoints: Double; let note: String }
}
struct Pick: Codable {
    let score: String; let tier: String; let tierLabel: String
    let leverage: String; let vsLeader: String; let exactChanceOneIn: Int
    let expectedPoints: Double; let reasons: [String]; let result: PickResult?
    struct PickResult: Codable { let points: Int; let outcome: String } // exact|goaldiff|tendency|draw|miss
}
struct ScoutReport: Codable, Identifiable {
    var id: String { name }
    let name: String; let rank: Int; let points: Int; let isLeader: Bool
    let tag: String; let blurb: String; let traits: [Trait]
    struct Trait: Codable, Identifiable { var id: String { label }
        let label: String; let value: String; let level: Int }
}
```

### 4.3 Loading + refresh trigger (`Core/AppStore.swift`)

`generation` increments on each (re)load; views key their assembly animation on it so a refresh
**replays the generative entrance** (see §8).

```swift
import SwiftUI

@MainActor
final class AppStore: ObservableObject {
    enum Phase { case loading, loaded(Feed), failed(String) }
    @Published var phase: Phase = .loading
    @Published var generation: Int = 0          // bump to replay the assembly animation

    var feedURL: URL? = nil                      // set later for live data (§16)

    private static let decoder: JSONDecoder = {
        let d = JSONDecoder(); d.dateDecodingStrategy = .iso8601; return d
    }()

    func load() async {
        if let bundled = try? Self.loadBundled() { phase = .loaded(bundled) }
        generation += 1
        guard let url = feedURL else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            phase = .loaded(try Self.decoder.decode(Feed.self, from: data)); generation += 1
        } catch {
            if case .loaded = phase { return }
            phase = .failed(error.localizedDescription)
        }
    }
    func refresh() async { await load() }        // .refreshable hook → replays assembly

    static func loadBundled() throws -> Feed {
        guard let url = Bundle.main.url(forResource: "SampleFeed", withExtension: "json")
        else { throw NSError(domain: "EDGE", code: 1) }
        return try decoder.decode(Feed.self, from: Data(contentsOf: url))
    }
}
```

`EDGEApp.swift`:

```swift
import SwiftUI
@main
struct EDGEApp: App {
    @StateObject private var store = AppStore()
    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(store)
                .preferredColorScheme(.light)
                .task { await store.load() }
        }
    }
}
```

---

## 5. Design system (light / opalescent)

### 5.1 Theme tokens (`DesignSystem/Theme.swift`)

```swift
import SwiftUI
enum Theme {
    // Surfaces
    static let bg       = Color(hex: "FCFCFE")          // app canvas (near white)
    static let card     = Color.white.opacity(0.55)     // frosted fill (over material)
    static let hairline = Color.white.opacity(0.85)     // 1px top-highlight border
    static let track    = Color(hex: "ECECF1")          // empty rail/ring track
    static let shadow   = Color(hex: "282A46")          // soft bluish shadow color (use ~0.10)

    // Text
    static let text     = Color(hex: "2B2B2E")
    static let textDim  = Color(hex: "9A9AA1")
    static let textMute = Color(hex: "BFC0C6")
    static let ink      = Color(hex: "161618")          // black CTA + strong text

    // Iridescent palette (the hero gradient)
    static let iridBlue  = Color(hex: "B9C9F2")
    static let iridLilac = Color(hex: "E7CDEE")
    static let iridBlush = Color(hex: "F6D4DC")
    static let iridPeach = Color(hex: "F8E7C8")
    static let iridMint  = Color(hex: "CBEBD9")
    static let spark     = Color(hex: "9B8CF0")         // the "generating" accent dot

    // Soft state pairs (pastel fill + darker same-hue text). Never neon.
    static let posBG = Color(hex: "DDF3E7"); static let posText = Color(hex: "1F7A52")  // good / win / up
    static let warnBG = Color(hex: "FBEBD3"); static let warnText = Color(hex: "9A6512") // coin-flip
    static let negBG = Color(hex: "FBE3E0"); static let negText = Color(hex: "B5483A")   // loss / risk / down
    static let actBG = Color(hex: "E7E6FB"); static let actText = Color(hex: "5B4FC0")   // active / contrarian

    // Spacing
    static let s1: CGFloat = 4;  static let s2: CGFloat = 8;  static let s3: CGFloat = 12
    static let s4: CGFloat = 16; static let s5: CGFloat = 20; static let s6: CGFloat = 24
    static let s8: CGFloat = 32; static let s10: CGFloat = 40
    // Radii
    static let rSm: CGFloat = 14; static let rMd: CGFloat = 20; static let rLg: CGFloat = 26; static let rXl: CGFloat = 34
}
```

`DesignSystem/Color+Hex.swift`:

```swift
import SwiftUI
extension Color {
    init(hex: String) {
        let s = Scanner(string: hex.trimmingCharacters(in: .alphanumerics.inverted))
        var v: UInt64 = 0; s.scanHexInt64(&v)
        self = Color(red: Double((v & 0xFF0000) >> 16)/255,
                     green: Double((v & 0x00FF00) >> 8)/255,
                     blue: Double(v & 0x0000FF)/255)
    }
}
```

### 5.2 Typography (`DesignSystem/Typography.swift`)

**Thin and airy.** The reference greeting is a light weight; lean into it.

| Token       | Font                              | Size | Weight  | Use                                  |
|-------------|-----------------------------------|------|---------|--------------------------------------|
| `.greeting` | SF Pro Display                    | 30   | light   | "Good evening, Niko"                 |
| `.hero`     | SF Pro Display                    | 48   | light   | the one giant number (#8 / rank)     |
| `.display`  | SF Pro Display (rounded ok)       | 26   | medium  | scorelines, ring center              |
| `.title`    | SF Pro Text                       | 20   | medium  | screen titles                        |
| `.headline` | SF Pro Text                       | 16   | medium  | team names, friend names, card title |
| `.body`     | SF Pro Text                       | 15   | regular | reasons, blurbs                      |
| `.callout`  | SF Pro Text                       | 13   | regular | meta, captions                       |
| `.eyebrow`  | SF Pro Text                       | 11   | medium  | small labels (slight tracking)       |

```swift
import SwiftUI
extension Font {
    static let greeting  = Font.system(size: 30, weight: .light,   design: .default)
    static let heroLight = Font.system(size: 48, weight: .light,   design: .default)
    static let displayX  = Font.system(size: 26, weight: .medium,  design: .default)
    static let titleX    = Font.system(size: 20, weight: .medium)
    static let headlineX = Font.system(size: 16, weight: .medium)
    static let bodyX     = Font.system(size: 15, weight: .regular)
    static let calloutX  = Font.system(size: 13, weight: .regular)
    static let eyebrowX  = Font.system(size: 11, weight: .medium)
}
struct Eyebrow: View {            // sentence-case small label, gentle tracking
    let text: String
    var body: some View { Text(text).font(.eyebrowX).tracking(0.6).foregroundStyle(Theme.textDim) }
}
```

### 5.3 ★ Iridescent breathing gradient (`Components/IridescentGlow.swift`)

The soul. Soft pastel blobs that drift, scale, and rotate forever, driven by `TimelineView`.
Place behind content (full on Today, faint at the top on other tabs). iOS 18 `MeshGradient`
alternative noted after.

```swift
import SwiftUI
struct IridescentGlow: View {
    var intensity: Double = 1.0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0/30.0, paused: reduceMotion)) { tl in
            let t = tl.date.timeIntervalSinceReferenceDate
            ZStack {
                blob(Theme.iridBlue,  baseX: -70, baseY: -10, t: t, sx: 0.21, sy: 0.17)
                blob(Theme.iridLilac, baseX:  70, baseY: -30, t: t, sx: 0.16, sy: 0.23)
                blob(Theme.iridBlush, baseX: -30, baseY:  40, t: t, sx: 0.13, sy: 0.20)
                blob(Theme.iridPeach, baseX:  60, baseY:  40, t: t, sx: 0.24, sy: 0.14)
                blob(Theme.iridMint,  baseX:   0, baseY:   0, t: t, sx: 0.18, sy: 0.16)
            }
            .blur(radius: 44)
            .opacity(0.85 * intensity)
        }
        .allowsHitTesting(false)
    }
    private func blob(_ c: Color, baseX: CGFloat, baseY: CGFloat, t: Double, sx: Double, sy: Double) -> some View {
        let dx = CGFloat(sin(t * sx)) * 22, dy = CGFloat(cos(t * sy)) * 18
        let s  = 1 + 0.12 * sin(t * (sx + 0.05))
        return Circle().fill(c).frame(width: 170, height: 170)
            .scaleEffect(s).offset(x: baseX + dx, y: baseY + dy)
    }
}
// iOS 18+ alternative: a MeshGradient with white at the corners and irid* colors in the
// center, wrapped in the same TimelineView to nudge the middle control point. Either is fine;
// the blurred-blob version above is the canonical, broadly-compatible one.
```

### 5.4 ★ Generative assembly (`Components/GenerativeAppear.swift`)

THE animation. Each element enters with **blur-to-focus** + rise + scale + fade, staggered by
`index`. Respects Reduce Motion. Re-keying the parent (via `AppStore.generation`) replays it.

```swift
import SwiftUI
struct GenerativeAppear: ViewModifier {
    let index: Int
    var base: Double = 0.12
    var step: Double = 0.085
    @State private var shown = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    func body(content: Content) -> some View {
        content
            .opacity(shown ? 1 : 0)
            .blur(radius: shown ? 0 : 9)
            .scaleEffect(shown ? 1 : 0.97, anchor: .center)
            .offset(y: shown ? 0 : 16)
            .onAppear {
                if reduceMotion { shown = true; return }
                withAnimation(.spring(response: 0.75, dampingFraction: 0.82)
                    .delay(base + Double(index) * step)) { shown = true }
            }
    }
}
extension View {
    /// Apply down a screen with an incrementing index: .generativeAppear(0), .generativeAppear(1)…
    func generativeAppear(_ index: Int) -> some View { modifier(GenerativeAppear(index: index)) }
}
```

**Replay-on-refresh pattern** (use on each screen's content stack):

```swift
ScrollView { content.id(store.generation) }     // new id → views remount → assembly replays
    .refreshable { await store.refresh() }
```

### 5.5 Frosted glass card (`Components/FrostCard.swift`)

```swift
import SwiftUI
struct FrostCard<Content: View>: View {
    var padding: CGFloat = Theme.s4
    var radius: CGFloat = Theme.rLg
    @ViewBuilder var content: Content
    var body: some View {
        content.padding(padding).frame(maxWidth: .infinity, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(.ultraThinMaterial))
            .background(RoundedRectangle(cornerRadius: radius, style: .continuous).fill(Theme.card))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous)
                .strokeBorder(Theme.hairline, lineWidth: 1))
            .shadow(color: Theme.shadow.opacity(0.10), radius: 24, x: 0, y: 14)
    }
}
```

### 5.6 Soft ring (`Components/SoftRing.swift`)

Light track + a soft tier-colored arc that **draws** on appear (no harsh glow). Center = custom.

```swift
import SwiftUI
struct SoftRing<Center: View>: View {
    var value: Double                 // 0...1
    var color: Color
    var lineWidth: CGFloat = 8
    var size: CGFloat = 108
    @ViewBuilder var center: Center
    @State private var animated: Double = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        ZStack {
            Circle().stroke(Theme.track, lineWidth: lineWidth)
            Circle().trim(from: 0, to: animated)
                .stroke(color.opacity(0.9), style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .shadow(color: color.opacity(0.25), radius: 6)     // soft, not neon
            center
        }
        .frame(width: size, height: size)
        .onAppear {
            let v = max(0, min(1, value))
            if reduceMotion { animated = v; return }
            withAnimation(.spring(response: 1.0, dampingFraction: 0.9).delay(0.25)) { animated = v }
        }
    }
}
```

### 5.7 Strength bar (`Components/StrengthBar.swift`) — pastel 1X2

```swift
import SwiftUI
struct StrengthBar: View {
    let home: Double, draw: Double, away: Double
    let homeCode: String, awayCode: String
    @State private var shown = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        VStack(alignment: .leading, spacing: Theme.s2) {
            GeometryReader { geo in
                HStack(spacing: 3) {
                    seg(home, Color(hex: "9DBBA9"), geo.size.width)   // soft sage (home)
                    seg(draw, Theme.textMute,       geo.size.width)   // gray (draw)
                    seg(away, Color(hex: "A9C2E6"), geo.size.width)   // soft blue (away)
                }
            }.frame(height: 8)
            HStack { Text(homeCode); Spacer(); Text("draw"); Spacer(); Text(awayCode) }
                .font(.eyebrowX).foregroundStyle(Theme.textDim)
        }
        .onAppear {
            if reduceMotion { shown = true; return }
            withAnimation(.easeOut(duration: 0.8).delay(0.2)) { shown = true }
        }
    }
    private func seg(_ p: Double, _ c: Color, _ total: CGFloat) -> some View {
        Capsule().fill(c).frame(width: shown ? max(4, total * p) : 0)
    }
}
```

### 5.8 Gap rail (`Components/GapRail.swift`) — the "18 —•— 24" timeline

Mirrors the reference's flight timeline: a rail from you→leader with a soft marker that slides in.

```swift
import SwiftUI
struct GapRail: View {
    let mine: Int, leader: Int          // 18, 24
    @State private var p: CGFloat = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private var frac: CGFloat { leader <= 0 ? 0 : CGFloat(mine)/CGFloat(leader) }
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Theme.track).frame(height: 6)
                    Capsule().fill(LinearGradient(colors: [Theme.iridBlue, Theme.iridLilac],
                                   startPoint: .leading, endPoint: .trailing))
                        .frame(width: geo.size.width * p, height: 6)
                    Circle().fill(.white).frame(width: 14, height: 14)
                        .overlay(Circle().strokeBorder(Theme.spark, lineWidth: 2))
                        .shadow(color: Theme.shadow.opacity(0.18), radius: 3, y: 1)
                        .offset(x: geo.size.width * p - 7)
                }
            }.frame(height: 16)
            HStack {
                Text("\(mine) you").font(.calloutX).foregroundStyle(Theme.text)
                Spacer()
                Text("\(leader) \(/* leaderName passed in */ "leader")").font(.calloutX).foregroundStyle(Theme.textDim)
            }.monospacedDigit()
        }
        .onAppear {
            if reduceMotion { p = frac; return }
            withAnimation(.spring(response: 1.0, dampingFraction: 0.9).delay(0.3)) { p = frac }
        }
    }
}
```

### 5.9 Soft pill (`Components/SoftPill.swift`) — state chips

```swift
import SwiftUI
struct SoftPill: View {
    let text: String
    var bg: Color = Theme.actBG
    var fg: Color = Theme.actText
    var systemImage: String? = nil
    var body: some View {
        HStack(spacing: 5) {
            if let s = systemImage { Image(systemName: s).font(.system(size: 10, weight: .semibold)) }
            Text(text).font(.eyebrowX)
        }
        .foregroundStyle(fg)
        .padding(.horizontal, 9).padding(.vertical, 5)
        .background(Capsule().fill(bg))
    }
}
```

### 5.10 Ink button (`Components/InkButton.swift`) — the one black pill

```swift
import SwiftUI
struct InkButton: View {
    let title: String
    var systemImage: String = "arrow.right"
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Text(title).font(.headlineX).foregroundStyle(.white)
                Image(systemName: systemImage).font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Theme.ink)
                    .frame(width: 22, height: 22).background(Circle().fill(.white))
            }
            .frame(maxWidth: .infinity).padding(.vertical, 13)
            .background(Capsule().fill(Theme.ink))
        }
        .buttonStyle(PressScale())
    }
}
struct PressScale: ButtonStyle {        // subtle tactile press, reused everywhere
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: configuration.isPressed)
    }
}
```

### 5.11 Movement arrow (`Components/MovementArrow.swift`)

```swift
import SwiftUI
struct MovementArrow: View {
    let move: Int
    var body: some View {
        let (icon, color): (String, Color) =
            move > 0 ? ("arrow.up.right", Theme.posText) :
            move < 0 ? ("arrow.down.right", Theme.negText) : ("minus", Theme.textMute)
        return HStack(spacing: 2) {
            Image(systemName: icon).font(.system(size: 10, weight: .semibold))
            if move != 0 { Text("\(abs(move))").font(.eyebrowX).monospacedDigit() }
        }.foregroundStyle(color)
    }
}
```

### 5.12 Team badge (`Components/TeamBadge.swift`)

Asset-free circular monogram, frosted.

```swift
import SwiftUI
struct TeamBadge: View {
    let code: String
    var size: CGFloat = 42
    var body: some View {
        Text(code).font(.system(size: size * 0.28, weight: .semibold))
            .foregroundStyle(Theme.text)
            .frame(width: size, height: size)
            .background(Circle().fill(.ultraThinMaterial))
            .overlay(Circle().fill(Theme.card)).overlay(Circle().strokeBorder(Theme.hairline, lineWidth: 1))
    }
}
```

### 5.13 Generated status (`Components/GeneratedStatus.swift`) — the agentic motif

A pulsing spark dot + "Generated just now" / "Generating…". Sits at the top of Today; doubles as
the refresh affordance (pull down → `store.refresh()` → text flips to "Generating…" while the
assembly replays).

```swift
import SwiftUI
struct GeneratedStatus: View {
    let updatedAt: Date
    var generating: Bool = false
    @State private var pulse = false
    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(Theme.spark).frame(width: 7, height: 7)
                .scaleEffect(pulse ? 1.2 : 0.8).opacity(pulse ? 1 : 0.5)
                .onAppear { withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) { pulse = true } }
            Text(generating ? "Generating your briefing…" : "Generated \(Format.relativeUpdated(updatedAt))")
                .font(.calloutX).foregroundStyle(Theme.textDim)
        }
    }
}
```

### 5.14 Sparkline (`Components/Sparkline.swift`)

```swift
import SwiftUI
struct Sparkline: View {
    let values: [Int]
    private var maxV: Int { max(values.max() ?? 1, 1) }
    var body: some View {
        GeometryReader { geo in
            HStack(alignment: .bottom, spacing: 3) {
                ForEach(values.indices, id: \.self) { i in
                    RoundedRectangle(cornerRadius: 2)
                        .fill(values[i] == 0 ? Theme.track : Theme.iridLilac)
                        .frame(height: max(2, geo.size.height * CGFloat(values[i]) / CGFloat(maxV)))
                }
            }
        }.frame(height: 34)
    }
}
```

### 5.15 Eyebrow — defined in §5.2 (`Eyebrow`).

---

## 6. Human-language layer (`Core/Format.swift`) — anti-jargon, soft-state colors

```swift
import SwiftUI
enum Format {

    // Tier → soft pill style (label + fg + bg) and a ring color
    static func tierStyle(_ tier: String, label: String) -> (text: String, fg: Color, bg: Color) {
        switch tier {
        case "strong":    return (label.isEmpty ? "Bank it"   : label, Theme.posText,  Theme.posBG)
        case "normal":    return (label.isEmpty ? "Solid pick": label, Theme.posText,  Theme.posBG)
        case "thin_edge": return (label.isEmpty ? "Coin-flip" : label, Theme.warnText, Theme.warnBG)
        default:          return (label.isEmpty ? "Wild card" : label, Theme.negText,  Theme.negBG)
        }
    }
    static func tierRingColor(_ tier: String) -> Color {
        switch tier { case "strong","normal": return Theme.posText
                      case "thin_edge": return Theme.warnText
                      default: return Theme.negText }
    }

    static func strengthWords(_ key: String) -> String {
        switch key { case "heavy": return "Heavy favorite"; case "clear": return "Clear favorite"
                     case "slight": return "Slight edge"; default: return "Even game" }
    }
    static func leverageChip(_ l: String) -> (text: String, fg: Color, bg: Color, icon: String) {
        l == "contrarian" ? ("Against the room", Theme.actText, Theme.actBG, "arrow.triangle.branch")
                          : ("With the room",    Theme.textDim, Color(hex: "F0F0F3"), "person.3")
    }
    static func leaderChip(_ v: String, leaderName: String) -> (text: String, fg: Color, bg: Color) {
        v == "different" ? ("Different from \(leaderName)", Theme.actText, Theme.actBG)
                         : ("Same as \(leaderName)",        Theme.textDim, Color(hex: "F0F0F3"))
    }
    static func ringFill(oneIn: Int) -> Double { oneIn <= 0 ? 0 : 1.0 / Double(oneIn) }
    static func chanceText(oneIn: Int) -> String { "1 in \(max(oneIn,1))" }

    static func outcomeChip(_ outcome: String, points: Int) -> (text: String, fg: Color, bg: Color) {
        switch outcome {
        case "exact":    return ("Spot on  +\(points)",        Theme.posText, Theme.posBG)
        case "goaldiff": return ("Right margin  +\(points)",   Theme.posText, Theme.posBG)
        case "tendency": return ("Right winner  +\(points)",   Theme.posText, Theme.posBG)
        case "draw":     return ("Called the draw  +\(points)",Theme.posText, Theme.posBG)
        default:         return ("Missed  +0",                 Theme.negText, Theme.negBG)
        }
    }
    static func modeIcon(_ mode: String) -> String {
        switch mode { case "safe": return "shield"; case "balanced": return "scalemass"
            case "controlled_attack": return "scope"; case "desperation": return "flame"
            case "protect_spieltag_win": return "lock"; default: return "scope" }
    }
    static func greeting(_ name: String, date: Date = Date()) -> String {
        let h = Calendar.current.component(.hour, from: date)
        let part = h < 12 ? "Good morning" : (h < 18 ? "Good afternoon" : "Good evening")
        return "\(part), \(name)."
    }
    static func countdown(to date: Date) -> String {
        let s = Int(date.timeIntervalSinceNow); if s <= 0 { return "Kicking off" }
        let h = s/3600, m = (s%3600)/60
        if h >= 24 { return "in \(h/24)d \(h%24)h" }
        return h >= 1 ? "in \(h)h \(m)m" : "in \(m)m"
    }
    static func kickoffClock(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "HH:mm"; return f.string(from: d) }
    static func relativeUpdated(_ d: Date) -> String {
        let r = RelativeDateTimeFormatter(); r.unitsStyle = .short; return r.localizedString(for: d, relativeTo: Date())
    }
}
```

**Copy doctrine (for feed strings + fallbacks):** reasons are full short sentences. Never show
`composite_score`, `expected_points` as text, raw probabilities, or p_gain/p_loss. `expectedPoints`
appears only as a **relative bar length**. Allowed as text: scoreline (1:0), points (+4), rank (#8),
gap (6 behind), "1 in 7", small counts ("1 of 8 friends"). All copy is **sentence case**.

---

## 7. Screens

> Every screen: `ZStack { Theme.bg.ignoresSafeArea(); IridescentGlow(intensity:…); ScrollView { … } }`.
> Content horizontal inset `Theme.s4`. Wrap the scroll content in `.id(store.generation)` and add
> `.refreshable { await store.refresh() }` so the **generative assembly replays** on open & refresh.
> Apply `.generativeAppear(i)` with an incrementing `i` down each screen so it builds top→bottom.

### 7.1 App shell — `RootView.swift` (floating frosted tab bar)

4 tabs. A floating frosted capsule pinned bottom; selected item = ink icon + label, others muted.

```
Tabs (SF Symbols):
  Today    → "sparkles"           Matches → "soccerball"
  Table    → "trophy"             Insights→ "chart.bar"
```
```
┌──────────────────────────────┐
│  (active screen, light)       │
│        ╭───────────────╮      │  ← frosted capsule (.ultraThinMaterial + white hairline +
│        │ ✦  ⚽  🏆  ◧ │      │    soft shadow), ~56pt tall, bottom inset ~12pt.
│        ╰───────────────╯      │    Selected: ink icon + small label. Light haptic on switch.
└──────────────────────────────┘
```
- `TabView(selection:)` with `.toolbar(.hidden, for: .tabBar)`; custom bar via `.safeAreaInset(edge:.bottom)`.
- `IridescentGlow(intensity: tab == .today ? 1.0 : 0.35)` shared behind all tabs (faint elsewhere).

### 7.2 Today — `TodayView.swift` (the self-assembling briefing)

**Goal:** in 2 seconds — standing, tonight's plan, next match — and it *builds itself* on open.
Strong `IridescentGlow` concentrated behind the greeting (top third).

Order (each `.generativeAppear(i)`, i = 0,1,2…):

0. **GeneratedStatus** (spark dot + "Generated just now") — top-left.
1. **Date label** "Wed, 17 Jun" (`.callout`, dim).
2. **Greeting** `Format.greeting("Niko")` → "Good evening, Niko." in `.greeting` (light). The word
   "Niko." in `.medium`. (Optional flourish: split into words, each its own `.generativeAppear` for
   a word-by-word build — see §8.)
3. **Standing card** (`FrostCard`):
   ```
   ┌───────────────────────────────────────────┐
   │ Eyebrow: YOUR POSITION              [orb]   │   orb = small iridescent circle (decorative)
   │ #8  of 9                                     │   #8 in .heroLight
   │ 6 points behind Alex                         │
   │ GapRail:  18 you ───●──────── 24 Alex        │   ← rail fills + marker slides in
   │ [pill: ties · matchday wins]                 │
   └───────────────────────────────────────────┘
   ```
4. **Tonight's plan card** (`FrostCard`):
   ```
   Eyebrow: TONIGHT'S PLAN        [icon Format.modeIcon]
   strategy.headline      ← .title, ink
   strategy.subtitle      ← .body, dim
   ──────────────────────
   ◐ drawPlan.planned draws planned · "drawPlan.reason"
   ```
5. **Next match spotlight** (`FrostCard`):
   ```
   Eyebrow: NEXT UP · 17:00 · (CountdownPill)
   [POR] Portugal            [SoftRing: 1:0]        ring arc = exact chance, tier-colored
   [COD] Congo DR
   StrengthBar (home/draw/away)
   [SoftPill Coin-flip] [SoftPill Against the room]
   InkButton "Why this pick →"        → pushes MatchDetail
   ```
6. **Today's other picks** — compact rows (`TeamBadge home  score  TeamBadge away · tier dot`),
   each `.generativeAppear(6+n)`. Tap → detail.

Empty state (no upcoming today): spotlight → "No matches today — next on {date}" with a soft
iridescent calendar glyph.

### 7.3 Matches — `MatchesView.swift`

Title "Matches" + a frosted segmented control **[ Upcoming | Results ]**. Grouped by matchday.
Rows = `MatchRowCard` (`FrostCard`), each `.generativeAppear(i)`.

- **Upcoming card:**
  ```
  CountdownPill                              [tier SoftPill]
  [POR] Portugal              [SoftRing 1:0]
  [COD] Congo DR
  StrengthBar
  ```
- **Results card** (status==final): ring → big **actual score**; outcome chip via `Format.outcomeChip`:
  ```
  Matchday 3 · 17 Jun                 [Spot on +4]   (soft mint pill)
  [POR] Portugal  2        your tip 1:0  ✓
  [COD] Congo DR  0
  ```
  Score color: posText if any points, negText if miss. Actual score `.display`.

Tap any card → `MatchDetailView`. Empty states: "No results yet — first picks score after kickoff."
/ "All caught up. Next matchday {date}."

### 7.4 Match detail — `MatchDetailView.swift`

Pushed. Faint `IridescentGlow` at top. Sections each `.generativeAppear(i)`:

1. **Hero:** teams + ranks; the **SoftRing** morphs in via `matchedGeometryEffect(id:"ring-\(id)")`
   from the tapped card. Below: tier `SoftPill` + countdown (or final result). Plain line:
   "1 in 7 chance it lands exactly." (`Format.chanceText`).
2. **Why this pick** (`FrostCard`): eyebrow "WHY 1:0"; each reason = soft check (`checkmark`,
   posText) + `.body`. Reasons stream in (stagger the bullets too).
3. **The matchup** (`FrostCard`): `StrengthBar` + one line from `favoriteStrength` / `upset`
   (red `exclamationmark.triangle` + text if `isUpset`).
4. **The room** (`FrostCard`): FriendDots-style row (8 dots, `onSamePick` filled iridescent) +
   sentence: `"Only \(onSame) of \(total) friends land here — that's your separation."` (flip copy
   if `onSame ≥ total/2`). Chips: leverage + vsLeader. "Leader's likely tip: 2:1".
5. **Other scores** (`FrostCard`): `alternates` rows — score + thin iridescent `expectedPoints`
   bar (relative length, no number) + note; chosen one tagged "Your pick".
6. **News** (if any): `newspaper` rows.

Nav: back chevron, title "Matchday {n}".

### 7.5 Table — `TableView.swift`

Title "League" + "{playersCount} players · {tiebreaker} decides ties". One `FrostCard` with rows
(each `.generativeAppear(i)`):
```
 #1  👑 Alex            24   ▲3
 #2     UnsPascha       23    –
 ...
 #8  (you) Niko         18   ▲1     ← your row: iridescent left accent + faint actBG tint, name ink
 #9     Katha           16   ▼1
```
- Rank `.headline` monospacedDigit; #1 in `actText`. Leader `crown` (actText). Your row: 3pt
  iridescent left bar, `Theme.actBG.opacity(0.5)` tint, "you" `SoftPill`.
- Points `.headline` monospacedDigit; `MovementArrow` right.
- Top of card: a slim **GapRail**-style track (last→leader) with a marker for you and a crown for
  the leader, so the spread is visual.
- Tap a non-you row → that friend's `ScoutCard` (sheet).

### 7.6 Insights — `InsightsView.swift`

**A) Engine form** (trust, human framing). Eyebrow "HOW THE PICKS ARE DOING (last {matches})".
Soft metric tiles (frosted, 2×2): `24 points won`, `1.5 avg per game`, `4 spot-on`, `8/16 scored`.
`Sparkline(recentPoints)` + caption "points per pick, most recent on the right". One takeaway line.

**B) Scouting** — eyebrow "SCOUTING THE FIELD"; vertical `ScoutCard` list by rank.

### 7.7 Scout card — `ScoutCard.swift`

```
┌───────────────────────────────────────────────┐
│ 👑 UnsPascha                 #2 · 23 pts         │
│ [SoftPill: Chaos merchant]                       │
│ "Loves big scorelines and wild results.          │
│  Rarely picks the draws you can copy."           │
│ ─────────────────────────────────────────       │
│ Goals   ●●●  High                                │
│ Draws   ●○○  Rare                                │
│ Upsets  ●●●  Often                               │
└───────────────────────────────────────────────┘
```
Traits: label (eyebrow, ~70pt) + 3-segment level bar (filled = `level`, iridescent; rest `track`) +
`value`. Tag pill color by keyword (chaos→warn, contrarian→active, default→neutral).

---

## 8. Motion & micro-interactions (the priority — implement all)

**The generative assembly is the headline animation.** It must feel like the UI is *thinking it
into existence*: soft, slightly slow, springy, blur-to-focus.

1. **Generative entrance** (`.generativeAppear`): per element — opacity 0→1, y +16→0, scale .97→1,
   **blur 9→0**, with `.spring(response:0.75, dampingFraction:0.82)` and `0.12 + index*0.085`s
   delay. Down each screen, top→bottom. This is §5.4.
2. **Replay on open & refresh:** content stack keyed `.id(store.generation)`; `.refreshable`
   bumps generation → remount → assembly replays. `GeneratedStatus` shows "Generating your
   briefing…" during, then "Generated just now".
3. **Breathing iridescent gradient** (`IridescentGlow`, §5.3): blobs drift/scale/rotate forever
   via `TimelineView`, ~10–18s implied periods, never looping visibly. Paused under Reduce Motion.
4. **Greeting word-build** (optional flourish): split "Good evening, Niko." into words; each word
   `.generativeAppear(1 + wordIndex)` so it assembles word-by-word like the reference.
5. **Rings draw** (`SoftRing`): arc 0→value, `.spring(response:1.0, damping:0.9)`, delay 0.25s.
6. **Bars / rails fill** (`StrengthBar`, `GapRail`): width 0→value, `.easeOut(0.8)` / spring,
   delay ~0.2–0.3s. Marker on the rail slides in.
7. **Shared-element morph:** match card → detail hero ring via
   `matchedGeometryEffect(id:"ring-\(match.id)", in: ns)` (shared `@Namespace`). Fallback to a
   `.scale + opacity + blur` transition if fiddly — don't block on it.
8. **Press feedback:** `PressScale` (scale .97 spring) on cards & buttons.
9. **Idle life:** the gradient breathing is enough; do NOT add card jitter (keeps it calm).
10. **Tab switch:** light `UIImpactFeedbackGenerator(.light)`; content cross-fades. Selecting
    Today re-runs its assembly (bump generation or re-key on appear).
11. **Reduce Motion:** every animated component checks `accessibilityReduceMotion` and snaps to the
    final state (no blur, no stagger; gradient paused). Already wired in the component code above.

Durations: luxurious but not sluggish — assembly completes in ~1.2–1.6s total. Springs are soft
(damping 0.8–0.9). Blur-to-focus is the defining texture; keep it.

---

## 9. Accessibility & polish

- **Dynamic Type:** use `.font` tokens; cap hero with `.minimumScaleFactor(0.7)`.
- **Color never the only signal:** results always show "+4 / +0" text; movement shows the number;
  tiers show a word. (Also covers color-blindness.)
- **Contrast on light:** `Theme.text` on `Theme.bg` passes AA. Soft pills use a darker same-hue
  text (posText on posBG, etc.) — verify each pair stays AA. Avoid `textMute` for essentials.
- **VoiceOver:** rings/bars get plain labels: ring → "Pick 1:0, coin-flip, lands about 1 in 7."
  StrengthBar → "Portugal heavy favorite." GapRail → "18 points, 6 behind Alex."
- **Reduce Motion:** assembly + breathing + draws all snap to final (see §8.11).
- **Haptics:** light on tab change & card tap; success haptic when opening a "Spot on" result.

---

## 10. Empty / loading / error states

- **Loading** (pre-decode, near-instant): light canvas + breathing glow + a soft skeleton.
- **Per-section empty:** friendly one-liners (per screen) with a soft SF Symbol in `textMute`.
- **Remote fetch failed but bundled exists:** keep bundled silently; optional tiny "offline —
  showing last saved" pill under GeneratedStatus. Never block if any data exists.
- **Hard failure (no data at all):** `ContentUnavailableView` (light): "Couldn't load your league"
  + Retry (`InkButton`).

---

## 11. KickTipp scoring (reference for copy & result coloring)

Exact **+4** → `exact` (mint). Winner+goal-diff **+3** → `goaldiff` (mint). Tendency **+2** →
`tendency` (mint). Non-exact draw **+2** → `draw` (mint). Exact draw **+4** → `exact`. Miss **0** →
`miss` (rose). Tiebreaker: matchday wins (Spieltagsiege).

---

## 12. Real content (seed the sample so it feels true — current state)

| # | Player        | Pts | Move |
|---|---------------|-----|------|
| 1 | Alex          | 24  | ▲3   |
| 2 | UnsPascha     | 23  | –    |
| 3 | Toegamorf     | 22  | ▼2   |
| 4 | Schirifötze   | 21  | ▼1   |
| 5 | Antinatio     | 21  | ▼1   |
| 6 | Klose4ev…     | 19  | –    |
| 6 | mehu97        | 19  | ▲1   |
| 8 | **Niko (you)**| 18  | ▲1   |
| 9 | Katha         | 16  | ▼1   |

Engine form (last 16): **24 pts, 1.5 avg, 4 exact, scored 8/16.** Mode: **controlled_attack**
("Chasing the lead"). Draw plan: **3**.

Scouting truths (for blurbs/traits): **Alex** ordinary chalk ("The leader"); **UnsPascha** avg 4.1
goals, 40% chaos ("Chaos merchant", Goals High/Draws Rare/Upsets Often); **Toegamorf** tidy 2:0/2:1
("Tidy & sharp"); **Schirifötze** lowest goals, low scores ("Low-scorer"); **Antinatio**
away-leaning ("Away-backer"); **mehu97/Klose4ev…** ~3.0–3.3 goals ("Goal-happy"); **Katha** high-ish
("Wildcard-lite"). League insight to surface: **the whole field underplays draws — when one lands,
you gain on everyone.**

---

## 13. Sample feed for early dev

Full sample is §18. Minimum to render Today + a detail: `me`, `strategy`, `form`, full `table`,
2–3 upcoming `matches` (Portugal 1:0 Congo DR; Brazil 3:0 Haiti; Ghana 1:1 Panama [chaos]), one
`final` match, 3–4 `scouting`.

---

## 14. Build order (sequential — each milestone compiles & runs)

**M0 — Skeleton (compiles, light, breathing gradient)**
1. New Xcode iOS App "EDGE", SwiftUI, iOS 18, **light only**.
2. Add `Color+Hex`, `Theme`, `Typography`, `IridescentGlow`, `GenerativeAppear`.
3. `EDGEApp` shows `ZStack { Theme.bg; IridescentGlow() ; Text("EDGE").generativeAppear(0) }`. **Run** — confirm the gradient breathes and "EDGE" blurs into focus.

**M1 — Data layer**
4. Add `Models`, `AppStore`. Drop §18 `SampleFeed.json` into `Resources/` (check target membership).
5. Temp `Text(me.name)` to confirm decode. **Run.**

**M2 — Components**
6. Build all `Components/` (§5.5–5.15). Make a `#Preview` gallery; verify ring draws, bar fills,
   rail marker slides, frosted cards look right on the light canvas. **Run.**

**M3 — Shell + Table**
7. `RootView` (4-tab `TabView` + floating frosted bar, §7.1).
8. `TableView` (§7.5) fully (mostly rows — good first screen). **Run.**

**M4 — Today (the showcase)**
9. `TodayView` (§7.2): GeneratedStatus, greeting, standing+GapRail, plan, next-match spotlight,
   mini-list. Wire `.generativeAppear`, `.id(generation)`, `.refreshable`. **Run** — pull to refresh
   replays the assembly.

**M5 — Matches + Detail**
10. `MatchesView` (§7.3) segmented + `MatchRowCard`.
11. `MatchDetailView` (§7.4) + nav + ring morph. **Run.**

**M6 — Insights + Scouting**
12. `InsightsView` (§7.6) + `ScoutCard` (§7.7). **Run.**

**M7 — Motion, a11y, states**
13. Polish §8 (word-build greeting, shared-element morph, haptics). Add empty/error (§10).
14. VoiceOver labels + Reduce Motion verification (§9). **Run & polish.**

**M8 — (later) Live data** — `scripts/build_app_feed.py` (§16); set `AppStore.feedURL`; host the JSON.

---

## 15. Acceptance criteria (definition of done)

- Launches to **Today** with the **breathing iridescent gradient** and the screen **assembling
  itself** (blur-to-focus, staggered), showing #8 / 18 pts / "6 points behind Alex" with the GapRail
  marker sliding in — **zero network**.
- **Pull-to-refresh replays** the generative assembly; `GeneratedStatus` flips to "Generating…".
- No raw probability, "%", `composite_score`, or `expected_points` appears as text anywhere.
- Every pick: scoreline + worded tier (soft pill) + ≥1 plain reason; tapping morphs the ring into detail.
- Results tab shows ≥1 final match with the actual score + a soft "+N / Spot on / Missed" pill.
- Table highlights **your** row (iridescent), crown on the leader, movement arrows.
- Insights shows form (24 / 1.5 / 4 / 8-of-16) + sparkline + a scout card per friend (3 trait bars).
- Looks **light & opalescent**: near-white, frosted cards with white hairlines, soft bluish shadows,
  one black CTA pill, only soft pastel state colors.
- Reduce Motion snaps everything to final and pauses the gradient; VoiceOver reads worded labels.

---

## 16. (Later task — spec only) `scripts/build_app_feed.py`

Do **not** build in the iOS task. Produces `app_feed.json`:
- **Read:** `reports/leverage_tip_sheet.json` (matches+picks), `data/kicktipp/rounds.local.json`
  (`current_state`; latest `screenshot_extraction.visible_matchdays` for table + movement;
  `round_history` → `worldcup_predictor.leverage_optimizer.estimate_player_tendencies` for scouting),
  `reports/kicktipp_optimizer_backtest.json` (form), completed results for `status:"final"`.
- **Translate per match:** `score`←`final_pick.scoreline`; `tier`←`source_risk_tier`; `tierLabel`←§6;
  `exactChanceOneIn`←`round(1/exact_probability)`; `leverage`←`edge_vs_field>0?contrarian:crowd`;
  `vsLeader`←`leader_correlation<0.5?different:same`; `odds`←`fitted_probabilities`;
  `favorite`/`favoriteStrength`←argmax+thresholds (heavy≥.70, clear≥.58, slight≥.50, else even);
  `upset`←elo ranks; `fieldExposure`←count `estimated_field_predictions`==pick, `leaderPick`←
  `estimated_leader_predictions[0]`; `reasons[]`←compose 1–3 sentences (favorite strength + best-value
  exact + leverage); `alternates[]`←top 3–4 of `top_candidates`.
- **Table:** latest `visible_matchdays` → `visible_total_points`+`positions`+`movement`
  (movement = prev position − current; + = up).
- **Scouting:** map each `PlayerTendency` (goals <2.6 Low / <3.2 Med / else High; draws <0.12 Rare /
  <0.22 Some / else Often; chaos <0.1 Rare / <0.25 Some / else Often).
- **Write & host:** validate against §4.1; serve via the repo's `cloudflare_app/public/`; set `feedURL`.

---

## 17. SF Symbols (no custom assets)

`sparkles`, `soccerball`, `trophy`, `chart.bar`, `scope`, `shield`, `scalemass`, `flame`, `lock`,
`crown`, `arrow.up.right`, `arrow.down.right`, `minus`, `arrow.triangle.branch`, `person.3`,
`checkmark`, `clock`, `newspaper`, `calendar`, `circle.lefthalf.filled` (draw plan),
`exclamationmark.triangle` (upset).

**Palette quick-reference:** canvas `#FCFCFE`; text `#2B2B2E` / dim `#9A9AA1`; ink/CTA `#161618`;
iridescent `#B9C9F2 #E7CDEE #F6D4DC #F8E7C8 #CBEBD9`; spark `#9B8CF0`; soft state pairs —
mint `#DDF3E7`/`#1F7A52`, peach `#FBEBD3`/`#9A6512`, rose `#FBE3E0`/`#B5483A`, periwinkle
`#E7E6FB`/`#5B4FC0`.

---

## 18. Appendix — full `SampleFeed.json`

> Save as `EDGE/Resources/SampleFeed.json` (target = app). Real values (2026-06-17).

```json
{
  "updatedAt": "2026-06-17T06:52:11Z",
  "season": "World Cup 2026",
  "me": {
    "name": "Niko", "rank": 8, "points": 18, "playersCount": 9,
    "leaderName": "Alex", "leaderPoints": 24, "deficit": 6, "tiebreaker": "matchday wins"
  },
  "strategy": {
    "mode": "controlled_attack",
    "headline": "Chasing the lead",
    "subtitle": "Calculated risks to close a 6-point gap",
    "drawPlan": { "planned": 3, "reason": "Nobody here backs draws — so a draw that lands gains on everyone" }
  },
  "form": {
    "matches": 16, "points": 24, "avgPoints": 1.5, "exact": 4, "scored": 8, "blanked": 8,
    "recentPoints": [2,0,4,2,0,3,2,0,4,2,2,0,3,0,0,0]
  },
  "table": [
    { "rank":1, "name":"Alex",        "points":24, "move":3,  "isMe":false, "isLeader":true  },
    { "rank":2, "name":"UnsPascha",   "points":23, "move":0,  "isMe":false, "isLeader":false },
    { "rank":3, "name":"Toegamorf",   "points":22, "move":-2, "isMe":false, "isLeader":false },
    { "rank":4, "name":"Schirifötze", "points":21, "move":-1, "isMe":false, "isLeader":false },
    { "rank":5, "name":"Antinatio",   "points":21, "move":-1, "isMe":false, "isLeader":false },
    { "rank":6, "name":"Klose4ev…",   "points":19, "move":0,  "isMe":false, "isLeader":false },
    { "rank":6, "name":"mehu97",      "points":19, "move":1,  "isMe":false, "isLeader":false },
    { "rank":8, "name":"Niko",        "points":18, "move":1,  "isMe":true,  "isLeader":false },
    { "rank":9, "name":"Katha",       "points":16, "move":-1, "isMe":false, "isLeader":false }
  ],
  "matches": [
    {
      "id":"760435","kickoff":"2026-06-17T17:00:00Z","matchday":3,"status":"upcoming",
      "home":{"name":"Portugal","code":"POR","rank":55},
      "away":{"name":"Congo DR","code":"COD","rank":5},
      "result":null,
      "myPick":{
        "score":"1:0","tier":"thin_edge","tierLabel":"Coin-flip","leverage":"contrarian",
        "vsLeader":"different","exactChanceOneIn":7,"expectedPoints":1.87,
        "reasons":[
          "Portugal are clear favorites tonight",
          "1:0 is the best-value exact score in this game",
          "Most friends go 2:0 or 2:1 — this buys you separation"
        ],
        "result":null
      },
      "odds":{"home":0.74,"draw":0.20,"away":0.06},
      "favorite":"Portugal","favoriteStrength":"heavy",
      "upset":{"isUpset":false,"text":"Form favors Portugal"},
      "fieldExposure":{"friendsTotal":8,"onSamePick":1,"leaderPick":"2:1"},
      "alternates":[
        {"score":"1:0","expectedPoints":1.87,"note":"Best value"},
        {"score":"2:0","expectedPoints":1.87,"note":"Crowd pick"},
        {"score":"1:1","expectedPoints":0.57,"note":"Draw swing"}
      ],
      "news":["Portugal expected to rotate two starters"]
    },
    {
      "id":"760444","kickoff":"2026-06-17T20:00:00Z","matchday":3,"status":"upcoming",
      "home":{"name":"Brazil","code":"BRA","rank":3},
      "away":{"name":"Haiti","code":"HAI","rank":83},
      "result":null,
      "myPick":{
        "score":"3:0","tier":"thin_edge","tierLabel":"Coin-flip","leverage":"crowd",
        "vsLeader":"same","exactChanceOneIn":9,"expectedPoints":1.71,
        "reasons":[
          "Brazil are heavy favorites at home",
          "3:0 balances a likely blowout with a realistic exact score",
          "Most of the field lands near here — limited separation"
        ],
        "result":null
      },
      "odds":{"home":0.86,"draw":0.10,"away":0.04},
      "favorite":"Brazil","favoriteStrength":"heavy",
      "upset":{"isUpset":false,"text":"Form heavily favors Brazil"},
      "fieldExposure":{"friendsTotal":8,"onSamePick":4,"leaderPick":"3:0"},
      "alternates":[
        {"score":"3:0","expectedPoints":1.71,"note":"Your pick"},
        {"score":"2:0","expectedPoints":1.69,"note":"Safer margin"},
        {"score":"4:0","expectedPoints":1.40,"note":"Blowout upside"}
      ],
      "news":[]
    },
    {
      "id":"760436","kickoff":"2026-06-17T17:00:00Z","matchday":3,"status":"upcoming",
      "home":{"name":"Ghana","code":"GHA","rank":68},
      "away":{"name":"Panama","code":"PAN","rank":40},
      "result":null,
      "myPick":{
        "score":"1:1","tier":"chaos","tierLabel":"Wild card","leverage":"contrarian",
        "vsLeader":"different","exactChanceOneIn":8,"expectedPoints":0.94,
        "reasons":[
          "This one's close to a coin-flip on paper",
          "A draw is live and almost nobody in your league backs draws",
          "1:1 here is pure separation if it lands"
        ],
        "result":null
      },
      "odds":{"home":0.39,"draw":0.31,"away":0.30},
      "favorite":"Draw","favoriteStrength":"even",
      "upset":{"isUpset":false,"text":"Too close to call"},
      "fieldExposure":{"friendsTotal":8,"onSamePick":0,"leaderPick":"2:1"},
      "alternates":[
        {"score":"1:1","expectedPoints":0.94,"note":"Draw separation"},
        {"score":"1:0","expectedPoints":0.91,"note":"Lean Ghana"},
        {"score":"0:1","expectedPoints":0.88,"note":"Lean Panama"}
      ],
      "news":[]
    },
    {
      "id":"760430","kickoff":"2026-06-16T19:00:00Z","matchday":2,"status":"final",
      "home":{"name":"France","code":"FRA","rank":2},
      "away":{"name":"Senegal","code":"SEN","rank":17},
      "result":{"home":2,"away":1},
      "myPick":{
        "score":"2:1","tier":"normal","tierLabel":"Solid pick","leverage":"crowd",
        "vsLeader":"same","exactChanceOneIn":8,"expectedPoints":1.66,
        "reasons":[
          "France favored but Senegal score goals",
          "2:1 was the best-value exact here"
        ],
        "result":{"points":4,"outcome":"exact"}
      },
      "odds":{"home":0.62,"draw":0.22,"away":0.16},
      "favorite":"France","favoriteStrength":"clear",
      "upset":{"isUpset":false,"text":"Form favored France"},
      "fieldExposure":{"friendsTotal":8,"onSamePick":3,"leaderPick":"2:1"},
      "alternates":[
        {"score":"2:1","expectedPoints":1.66,"note":"Your pick"},
        {"score":"2:0","expectedPoints":1.58,"note":"Clean sheet"},
        {"score":"1:0","expectedPoints":1.41,"note":"Tight"}
      ],
      "news":[]
    }
  ],
  "scouting": [
    { "name":"Alex","rank":1,"points":24,"isLeader":true,"tag":"The leader",
      "blurb":"Plays the obvious favorites and rarely slips. Beat him with separation, not by copying.",
      "traits":[{"label":"Goals","value":"Medium","level":2},{"label":"Draws","value":"Rare","level":1},{"label":"Upsets","value":"Rare","level":1}] },
    { "name":"UnsPascha","rank":2,"points":23,"isLeader":false,"tag":"Chaos merchant",
      "blurb":"Loves big scorelines and wild results. Rarely picks the tidy draws you can copy.",
      "traits":[{"label":"Goals","value":"High","level":3},{"label":"Draws","value":"Rare","level":1},{"label":"Upsets","value":"Often","level":3}] },
    { "name":"Toegamorf","rank":3,"points":22,"isLeader":false,"tag":"Tidy & sharp",
      "blurb":"Clean favorite wins, 2:0 and 2:1. Disciplined — you won't catch him with chalk.",
      "traits":[{"label":"Goals","value":"Medium","level":2},{"label":"Draws","value":"Some","level":2},{"label":"Upsets","value":"Rare","level":1}] },
    { "name":"Schirifötze","rank":4,"points":21,"isLeader":false,"tag":"Low-scorer",
      "blurb":"Tight, low scores and the occasional underdog. Goes where the crowd doesn't.",
      "traits":[{"label":"Goals","value":"Low","level":1},{"label":"Draws","value":"Some","level":2},{"label":"Upsets","value":"Some","level":2}] },
    { "name":"Antinatio","rank":5,"points":21,"isLeader":false,"tag":"Away-backer",
      "blurb":"Fades weak home favorites and leans to the away side more than anyone.",
      "traits":[{"label":"Goals","value":"Medium","level":2},{"label":"Draws","value":"Rare","level":1},{"label":"Upsets","value":"Some","level":2}] },
    { "name":"Klose4ev…","rank":6,"points":19,"isLeader":false,"tag":"Goal-happy",
      "blurb":"Higher-scoring picks across the board. Overshoots tight games.",
      "traits":[{"label":"Goals","value":"High","level":3},{"label":"Draws","value":"Some","level":2},{"label":"Upsets","value":"Some","level":2}] },
    { "name":"mehu97","rank":6,"points":19,"isLeader":false,"tag":"Goal-happy",
      "blurb":"Leans to more goals than the game warrants. Predictable on favorites.",
      "traits":[{"label":"Goals","value":"High","level":3},{"label":"Draws","value":"Some","level":2},{"label":"Upsets","value":"Some","level":2}] },
    { "name":"Katha","rank":9,"points":16,"isLeader":false,"tag":"Wildcard-lite",
      "blurb":"A bit higher-scoring and streaky. Currently last — chasing.",
      "traits":[{"label":"Goals","value":"High","level":3},{"label":"Draws","value":"Rare","level":1},{"label":"Upsets","value":"Some","level":2}] }
  ]
}
```

---

### One-paragraph brief (paste this first when handing off)

> Build **EDGE**, a **light, opalescent** iOS 18 SwiftUI app (no third-party deps) that turns a
> bundled `app_feed.json` into a glanceable KickTipp dashboard for beating a 9-person friends'
> league. Aesthetic = the "agentic gen UI" look: a near-white canvas with one **iridescent pastel
> gradient that slowly breathes**, **frosted-glass** cards (translucent white + blur + white
> hairline + soft bluish shadow), **thin** typography, soft pastel state pills (mint/peach/rose/
> periwinkle), and a single **black pill** for the primary action. The signature motion is
> **generative assembly**: on open and on pull-to-refresh the screen builds itself — every element
> fades up from a soft **blur into focus**, staggered top-to-bottom — while rings draw and bars
> fill. Four structured tabs (no chat): **Today** (a self-assembling briefing — greeting, standing
> with a gap rail, tonight's plan, next-match spotlight), **Matches** (upcoming + results), **Table**
> (league standings), **Insights** (engine form + per-friend scouting). Tapping a match opens a
> detail with the score ring morphing in and three plain-English reasons. **Never show raw
> percentages or jargon** — translate every number into a word, ring, bar, or soft-colored pill.
> Follow the build order in §14, the data contract in §4, the design system in §5, the human-
> language rules in §6, and the motion spec in §8. Ship it running fully offline on §18.
