from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable

from worldcup_predictor.tip_optimizer import (
    Odds,
    ScoreRules,
    distribution_outcome_probabilities,
    expected_tip_points,
    fair_probabilities,
    fit_market_lambdas,
    outcome_from_goals,
    poisson_distribution,
    ranked_market_tips,
    score_tip,
)

Score = tuple[int, int]


@dataclass(frozen=True)
class PlayerTendency:
    player: str
    picks: int
    draw_rate: float
    favorite_rate: float | None
    exact_1_1_rate: float
    average_goals: float
    chaos_rate: float


@dataclass(frozen=True)
class LeverageCandidate:
    scoreline: str
    pick: str
    expected_points: float
    exact_probability: float
    outcome_probability: float
    edge_vs_field: float
    edge_vs_leaders: float
    p_gain_2plus: float
    p_loss_2plus: float
    leader_correlation: float
    composite_score: float = 0.0


MODE_WEIGHTS: dict[str, dict[str, float]] = {
    "safe": {
        "ev": 1.15,
        "field_edge": 0.15,
        "leader_edge": 0.10,
        "gain": 0.10,
        "loss": 0.75,
        "corr": 0.10,
        "ev_slack": 0.22,
    },
    "balanced": {
        "ev": 1.00,
        "field_edge": 0.35,
        "leader_edge": 0.20,
        "gain": 0.22,
        "loss": 0.40,
        "corr": 0.15,
        "ev_slack": 0.35,
    },
    "controlled_attack": {
        "ev": 0.95,
        "field_edge": 0.55,
        "leader_edge": 0.35,
        "gain": 0.36,
        "loss": 0.25,
        "corr": 0.22,
        "ev_slack": 0.50,
    },
    "desperation": {
        "ev": 0.70,
        "field_edge": 0.85,
        "leader_edge": 0.65,
        "gain": 0.70,
        "loss": 0.08,
        "corr": 0.35,
        "ev_slack": 0.90,
    },
    "protect_spieltag_win": {
        "ev": 1.20,
        "field_edge": 0.05,
        "leader_edge": 0.05,
        "gain": 0.05,
        "loss": 1.05,
        "corr": -0.10,
        "ev_slack": 0.18,
    },
}


def parse_scoreline(value: str | Iterable[int] | Score) -> Score:
    if isinstance(value, tuple) and len(value) == 2:
        return int(value[0]), int(value[1])
    if not isinstance(value, str):
        parts = list(value)
        if len(parts) != 2:
            raise ValueError(f"Not a scoreline: {value!r}")
        return int(parts[0]), int(parts[1])
    match = re.search(r"(\d+)\s*[:\-]\s*(\d+)", value)
    if not match:
        raise ValueError(f"Not a scoreline: {value!r}")
    return int(match.group(1)), int(match.group(2))


def scoreline(score: Score) -> str:
    return f"{score[0]}:{score[1]}"


def weighted_correlation(points_a: list[float], points_b: list[float], weights: list[float]) -> float:
    total = sum(weights)
    if total <= 0:
        return 0.0
    mean_a = sum(a * w for a, w in zip(points_a, weights, strict=True)) / total
    mean_b = sum(b * w for b, w in zip(points_b, weights, strict=True)) / total
    var_a = sum(w * (a - mean_a) ** 2 for a, w in zip(points_a, weights, strict=True)) / total
    var_b = sum(w * (b - mean_b) ** 2 for b, w in zip(points_b, weights, strict=True)) / total
    if var_a <= 1e-12 or var_b <= 1e-12:
        return 0.0
    cov = sum(w * (a - mean_a) * (b - mean_b) for a, b, w in zip(points_a, points_b, weights, strict=True)) / total
    return max(-1.0, min(1.0, cov / math.sqrt(var_a * var_b)))


def rank_leverage_candidates(
    distribution: dict[Score, float],
    *,
    field_predictions: list[Score] | None = None,
    leader_predictions: list[Score] | None = None,
    max_candidate_goals: int = 5,
    rules: ScoreRules | None = None,
) -> list[LeverageCandidate]:
    """Rank score picks by KickTipp EV plus relative edge against the private field.

    field_predictions should be either observed friend picks or a deterministic estimate
    of what the private round will probably tip. leader_predictions can be a subset for
    Toegamorf/other leaders; if omitted, the whole field is used as the leader proxy.
    """
    rules = rules or ScoreRules()
    field_predictions = field_predictions or []
    leader_predictions = leader_predictions or field_predictions
    outcome_probs = distribution_outcome_probabilities(distribution)
    actual_scores = list(distribution)
    actual_probs = [distribution[actual] for actual in actual_scores]
    candidates: list[LeverageCandidate] = []

    for home in range(max_candidate_goals + 1):
        for away in range(max_candidate_goals + 1):
            predicted = (home, away)
            my_points = [score_tip(predicted, actual, rules) for actual in actual_scores]
            ev = sum(points * probability for points, probability in zip(my_points, actual_probs, strict=True))

            if field_predictions:
                field_points = [
                    sum(score_tip(field_pick, actual, rules) for field_pick in field_predictions) / len(field_predictions)
                    for actual in actual_scores
                ]
                deltas = [mine - field for mine, field in zip(my_points, field_points, strict=True)]
                edge_vs_field = sum(delta * probability for delta, probability in zip(deltas, actual_probs, strict=True))
                p_gain_2plus = sum(probability for delta, probability in zip(deltas, actual_probs, strict=True) if delta >= 2)
                p_loss_2plus = sum(probability for delta, probability in zip(deltas, actual_probs, strict=True) if delta <= -2)
            else:
                field_points = [0.0 for _ in actual_scores]
                edge_vs_field = ev
                p_gain_2plus = 0.0
                p_loss_2plus = 0.0

            if leader_predictions:
                leader_points = [
                    sum(score_tip(leader_pick, actual, rules) for leader_pick in leader_predictions) / len(leader_predictions)
                    for actual in actual_scores
                ]
                leader_deltas = [mine - leader for mine, leader in zip(my_points, leader_points, strict=True)]
                edge_vs_leaders = sum(delta * probability for delta, probability in zip(leader_deltas, actual_probs, strict=True))
                leader_correlation = weighted_correlation([float(p) for p in my_points], leader_points, actual_probs)
            else:
                edge_vs_leaders = edge_vs_field
                leader_correlation = 0.0

            pick = outcome_from_goals(home, away)
            candidates.append(
                LeverageCandidate(
                    scoreline=scoreline(predicted),
                    pick=pick,
                    expected_points=ev,
                    exact_probability=distribution.get(predicted, 0.0),
                    outcome_probability=outcome_probs[pick],
                    edge_vs_field=edge_vs_field,
                    edge_vs_leaders=edge_vs_leaders,
                    p_gain_2plus=p_gain_2plus,
                    p_loss_2plus=p_loss_2plus,
                    leader_correlation=leader_correlation,
                )
            )

    candidates.sort(key=lambda c: (c.expected_points, c.edge_vs_field, c.p_gain_2plus, c.exact_probability), reverse=True)
    return candidates


def estimate_public_field_predictions(odds: Odds, *, over_under: float | None = None, field_size: int = 4) -> list[Score]:
    """Estimate what normal humans in a KickTipp round will probably pick.

    This is intentionally boring: it models favorite-chalk scorelines. Observed friend
    picks should override this whenever screenshots/data are available.
    """
    fair = fair_probabilities(odds)
    market_candidates = ranked_market_tips(odds, over_under=over_under, limit=8)
    favorite_side = "home" if fair["home"] >= fair["away"] else "away"
    favorite_prob = max(fair["home"], fair["away"])

    templates: list[Score] = [parse_scoreline(market_candidates[0].scoreline)]
    if favorite_side == "home":
        if favorite_prob >= 0.82:
            templates += [(3, 0), (4, 0), (2, 0), (3, 1)]
        elif favorite_prob >= 0.65:
            templates += [(2, 0), (2, 1), (3, 1), (1, 0)]
        elif favorite_prob >= 0.52:
            templates += [(2, 1), (1, 0), (1, 1), (2, 0)]
        else:
            templates += [(1, 1), (1, 0), (0, 1), (2, 1)]
    else:
        if favorite_prob >= 0.82:
            templates += [(0, 3), (0, 4), (0, 2), (1, 3)]
        elif favorite_prob >= 0.65:
            templates += [(0, 2), (1, 2), (1, 3), (0, 1)]
        elif favorite_prob >= 0.52:
            templates += [(1, 2), (0, 1), (1, 1), (0, 2)]
        else:
            templates += [(1, 1), (1, 0), (0, 1), (1, 2)]

    unique: list[Score] = []
    for template in templates:
        if template not in unique:
            unique.append(template)
        if len(unique) >= field_size:
            break
    return unique


def estimate_leader_predictions(odds: Odds, *, over_under: float | None = None, leader_style: str = "sharp") -> list[Score]:
    field = estimate_public_field_predictions(odds, over_under=over_under, field_size=4)
    fair = fair_probabilities(odds)
    if leader_style == "sharp" and fair["draw"] >= 0.24 and max(fair["home"], fair["away"]) < 0.62:
        return [(1, 1), field[0]]
    if leader_style == "chaos":
        favorite_side = "home" if fair["home"] >= fair["away"] else "away"
        return [field[0], (4, 2) if favorite_side == "home" else (2, 4)]
    return field[:2]


def project_opponent_pick(scores: list[Score], odds: Odds, *, draw_prob_floor: float = 0.26) -> Score:
    """Project a specific opponent's likely scoreline for THIS match from their history.

    This is the core of actually *exploiting friends* rather than a faceless chalk
    template: each opponent's revealed tendencies (draw appetite, scoring level, typical
    winning margin, away/underdog willingness) are rotated onto the current fixture's
    market favorite. It is intentionally coarse — 12-16 picks per player is a small
    sample, so we model stable rates, not a brittle per-match oracle.
    """
    if not scores:
        raise ValueError("Cannot project from an empty pick history")
    fair = fair_probabilities(odds)
    favorite_side = "home" if fair["home"] >= fair["away"] else "away"
    favorite_prob = max(fair["home"], fair["away"])

    count = len(scores)
    draw_rate = sum(1 for score in scores if score[0] == score[1]) / count
    away_rate = sum(1 for score in scores if score[0] < score[1]) / count
    average_total = sum(sum(score) for score in scores) / count
    margins = [abs(score[0] - score[1]) for score in scores if score[0] != score[1]]
    average_margin = sum(margins) / len(margins) if margins else 1.0

    # A genuinely draw-prone player in a draw-live match tips their habitual draw. Most
    # of the field is NOT draw-prone, which is exactly why draws are high-leverage.
    if draw_rate >= 0.30 and fair["draw"] >= draw_prob_floor and favorite_prob < 0.62:
        return (1, 1) if average_total >= 1.5 else (0, 0)

    # Side: back the market favorite, unless this player is a real away/underdog
    # contrarian (high absolute away rate) AND the favorite is not commanding. Even
    # contrarians respect a strong favorite.
    side = favorite_side
    if favorite_side == "home" and away_rate >= 0.40 and favorite_prob < 0.58:
        side = "away"

    winner_goals = max(1, min(6, round((average_total + average_margin) / 2)))
    loser_goals = max(0, min(winner_goals, round((average_total - average_margin) / 2)))
    return (winner_goals, loser_goals) if side == "home" else (loser_goals, winner_goals)


def estimate_opponents_from_history(
    context: dict[str, Any],
    odds: Odds,
    *,
    min_history: int = 6,
    draw_prob_floor: float = 0.26,
) -> tuple[list[Score], list[Score]]:
    """Project (field, leaders) scoreline picks for a match from real ``round_history``.

    Returns ``([], [])`` when there is not enough history, so callers can fall back to the
    generic public-chalk template. Niko's own picks are excluded from the field; the three
    tracked leaders (by ``leader_names`` or the ``is_leader`` flag) also form the leader
    sub-field that the anti-leader / leader-correlation terms key off.
    """
    history = context.get("round_history") or []
    if not history:
        return [], []

    state = context.get("current_state") or {}
    excluded = {str(state.get("niko_player") or "")}
    excluded |= {str(alias) for alias in (state.get("niko_player_visible_aliases") or [])}
    for player in context.get("players") or []:
        if player.get("role") == "niko" and player.get("name"):
            excluded.add(str(player["name"]))
    excluded.discard("")
    leader_names = {str(name) for name in (context.get("leader_names") or [])}

    by_player: dict[str, list[Score]] = {}
    is_leader: dict[str, bool] = {}
    for row in history:
        player = row.get("player")
        tip = row.get("tip")
        if not player or not tip or str(player) in excluded:
            continue
        try:
            score = parse_scoreline(str(tip))
        except ValueError:
            continue
        by_player.setdefault(str(player), []).append(score)
        if row.get("is_leader"):
            is_leader[str(player)] = True

    field: list[Score] = []
    leaders: list[Score] = []
    for player, scores in sorted(by_player.items()):
        if len(scores) < min_history:
            continue
        projected = project_opponent_pick(scores, odds, draw_prob_floor=draw_prob_floor)
        field.append(projected)
        if player in leader_names or is_leader.get(player):
            leaders.append(projected)
    return field, leaders


def score_candidate(candidate: LeverageCandidate, mode: str, top_ev: float, *, tournament_phase: str = "group_stage") -> float:
    if tournament_phase == "knockout" and candidate.pick == "draw":
        # KickTipp is configured as knockout result after penalties. A draw may be a
        # useful 90-minute market signal, but it is not a valid final tip. Do not let
        # the scorer smuggle X back in via leverage math.
        return -9999.0 + candidate.expected_points
    weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["controlled_attack"])
    if candidate.expected_points < top_ev - weights["ev_slack"]:
        # Keep lunacy out unless the mode explicitly permits it. Exotic 4:3 hero balls
        # are how you donate points to friends.
        return -999.0 + candidate.expected_points
    score = (
        weights["ev"] * candidate.expected_points
        + weights["field_edge"] * candidate.edge_vs_field
        + weights["leader_edge"] * candidate.edge_vs_leaders
        + weights["gain"] * (4.0 * candidate.p_gain_2plus)
        - weights["loss"] * (4.0 * candidate.p_loss_2plus)
        - weights["corr"] * candidate.leader_correlation
    )
    if tournament_phase == "group_stage" and candidate.pick == "draw":
        # Group-stage draw hunting must stay probability-first. The old scorer could
        # choose a cute 0:0 purely because it decorrelated from favorite chalk, even when
        # the normal side pick had better EV and less downside. With many games still on
        # the board, that's not leverage — that's donating points in a tuxedo.
        ev_gap = max(0.0, top_ev - candidate.expected_points)
        downside_gap = max(0.0, candidate.p_loss_2plus - candidate.p_gain_2plus)
        score -= 1.60 * ev_gap + downside_gap
    return score


def select_final_candidate(
    candidates: list[LeverageCandidate], *, mode: str = "controlled_attack", tournament_phase: str = "group_stage"
) -> LeverageCandidate:
    if not candidates:
        raise ValueError("No leverage candidates")
    top_ev = max(candidate.expected_points for candidate in candidates)
    rescored = [
        LeverageCandidate(
            **{**asdict(candidate), "composite_score": score_candidate(candidate, mode, top_ev, tournament_phase=tournament_phase)}
        )
        for candidate in candidates
    ]
    return max(rescored, key=lambda c: (c.composite_score, c.expected_points, c.edge_vs_field))


def best_candidate(candidates: list[LeverageCandidate], predicate: Any) -> LeverageCandidate | None:
    filtered = [candidate for candidate in candidates if predicate(candidate)]
    if not filtered:
        return None
    return max(filtered, key=lambda c: (c.composite_score, c.expected_points, c.edge_vs_field, c.p_gain_2plus))


def candidate_to_dict(candidate: LeverageCandidate | None) -> dict[str, Any] | None:
    if candidate is None:
        return None
    data = asdict(candidate)
    for key in [
        "expected_points",
        "exact_probability",
        "outcome_probability",
        "edge_vs_field",
        "edge_vs_leaders",
        "p_gain_2plus",
        "p_loss_2plus",
        "leader_correlation",
        "composite_score",
    ]:
        data[key] = round(float(data[key]), 4)
    return data


def _state_float(state: dict[str, Any] | None, key: str, default: float = 0.0) -> float:
    if not state:
        return default
    try:
        return float(state.get(key, default))
    except (TypeError, ValueError):
        return default


def comeback_draw_target(auto_target: int, state: dict[str, Any] | None, *, mode: str) -> int:
    """Cap draw traps when Niko is chasing a real deficit.

    The early tournament sample rewarded aggressive draw hunting, but once the private
    league deficit is large the failure mode changes: too many 1:1 traps cap upside and
    donate favorite-win cells to leaders. Keep one high-conviction draw trap alive, not a
    whole slate of draw cosplay.
    """
    deficit = _state_float(state, "deficit", 0.0)
    if mode == "desperation" or (mode == "controlled_attack" and deficit >= 8):
        return min(auto_target, 1)
    return auto_target


def _dict_score(value: dict[str, Any]) -> Score:
    return parse_scoreline(str(value["scoreline"]))


def _same_side(candidate: dict[str, Any], final: dict[str, Any]) -> bool:
    return candidate.get("pick") == final.get("pick") and candidate.get("pick") != "draw"


def _score_total(candidate: dict[str, Any]) -> int:
    home, away = _dict_score(candidate)
    return home + away


def _score_margin(candidate: dict[str, Any]) -> int:
    home, away = _dict_score(candidate)
    return abs(home - away)


def _exact_chase_candidate_score(candidate: dict[str, Any]) -> float:
    """Rank same-side exact-score alternatives for comeback mode."""
    return (
        float(candidate.get("expected_points", 0.0))
        + 0.045 * _score_total(candidate)
        + 0.035 * _score_margin(candidate)
        + 0.15 * float(candidate.get("p_gain_2plus", 0.0))
        - 0.20 * float(candidate.get("p_loss_2plus", 0.0))
        - 0.04 * float(candidate.get("leader_correlation", 0.0))
    )


def _is_sane_exact_chase_template(candidate: dict[str, Any], favorite_probability: float) -> bool:
    home, away = _dict_score(candidate)
    if home == away:
        return False
    winner_goals = max(home, away)
    loser_goals = min(home, away)
    relative_score = (winner_goals, loser_goals)
    if favorite_probability >= 0.82:
        return relative_score in {(3, 0), (4, 0), (3, 1), (4, 1)}
    if favorite_probability >= 0.62:
        return relative_score in {(2, 0), (3, 0), (2, 1), (3, 1)}
    return relative_score in {(1, 0), (2, 0), (2, 1), (3, 1)}


def _is_comeback_mode(state: dict[str, Any] | None, mode: str) -> bool:
    deficit = _state_float(state, "deficit", 0.0)
    return mode == "desperation" or (mode == "controlled_attack" and deficit >= 8)


def _candidate_pool(row: dict[str, Any]) -> list[dict[str, Any]]:
    pool: list[dict[str, Any]] = []
    for key in ["final_pick", "ev_pick", "leverage_pick", "anti_field_pick", "anti_leader_pick", "best_non_draw_pick"]:
        candidate = row.get(key)
        if isinstance(candidate, dict):
            pool.append(candidate)
    pool.extend(candidate for candidate in row.get("top_candidates", []) if isinstance(candidate, dict))

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in pool:
        scoreline_value = str(candidate.get("scoreline"))
        if not scoreline_value or scoreline_value in seen:
            continue
        seen.add(scoreline_value)
        unique.append(candidate)
    return unique


def _favorite_side_from_fair(fair: dict[str, Any]) -> tuple[str, float]:
    home = float(fair.get("home", 0.0) or 0.0)
    away = float(fair.get("away", 0.0) or 0.0)
    return ("home", home) if home >= away else ("away", away)


def _top_ev_for_row(row: dict[str, Any]) -> float:
    values = [float(candidate.get("expected_points", 0.0) or 0.0) for candidate in _candidate_pool(row)]
    return max(values or [0.0])


def _best_side_candidate(row: dict[str, Any], side: str, *, max_ev_gap: float) -> dict[str, Any] | None:
    top_ev = _top_ev_for_row(row)
    candidates = [
        candidate
        for candidate in _candidate_pool(row)
        if candidate.get("pick") == side
        and candidate.get("pick") != "draw"
        and float(candidate.get("expected_points", 0.0) or 0.0) >= top_ev - max_ev_gap
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda candidate: (
            float(candidate.get("expected_points", 0.0) or 0.0)
            + 0.20 * float(candidate.get("exact_probability", 0.0) or 0.0)
            + 0.035 * _score_total(candidate)
            + 0.025 * _score_margin(candidate)
            - 0.08 * float(candidate.get("leader_correlation", 0.0) or 0.0),
            float(candidate.get("expected_points", 0.0) or 0.0),
        ),
    )


def apply_selective_miracle_policy(
    rows: list[dict[str, Any]], *, state: dict[str, Any] | None = None, mode: str = "controlled_attack"
) -> list[dict[str, Any]]:
    """Stop desperation mode from becoming blind-underdog cosplay.

    The comeback shape is selective violence:
    - strong favorites stay on the favorite side; we attack exact score, not the outcome;
    - medium favorites may only be faded with real swing math;
    - balanced markets are where contrarian winner picks are allowed.
    """
    if not _is_comeback_mode(state, mode):
        return rows

    adjusted = [json.loads(json.dumps(row)) for row in rows]
    for row in adjusted:
        final = row.get("final_pick") or {}
        fair = row.get("fair_probabilities") or {}
        if row.get("status") != "ok" or not final or final.get("pick") == "draw" or not fair:
            continue

        favorite_side, favorite_probability = _favorite_side_from_fair(fair)
        draw_probability = float(fair.get("draw", 0.0) or 0.0)
        final_side = str(final.get("pick"))
        top_ev = _top_ev_for_row(row)
        ev_gap = top_ev - float(final.get("expected_points", 0.0) or 0.0)
        gain = float(final.get("p_gain_2plus", 0.0) or 0.0)
        loss = float(final.get("p_loss_2plus", 0.0) or 0.0)
        replacement: dict[str, Any] | None = None
        reason: str | None = None

        if favorite_probability >= 0.62 and final_side != favorite_side:
            replacement = _best_side_candidate(row, favorite_side, max_ev_gap=0.45)
            reason = "selective miracle: strong favorite protected; attack exact score, not random upset"
        elif favorite_probability >= 0.55 and final_side != favorite_side:
            credible_fade = gain >= 0.22 and loss <= 0.46 and ev_gap <= 0.45 and draw_probability >= 0.24
            if not credible_fade:
                replacement = _best_side_candidate(row, favorite_side, max_ev_gap=0.45)
                reason = "selective miracle: medium favorite fade rejected; not enough leverage for the risk"
        elif final_side != favorite_side:
            credible_swing = gain >= 0.18 and loss <= 0.52 and ev_gap <= 0.65 and draw_probability >= 0.24
            if credible_swing:
                row["tactical_posture"] = "selective_swing"
                row["selective_miracle_allowed"] = True
            else:
                replacement = _best_side_candidate(row, favorite_side, max_ev_gap=0.55) or row.get("ev_pick")
                reason = "selective miracle: underdog swing rejected; balanced-market math was not strong enough"
        else:
            row["tactical_posture"] = "favorite_exact_attack" if favorite_probability >= 0.62 else "clean_side_pick"

        if replacement and replacement.get("scoreline") != final.get("scoreline"):
            row["pre_selective_miracle_pick"] = final
            row["final_pick"] = replacement
            row["selective_miracle_adjusted"] = True
            row["tactical_posture"] = "favorite_exact_attack" if replacement.get("pick") == favorite_side else "clean_side_pick"
            row["selection_reason"] = reason or "selective miracle: cleaned up desperation pick"
    return adjusted


def apply_exact_score_chase(
    rows: list[dict[str, Any]], *, state: dict[str, Any] | None = None, mode: str = "controlled_attack", tournament_phase: str = "group_stage"
) -> list[dict[str, Any]]:
    """Upgrade low-upside same-side picks when the league state demands a chase.

    It does not turn favorites into random underdogs. It only swaps e.g. 1:0 into a
    nearby 2:0 / 2:1 / 3:0 / 4:0 style candidate when the EV cost is small enough. That is
    the correct kind of aggression for KickTipp: more exact-score upside, not hero-ball.
    """
    deficit = _state_float(state, "deficit", 0.0)
    if mode != "desperation" and not (mode == "controlled_attack" and deficit >= 8):
        return rows

    adjusted = [json.loads(json.dumps(row)) for row in rows]
    max_ev_cost = 0.30 if mode == "desperation" or deficit >= 12 else 0.22
    if tournament_phase == "group_stage" and mode != "desperation":
        max_ev_cost = min(max_ev_cost, 0.08)

    for row in adjusted:
        final = row.get("final_pick") or {}
        if row.get("status") != "ok" or final.get("pick") == "draw":
            continue
        fair = row.get("fair_probabilities") or {}
        favorite_probability = max(float(fair.get("home", 0.0)), float(fair.get("away", 0.0)))
        draw_probability = float(fair.get("draw", 0.0))
        current_total = _score_total(final)
        if tournament_phase == "group_stage" and mode != "desperation":
            # Group-stage chase is exact-score discipline, not panic. In balanced or
            # low-total matches, keep the market side score instead of inflating a 1:0
            # into 2:1 just because we are behind in the table.
            low_total_market = row.get("over_under") is not None and float(row.get("over_under") or 0.0) <= 2.0
            if favorite_probability < 0.58 or draw_probability >= 0.30 or low_total_market:
                continue
        current_margin = _score_margin(final)
        if favorite_probability >= 0.82:
            min_total = 3
            min_margin = 3
        elif favorite_probability >= 0.62:
            min_total = 2
            min_margin = 2
        else:
            min_total = 3
            min_margin = 1

        pool: list[dict[str, Any]] = []
        for key in ["ev_pick", "leverage_pick", "anti_field_pick", "anti_leader_pick", "best_non_draw_pick"]:
            candidate = row.get(key)
            if isinstance(candidate, dict):
                pool.append(candidate)
        pool.extend(candidate for candidate in row.get("top_candidates", []) if isinstance(candidate, dict))

        seen: set[str] = set()
        candidates: list[dict[str, Any]] = []
        for candidate in pool:
            scoreline_value = str(candidate.get("scoreline"))
            if scoreline_value in seen or not _same_side(candidate, final):
                continue
            seen.add(scoreline_value)
            if scoreline_value == final.get("scoreline"):
                continue
            ev_gap = float(final.get("expected_points", 0.0)) - float(candidate.get("expected_points", 0.0))
            if ev_gap > max_ev_cost:
                continue
            if _score_total(candidate) < max(min_total, current_total + 1):
                continue
            if _score_margin(candidate) < max(min_margin, current_margin):
                continue
            if not _is_sane_exact_chase_template(candidate, favorite_probability):
                continue
            if float(candidate.get("p_loss_2plus", 0.0)) > max(0.28, float(final.get("p_loss_2plus", 0.0)) + 0.16):
                continue
            candidates.append(candidate)

        if not candidates:
            continue
        replacement = max(candidates, key=_exact_chase_candidate_score)
        row["pre_exact_chase_pick"] = final
        row["final_pick"] = replacement
        row["exact_chase_adjusted"] = True
        row["selection_reason"] = (
            f"{mode}: comeback exact-score chase upgraded {final['scoreline']} to {replacement['scoreline']} "
            "without changing the match side"
        )
    return adjusted


def apply_market_ev_backtest_guard(
    rows: list[dict[str, Any]],
    *,
    state: dict[str, Any] | None = None,
    mode: str = "controlled_attack",
    max_ev_cost: float = 0.05,
) -> list[dict[str, Any]]:
    """Undo leverage/exact-score theatrics when they donate too much EV.

    The archived KickTipp backtest is the adult in the room: once the comeback layers
    have trailed the market-EV scoreline over a real sample, future sheets should use
    market EV as the default and only keep leverage tweaks that are essentially free.
    """
    if state and str(state.get("market_ev_guard", "on")).lower() in {"off", "false", "0", "no"}:
        return rows
    if not _is_comeback_mode(state, mode):
        return rows

    adjusted = [json.loads(json.dumps(row)) for row in rows]
    for row in adjusted:
        final = row.get("final_pick") or {}
        ev_pick = row.get("ev_pick") or {}
        if row.get("status") != "ok" or not final or not ev_pick:
            continue
        if final.get("scoreline") == ev_pick.get("scoreline"):
            continue
        ev_gap = float(ev_pick.get("expected_points", 0.0) or 0.0) - float(final.get("expected_points", 0.0) or 0.0)
        if ev_gap <= max_ev_cost:
            continue
        fair = row.get("fair_probabilities") or {}
        favorite_probability = max(float(fair.get("home", 0.0) or 0.0), float(fair.get("away", 0.0) or 0.0))
        draw_probability = float(fair.get("draw", 0.0) or 0.0)
        credible_balanced_swing = (
            str(final.get("pick")) != str(ev_pick.get("pick"))
            and favorite_probability <= 0.46
            and draw_probability >= 0.26
            and float(final.get("p_gain_2plus", 0.0) or 0.0) >= 0.22
            and float(final.get("p_loss_2plus", 0.0) or 0.0) <= 0.48
        )
        if credible_balanced_swing:
            row["market_ev_guard_skipped"] = "credible balanced-market swing"
            continue
        row["pre_market_ev_guard_pick"] = final
        row["final_pick"] = ev_pick
        row["market_ev_guard_adjusted"] = True
        row["selection_reason"] = (
            f"backtest guard: archived comeback picks lagged market-EV; kept {ev_pick['scoreline']} "
            f"instead of paying {ev_gap:.2f} EV for leverage"
        )
    return adjusted


def optimize_match(
    *,
    match: str,
    odds: Odds,
    over_under: float | None = None,
    field_predictions: list[Score] | None = None,
    leader_predictions: list[Score] | None = None,
    mode: str = "controlled_attack",
    tournament_phase: str = "group_stage",
    max_candidate_goals: int = 5,
) -> dict[str, Any]:
    home_lambda, away_lambda, fitted = fit_market_lambdas(odds, over_under=over_under)
    distribution = poisson_distribution(home_lambda, away_lambda)
    if field_predictions is None:
        field_predictions = estimate_public_field_predictions(odds, over_under=over_under)
    if leader_predictions is None:
        leader_predictions = estimate_leader_predictions(odds, over_under=over_under)
    candidates = rank_leverage_candidates(
        distribution,
        field_predictions=field_predictions,
        leader_predictions=leader_predictions,
        max_candidate_goals=max_candidate_goals,
    )
    top_ev = max(candidate.expected_points for candidate in candidates)
    rescored = [
        LeverageCandidate(
            **{**asdict(candidate), "composite_score": score_candidate(candidate, mode, top_ev, tournament_phase=tournament_phase)}
        )
        for candidate in candidates
    ]
    rescored.sort(key=lambda c: (c.composite_score, c.expected_points, c.edge_vs_field), reverse=True)

    ev_pick = max(rescored, key=lambda c: (c.expected_points, c.exact_probability))
    leverage_pick = max(rescored, key=lambda c: (c.p_gain_2plus, c.edge_vs_field, c.expected_points))
    anti_field_pick = max(rescored, key=lambda c: (c.edge_vs_field, c.expected_points))
    anti_leader_pick = max(rescored, key=lambda c: (c.edge_vs_leaders, -c.leader_correlation, c.expected_points))
    final = rescored[0]
    draw_pick = best_candidate(rescored, lambda c: c.pick == "draw")
    non_draw_pick = best_candidate(rescored, lambda c: c.pick != "draw")
    fair = fair_probabilities(odds)

    return {
        "match": match,
        "mode": mode,
        "tournament_phase": tournament_phase,
        "odds_decimal": {"home": odds.home, "draw": odds.draw, "away": odds.away},
        "fair_probabilities": fair,
        "fitted_probabilities": fitted,
        "fitted_lambdas": {"home": home_lambda, "away": away_lambda},
        "over_under": over_under,
        "estimated_field_predictions": [scoreline(score) for score in field_predictions],
        "estimated_leader_predictions": [scoreline(score) for score in leader_predictions],
        "ev_pick": candidate_to_dict(ev_pick),
        "leverage_pick": candidate_to_dict(leverage_pick),
        "anti_field_pick": candidate_to_dict(anti_field_pick),
        "anti_leader_pick": candidate_to_dict(anti_leader_pick),
        "best_draw_pick": candidate_to_dict(draw_pick),
        "best_non_draw_pick": candidate_to_dict(non_draw_pick),
        "final_pick": candidate_to_dict(final),
        "top_candidates": [candidate_to_dict(candidate) for candidate in rescored[:10]],
        "draw_budget_adjusted": False,
        "selection_reason": selection_reason(final, ev_pick, anti_field_pick, anti_leader_pick, mode),
    }


def selection_reason(
    final: LeverageCandidate,
    ev_pick: LeverageCandidate,
    anti_field_pick: LeverageCandidate,
    anti_leader_pick: LeverageCandidate,
    mode: str,
) -> str:
    if final.scoreline == ev_pick.scoreline:
        return f"{mode}: highest scoring-rule EV while staying acceptable versus the field"
    if final.scoreline == anti_leader_pick.scoreline:
        return f"{mode}: lower-correlation anti-leader pick with playable EV"
    if final.scoreline == anti_field_pick.scoreline:
        return f"{mode}: best edge against expected friend-field chalk"
    return f"{mode}: composite EV/leverage tradeoff beats raw favorite-chalk"


def slate_draw_target(draw_probabilities: list[float], *, min_draws: int | None = None, max_draw_share: float = 0.45) -> int:
    if not draw_probabilities:
        return 0
    expected_draws = sum(draw_probabilities)
    target = int(round(expected_draws))
    if expected_draws >= 0.8:
        target = max(1, target)
    if min_draws is not None:
        target = max(min_draws, target)
    cap = max(1, math.ceil(len(draw_probabilities) * max_draw_share))
    return max(0, min(target, cap, len(draw_probabilities)))


def apply_slate_draw_budget(
    reports: list[dict[str, Any]], *, target_draws: int | None = None, tournament_phase: str = "group_stage"
) -> list[dict[str, Any]]:
    if not reports:
        return reports
    adjusted = [json.loads(json.dumps(row)) for row in reports]
    if tournament_phase == "knockout":
        target_draws = 0
    if target_draws is None:
        target_draws = slate_draw_target([float(row.get("fair_probabilities", {}).get("draw", 0.0)) for row in adjusted])

    def final_is_draw(row: dict[str, Any]) -> bool:
        return (row.get("final_pick") or {}).get("pick") == "draw"

    current_draws = sum(1 for row in adjusted if final_is_draw(row))
    if current_draws < target_draws:
        promotable = []
        for idx, row in enumerate(adjusted):
            if final_is_draw(row) or not row.get("best_draw_pick"):
                continue
            final = row["final_pick"]
            draw = row["best_draw_pick"]
            ev_gap = final["expected_points"] - draw["expected_points"]
            if ev_gap > 0.60:
                continue
            if tournament_phase == "group_stage":
                # In group-stage mode the draw budget is a ceiling/opportunity scan, not
                # a religious quota. Promote a draw only when it is a near-EV pick and
                # does not lose more 2+ point scenarios than it gains. A 0:0 that is only
                # attractive because everyone else might pick the favorite is too cute.
                if ev_gap > 0.10:
                    continue
                if draw["p_loss_2plus"] > draw["p_gain_2plus"] + 0.02:
                    continue
                if draw["edge_vs_field"] < final.get("edge_vs_field", 0.0) - 0.10:
                    continue
            if draw["edge_vs_field"] < -0.45 and draw["p_loss_2plus"] > 0.30:
                continue
            pressure = draw["edge_vs_field"] + draw["p_gain_2plus"] - 0.35 * ev_gap
            promotable.append((pressure, idx))
        promotable.sort(reverse=True)
        for _pressure, idx in promotable[: target_draws - current_draws]:
            row = adjusted[idx]
            row["pre_budget_pick"] = row["final_pick"]
            row["final_pick"] = row["best_draw_pick"]
            row["draw_budget_adjusted"] = True
            row["selection_reason"] = f"slate draw budget promoted {row['final_pick']['scoreline']}; field likely underplays draws"
    elif current_draws > target_draws:
        demotable = []
        for idx, row in enumerate(adjusted):
            if not final_is_draw(row) or not row.get("best_non_draw_pick"):
                continue
            final = row["final_pick"]
            non_draw = row["best_non_draw_pick"]
            penalty = final["composite_score"] - non_draw["composite_score"]
            demotable.append((penalty, idx))
        demotable.sort()
        for _penalty, idx in demotable[: current_draws - target_draws]:
            row = adjusted[idx]
            row["pre_budget_pick"] = row["final_pick"]
            row["final_pick"] = row["best_non_draw_pick"]
            row["draw_budget_adjusted"] = True
            row["selection_reason"] = f"slate draw budget capped draws; switched to {row['final_pick']['scoreline']}"
    return adjusted


def choose_mode_from_state(state: dict[str, Any] | None) -> str:
    state = state or {}
    explicit = state.get("mode")
    if explicit in MODE_WEIGHTS:
        return str(explicit)

    def as_float(value: Any, default: float) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def as_int(value: Any, default: int) -> int:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    deficit_value = as_float(state.get("deficit"), 0.0)
    remaining_value = as_int(state.get("remaining_matches"), 999)
    spieltag_lead_value = as_float(state.get("spieltag_lead"), 0.0)

    if spieltag_lead_value >= 2 and remaining_value <= 3:
        return "protect_spieltag_win"
    if remaining_value <= 5 and deficit_value >= 6:
        return "desperation"
    if deficit_value >= 4:
        return "controlled_attack"
    if deficit_value <= 0:
        return "safe"
    return "balanced"


def load_kicktipp_context(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    context_path = Path(path)
    if not context_path.exists():
        return {}
    return json.loads(context_path.read_text(encoding="utf-8"))


def known_predictions_for_match(context: dict[str, Any], *, event_id: str | int | None = None, match: str | None = None) -> tuple[list[Score], list[Score]]:
    picks = context.get("known_picks") or []
    leader_names = set(context.get("leader_names") or [])
    field: list[Score] = []
    leaders: list[Score] = []
    for row in picks:
        row_event_id = row.get("event_id")
        row_match = row.get("match")
        has_event_id = row_event_id not in {None, "", "None"}
        if has_event_id:
            if event_id is None or str(row_event_id) != str(event_id):
                continue
        elif row_match and match:
            if normalize_match(str(row_match)) != normalize_match(match):
                continue
        elif event_id is not None or match:
            # A pick with neither event_id nor match cannot be safely attached to a
            # specific fixture. Better to ignore it than poison every slate.
            continue
        if not row.get("tip"):
            continue
        try:
            pick = parse_scoreline(row["tip"])
        except ValueError:
            continue
        field.append(pick)
        if row.get("is_leader") or row.get("player") in leader_names:
            leaders.append(pick)
    return field, leaders


def normalize_match(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def estimate_player_tendencies(rows: list[dict[str, Any]]) -> list[PlayerTendency]:
    by_player: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        player = row.get("player")
        tip = row.get("tip")
        if not player or not tip:
            continue
        by_player.setdefault(str(player), []).append(row)

    tendencies: list[PlayerTendency] = []
    for player, player_rows in sorted(by_player.items()):
        scores = []
        favorite_hits = 0
        favorite_known = 0
        for row in player_rows:
            try:
                scores.append(parse_scoreline(row["tip"]))
            except ValueError:
                continue
            favorite = row.get("favorite")
            if favorite in {"home", "away", "draw"}:
                favorite_known += 1
                if outcome_from_goals(*scores[-1]) == favorite:
                    favorite_hits += 1
        if not scores:
            continue
        tendencies.append(
            PlayerTendency(
                player=player,
                picks=len(scores),
                draw_rate=sum(1 for score in scores if score[0] == score[1]) / len(scores),
                favorite_rate=(favorite_hits / favorite_known) if favorite_known else None,
                exact_1_1_rate=sum(1 for score in scores if score == (1, 1)) / len(scores),
                average_goals=sum(sum(score) for score in scores) / len(scores),
                chaos_rate=sum(1 for score in scores if max(score) >= 4 or sum(score) >= 5) / len(scores),
            )
        )
    return tendencies
