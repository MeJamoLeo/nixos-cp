"""Faithful port of AtCoder Problems Recommendation.

Source: kenkoooo/AtCoderProblems frontend (master)
  - src/pages/UserPage/Recommendations/RecommendProblems.ts
  - src/utils/ProblemModelUtil.ts  (predictSolveProbability)
  - src/utils/RatingInfo.ts        (internalRating)

Output matches the "Recommendation" tab of AtCoder Problems.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

OPTIONS: dict[str, dict[str, float]] = {
    "easy":      {"target": 0.8, "lower": 0.5,        "upper": math.inf},
    "moderate":  {"target": 0.5, "lower": 0.2,        "upper": 0.8},
    "difficult": {"target": 0.2, "lower": -math.inf,  "upper": 0.5},
}


def compute_internal_rating(
    latest_rating: float,
    participation_count: int,
) -> float | None:
    """Port of utils/RatingInfo.ts."""
    if participation_count <= 0 or latest_rating <= 0:
        return None
    if latest_rating <= 400:
        before = 400 * (1 - math.log(400 / latest_rating))
    else:
        before = float(latest_rating)
    adj = (
        (math.sqrt(1 - 0.9 ** (2 * participation_count))
         / (1 - 0.9 ** participation_count) - 1)
        / (math.sqrt(19) - 1)
    ) * 1200
    return before + adj


def participation_count_from_history(rating_history: list[dict]) -> int:
    return sum(1 for r in rating_history if r.get("IsRated"))


def _raw_difficulty(model: dict) -> float | None:
    """Reverse the lower-bound clipping AtCoder Problems applies to display difficulty.

    rawDifficulty == difficulty for difficulty >= 400.
    For difficulty < 400, the displayed value is 400 / exp((400 - raw)/400);
    inverting:  raw = 400 - 400 * ln(400 / difficulty).
    """
    d = model.get("difficulty")
    if d is None:
        return None
    if d >= 400:
        return float(d)
    if d <= 0:
        return None
    return 400 - 400 * math.log(400 / d)


def predict_solve_probability(model: dict, internal_rating: float) -> float:
    raw = _raw_difficulty(model)
    disc = model.get("discrimination")
    if raw is None or disc is None:
        return -1.0
    return 1.0 / (1.0 + math.exp(-disc * (internal_rating - raw)))


def recommend(
    *,
    problems: Iterable[dict],
    problem_models: dict[str, dict],
    submitted_ids: set[str],
    internal_rating: float | None,
    option: str = "moderate",
    num: int = 10,
    include_experimental: bool = True,
) -> list[dict]:
    if internal_rating is None or option not in OPTIONS:
        return []
    cfg = OPTIONS[option]
    scored: list[tuple[dict, dict, float]] = []
    for p in problems:
        pid = p.get("id") or p.get("problem_id")
        if not pid or pid in submitted_ids:
            continue
        model = problem_models.get(pid)
        if not model:
            continue
        if model.get("is_experimental") and not include_experimental:
            continue
        prob = predict_solve_probability(model, internal_rating)
        if prob < cfg["lower"] or prob >= cfg["upper"]:
            continue
        scored.append((p, model, prob))

    # 1. sort by |prob - target| ascending, take top N
    scored.sort(key=lambda t: abs(t[2] - cfg["target"]))
    scored = scored[:num]
    # 2. re-sort by difficulty descending (matches frontend display order)
    scored.sort(key=lambda t: (t[1].get("difficulty") or 0), reverse=True)

    out: list[dict] = []
    for p, model, prob in scored:
        pid = p.get("id") or p["problem_id"]
        cid = p.get("contest_id", "")
        out.append({
            "problem_id": pid,
            "contest_id": cid,
            "title": p.get("title", ""),
            "difficulty": int(model.get("difficulty") or 0),
            "is_experimental": bool(model.get("is_experimental", False)),
            "predicted_probability": round(prob, 4),
            "url": f"https://atcoder.jp/contests/{cid}/tasks/{pid}",
        })
    return out


def recommend_all(
    *,
    problems: Iterable[dict],
    problem_models: dict[str, dict],
    submitted_ids: set[str],
    internal_rating: float | None,
    num: int = 10,
    include_experimental: bool = True,
) -> dict[str, list[dict]]:
    """Compute all three buckets at once."""
    problems_list = list(problems)
    return {
        opt: recommend(
            problems=problems_list,
            problem_models=problem_models,
            submitted_ids=submitted_ids,
            internal_rating=internal_rating,
            option=opt,
            num=num,
            include_experimental=include_experimental,
        )
        for opt in OPTIONS
    }
