---
phase: 03-components
plan: 02
subsystem: design-system
tags: [swiftui, ios18, components, comp-02]
requires:
  - 03-01 (Theme, Typography, Format — token + helper foundation)
provides:
  - SoftPill (pastel state chip)
  - InkButton + PressScale (black primary CTA + reusable press-scale ButtonStyle)
  - MovementArrow (rank delta indicator, color+icon+number)
  - TeamBadge (asset-free frosted circular monogram)
affects:
  - Today, Matches, Detail, Insights, Table screens (all consume these primitives)
tech-stack:
  added: []
  patterns:
    - "Pastel-fill + darker same-hue text pairing (SoftPill)"
    - "Single high-contrast CTA pattern (InkButton is the only black control)"
    - "Reusable ButtonStyle for tactile press feedback (PressScale)"
    - "Color paired with icon + number for A11Y (MovementArrow)"
    - "Asset-free identity via material + monogram (TeamBadge)"
key-files:
  created:
    - EDGE/Sources/DesignSystem/Components/SoftPill.swift
    - EDGE/Sources/DesignSystem/Components/InkButton.swift
    - EDGE/Sources/DesignSystem/Components/MovementArrow.swift
    - EDGE/Sources/DesignSystem/Components/TeamBadge.swift
  modified: []
decisions:
  - "Copied §5.9–5.12 verbatim from docs/ios_app_plan.md (design fidelity is paramount)"
  - "Kept the single spec comment on PressScale (// subtle tactile press, reused everywhere); no other comments added per project convention"
  - "Components consume Theme tokens + Format helpers exclusively — zero hardcoded colors"
metrics:
  duration: ~6 min
  completed: 2026-06-17
  tasks: 4
  files: 4
---

# Phase 03 Plan 02: Chip / Action / Indicator / Badge Components Summary

Four recurring UI primitives — `SoftPill`, `InkButton` (+`PressScale`), `MovementArrow`, `TeamBadge` — implemented verbatim from spec §5.9–5.12, each consuming `Theme` tokens and `Format` helpers (no hardcoded colors, no raw probabilities as text).

## What Was Built

### Task 1 — SoftPill (`SoftPill.swift`, commit `e96e206`)
Pastel capsule chip with darker same-hue text. Optional SF Symbol at `.system(size: 10, weight: .semibold)`, label at `.eyebrowX`. Padding h9/v5. Defaults `Theme.actBG`/`Theme.actText`; callers swap pairs via `Format.tierStyle`/`outcomeChip`/`leverageChip`/`leaderChip`.

### Task 2 — InkButton + PressScale (`InkButton.swift`, commit `d4e8db8`)
The one black full-width CTA: `Capsule().fill(Theme.ink)`, white `.headlineX` title, white circular badge holding the (default `arrow.right`) symbol in `Theme.ink`. `PressScale: ButtonStyle` scales to 0.97 under press with `.spring(response: 0.3, dampingFraction: 0.7)` — reusable across cards/buttons per spec §5.10.

### Task 3 — MovementArrow (`MovementArrow.swift`, commit `03205a3`)
Rank-delta indicator: `move > 0` → `arrow.up.right` in `Theme.posText`; `< 0` → `arrow.down.right` in `Theme.negText`; `== 0` → `minus` in `Theme.textMute`. Shows `abs(move)` in `.eyebrowX` + `.monospacedDigit()` when nonzero. Color is always paired with icon + number (A11Y-safe, never color-only).

### Task 4 — TeamBadge (`TeamBadge.swift`, commit `fb04d2b`)
Asset-free frosted circular monogram. `code` rendered at `size * 0.28` weight `.semibold` in `Theme.text`, framed by `Circle().fill(.ultraThinMaterial)` + `Theme.card` overlay + `Theme.hairline` 1px stroke. Default size 42. No image pipeline required.

## Verification

- `xcodebuild -target EDGE -sdk iphonesimulator ...` → **BUILD SUCCEEDED** after each of the 4 tasks.
- Acceptance-criteria greps all passed:
  - SoftPill: `Capsule().fill(bg)`, `Theme.actBG`, `Theme.actText` ✓
  - InkButton: `Capsule().fill(Theme.ink)`, `struct PressScale: ButtonStyle`, `scaleEffect(configuration.isPressed ? 0.97 : 1)` ✓
  - MovementArrow: `arrow.up.right`, `arrow.down.right`, `Theme.posText`, `Theme.negText` ✓
  - TeamBadge: `ultraThinMaterial`, `Theme.hairline`, `var size: CGFloat` ✓

## Deviations from Plan

None — plan executed exactly as written. All four files are byte-faithful to spec §5.9–5.12.

## Commits

| Task | Component | Commit |
| ---- | --------- | ------ |
| 1 | SoftPill | `e96e206` |
| 2 | InkButton + PressScale | `d4e8db8` |
| 3 | MovementArrow | `03205a3` |
| 4 | TeamBadge | `fb04d2b` |

## Self-Check: PASSED

- `EDGE/Sources/DesignSystem/Components/SoftPill.swift` — FOUND
- `EDGE/Sources/DesignSystem/Components/InkButton.swift` — FOUND
- `EDGE/Sources/DesignSystem/Components/MovementArrow.swift` — FOUND
- `EDGE/Sources/DesignSystem/Components/TeamBadge.swift` — FOUND
- Commit `e96e206` — FOUND
- Commit `d4e8db8` — FOUND
- Commit `03205a3` — FOUND
- Commit `fb04d2b` — FOUND
