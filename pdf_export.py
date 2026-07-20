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

    # cost breakdown of best
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Cost Breakdown (Recommended)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for label, val in [
        ("Freight", best["cost"]["freight"]),
        ("War-Risk Insurance", best["cost"]["war_ins"]),
        ("Cargo Insurance", best["cost"]["cargo_ins"]),
        ("Customs & Clearance", best["cost"]["customs"]),
        ("Security & Escort", best["cost"]["security"]),
        ("Delivery to Gold Souk", best["cost"]["last_mile"]),
        ("Port Waiting", best["cost"]["waiting"]),
    ]:
        pdf.cell(90, 6, label, border="B")
        pdf.cell(0, 6, f"${val:,.2f}", border="B", ln=True,
                 align="R")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 7, "TOTAL", border="B")
    pdf.cell(0, 7, f"${best['cost']['total']:,.2f}", border="B", ln=True, align="R")
    pdf.ln(4)

    # all options table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "All Route Options (ranked)", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(26, 37, 53)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(12, 7, "Rank", border=1, fill=True, align="C")
    pdf.cell(50, 7, "Route", border=1, fill=True)
    pdf.cell(30, 7, "Mode", border=1, fill=True)
    pdf.cell(35, 7, "Total USD", border=1, fill=True, align="R")
    pdf.cell(25, 7, "Transit h", border=1, fill=True, align="R")
    pdf.cell(0, 7, "Score", border=1, fill=True, align="R", ln=True)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    for r in feasible:
        pdf.cell(12, 6, str(r["rank"]), border=1, align="C")
        pdf.cell(50, 6, f"{meta.get('origin')}->{meta.get('port')[:12]}", border=1)
        pdf.cell(30, 6, r["mode"].title(), border=1)
        pdf.cell(35, 6, f"${r['cost']['total']:,.0f}", border=1, align="R")
        pdf.cell(25, 6, f"{r['transit_h']:.0f}", border=1, align="R")
        pdf.cell(0, 6, f"{r['cc_score']:.3f}", border=1, align="R", ln=True)

    pdf.ln(6)
    # ── Full study: why each alternative was NOT chosen ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(139, 38, 53)
    pdf.cell(0, 8, "Alternatives Analysed (not selected)", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    alts = [r for r in feasible if r["rank"] != 1]
    for r in alts:
        pdf.set_x(pdf.l_margin)
        diff = r["cost"]["total"] - best["cost"]["total"]
        slower = r["transit_h"] - best["transit_h"]
        reason = []
        if diff > 0:
            reason.append(f"${diff:,.0f} more expensive")
        if slower > 0:
            reason.append(f"{slower:.0f}h slower")
        if r["cc_score"] < best["cc_score"]:
            reason.append(f"lower score ({r['cc_score']:.3f} vs {best['cc_score']:.3f})")
        why = "; ".join(reason) if reason else "lower overall score"
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(0, 5,
            f"#{r['rank']} {r['mode'].title()} to {r['port']['en']}: "
            f"${r['cost']['total']:,.0f}, {r['transit_h']:.0f}h", border=0)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(110, 110, 110)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, f"Not chosen: {why}.", border=0)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(1)

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5,
        "Generated by Gold Route Optimizer (TOPSIS + AI). Freight, customs, security and "
        "port figures are realistic simulations; metal prices and weather are live where available. "
        "Proof-of-concept for academic research.")

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
