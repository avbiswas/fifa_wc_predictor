## Project

**EDGE — iOS App**

EDGE is a light, opalescent iOS app (SwiftUI, iOS 18+) that turns the KickTipp exploit engine's
JSON into a glanceable, **self-assembling** dashboard for winning Niko's 9-person World Cup 2026
prediction league. It shows where Niko stands, what to tip tonight and *why* in plain language,
what already happened (scores + points), and how to beat each specific friend. v1 runs **fully
offline** from a bundled `SampleFeed.json`.

The complete, implementation-ready specification lives at **`docs/ios_app_plan.md`** — it is the
single source of truth for the data contract, design system (with full SwiftUI component code),
human-language rules, screens, and motion. This milestone packages that spec into executable
implementation phases.

**Core Value:** On open, in one glance, Niko knows exactly what to tip tonight and why — in plain language —
inside a UI so beautiful and self-explanatory it needs no manual. **If everything else fails, the
Today screen must look stunning and be instantly understandable.**

### Constraints

- **Tech stack**: Swift 5.9+, SwiftUI, **iOS 18.0+**, **light mode only**. No third-party packages.
  Icons = SF Symbols. All data-viz (rings, bars, gradient) hand-rolled with `Shape`/`Canvas`/
  `TimelineView`. — Matches the spec; keeps it dependency-free and fully controllable.
- **Design fidelity**: the opalescent aesthetic + the generative animations are the **highest
  priority** and must match `docs/ios_app_plan.md` §1/§5/§8 exactly. — This is the whole point.
- **Data**: v1 reads only the bundled `SampleFeed.json`; no network calls. — Offline-first, demoable.
- **No-jargon rule**: no raw probabilities, "%", `composite_score`, or `expected_points` as text
  anywhere. — Core UX doctrine (spec §0/§6).
- **Tooling**: Xcode build/run + simulator. Plans must remain implementation-ready and independently verifiable.
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
