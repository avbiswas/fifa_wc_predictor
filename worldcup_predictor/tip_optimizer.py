from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Odds:
    home: float
    draw: float
    away: float


@dataclass(frozen=True)
class Tip:
    pick: str
    home_goals: int
    away_goals: int
    reason: str

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}:{self.away_goals}"


@dataclass(frozen=True)
class TipCandidate:
    scoreline: str
    pick: str
    expected_points: float
    exact_probability: float
    outcome_probability: float


@dataclass(frozen=True)
class ScoreRules:
    exact: int = 4
    goal_difference: int = 3
    tendency: int = 2


def fair_probabilities(odds: Odds) -> dict[str, float]:
    implied = {
        "home": 1 / odds.home,
        "draw": 1 / odds.draw,
        "away": 1 / odds.away,
    }
    overround = sum(implied.values())
    return {key: value / overround for key, value in implied.items()}


def american_to_decimal(value: int | float | str) -> float:
    if isinstance(value, str):
        value = value.strip().replace("+", "")
    number = float(value)
    if number > 0:
        return 1 + number / 100
    return 1 + 100 / abs(number)


def poisson_distribution(home_lambda: float, away_lambda: float, max_goals: int = 8) -> dict[tuple[int, int], float]:
    scores: dict[tuple[int, int], float] = {}
    total = 0.0
    for home_goals in range(max_goals + 1):
        home_prob = math.exp(-home_lambda) * home_lambda ** home_goals / math.factorial(home_goals)
        for away_goals in range(max_goals + 1):
            away_prob = math.exp(-away_lambda) * away_lambda ** away_goals / math.factorial(away_goals)
            probability = home_prob * away_prob
            scores[(home_goals, away_goals)] = probability
            total += probability
    return {score: probability / total for score, probability in scores.items()}


def distribution_outcome_probabilities(distribution: dict[tuple[int, int], float]) -> dict[str, float]:
    probs = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for score, probability in distribution.items():
        probs[outcome_from_goals(*score)] += probability
    return probs


def fit_market_lambdas(
    odds: Odds,
    *,
    over_under: float | None = None,
    max_goals: int = 8,
) -> tuple[float, float, dict[str, float]]:
    target = fair_probabilities(odds)
    target_total = over_under if over_under and over_under > 0 else 2.5
    best: tuple[float, float, float, dict[str, float]] | None = None
    for home_step in range(20, 421, 5):
        home_lambda = home_step / 100
        for away_step in range(20, 421, 5):
            away_lambda = away_step / 100
            distribution = poisson_distribution(home_lambda, away_lambda, max_goals=max_goals)
            probs = distribution_outcome_probabilities(distribution)
            loss = (
                6.0 * sum((probs[key] - target[key]) ** 2 for key in target)
                + 0.45 * ((home_lambda + away_lambda - target_total) / max(target_total, 0.1)) ** 2
            )
            if best is None or loss < best[0]:
                best = (loss, home_lambda, away_lambda, probs)
    assert best is not None
    return best[1], best[2], best[3]


def expected_tip_points(
    predicted: tuple[int, int],
    distribution: dict[tuple[int, int], float],
    rules: ScoreRules | None = None,
) -> float:
    return sum(probability * score_tip(predicted, actual, rules) for actual, probability in distribution.items())


def ranked_market_tips(
    odds: Odds,
    *,
    over_under: float | None = None,
    rules: ScoreRules | None = None,
    max_candidate_goals: int = 5,
    limit: int = 6,
) -> list[TipCandidate]:
    rules = rules or ScoreRules()
    home_lambda, away_lambda, _fitted_probs = fit_market_lambdas(odds, over_under=over_under)
    distribution = poisson_distribution(home_lambda, away_lambda)
    outcome_probs = distribution_outcome_probabilities(distribution)
    candidates: list[TipCandidate] = []
    for home in range(max_candidate_goals + 1):
        for away in range(max_candidate_goals + 1):
            pick = outcome_from_goals(home, away)
            candidates.append(
                TipCandidate(
                    scoreline=f"{home}:{away}",
                    pick=pick,
                    expected_points=expected_tip_points((home, away), distribution, rules),
                    exact_probability=distribution.get((home, away), 0.0),
                    outcome_probability=outcome_probs[pick],
                )
            )
    candidates.sort(key=lambda c: (c.expected_points, c.exact_probability), reverse=True)
    return candidates[:limit]


def risk_tier(top_candidates: list[TipCandidate]) -> str:
    if not top_candidates:
        return "unknown"
    top = top_candidates[0]
    second = top_candidates[1] if len(top_candidates) > 1 else None
    gap = top.expected_points - (second.expected_points if second else 0.0)
    if top.expected_points >= 1.85 and gap >= 0.12:
        return "strong"
    if top.expected_points >= 1.55 and gap >= 0.06:
        return "normal"
    if top.expected_points >= 1.25:
        return "thin_edge"
    return "chaos"


def exploit_engine_tip(
    odds: Odds,
    *,
    over_under: float | None = None,
    draw_floor: float = 0.22,
    draw_favorite_ceiling: float = 0.65,
    rules: ScoreRules | None = None,
) -> Tip:
    """KickTipp-specific baseline: market EV with an empirical draw-trap layer.

    The early tournament sample punished favorite scorelines whenever draw probability
    was live and the favorite was not clearly above ~65%. This is not betting advice;
    it is scoring-rule exploitation for 2/3/4-point friend leagues. The full private-
    league decision layer lives in ``leverage_optimizer.py``.
    """
    fair = fair_probabilities(odds)
    favorite_prob = max(fair["home"], fair["away"])
    if fair["draw"] >= draw_floor and favorite_prob < draw_favorite_ceiling:
        return Tip(
            pick="draw",
            home_goals=1,
            away_goals=1,
            reason=(
                f"draw trap override: fair draw {fair['draw']:.1%}, favorite only {favorite_prob:.1%}; "
                "1:1 maximizes survival under the current draw-heavy tournament pattern"
            ),
        )
    return market_optimal_tip(odds, over_under=over_under, rules=rules)


def war_machine_tip(
    odds: Odds,
    *,
    over_under: float | None = None,
    draw_floor: float = 0.22,
    draw_favorite_ceiling: float = 0.65,
    rules: ScoreRules | None = None,
) -> Tip:
    """Backward-compatible alias for ``exploit_engine_tip``."""
    return exploit_engine_tip(
        odds,
        over_under=over_under,
        draw_floor=draw_floor,
        draw_favorite_ceiling=draw_favorite_ceiling,
        rules=rules,
    )


def market_optimal_tip(
    odds: Odds,
    *,
    over_under: float | None = None,
    rules: ScoreRules | None = None,
    max_candidate_goals: int = 5,
) -> Tip:
    rules = rules or ScoreRules()
    home_lambda, away_lambda, fitted_probs = fit_market_lambdas(odds, over_under=over_under)
    distribution = poisson_distribution(home_lambda, away_lambda)
    candidates = [(home, away) for home in range(max_candidate_goals + 1) for away in range(max_candidate_goals + 1)]
    best_score = max(
        candidates,
        key=lambda score: (
            expected_tip_points(score, distribution, rules),
            -abs(score[0] + score[1] - (over_under or home_lambda + away_lambda)),
            -(score[0] + score[1]),
        ),
    )
    expected = expected_tip_points(best_score, distribution, rules)
    pick = outcome_from_goals(*best_score)
    return Tip(
        pick=pick,
        home_goals=best_score[0],
        away_goals=best_score[1],
        reason=(
            f"market EV {expected:.2f} pts; fitted λ={home_lambda:.2f}-{away_lambda:.2f}; "
            f"1X2={fitted_probs['home']:.1%}/{fitted_probs['draw']:.1%}/{fitted_probs['away']:.1%}"
        ),
    )


def outcome_from_goals(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "home"
    if away_goals > home_goals:
        return "away"
    return "draw"


def score_tip(predicted: tuple[int, int], actual: tuple[int, int], rules: ScoreRules | None = None) -> int:
    rules = rules or ScoreRules()
    if predicted == actual:
        return rules.exact
    predicted_outcome = outcome_from_goals(*predicted)
    actual_outcome = outcome_from_goals(*actual)
    if predicted_outcome != actual_outcome:
        return 0
    if predicted_outcome == "draw":
        # The KickTipp-style table gives draws only Tendenz (2) unless exact (4).
        # There is no Tordifferenz bonus for non-exact draws.
        return rules.tendency
    if predicted[0] - predicted[1] == actual[0] - actual[1]:
        return rules.goal_difference
    return rules.tendency


def draw_guard_tip(odds: Odds, *, draw_floor: float = 0.20, mega_favorite_floor: float = 0.88) -> Tip:
    """Odds-only tip-round heuristic.

    Betting markets are good at 1X2 tendencies but poor for friend tip rounds where
    exact scoreline EV matters. If the fair draw probability is high enough and no
    team is a mega favorite, the 1:1 line is the boring-but-profitable hedge.
    """
    probs = fair_probabilities(odds)
    favorite = max(("home", probs["home"]), ("away", probs["away"]), key=lambda item: item[1])
    favorite_side, favorite_prob = favorite

    if probs["draw"] >= draw_floor and favorite_prob < mega_favorite_floor:
        return Tip(
            pick="draw",
            home_goals=1,
            away_goals=1,
            reason=f"fair draw probability {probs['draw']:.1%} is high and favorite is not mega-safe ({favorite_prob:.1%})",
        )

    if favorite_side == "home":
        if favorite_prob >= 0.85:
            return Tip("home", 3, 0, f"home mega favorite {favorite_prob:.1%}")
        if favorite_prob >= 0.70:
            return Tip("home", 2, 0, f"home strong favorite {favorite_prob:.1%}")
        return Tip("home", 2, 1, f"home favorite {favorite_prob:.1%}")

    if favorite_prob >= 0.85:
        return Tip("away", 0, 3, f"away mega favorite {favorite_prob:.1%}")
    if favorite_prob >= 0.70:
        return Tip("away", 0, 2, f"away strong favorite {favorite_prob:.1%}")
    return Tip("away", 1, 2, f"away favorite {favorite_prob:.1%}")
