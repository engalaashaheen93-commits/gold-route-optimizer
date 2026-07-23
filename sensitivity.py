"""
sensitivity.py — Robustness analysis for the AI-GSCO decision model.

Purpose
-------
The model's external validation is limited (no historical log of expert
shipping decisions is available). Sensitivity analysis provides an
*internal* form of validation instead: rather than asking "is this
decision correct?", it asks "is this decision STABLE?".

It re-runs the TOPSIS ranking many times under systematically perturbed
conditions and measures how often the originally recommended route still
comes first. A recommendation that survives most perturbations is robust;
one that flips easily is fragile and should be flagged to the user.

Three perturbation families are applied:
  1. WEIGHTS  — each criterion weight is shifted +/- a percentage,
                then all weights are renormalised to sum to 1.
  2. COST     — total landed cost is scaled up/down (freight-market swings).
  3. TIME     — transit time is scaled up/down (congestion, delays).

Everything here is deterministic and reproducible: the scenario grid is
fixed, not random, so the same shipment always yields the same robustness
figure — which matters for a result quoted in a thesis.
"""
import math
import copy
from config import TOPSIS_WEIGHTS

CRITERIA = list(TOPSIS_WEIGHTS.keys())


# ══════════════════════════════════════════════════════════════════
# A self-contained TOPSIS that accepts an arbitrary weight vector.
# (topsis.run_topsis reads the global weights; here we need to vary them.)
# ══════════════════════════════════════════════════════════════════
def _rank_with(metrics_list: list, weights: dict) -> int:
    """
    Rank the option set with the given weights and return the INDEX of the
    winner. metrics_list is a list of dicts (one per route).
    All criteria are cost-type: lower is better.
    """
    n = len(metrics_list)
    if n == 0:
        return -1
    if n == 1:
        return 0

    matrix = [[m[c] for c in CRITERIA] for m in metrics_list]

    # vector normalisation
    norms = []
    for j in range(len(CRITERIA)):
        col = [row[j] for row in matrix]
        norms.append(math.sqrt(sum(v * v for v in col)) or 1.0)

    w = [weights[c] for c in CRITERIA]
    weighted = [[(matrix[i][j] / norms[j]) * w[j] for j in range(len(CRITERIA))]
                for i in range(n)]

    ideal_best = [min(row[j] for row in weighted) for j in range(len(CRITERIA))]
    ideal_worst = [max(row[j] for row in weighted) for j in range(len(CRITERIA))]

    best_idx, best_cc = 0, -1.0
    for i in range(n):
        d_b = math.sqrt(sum((weighted[i][j] - ideal_best[j]) ** 2
                            for j in range(len(CRITERIA))))
        d_w = math.sqrt(sum((weighted[i][j] - ideal_worst[j]) ** 2
                            for j in range(len(CRITERIA))))
        cc = d_w / (d_b + d_w) if (d_b + d_w) else 0.0
        if cc > best_cc:
            best_cc, best_idx = cc, i
    return best_idx


def _renormalise(weights: dict) -> dict:
    """Scale weights so they sum to 1.0 (TOPSIS requires a normalised vector)."""
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


# ══════════════════════════════════════════════════════════════════
# Scenario generation
# ══════════════════════════════════════════════════════════════════
def _weight_scenarios(deltas=(0.10, 0.20)):
    """
    Vary ONE criterion at a time by +/- delta, renormalising the rest.
    This isolates the influence of each individual weight.
    """
    out = []
    for c in CRITERIA:
        for d in deltas:
            for sign in (+1, -1):
                w = dict(TOPSIS_WEIGHTS)
                w[c] = max(w[c] * (1 + sign * d), 1e-6)
                out.append((f"weight:{c}{'+' if sign > 0 else '-'}{int(d*100)}%",
                            _renormalise(w)))
    return out


def _metric_scenarios(scales=(0.80, 0.90, 1.10, 1.20)):
    """Scale total_cost or transit_time across ALL routes."""
    out = []
    for s in scales:
        out.append((f"cost x{s:.2f}", "total_cost", s))
        out.append((f"time x{s:.2f}", "transit_time", s))
    return out


# ══════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════
def analyse(ranked: list) -> dict:
    """
    Run the full robustness grid on an already-ranked route list.

    Returns a dict with:
      total_scenarios  — how many perturbations were tested
      wins             — how many kept the original winner in first place
      robustness       — wins / total (0..1)
      flips            — list of scenarios that changed the winner,
                         each with the route that displaced it
      by_family        — robustness broken down by perturbation type
      verdict          — 'high' | 'moderate' | 'fragile'
    """
    feasible = [r for r in ranked if r.get("feasible", True)]
    if len(feasible) < 2:
        return {"total_scenarios": 0, "wins": 0, "robustness": 1.0,
                "flips": [], "by_family": {}, "verdict": "high"}

    base_metrics = [r["metrics"] for r in feasible]
    base_winner = 0          # feasible is already sorted, so index 0 is the winner

    def label(r):
        hub = (r.get("hub_txt") or "").replace(" via ", "via ")
        svc = ("D2D" if r.get("service") == "door_to_door"
               else "D2A" if r.get("service") == "door_to_airport" else "")
        port = r.get("port", {}).get("en", "?")
        return f"{r['mode'].title()} {svc} -> {port}{(' (' + hub + ')') if hub else ''}".strip()

    results = []          # (family, scenario_name, winner_index)

    # ── family 1: weight perturbations ──
    for name, w in _weight_scenarios():
        results.append(("weights", name, _rank_with(base_metrics, w)))

    # ── families 2 & 3: metric perturbations ──
    for name, key, scale in _metric_scenarios():
        pert = []
        for m in base_metrics:
            mm = dict(m)
            mm[key] = mm[key] * scale
            pert.append(mm)
        fam = "cost" if key == "total_cost" else "time"
        results.append((fam, name, _rank_with(pert, TOPSIS_WEIGHTS)))

    # ── tally ──
    wins = sum(1 for _, _, idx in results if idx == base_winner)
    total = len(results)

    flips = []
    for fam, name, idx in results:
        if idx != base_winner and 0 <= idx < len(feasible):
            flips.append({
                "scenario": name,
                "family": fam,
                "new_winner": label(feasible[idx]),
                "new_cost": feasible[idx]["cost"]["total"],
                "new_time": feasible[idx]["transit_h"],
            })

    by_family = {}
    for fam in ("weights", "cost", "time"):
        subset = [r for r in results if r[0] == fam]
        if subset:
            w_ = sum(1 for _, _, idx in subset if idx == base_winner)
            by_family[fam] = {"wins": w_, "total": len(subset),
                              "pct": round(100.0 * w_ / len(subset), 1)}

    robustness = wins / total if total else 1.0
    verdict = ("high" if robustness >= 0.80
               else "moderate" if robustness >= 0.60
               else "fragile")

    return {
        "total_scenarios": total,
        "wins": wins,
        "robustness": round(robustness, 4),
        "robustness_pct": round(100.0 * robustness, 1),
        "flips": flips,
        "by_family": by_family,
        "verdict": verdict,
        "winner_label": label(feasible[base_winner]),
    }


def margin_analysis(ranked: list) -> dict:
    """
    How decisive is the win? Compares the recommended route with the runner-up
    on score, cost and time.

    A high robustness figure can hide a razor-thin score gap, so this is
    reported alongside it: robustness says the decision is stable, margin says
    how comfortable it is.
    """
    feasible = [r for r in ranked if r.get("feasible", True)]
    if len(feasible) < 2:
        return {}
    first, second = feasible[0], feasible[1]
    gap = first["cc_score"] - second["cc_score"]
    return {
        "score_first": first["cc_score"],
        "score_second": second["cc_score"],
        "score_gap": round(gap, 4),
        "score_gap_pct": round(100.0 * gap / (first["cc_score"] or 1), 2),
        "cost_gap": round(second["cost"]["total"] - first["cost"]["total"], 2),
        "time_gap": round(second["transit_h"] - first["transit_h"], 1),
        "decisive": gap >= 0.02,
    }


def breakeven_cost(ranked: list, max_scale: float = 3.0, step: float = 0.01):
    """
    How far can the recommended route's OWN cost rise before it loses first
    place? Returns the multiplier (e.g. 1.35 = it tolerates a 35% cost rise),
    or None if it survives the whole tested span.

    This answers a question a supervisor is likely to ask directly:
    "how much margin does this recommendation actually have?"
    """
    feasible = [r for r in ranked if r.get("feasible", True)]
    if len(feasible) < 2:
        return None

    base_metrics = [r["metrics"] for r in feasible]
    scale = 1.0
    while scale <= max_scale:
        scale = round(scale + step, 4)
        pert = []
        for i, m in enumerate(base_metrics):
            mm = dict(m)
            if i == 0:                       # only the winner gets more expensive
                mm["total_cost"] = mm["total_cost"] * scale
            pert.append(mm)
        if _rank_with(pert, TOPSIS_WEIGHTS) != 0:
            return scale
    return None
