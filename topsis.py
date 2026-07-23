"""
TOPSIS — Technique for Order of Preference by Similarity to Ideal Solution.
All 9 criteria are 'cost' type (lower is better).
"""
import math
from config import TOPSIS_WEIGHTS

CRITERIA = list(TOPSIS_WEIGHTS.keys())


def run_topsis(options: list, weights_override: dict | None = None) -> list:
    """
    Rank options (each has ['metrics'] dict). Returns sorted list, best first.

    weights_override lets a caller supply a different weight vector — used when
    the weights are derived from the user's stated priority rather than taken
    from the defaults. It must contain every criterion and sum to 1.
    """
    W = weights_override if weights_override else TOPSIS_WEIGHTS
    if not options:
        return []
    if len(options) == 1:
        options[0]["cc_score"] = 1.0
        options[0]["rank"] = 1
        _assign_badges(options)
        return options

    # 1) decision matrix
    matrix = [[opt["metrics"][c] for c in CRITERIA] for opt in options]

    # 2) vector normalisation
    norms = []
    for j in range(len(CRITERIA)):
        col = [row[j] for row in matrix]
        denom = math.sqrt(sum(v * v for v in col)) or 1.0
        norms.append(denom)
    norm_matrix = [[matrix[i][j] / norms[j] for j in range(len(CRITERIA))]
                   for i in range(len(matrix))]

    # 3) weighted
    weights = [W[c] for c in CRITERIA]
    weighted = [[norm_matrix[i][j] * weights[j] for j in range(len(CRITERIA))]
                for i in range(len(matrix))]

    # 4) ideal best / worst  (all cost → best = min, worst = max)
    ideal_best = [min(row[j] for row in weighted) for j in range(len(CRITERIA))]
    ideal_worst = [max(row[j] for row in weighted) for j in range(len(CRITERIA))]

    # 5) distances + 6) closeness
    for i, opt in enumerate(options):
        d_best = math.sqrt(sum((weighted[i][j] - ideal_best[j]) ** 2
                               for j in range(len(CRITERIA))))
        d_worst = math.sqrt(sum((weighted[i][j] - ideal_worst[j]) ** 2
                                for j in range(len(CRITERIA))))
        cc = d_worst / (d_best + d_worst) if (d_best + d_worst) else 0.0
        opt["cc_score"] = round(cc, 4)
        opt["_d_best"] = d_best
        opt["_d_worst"] = d_worst

        # ── per-criterion transparency ──
        # For each criterion: how good is this option relative to the best and
        # worst value observed on that criterion (1 = best, 0 = worst), plus the
        # weighted contribution it makes to the final score.
        detail = {}
        for j, cname in enumerate(CRITERIA):
            col = [row[j] for row in matrix]
            lo, hi = min(col), max(col)
            raw = matrix[i][j]
            # all criteria are cost-type → lower is better
            rel = 1.0 if hi == lo else (hi - raw) / (hi - lo)
            detail[cname] = {
                "raw": raw,
                "score": round(rel, 4),                       # 0..1, higher = better
                "weight": W[cname],
                "weighted": round(rel * W[cname], 4),
                "best": lo, "worst": hi,
            }
        opt["criteria_detail"] = detail
        opt["weighted_sum"] = round(sum(d["weighted"] for d in detail.values()), 4)

    ranked = sorted(options, key=lambda o: o["cc_score"], reverse=True)
    for i, opt in enumerate(ranked):
        opt["rank"] = i + 1
    _assign_badges(ranked)
    return ranked


def _assign_badges(ranked: list):
    """Tag cheapest / fastest / safest for UI highlights."""
    if not ranked:
        return
    cheapest = min(ranked, key=lambda r: r["cost"]["total"])
    fastest = min(ranked, key=lambda r: r["transit_h"])
    safest = min(ranked, key=lambda r: (r["metrics"]["geopolitical"]
                                        + r["metrics"]["weather_risk"]
                                        + r["metrics"]["war_risk"]))
    for r in ranked:
        r["badges"] = []
    cheapest["badges"].append("cheapest")
    fastest["badges"].append("fastest")
    safest["badges"].append("safest")
    ranked[0]["badges"].append("best")


def confidence_score(opt: dict) -> int:
    """Confidence 0..100 from separation between best and worst distance."""
    db = opt.get("_d_best", 0)
    dw = opt.get("_d_worst", 0)
    if (db + dw) == 0:
        return 50
    sep = abs(dw - db) / (db + dw)
    return int(round(50 + sep * 50))
