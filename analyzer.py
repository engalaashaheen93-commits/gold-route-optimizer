"""
Route Analyzer — builds every (origin × mode) option to a chosen Dubai port,
computes full landed cost (incl. war-risk + last-mile to Gold Souk),
and ranks them with TOPSIS.
"""
from typing import List, Dict, Any
from config import (ORIGINS, DEST_POINTS, MODES, WEIGHT_UNITS,
                    SECURE_CARRIERS, last_mile_cost)
from providers import (
    get_freight, get_customs, get_security, get_insurance,
    get_geopolitical, get_weather, get_port_wait,
)
from topsis import run_topsis, confidence_score


def compute_weight(qty: float, unit_key: str) -> dict:
    """Return gross kg and pure-content kg for a quantity in a given unit."""
    u = WEIGHT_UNITS[unit_key]
    grams_total = qty * u["grams"]
    gross_kg = grams_total / 1000.0
    pure_kg = gross_kg * u.get("purity", 0.9999)
    return {"gross_kg": round(gross_kg, 4), "pure_kg": round(pure_kg, 4)}


def analyze(
    origin_code: str,
    dest_port: str,
    value_usd: float,
    qty: float,
    unit_key: str,
    escort: bool,
    full_insurance: bool,
    urgency: str,          # 'normal' | 'express' | 'urgent'
    carrier: str = "TRANSGUARD",
) -> List[Dict[str, Any]]:
    """
    Build all mode options for the chosen origin → chosen UAE arrival point,
    comparing MODES (air/sea/multimodal). Last-mile secure delivery to the
    Dubai Gold Souk uses the chosen specialised carrier.
    """
    w = compute_weight(qty, unit_key)
    gross_kg = max(w["gross_kg"], 0.001)

    o = ORIGINS[origin_code]
    port = DEST_POINTS[dest_port]
    lm = last_mile_cost(dest_port, carrier, value_usd)

    # urgency multipliers
    if urgency == "urgent":
        freight_mult, time_mult = 1.45, 0.75
    elif urgency == "express":
        freight_mult, time_mult = 1.15, 0.9
    else:
        freight_mult, time_mult = 1.0, 1.0

    # a port that is air-type only makes sense for air; sea ports for sea/multi.
    # We still compute all modes but flag feasibility.
    options = []
    for mode in MODES:
        fr = get_freight(origin_code, gross_kg, mode)
        cust = get_customs(o["country"], value_usd, gross_kg)
        sec = get_security(origin_code, escort, value_usd)
        ins = get_insurance(value_usd, full_insurance, origin_code)
        geo = get_geopolitical(origin_code)
        wx = get_weather(o["city"])
        wait = get_port_wait(dest_port)

        freight_cost = fr["freight_usd"] * freight_mult
        transit_h = fr["transit_h"] * time_mult + wait["wait_h"]

        last_mile = lm["cost_usd"]
        waiting_cost = wait["wait_h"] * 120

        total = (freight_cost + cust["total_usd"] + sec["escort_usd"]
                 + ins["cargo_usd"] + ins["war_usd"] + last_mile + waiting_cost)

        # feasibility: air port can't take sea; sea port can't take pure air
        feasible = True
        if port["type"] == "air" and mode == "sea":
            feasible = False
        if port["type"] == "sea" and mode == "air":
            feasible = False

        metrics = {
            "shipping_cost": freight_cost,
            "insurance":     ins["cargo_usd"],
            "customs":       cust["total_usd"],
            "security":      sec["risk_score"] * 10000,
            "transit_time":  transit_h,
            "war_risk":      ins["war_usd"],
            "weather_risk":  wx["score"] * 5000,
            "geopolitical":  geo["score"] * 5000,
            "last_mile":     last_mile,
        }

        options.append({
            "origin_code": origin_code,
            "origin":      o,
            "dest_port":   dest_port,
            "port":        port,
            "mode":        mode,
            "feasible":    feasible,
            "weather":     wx,
            "geo":         geo,
            "weight":      w,
            "carrier":     carrier,
            "last_mile_km": lm["km"],
            "market_pressure": fr["market_pressure"],
            "metrics":     metrics,
            "cost": {
                "freight":   round(freight_cost, 2),
                "customs":   round(cust["total_usd"], 2),
                "security":  round(sec["escort_usd"], 2),
                "cargo_ins": round(ins["cargo_usd"], 2),
                "war_ins":   round(ins["war_usd"], 2),
                "last_mile": round(last_mile, 2),
                "waiting":   round(waiting_cost, 2),
                "total":     round(total, 2),
                "per_kg":    round(freight_cost / gross_kg, 2),
            },
            "transit_h": round(transit_h, 1),
        })

    # keep feasible ones for ranking; if none feasible, keep all
    feasible_opts = [o for o in options if o["feasible"]] or options
    ranked = run_topsis(feasible_opts)
    for r in ranked:
        r["confidence"] = confidence_score(r)

    # attach any infeasible options at the end (not ranked)
    infeasible = [o for o in options if not o["feasible"]]
    for o in infeasible:
        o["cc_score"] = 0.0
        o["rank"] = len(ranked) + 1
    return ranked + infeasible
