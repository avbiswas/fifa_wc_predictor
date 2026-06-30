from __future__ import annotations

import os
from typing import Literal

import dspy

from .paths import MODEL


class NewsSummary(dspy.Signature):
    """Summarize match-relevant news for a football prediction model."""

    match: str = dspy.InputField()
    news_items: str = dspy.InputField(desc="Search results with title, source, date, url, and text snippets.")
    summary: str = dspy.OutputField(desc="Concise bullet summary of injuries, tactical news, form, suspensions, and uncertainty.")


class MatchPredictor(dspy.Module):
    def __init__(self, team1: str, team2: str, allow_draw: bool = True):
        super().__init__()
        choice_values = (team1, team2, "Draw") if allow_draw else (team1, team2)
        choices = Literal.__getitem__(choice_values)
        choice_text = ", ".join(choice_values)
        scoreline_desc = (
            f"Predicted final scoreline in the format '{team1} X-Y {team2}', where X and Y are the "
            "goals you expect each side to score after 90 minutes. Derive the goal counts from the evidence; do not "
            "default to a common scoreline unless the evidence specifically supports it."
        )
        if not allow_draw:
            scoreline_desc = (
                f"Predicted knockout scoreline in the format '{team1} X-Y {team2}', where X and Y are the "
                "goals you expect each side to score after 90 or 120 minutes. You must also pick a winner. "
                "If you keep the scoreline tied and pick a winner, that means you predict the winner advances on penalties. "
                "Derive the goal counts from the evidence; do not default to a common scoreline unless the evidence specifically supports it."
            )
        predict_match = dspy.Signature(
            {
                "match": (str, dspy.InputField()),
                "match_context": (str, dspy.InputField()),
                "news_summary": (str, dspy.InputField()),
                "team1_squad": (str, dspy.InputField()),
                "team2_squad": (str, dspy.InputField()),
                "recent_record": (str, dspy.InputField()),
                "performance_history": (str, dspy.InputField(desc="The model's own last five scored match predictions and points.")),
                "polymarket_odds": (str, dspy.InputField()),
                "prediction": (choices, dspy.OutputField(desc=f"Must be exactly one of: {choice_text}.")),
                "scoreline": (
                    str,
                    dspy.OutputField(desc=scoreline_desc),
                ),
                "goal_scorers": (
                    str,
                    dspy.OutputField(desc="Exactly three comma-separated players most likely to score a goal."),
                ),
                "confidence": (float, dspy.OutputField(desc="Probability-like confidence from 0.0 to 1.0.")),
                "rationale": (str, dspy.OutputField(desc="Brief evidence-based reasoning.")),
            },
            "Predict the result of a FIFA World Cup match from available evidence.",
        )

        self.predict = dspy.ChainOfThought(predict_match)

    def forward(
        self,
        match: str,
        match_context: str,
        news_summary: str,
        team1_squad: str,
        team2_squad: str,
        recent_record: str,
        performance_history: str,
        polymarket_odds: str,
    ):
        return self.predict(
            match=match,
            match_context=match_context,
            news_summary=news_summary,
            team1_squad=team1_squad,
            team2_squad=team2_squad,
            recent_record=recent_record,
            performance_history=performance_history,
            polymarket_odds=polymarket_odds,
        )

    async def aforward(
        self,
        match: str,
        match_context: str,
        news_summary: str,
        team1_squad: str,
        team2_squad: str,
        recent_record: str,
        performance_history: str,
        polymarket_odds: str,
    ):
        return await self.predict.acall(
            match=match,
            match_context=match_context,
            news_summary=news_summary,
            team1_squad=team1_squad,
            team2_squad=team2_squad,
            recent_record=recent_record,
            performance_history=performance_history,
            polymarket_odds=polymarket_odds,
        )


def make_lm(model: str) -> dspy.LM:
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY is not set. Add it to .env or .envrc.")
    temperature = 1.0 if model.startswith("openrouter/openai/gpt-5") else 0.7
    max_tokens = 16000
    return dspy.LM(
        model,
        temperature=temperature,
        max_tokens=max_tokens,
        cache=False,
        extra_headers={
            "HTTP-Referer": "http://localhost/world_cup",
            "X-Title": "world-cup-predictor",
        },
    )


def configure_dspy(model: str = MODEL) -> dspy.LM:
    lm = make_lm(model)
    dspy.configure(lm=lm, cache=False)
    return lm


def summarize_news(match_name: str, news_text: str) -> str:
    return dspy.ChainOfThought(NewsSummary)(match=match_name, news_items=news_text).summary
