"""
PDF report generator (English) for the ranked route analysis.
"""
from fpdf import FPDF


def generate_pdf(ranked: list, meta: dict) -> bytes:
    feasible = [r for r in ranked if r.get("feasible", True)]
    best = feasible[0]

    pdf = FPDF()
    pdf.add_page()

    # header
    pdf.set_fill_color(26, 37, 53)
    pdf.set_text_color(201, 168, 76)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 14, "Gold Route Optimizer - Analysis Report", ln=True)
    pdf.set_draw_color(201, 168, 76)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # shipment meta
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Shipment", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [
        ("Origin", meta.get("origin", "-")),
        ("UAE Arrival", meta.get("port", "-")),
        ("Metal", meta.get("metal", "-")),
        ("Secure Carrier", meta.get("carrier", "-")),
        ("Value (USD)", f"${meta.get('value_usd',0):,.0f}"),
        ("Departure", meta.get("depart", "-")),
        ("Arrival", meta.get("arrive", "-")),
    ]:
        pdf.cell(45, 6, f"{label}:", border=0)
        pdf.cell(0, 6, str(val), ln=True)
    pdf.ln(3)

    # recommended
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 120, 60)
    pdf.cell(0, 8, "Recommended Route", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6,
        f"{meta.get('origin')} -> {meta.get('port')} via {best['mode'].title()}  |  "
        f"TOPSIS score {best['cc_score']}  |  Total ${best['cost']['total']:,.0f}  |  "
        f"{best['transit_h']:.0f}h transit  |  Confidence {best.get('confidence',0)}%")
    pdf.ln(3)

    # ── Risk alerts ──
    hz = best.get("hazards", [])
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(139, 38, 53)
    pdf.cell(0, 8, "Risk Alerts", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.l_margin)
    if hz:
        for h in hz:
            kind = "Severe weather" if h["type"] == "weather" else "Geopolitical risk"
            lvl = "HIGH" if h["level"] == "high" else "MODERATE"
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, f"- [{lvl}] {kind} at {h['where']}")
    else:
        pdf.multi_cell(0, 5, "No significant hazards on the recommended route.")
    pdf.ln(3)

    # ── Data sources transparency ──
    best_src = best.get("freight_source", "mock")
    freight_live = best_src == "live"
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(139, 38, 53)
    pdf.cell(0, 8, "Data Sources", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5,
        "LIVE (free public sources): "
        + ("freight rates via Freightos; " if freight_live else "")
        + "metal spot prices via gold-api.com; weather via Open-Meteo.")
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5,
        "Simulated (calibrated estimates): "
        + ("" if freight_live else "freight rates; ")
        + "customs, security, cargo & war-risk insurance, port waiting, and the inland secure-"
        "transport rates of the four carriers (Transguard, Brink's, Loomis, Erbay). Precise "
        "carrier pricing is confidential and quoted per shipment, so realistic estimates were "
        "used. Commercial live-data providers for freight (SeaRates, Freightos subscription "
        "tiers, Shanghai Shipping Exchange) require paid subscriptions, which is consistent "
        "with the data-privacy challenge noted by Sun et al. (2025).")
    pdf.ln(3)

    # ── Security tier explanation ──
    tier = best.get("tier", "medium")
    tier_names = {"low": "Low", "medium": "Medium", "high": "High"}
    tier_rates = {"low": "0.15%", "medium": "0.25%", "high": "0.45%"}
    tier_why = {
        "low": "gold/silver, organised delivery, no special escort",
        "medium": "higher value or full insurance selected",
        "high": "armed escort selected or shipment value >= $5M",
    }
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(139, 38, 53)
    pdf.cell(0, 8, "Security Tier Applied", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5,
        f"Tier: {tier_names.get(tier,tier)} (auto-selected because {tier_why.get(tier,'')}). "
        f"This tier sets the cargo-insurance rate at {tier_rates.get(tier,'')} of shipment value, "
        f"plus fixed security and per-kg handling fees. Insurance and security scale with this tier.")
    pdf.ln(3)

    # cost breakdown of best — WITH formulas
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Cost Breakdown with Calculations (Recommended)", ln=True)
    calc = best.get("calc", {})
    rows = [
        ("Freight", best["cost"]["freight"], calc.get("freight", "")),
        ("War-Risk Insurance", best["cost"]["war_ins"], calc.get("war_ins", "")),
        ("Cargo Insurance", best["cost"]["cargo_ins"], calc.get("cargo_ins", "")),
        ("Customs & Clearance", best["cost"]["customs"], calc.get("customs", "")),
        ("Security & Escort", best["cost"]["security"], calc.get("security", "")),
        ("Delivery to Gold Souk", best["cost"]["last_mile"], calc.get("last_mile", "")),
        ("Port Waiting", best["cost"]["waiting"], calc.get("waiting", "")),
    ]
    for label, val, formula in rows:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(70, 6, label, border="B")
        pdf.cell(30, 6, f"${val:,.2f}", border="B", align="R")
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(110, 110, 110)
        pdf.multi_cell(0, 6, f"= {formula}" if formula else "", border="B")
        pdf.set_text_color(30, 30, 30)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(70, 7, "TOTAL", border="B")
    pdf.cell(30, 7, f"${best['cost']['total']:,.2f}", border="B", align="R", ln=True)
    pdf.ln(4)

    # all options table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "All Route Options (ranked)", ln=True)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(26, 37, 53)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(8, 7, "#", border=1, fill=True, align="C")
    pdf.cell(27, 7, "Arrival", border=1, fill=True)
    pdf.cell(22, 7, "Via hub", border=1, fill=True)
    pdf.cell(17, 7, "Mode", border=1, fill=True)
    pdf.cell(26, 7, "Service", border=1, fill=True)
    pdf.cell(24, 7, "Total USD", border=1, fill=True, align="R")
    pdf.cell(14, 7, "Hours", border=1, fill=True, align="R")
    pdf.cell(17, 7, "War risk", border=1, fill=True, align="C")
    pdf.cell(20, 7, "Weather", border=1, fill=True, align="C")
    pdf.cell(0, 7, "Score", border=1, fill=True, align="R", ln=True)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 7)
    SVC = {"door_to_door": "Door-to-Door", "door_to_airport": "Door-to-Airport"}
    for r in feasible:
        arrival = r.get("port", {}).get("en", "-")
        hub = r.get("hub_txt", "").replace(" via ", "") or "Direct"
        svc = SVC.get(r.get("service"), "-")
        # risk flags for THIS route
        hzs = r.get("hazards", [])
        geo_hz = [h for h in hzs if h["type"] == "geo"]
        wx_hz = [h for h in hzs if h["type"] == "weather"]
        war_txt = (f"{geo_hz[0]['level'].upper()}" if geo_hz else "none")
        wx_txt = (f"{wx_hz[0]['level'].upper()} {wx_hz[0]['where'][:6]}" if wx_hz else "clear")
        pdf.cell(8, 6, str(r["rank"]), border=1, align="C")
        pdf.cell(27, 6, arrival[:16], border=1)
        pdf.cell(22, 6, hub[:12], border=1)
        pdf.cell(17, 6, r["mode"].title()[:9], border=1)
        pdf.cell(26, 6, svc[:15], border=1)
        pdf.cell(24, 6, f"${r['cost']['total']:,.0f}", border=1, align="R")
        pdf.cell(14, 6, f"{r['transit_h']:.0f}", border=1, align="R")
        pdf.cell(17, 6, war_txt[:9], border=1, align="C")
        pdf.cell(20, 6, wx_txt[:12], border=1, align="C")
        pdf.cell(0, 6, f"{r['cc_score']:.3f}", border=1, align="R", ln=True)

    pdf.ln(6)
    # ── Robustness / sensitivity analysis ──
    try:
        import sensitivity as _sens
        _s = _sens.analyse(feasible)
        _m = _sens.margin_analysis(feasible)
        _be = _sens.breakeven_cost(feasible)
    except Exception:
        _s = None

    if _s and _s.get("total_scenarios"):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(139, 38, 53)
        pdf.cell(0, 8, "Decision Robustness (Sensitivity Analysis)", ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5,
            "External validation against historical expert decisions was not possible, as no "
            "accessible log of past shipping choices exists. Robustness analysis provides an "
            "internal alternative: instead of asking whether the decision is correct, it asks "
            "whether it is STABLE. The ranking is recomputed under systematically perturbed "
            "conditions, and the share of scenarios in which the recommended route remains "
            "first is reported below.")
        pdf.ln(2)

        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7,
            f"The recommended route stayed first in {_s['wins']} of "
            f"{_s['total_scenarios']} scenarios  ({_s['robustness_pct']}%) - "
            f"{_s['verdict'].upper()}")
        pdf.ln(1)

        # per-family table
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(26, 37, 53)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(pdf.l_margin)
        pdf.cell(70, 6, "Perturbation family", border=1, fill=True)
        pdf.cell(35, 6, "Scenarios", border=1, fill=True, align="C")
        pdf.cell(35, 6, "Stayed first", border=1, fill=True, align="C")
        pdf.cell(0, 6, "Share", border=1, fill=True, align="R", ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        FAM = {"weights": "Criterion weights +/-10%, +/-20%",
               "cost": "Total cost +/-10%, +/-20%",
               "time": "Transit time +/-10%, +/-20%"}
        for fam, lbl in FAM.items():
            d = _s["by_family"].get(fam)
            if not d:
                continue
            pdf.set_x(pdf.l_margin)
            pdf.cell(70, 6, lbl, border=1)
            pdf.cell(35, 6, str(d["total"]), border=1, align="C")
            pdf.cell(35, 6, str(d["wins"]), border=1, align="C")
            pdf.cell(0, 6, f"{d['pct']}%", border=1, align="R", ln=True)
        pdf.ln(3)

        # margin + break-even
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Margin over the runner-up", ln=True)
        pdf.set_font("Helvetica", "", 9)
        if _m:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5,
                f"Score {_m['score_first']:.4f} vs {_m['score_second']:.4f} "
                f"(gap {_m['score_gap']:.4f}); the runner-up costs "
                f"${_m['cost_gap']:,.0f} more and takes {_m['time_gap']:.0f}h longer. "
                + ("The gap is decisive."
                   if _m["decisive"] else
                   "The gap is narrow, so the top two routes are near-equivalent and the "
                   "choice between them may reasonably rest on factors outside the model."))
        if _be:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5,
                f"Break-even: the recommended route keeps first place until its own total "
                f"cost rises by approximately {(_be-1)*100:.0f}%.")
        else:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5,
                "Break-even: the recommended route holds first place across the entire "
                "tested cost range.")

        if _s["flips"]:
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"Scenarios that changed the winner ({len(_s['flips'])})", ln=True)
            pdf.set_font("Helvetica", "", 8)
            for f in _s["flips"][:15]:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 5,
                    f"  {f['scenario']}  ->  {f['new_winner']} "
                    f"(${f['new_cost']:,.0f}, {f['new_time']:.0f}h)")

    # ── How each route earned its score (per-criterion breakdown) ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(139, 38, 53)
    pdf.cell(0, 8, "How Each Route Earned Its Score", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5,
        "Each criterion is scored 0 to 1 (1 = best value observed among all routes, "
        "0 = worst), then multiplied by its weight. The weighted values are summed, and "
        "TOPSIS converts the result into the final closeness score used for ranking.")
    pdf.ln(2)

    # ── compact overview: every route's weighted contributions on one line ──
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(26, 37, 53)
    pdf.set_text_color(255, 255, 255)
    pdf.set_x(pdf.l_margin)
    pdf.cell(9, 6, "#", border=1, fill=True, align="C")
    pdf.cell(52, 6, "Route", border=1, fill=True)
    pdf.cell(21, 6, "Cost 46%", border=1, fill=True, align="C")
    pdf.cell(21, 6, "Time 30%", border=1, fill=True, align="C")
    pdf.cell(18, 6, "Geo 9%", border=1, fill=True, align="C")
    pdf.cell(19, 6, "Wx 9%", border=1, fill=True, align="C")
    pdf.cell(18, 6, "War 6%", border=1, fill=True, align="C")
    pdf.cell(0, 6, "Score", border=1, fill=True, align="R", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 7)
    for r in feasible:
        d = r.get("criteria_detail", {})
        if not d:
            continue
        hub = r.get("hub_txt", "").replace(" via ", "via ") or "Direct"
        svc = "D2D" if r.get("service") == "door_to_door" else (
              "D2A" if r.get("service") == "door_to_airport" else "-")
        label = f"{r['mode'].title()} {svc} {r['port']['en']} ({hub})"
        pdf.set_x(pdf.l_margin)
        pdf.cell(9, 5, str(r["rank"]), border=1, align="C")
        pdf.cell(52, 5, label[:34], border=1)
        pdf.cell(21, 5, f"{d['total_cost']['weighted']:.3f}", border=1, align="C")
        pdf.cell(21, 5, f"{d['transit_time']['weighted']:.3f}", border=1, align="C")
        pdf.cell(18, 5, f"{d['geopolitical']['weighted']:.3f}", border=1, align="C")
        pdf.cell(19, 5, f"{d['weather_risk']['weighted']:.3f}", border=1, align="C")
        pdf.cell(18, 5, f"{d['war_risk']['weighted']:.3f}", border=1, align="C")
        pdf.cell(0, 5, f"{r['cc_score']:.3f}", border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(139, 38, 53)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 7, "Detailed scoring per route", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.ln(1)

    CRIT_LABEL = {
        "total_cost": "Total cost", "transit_time": "Transit time",
        "war_risk": "War risk", "geopolitical": "Geopolitical", "weather_risk": "Weather",
    }
    for r in feasible:      # every route gets its own scoring table
        det = r.get("criteria_detail", {})
        if not det:
            continue
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(245, 238, 226)
        hub = r.get("hub_txt", "").replace(" via ", "via ") or "Direct"
        pdf.multi_cell(0, 6,
            f"#{r['rank']}  {r['mode'].title()} {hub} -> {r['port']['en']} "
            f"[{SVC.get(r.get('service'),'-')}]  |  ${r['cost']['total']:,.0f}  |  "
            f"{r['transit_h']:.0f}h  |  final score {r['cc_score']:.3f}",
            border=0, fill=True)
        # header row
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(38, 5, "Criterion", border=1)
        pdf.cell(30, 5, "Raw value", border=1, align="R")
        pdf.cell(22, 5, "Score", border=1, align="C")
        pdf.cell(20, 5, "Weight", border=1, align="C")
        pdf.cell(0, 5, "Weighted", border=1, align="R", ln=True)
        pdf.set_font("Helvetica", "", 7)
        for cname, d in det.items():
            raw = d["raw"]
            raw_txt = (f"${raw:,.0f}" if cname in ("total_cost", "war_risk")
                       else (f"{raw:,.0f} h" if cname == "transit_time" else f"{raw:,.0f}"))
            pdf.set_x(pdf.l_margin)
            pdf.cell(38, 5, CRIT_LABEL.get(cname, cname), border=1)
            pdf.cell(30, 5, raw_txt, border=1, align="R")
            pdf.cell(22, 5, f"{d['score']:.3f}", border=1, align="C")
            pdf.cell(20, 5, f"{int(d['weight']*100)}%", border=1, align="C")
            pdf.cell(0, 5, f"{d['weighted']:.4f}", border=1, align="R", ln=True)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(110, 5, "Weighted sum", border=1)
        pdf.cell(0, 5, f"{r.get('weighted_sum',0):.4f}", border=1, align="R", ln=True)
        # route-specific hazards
        hzs = r.get("hazards", [])
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(110, 110, 110)
        if hzs:
            txt = "; ".join(
                f"{'Weather' if h['type']=='weather' else 'Geopolitical'} "
                f"({h['level']}) at {h['where']}" for h in hzs)
            pdf.multi_cell(0, 5, f"Risk flags: {txt}")
        else:
            pdf.multi_cell(0, 5, "Risk flags: none on this route.")
        pdf.set_text_color(30, 30, 30)
        pdf.ln(2)

    pdf.ln(4)
    # highlighted precious-metals cost-structure note
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(245, 235, 220)
    pdf.set_text_color(110, 30, 42)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, 5,
        "Note: base freight is inherently low for small, high-value parcels; the bulk of the "
        "cost lies in insurance and security - a defining characteristic of precious-metals "
        "logistics.", border=1, fill=True)
    pdf.ln(3)

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "Generated by Gold Route Optimizer (TOPSIS + AI). Freight, customs, security and "
        "port figures are realistic simulations; metal prices and weather are live where available. "
        "Proof-of-concept for academic research.")

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
