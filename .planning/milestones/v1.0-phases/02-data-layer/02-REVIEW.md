---
phase: 02-data-layer
reviewed: 2026-06-17T13:15:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - EDGE/Sources/Core/Models.swift
  - EDGE/Sources/Resources/SampleFeed.json
  - EDGE/Sources/Core/AppStore.swift
  - EDGE/Sources/Core/Format.swift
  - EDGE/Sources/EDGEApp.swift
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: findings
---

# Phase 02: Code Review Report

**Reviewed:** 2026-06-17T13:15:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** findings

## Summary

The Phase 02 data layer is **structurally sound and faithful to the spec**: `Models.swift`,
`AppStore.swift`, `Format.swift`, and `EDGEApp.swift` are byte/word-for-word copies of
`docs/ios_app_plan.md` §4.2/§4.3/§6, and `SampleFeed.json` is **byte-identical** to §18 (verified
via `diff`). The bundled JSON parses, the field names match the Codable structs exactly, the
ISO8601 dates decode cleanly, and the German umlaut (`Schirifötze`) + ellipsis (`Klose4ev…`)
survive round-trip. The `generation` counter does increment on every load path including failures.
Format emits **no** raw `%`, `composite_score`, `expected_points`, or probability strings as text —
the no-jargon doctrine (LANG-01) is honored at the Format layer.

No Critical issues. No security concerns (offline v1, no eval, no secrets, no path traversal,
no injection surface). The 3 Warnings are robustness/quality defects that the spec itself
blesses — they will not break today's bundled feed but will bite the moment data drifts or a
remote feed is introduced.

**Spec fidelity note (not a finding):** the bundled `SampleFeed.json` table has an internal
ranking inconsistency — the two 21-pt players are ranked 4 and 5 (not tied), while the two
19-pt players are both ranked 6 (tied). This is data, not code, and the file is byte-faithful
to spec §18, so it is not flagged below. Surfaced here for visibility.

## Warnings

### WR-01: Bundled-load failure leaves the app stuck on `.loading` forever (silent brick)

**File:** `EDGE/Sources/Core/AppStore.swift:15-26`
**Issue:**
In offline mode (`feedURL == nil`, which is the v1 default), `load()` only ever sets `phase`
to `.loaded`. If `Self.loadBundled()` throws — e.g. the JSON file is missing from the bundle
(build misconfiguration), corrupt (bad merge, re-saved in latin-1), or fails to decode (a
future phase adds a required field without regenerating the fixture) — the `try?` on line 16
**silently swallows the error**, `phase` is never assigned, and the function returns at the
`guard let url = feedURL else { return }` on line 18 with `phase` still at its initial
`.loading` value. There is no path to `.failed` in the offline branch. The user sees an
infinite loading screen with no diagnostic and no recovery — violating spec §10 (empty /
loading / **error** states) and the validated requirement "App launches offline (bundled JSON)".

The remote branch does set `.failed` (line 24), but only when the bundled load *also* failed
(the `if case .loaded = phase { return }` guard on line 23 prefers a stale `.loaded` over the
error). So the error-reporting path exists but is unreachable for the v1 offline-first flow.

The `02-01-SUMMARY.md` claim "Decode verified" is true for the *current* JSON, but does not
cover this failure mode.

**Fix:**
Surface the bundled-decode error instead of swallowing it, and transition to `.failed` so the
UI can render an error state:

```swift
func load() async {
    do {
        let bundled = try Self.loadBundled()
        phase = .loaded(bundled)
        generation += 1
    } catch {
        phase = .failed("Could not load bundled feed: \(error.localizedDescription)")
        generation += 1   // still bump so any error-state entrance replays
        return
    }
    guard let url = feedURL else { return }
    // …existing remote path…
}
```

(If the spec's exact control flow must be preserved for the remote-fallback semantics, at
minimum replace `try?` with a `do/catch` that sets `phase = .failed(...)` before the
`feedURL` guard, so the bundled-only path can reach an error state.)

---

### WR-02: `Format.swift` hardcodes `Color(hex: "F0F0F3")` in two places, bypassing Theme tokens

**File:** `EDGE/Sources/Core/Format.swift:25` and `:29`
**Issue:**
The neutral "with the room" / "same as {leader}" chip backgrounds are constructed inline as
`Color(hex: "F0F0F3")` rather than via a Theme token. This contradicts:
1. The project doctrine that `Theme` is the single source of truth for color tokens (spec §5.1).
2. The Phase-02 summary's own claim: *"All colors come from Theme soft-state tokens; no raw
   `%`, `composite_score`, or `expected_points` ever appear as text."* — which is verifiably
   false for these two literals.
3. DRY — the magic string `"F0F0F3"` is duplicated, so a designer tweak requires editing two
   call sites (and risks drifting). `Theme` already defines the visually-similar `track =
   Color(hex: "ECECF1")`; the new near-white belongs beside it.

This is spec-blessed (spec §6 has the same literals verbatim), but it is still a quality
defect — and the summary's misrepresentation of it is the more important signal.

**Fix:**
Add a dedicated token to `Theme.swift` (Phase 1 file, but the token gap is exposed by Phase 2):

```swift
// in Theme.swift
static let chipNeutralBG = Color(hex: "F0F0F3")  // neutral "with the room / same as" chip
```

then in `Format.swift`:
```swift
: ("With the room", Theme.textDim, Theme.chipNeutralBG, "person.3")
…
: ("Same as \(leaderName)", Theme.textDim, Theme.chipNeutralBG)
```

---

### WR-03: `outcomeChip` default branch hardcodes `"+0"` and ignores the `points` parameter

**File:** `EDGE/Sources/Core/Format.swift:34-42`
**Issue:**
```swift
static func outcomeChip(_ outcome: String, points: Int) -> (…) {
    switch outcome {
    case "exact":    return ("Spot on  +\(points)", …)
    …
    default:         return ("Missed  +0", Theme.negText, Theme.negBG)   // ← ignores `points`
    }
}
```
The default branch hard-codes `"+0"`, so any unrecognized outcome string (e.g. a future engine
value like `"exact_late"`, `"void"`, `"forfeit"`) silently renders as "Missed  +0" **even when
the caller passed `points > 0`**. The function signature promises that `points` is used; the
body breaks that contract for the fallback. KickTipp scoring today always yields 0 for `miss`,
so the bundled feed is unaffected — but this is a forward-compatibility footgun: the next
engine revision that introduces a new outcome tier will silently drop the points value in the UI.

**Fix:**
Either honor `points` in the default (defensive):
```swift
default: return ("Missed  +\(max(points, 0))", Theme.negText, Theme.negBG)
```
or drop the misleading parameter for the miss case by making it explicit:
```swift
case "miss":   return ("Missed", Theme.negText, Theme.negBG)
default:       return ("Missed  +\(max(points, 0))", Theme.negText, Theme.negBG)
```

## Info

### IN-01: `Identifiable` IDs are derived from feed data values (latent collision risk for `ForEach`)

**File:** `EDGE/Sources/Core/Models.swift:26, 39, 49, 52`
**Issue:**
Several model IDs are computed from data fields rather than a stable unique key:
- `TableRow.id = name`
- `Alternate.id = score`
- `ScoutReport.id = name`
- `Trait.id = label`

In the current bundled feed these are all unique within their containing array, so SwiftUI
`ForEach` works today. But if a future remote feed ever emits two `Alternate`s with the same
`score` (plausible — "1:0 best value" vs "1:0 alternate reasoning"), two `Trait`s with the
same `label`, or two friends with the same name, `ForEach` will trap at runtime with
*"identity is not unique"*. The contract is data-dependent rather than structurally enforced.

**Fix:** No change required for v1; consider a composite ID (e.g. `"\(rank)-\(name)"` for
`TableRow`) or promote the engine to emit a stable `id` field when the remote feed lands.

---

### IN-02: `ringFill(0)` and `chanceText(0)` diverge for the same edge-case input

**File:** `EDGE/Sources/Core/Format.swift:31-32`
**Issue:**
```swift
static func ringFill(oneIn: Int) -> Double { oneIn <= 0 ? 0 : 1.0 / Double(oneIn) }   // 0 → 0.0 (empty ring)
static func chanceText(oneIn: Int) -> String { "1 in \(max(oneIn,1))" }                // 0 → "1 in 1" (full ring)
```
Both helpers clamp `oneIn <= 0` defensively (good — avoids divide-by-zero), but they disagree
semantically: `ringFill(0)` renders an empty ring, while `chanceText(0)` reads as a certainty.
If both are ever derived from the same source value (e.g. an engine that yields
`exactChanceOneIn = 0` to mean "impossible"), the UI would show an empty ring labeled "1 in 1".

**Fix:** Align the semantics — either `chanceText(0)` → `""` / `"—"`, or `ringFill(0)` → `1.0`
matching `chanceText`. Bundled feed never emits `0`, so this is forward-looking only.

---

### IN-03: `kickoffClock` forces 24-hour display and allocates a new formatter per call

**File:** `EDGE/Sources/Core/Format.swift:59`
**Issue:**
```swift
static func kickoffClock(_ d: Date) -> String {
    let f = DateFormatter()
    f.dateFormat = "HH:mm"
    return f.string(from: d)
}
```
- `dateFormat = "HH:mm"` overrides the user's 12/24-hour preference. In a US locale where the
  user has chosen 12-hour, this still shows `17:00` instead of `5:00 PM`. iOS convention is to
  honor the user preference via `dateStyle = .short` or a localized template
  (`DateFormatter.setLocalizedDateFormatFromTemplate("jm")`).
- A `DateFormatter` is allocated on every call. Not a correctness issue (perf is out of v1
  scope) but the same observation applies to `relativeUpdated` allocating a
  `RelativeDateTimeFormatter` per call (line 61). Both are typical candidates for a `static
  let`.

**Fix:**
```swift
static func kickoffClock(_ d: Date) -> String {
    let f = DateFormatter()
    f.setLocalizedDateFormatFromTemplate("HHmm")   // respects user 12/24h preference + locale
    return f.string(from: d)
}
```

---

### IN-04: `AppStore.feedURL` is a publicly mutable `var`

**File:** `EDGE/Sources/Core/AppStore.swift:9`
**Issue:**
```swift
var feedURL: URL? = nil
```
The property is internal (default access) and mutable from any file in the module. Nothing in
Phase 02 mutates it after init, but nothing prevents a future view from doing so concurrently
with an in-flight `load()` (which reads `feedURL` mid-function). For a single-store app this
is unlikely to cause issues today, but a `private(set)` would make the read/write contract
explicit and remove the race surface.

**Fix:** `private(set) var feedURL: URL? = nil` (and expose an initializer or method when v2
needs to set it).

---

_Reviewed: 2026-06-17T13:15:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
