"""
Route Analyzer.

Given ONE origin and the user's preferred sea port + preferred airport,
build the realistic options:
  • SEA  → preferred sea port
  • AIR  → preferred airport
  • MULTIMODAL → preferred sea port (sea leg dominant)
Compute full landed cost (freight + customs + tier security + tier insurance
+ war-risk + secure last-mile to Gold Souk + waiting), then rank with TOPSIS
and return best-first. The winner tells us BOTH the mode AND the arrival point.
"""
from typing import List, Dict, Any
from config import (ORIGINS, DEST_POINTS, WEIGHT_UNITS,
                    SECURE_CARRIERS, last_mile_cost, tier_security,
                    tier_insurance, select_tier)
from providers import (
    get_freight, get_customs, get_insurance,
    get_geopolitical, get_weather, get_port_wait,
)
from topsis import run_topsis, confidence_score


def compute_weight(qty: float, unit_key: str) -> dict:
    u = WEIGHT_UNITS[unit_key]
    grams_total = qty * u["grams"]
    gross_kg = grams_total / 1000.0
    pure_kg = gross_kg * u.get("purity", 0.9999)
    return {"gross_kg": round(gross_kg, 4), "pure_kg": round(pure_kg, 4)}


def analyze(
    origin_code: str,
    pref_port: str,        # preferred SEA port  (JEA/RAS/HAM)
    pref_airport: str,     # preferred AIRPORT   (DXB/SHJ/AUH)
    value_usd: float,
    qty: float,
    unit_key: str,
    escort: bool,
    full_insurance: bool,
    urgency: str,
    carrier: str = "TRANSGUARD",
) -> List[Dict[str, Any]]:

    w = compute_weight(qty, unit_key)
    gross_kg = max(w["gross_kg"], 0.001)
    o = ORIGINS[origin_code]
    tier = select_tier(value_usd, escort, full_insurance)

    if urgency == "urgent":
        freight_mult, time_mult = 1.45, 0.75
    elif urgency == "express":
        freight_mult, time_mult = 1.15, 0.9
    else:
        freight_mult, time_mult = 1.0, 1.0

    # define the option set: (mode, destination point)
    plans = [
        ("sea",        pref_port),
        ("air",        pref_airport),
        ("multimodal", pref_port),
    ]

    options = []
    for mode, dest_code in plans:
        dest = DEST_POINTS[dest_code]
        fr = get_freight(origin_code, gross_kg, mode)
        cust = get_customs(o["country"], value_usd, gross_kg)
        ins_war = get_insurance(value_usd, full_insurance, origin_code)  # for war-risk only
        geo = get_geopolitical(origin_code)
        wx = get_weather(o["city"])
        wait = get_port_wait(dest_code)

        # tier-based costs
        sec = tier_security(gross_kg, tier)
        cargo_ins = tier_insurance(value_usd, tier)
        lm = last_mile_cost(dest_code, carrier, value_usd, tier)

        freight_cost = fr["freight_usd"] * freight_mult
        transit_h = fr["transit_h"] * time_mult + wait["wait_h"]
        waiting_cost = wait["wait_h"] * 120

        total = (freight_cost + cust["total_usd"] + sec["security_usd"]
                 + cargo_ins + ins_war["war_usd"] + lm["cost_usd"] + waiting_cost)

        metrics = {
            "shipping_cost": freight_cost,
            "insurance":     cargo_ins,
            "customs":       cust["total_usd"],
            "security":      sec["security_usd"],
            "transit_time":  transit_h,
            "war_risk":      ins_war["war_usd"],
            "weather_risk":  wx["score"] * 5000,
            "geopolitical":  geo["score"] * 5000,
            "last_mile":     lm["cost_usd"],
        }

        options.append({
            "origin_code": origin_code,
            "origin":      o,
            "dest_code":   dest_code,
            "port":        dest,
            "dest_type":   dest["type"],
            "mode":        mode,
            "feasible":    True,
            "tier":        tier,
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
                "security":  round(sec["security_usd"], 2),
                "cargo_ins": round(cargo_ins, 2),
                "war_ins":   round(ins_war["war_usd"], 2),
                "last_mile": round(lm["cost_usd"], 2),
                "waiting":   round(waiting_cost, 2),
                "total":     round(total, 2),
                "per_kg":    round(freight_cost / gross_kg, 2),
            },
            "transit_h": round(transit_h, 1),
        })

    ranked = run_topsis(options)
    for r in ranked:
        r["confidence"] = confidence_score(r)
    return ranked
