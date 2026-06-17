# Milestones

## v1.0 EDGE iOS App (Shipped: 2026-06-17)

**Phases completed:** 8 phases, 16 plans, 53 tasks

**Key accomplishments:**

- Buildable iOS 18 SwiftUI app (xcodegen-owned) with verbatim-from-spec Theme + Typography token layer and a light-locked `@main` entry — every later phase composes from these tokens.
- The two signature aesthetic primitives — a breathing pastel gradient driven by TimelineView and a blur-to-focus staggered entrance — copied verbatim from spec §5.3/§5.4, both Reduce-Motion-aware, and composed into the EDGE root so the app opens to the breathing glow with "EDGE" materializing into focus.
- Codable feed models, an observable AppStore whose `generation` counter bumps on every refresh (so screens replay their generative entrance), a byte-verbatim bundled SampleFeed.json, and the Format anti-jargon translation layer — all four copied verbatim from spec §4.2/§4.3/§6/§18 and runtime-verified to decode cleanly.
- Four hand-rolled SwiftUI data-viz components — the frosted glass surface plus the three animated feed-visuals (drawing ring, pastel 1X2 bar, you->leader timeline) — copied byte-for-byte from spec §5.5-§5.8, all building clean and Reduce-Motion-safe.
- The agentic status affordance (pulsing spark dot) and the tiny-bars sparkline complete the component vocabulary, and a single scrollable ComponentGallery renders all 10 EDGE primitives over a faint breathing gradient on the light canvas — proving the whole library looks right before screens are assembled.
- 4-tab RootView shell with a floating frosted capsule tab bar (Today/Matches/Table/Insights), shared breathing IridescentGlow behind every tab, light haptic + spring on switch — now the EDGE app root.
- 9-player standings rendered spec-exact (§7.5) inside one FrostCard — rank, crown on Alex, SoftPill "you" + iridescent left bar + actBG tint on Niko's row, GapRail header above; rows blur-to-focus in via GenerativeAppear and replay on pull-to-refresh.
- TodayView scaffold with GeneratedStatus, greeting word-by-word build, standing card (rank + GapRail + tiebreaker pill), and tonight's plan card
- CountdownPill component, next-match spotlight with pick ring + strength bar, today's other picks list, navigation to match detail stub, and refresh replays assembly with generating status
- Segmented Upcoming/Results match list with MatchRowCard (countdown + ring for upcoming, scores + outcome chips for final) wired into the shell
- Full match detail screen with hero ring, 3 plain-English reasons, matchup strength bar, room leverage dots, alternate score bars, and news — zero jargon
- InsightsView with 4 frosted metric tiles, Sparkline bar chart, and plain-English takeaway — wired into the Insights tab replacing placeholder
- Friend scouting cards with keyword-colored tags, trait level bars, and Table-row sheet presentation
- iOS 18 zoom morph from match cards to detail, success haptic on exact-score results, and word-by-word greeting assembly animation
- VoiceOver worded labels on rings/bars/rows, graceful loading/error states, and a global no-jargon audit proving LANG-01 across the entire codebase

---
