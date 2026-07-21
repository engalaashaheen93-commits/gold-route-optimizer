"""
Route Analyzer — door-to-door optimisation.

Given ONE origin, the system automatically tries:
  • every UAE arrival point (3 airports + 3 sea ports)
  • direct legs AND one-transit-hub legs (transshipment)
  • all 4 secure carriers for the inland leg to the Gold Souk
and picks the cheapest complete door-to-door journey overall.

Each option = international freight + (optional) transit + inland secure
transport + tier insurance + tier security + war-risk + waiting.
Ranked by TOPSIS. Insurance/security use the agreed 3-tier model.
"""
from typing import List, Dict, Any
from config import (ORIGINS, DEST_POINTS, WEIGHT_UNITS, SECURE_CARRIERS,
                    TRANSIT_SEA, TRANSIT_AIR, SECURITY_TIERS, AED,
                    GEO_RISK, NODE_CITY,
                    last_mile_cost, tier_security, tier_insurance, select_tier)
from providers import (get_freight, get_customs, get_insurance,
                       get_geopolitical, get_weather, get_port_wait)
from topsis import run_topsis, confidence_score


def compute_weight(qty: float, unit_key: str) -> dict:
    u = WEIGHT_UNITS[unit_key]
    grams_total = qty * u["grams"]
    gross_kg = grams_total / 1000.0
    pure_kg = gross_kg * u.get("purity", 0.9999)
    return {"gross_kg": round(gross_kg, 4), "pure_kg": round(pure_kg, 4)}


def _cheapest_carrier(dest_code, value_usd, tier):
    """Pick the cheapest secure carrier for the inland leg to the Souk."""
    best_key, best_lm = None, None
    for ck in SECURE_CARRIERS:
        lm = last_mile_cost(dest_code, ck, value_usd, tier)
        if best_lm is None or lm["cost_usd"] < best_lm["cost_usd"]:
            best_key, best_lm = ck, lm
    return best_key, best_lm


def _node_name(code):
    """Human name for any routing node (origin/hub/dest)."""
    for src in (ORIGINS, DEST_POINTS, TRANSIT_SEA, TRANSIT_AIR):
        if code in src:
            return src[code].get("en", code)
    return code


def analyze(
    origin_code: str,
    value_usd: float,
    qty: float,
    unit_key: str,
    escort: bool,
    full_insurance: bool,
    urgency: str,
    carrier_mode: str = "auto",   # "auto" = try all & pick cheapest, or a specific key
) -> List[Dict[str, Any]]:

    w = compute_weight(qty, unit_key)
    gross_kg = max(w["gross_kg"], 0.001)
    o = ORIGINS[origin_code]
    tier = select_tier(value_usd, escort, full_insurance)

    if urgency == "urgent":
        fmult, tmult = 1.45, 0.75
    elif urgency == "express":
        fmult, tmult = 1.15, 0.9
    else:
        fmult, tmult = 1.0, 1.0

    cust = get_customs(o["country"], value_usd, gross_kg)
    ins_war = get_insurance(value_usd, full_insurance, origin_code)
    geo = get_geopolitical(origin_code)
    wx = get_weather(o["city"])
    cargo_ins = tier_insurance(value_usd, tier)
    sec = tier_security(gross_kg, tier)

    options = []

    # airports vs sea ports in the UAE
    air_points = [k for k, v in DEST_POINTS.items() if v["type"] == "air"]
    sea_points = [k for k, v in DEST_POINTS.items() if v["type"] == "sea"]

    def build(mode, dest_code, transit=None):
        """Create one door-to-door option."""
        dest = DEST_POINTS[dest_code]
        wait = get_port_wait(dest_code)

        # ── collect the nodes this route passes through ──
        nodes = [origin_code]
        if transit:
            nodes.append(transit)
        nodes.append(dest_code)

        # ── hazard detection: geopolitical + severe weather ──
        hazards = []
        geo_max = 0.0
        wx_max = wx["score"]
        for nd in nodes:
            g = GEO_RISK.get(nd, 0.2)
            geo_max = max(geo_max, g)
            if g >= 0.40:
                nm = _node_name(nd)
                hazards.append({"type": "geo", "level": "high" if g >= 0.5 else "med",
                                "where": nm})
            # live weather at this node
            city = NODE_CITY.get(nd)
            if city:
                w2 = get_weather(city)
                wx_max = max(wx_max, w2["score"])
                if w2["score"] >= 0.55:
                    hazards.append({"type": "weather", "level": "high",
                                    "where": _node_name(nd)})
                elif w2["score"] >= 0.30 and w2["level"] == "med":
                    hazards.append({"type": "weather", "level": "med",
                                    "where": _node_name(nd)})

        # international freight (live via Freightos where possible)
        fr = get_freight(origin_code, gross_kg, mode)
        freight_cost = fr["freight_usd"] * fmult
        transit_h = fr["transit_h"] * tmult

        # add a transit-hub leg penalty (extra handling + time) if used
        if transit:
            freight_cost *= 1.18          # re-consolidation surcharge
            transit_h += 36 if mode == "sea" else 8

        transit_h += wait["wait_h"]

        # inland secure transport — cheapest carrier (or fixed)
        if carrier_mode == "auto":
            carrier, lm = _cheapest_carrier(dest_code, value_usd, tier)
        else:
            carrier = carrier_mode
            lm = last_mile_cost(dest_code, carrier, value_usd, tier)

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
            "weather_risk":  wx_max * 5000,
            "geopolitical":  geo_max * 5000,
            "last_mile":     lm["cost_usd"],
        }

        # route label
        hub_txt = ""
        if transit:
            hub = (TRANSIT_AIR if mode == "air" else TRANSIT_SEA).get(transit, {})
            hub_txt = f" via {hub.get('en','?')}"

        return {
            "origin_code": origin_code, "origin": o,
            "dest_code": dest_code, "port": dest, "dest_type": dest["type"],
            "mode": mode, "transit": transit, "hub_txt": hub_txt,
            "feasible": True, "tier": tier, "weather": wx, "geo": geo,
            "weight": w, "carrier": carrier, "last_mile_km": lm["km"],
            "freight_source": fr.get("source", "mock"),
            "freight_range": fr.get("live_range"),
            "market_pressure": fr["market_pressure"],
            "metrics": metrics,
            "hazards": hazards,
            "geo_risk": round(geo_max, 2),
            "wx_risk": round(wx_max, 2),
            "cost": {
                "freight": round(freight_cost, 2), "customs": round(cust["total_usd"], 2),
                "security": round(sec["security_usd"], 2), "cargo_ins": round(cargo_ins, 2),
                "war_ins": round(ins_war["war_usd"], 2), "last_mile": round(lm["cost_usd"], 2),
                "waiting": round(waiting_cost, 2), "total": round(total, 2),
                "per_kg": round(freight_cost / gross_kg, 2),
            },
            "transit_h": round(transit_h, 1),
        }

    # ── DIRECT routes ──
    for dc in air_points:
        options.append(build("air", dc))
    for dc in sea_points:
        options.append(build("sea", dc))
        options.append(build("multimodal", dc))

    # ── VIA-TRANSIT routes (one hub) ──
    for hub in TRANSIT_AIR:
        if hub == origin_code:
            continue
        for dc in air_points:
            options.append(build("air", dc, transit=hub))
    for hub in TRANSIT_SEA:
        if hub == origin_code:
            continue
        for dc in sea_points:
            options.append(build("sea", dc, transit=hub))

    ranked = run_topsis(options)
    for r in ranked:
        r["confidence"] = confidence_score(r)
    # keep the meaningful top set for display (all still available)
    return ranked
