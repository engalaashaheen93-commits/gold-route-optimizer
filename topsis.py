"""
TOPSIS — Technique for Order of Preference by Similarity to Ideal Solution.
All 9 criteria are 'cost' type (lower is better).
"""
import math
from config import TOPSIS_WEIGHTS

CRITERIA = list(TOPSIS_WEIGHTS.keys())


def run_topsis(options: list) -> list:
    """Rank options (each has ['metrics'] dict). Returns sorted list, best first."""
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
    weights = [TOPSIS_WEIGHTS[c] for c in CRITERIA]
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
    safest = min(ranked, key=lambda r: r["metrics"]["security"] + r["metrics"]["war_risk"])
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
