"""
Gold Route Optimizer — bilingual (EN/AR) Streamlit app.
Compares every origin×mode to a chosen Dubai port using TOPSIS.
"""
import streamlit as st
from datetime import date, timedelta
import plotly.graph_objects as go

from config import (ORIGINS, DEST_POINTS, METALS, WEIGHT_UNITS, APP_MODE,
                    DEFAULT_LANG, TOPSIS_WEIGHTS, SECURE_CARRIERS, t, name_of)
DUBAI_PORTS = DEST_POINTS
from analyzer import analyze, compute_weight
from providers import get_metal_price
from claude_advisor import build_recommendation

st.set_page_config(page_title="Gold Route Optimizer", page_icon="⚡", layout="wide")

# ── language state ────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = DEFAULT_LANG
LANG = st.session_state.lang
RTL = LANG == "ar"
DIR = "rtl" if RTL else "ltr"
ALIGN = "right" if RTL else "left"

# ── global CSS (theme + direction) ────────────────────────────────
st.markdown(f"""
<style>
/* ─── Gold & Burgundy theme ─── */
.stApp {{ background:radial-gradient(ellipse at top,#1A1410 0%,#0D0A08 60%); }}
section.main > div {{ direction:{DIR}; text-align:{ALIGN}; }}
h1,h2,h3,h4,h5,p,div,span,label {{ color:#F0E6D2; }}
.block-container {{ padding-top:1rem; }}

/* inputs */
.stSelectbox div[data-baseweb="select"] > div,
.stNumberInput input, .stDateInput input {{
  background:#241812 !important; border:1px solid #3D2419 !important; color:#F0E6D2 !important; }}
[data-testid="stSidebar"] {{ background:#140F0B; border-{'left' if not RTL else 'right'}:1px solid #3D2419; }}

/* metals ticker */
@keyframes scroll-{ 'rtl' if RTL else 'ltr' } {{
  0%   {{ transform: translateX({'-100%' if RTL else '0'}); }}
  100% {{ transform: translateX({'0' if RTL else '-100%'}); }}
}}
.ticker-wrap {{ overflow:hidden;
  background:linear-gradient(90deg,#241812,#1A1410,#241812);
  border-top:2px solid #C9A24B; border-bottom:2px solid #6E1E2A;
  padding:8px 0; margin:6px 0 14px 0; white-space:nowrap; }}
.ticker {{ display:inline-block; animation: scroll-{ 'rtl' if RTL else 'ltr' } 30s linear infinite;
  white-space:nowrap; }}
.ticker span {{ margin:0 28px; font-size:15px; font-weight:600; }}

.badge {{ display:inline-block; padding:2px 9px; border-radius:10px; font-size:11px;
  font-weight:700; margin:0 3px; }}
.hero {{ background:linear-gradient(135deg,#3D2419 0%,#241812 55%,#1A1410 100%);
  border:1px solid #8B6F3A; border-radius:14px; padding:18px 22px; margin-bottom:12px;
  box-shadow:0 4px 20px rgba(110,30,42,0.25); }}
.route-card {{ background:linear-gradient(135deg,#241812,#1A1410);
  border:1px solid #3D2419; border-radius:12px; padding:14px 16px; margin:8px 0; }}
.route-best {{ border:2px solid #C9A24B;
  box-shadow:0 0 22px rgba(201,162,75,0.22); background:linear-gradient(135deg,#2E1D12,#241812); }}
.kpi {{ background:linear-gradient(135deg,#241812,#1A1410);
  border:1px solid #3D2419; border-radius:10px; padding:12px 14px; text-align:center; }}
.kpi .v {{ color:#E8C874; font-size:22px; font-weight:800; }}
.kpi .l {{ color:#9A8A78; font-size:12px; }}

/* primary button → gold gradient */
.stButton button[kind="primary"] {{
  background:linear-gradient(135deg,#C9A24B,#8B6F3A) !important;
  color:#0D0A08 !important; border:none !important; font-weight:800 !important; }}
.stButton button[kind="primary"]:hover {{
  background:linear-gradient(135deg,#E8C874,#C9A24B) !important; }}
</style>
""", unsafe_allow_html=True)

# theme color constants for charts / inline html
GOLD = "#C9A24B"; GOLD_LT = "#E8C874"; BURG = "#8B2635"; BURG_DP = "#6E1E2A"
CREAM = "#F0E6D2"; MUTED = "#9A8A78"; PANEL = "#241812"; BORDER = "#3D2419"


# ══════════════════════════════════════════════════════════════════
# metals ticker (live if possible)
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=180)
def metals_ticker_data():
    out = []
    for sym, info in METALS.items():
        p = get_metal_price(sym)
        out.append({
            "sym": sym,
            "name": name_of(info, LANG),
            "oz": p["price_oz"],
            "g": p["price_g"],
            "live": p["source"] == "live",
        })
    return out


def render_ticker():
    data = metals_ticker_data()
    dot = "#4ADE80" if any(d["live"] for d in data) else "#E8C874"
    items = ""
    for d in data:
        items += (f"<span><span style='color:{dot};'>●</span> "
                  f"<b style='color:#F0E6D2;'>{d['name']} ({d['sym']})</b> "
                  f"<span style='color:#C9A24B;'>${d['oz']:,.2f}/oz</span> "
                  f"<span style='color:#9A8A78;'>· ${d['g']:,.2f}/g</span></span>")
    # duplicate for seamless scroll
    st.markdown(f"<div class='ticker-wrap'><div class='ticker'>{items}{items}</div></div>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# HEADER  +  language toggle
# ══════════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([5, 1])
with hc1:
    st.markdown(f"<div class='hero'><h2 style='margin:0;color:#C9A24B;'>⚡ {t('app_title',LANG)}</h2>"
                f"<p style='margin:4px 0 0 0;color:#9A8A78;font-size:13px;'>{t('app_subtitle',LANG)}</p></div>",
                unsafe_allow_html=True)
with hc2:
    if st.button(t("lang_button", LANG), use_container_width=True):
        st.session_state.lang = "ar" if LANG == "en" else "en"
        st.rerun()

render_ticker()


# ══════════════════════════════════════════════════════════════════
# SIDEBAR — data sources + weights
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"### ⚡ {t('app_title',LANG)}")
    st.caption(f"{t('mode_badge',LANG)}: `{APP_MODE}`")

    st.markdown(f"### 📡 {t('data_sources',LANG)}")
    tick = metals_ticker_data()
    metals_live = any(d["live"] for d in tick)

    def src_row(label, is_live, note=""):
        color = "#4ADE80" if is_live else "#E8C874"
        tag = t("live", LANG) if is_live else t("estimated", LANG)
        html = (f"<div style='background:#241812;border-{'right' if RTL else 'left'}:3px solid {color};"
                f"border-radius:6px;padding:7px 10px;margin:5px 0;'>"
                f"<span style='color:{color};font-size:11px;font-weight:700;'>● {tag}</span> "
                f"<span style='color:#F0E6D2;font-size:12px;'>{label}</span>")
        if note:
            html += f"<div style='color:#9A8A78;font-size:10px;margin-top:2px;'>{note}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    src_row(t("src_metals", LANG), metals_live, "gold-api.com")
    src_row(t("src_weather", LANG), APP_MODE in ("live", "hybrid"), "Open-Meteo")
    src_row(t("src_freight", LANG), False, t("src_freight_note", LANG))

    st.markdown(f"### ⚖️ {t('topsis_weights',LANG)}")
    for c, w in TOPSIS_WEIGHTS.items():
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:12px;"
                    f"color:#9A8A78;'><span>{c}</span><span style='color:#C9A24B;'>{int(w*100)}%</span></div>",
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# INPUT FORM
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### 📦 {t('shipment',LANG)}")

# ── Row 1: Metal · Quantity · Unit ──
r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    metal = st.selectbox(t("metal", LANG), list(METALS.keys()),
                         format_func=lambda k: name_of(METALS[k], LANG))
with r1c2:
    qty = st.number_input(t("weight_qty", LANG), min_value=0.1, value=50.0, step=0.5)
with r1c3:
    unit_key = st.selectbox(t("weight_unit", LANG), list(WEIGHT_UNITS.keys()),
                            format_func=lambda k: name_of(WEIGHT_UNITS[k], LANG))
w = compute_weight(qty, unit_key)
st.caption(f"{t('gross_weight',LANG)}: {w['gross_kg']:.3f} kg · "
           f"{t('pure_weight',LANG)}: {w['pure_kg']:.3f} kg")

# ── Row 2: Origin · Departure · Arrival ──
r2c1, r2c2, r2c3 = st.columns(3)
with r2c1:
    origin_code = st.selectbox(
        t("origin", LANG), list(ORIGINS.keys()),
        format_func=lambda k: f"{ORIGINS[k]['flag']} {name_of(ORIGINS[k],LANG)}")
with r2c2:
    depart = st.date_input(t("depart_date", LANG), value=date.today() + timedelta(days=3),
                           min_value=date.today())
with r2c3:
    arrive = st.date_input(t("arrive_date", LANG), value=date.today() + timedelta(days=14),
                           min_value=date.today())

# ── Row 3: Preferred Sea Port · Preferred Airport · Urgency ──
SEA_PORTS = {k: v for k, v in DEST_POINTS.items() if v["type"] == "sea"}
AIRPORTS = {k: v for k, v in DEST_POINTS.items() if v["type"] == "air"}
r3c1, r3c2, r3c3 = st.columns(3)
with r3c1:
    pref_port = st.selectbox(
        t("pref_port", LANG), list(SEA_PORTS.keys()),
        format_func=lambda k: f"{DEST_POINTS[k]['flag']} {name_of(DEST_POINTS[k],LANG)}")
with r3c2:
    pref_airport = st.selectbox(
        t("pref_airport", LANG), list(AIRPORTS.keys()),
        format_func=lambda k: f"{DEST_POINTS[k]['flag']} {name_of(DEST_POINTS[k],LANG)}")
with r3c3:
    urg_map = {"normal": t("urg_normal", LANG), "express": t("urg_express", LANG),
               "urgent": t("urg_urgent", LANG)}
    urgency = st.selectbox(t("urgency", LANG), list(urg_map.keys()),
                           format_func=lambda k: urg_map[k])

# ── Row 4 (centered): Shipment value ──
_, vc, _ = st.columns([1, 2, 1])
with vc:
    value_usd = st.number_input(t("value", LANG), min_value=1000, value=4800000,
                                step=10000, format="%d", help=t("value_help", LANG))

# ── Row 5 (centered): Insurance · Escort toggles ──
_, tc1, tc2, _ = st.columns([1, 1, 1, 1])
with tc1:
    full_ins = st.toggle(t("full_insurance", LANG), value=True)
with tc2:
    escort = st.toggle(t("escort", LANG), value=True)

# ── Secure carrier row ──
st.markdown(f"##### 🛡️ {t('carrier',LANG)}")
cc_col1, cc_col2 = st.columns([2, 3])
with cc_col1:
    carrier = st.selectbox(
        t("carrier", LANG), list(SECURE_CARRIERS.keys()),
        format_func=lambda k: name_of(SECURE_CARRIERS[k], LANG),
        label_visibility="collapsed")
with cc_col2:
    st.caption(f"ℹ️ {name_of(SECURE_CARRIERS[carrier], LANG)} — "
               f"{SECURE_CARRIERS[carrier]['note_'+LANG]}")

analyze_clicked = st.button(t("analyze", LANG), type="primary", use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# helpers for results
# ══════════════════════════════════════════════════════════════════
BADGE_STYLE = {
    "best":     ("#C9A24B", "#0D0A08"),   # gold
    "cheapest": ("#4ADE80", "#0D0A08"),   # green
    "fastest":  ("#E8C874", "#0D0A08"),   # light gold
    "safest":   ("#8B2635", "#F0E6D2"),   # burgundy
}
BADGE_LABEL = {
    "best":     {"en": "★ BEST",     "ar": "★ الأفضل"},
    "cheapest": {"en": "💰 CHEAPEST", "ar": "💰 الأوفر"},
    "fastest":  {"en": "⚡ FASTEST",  "ar": "⚡ الأسرع"},
    "safest":   {"en": "🛡 SAFEST",   "ar": "🛡 الأأمن"},
}
MODE_LABEL = {"air": "mode_air", "sea": "mode_sea", "multimodal": "mode_multi"}
RISK_LABEL = {"low": "risk_low", "med": "risk_med", "high": "risk_high"}


def badges_html(bl):
    out = ""
    for b in bl:
        if b in BADGE_STYLE:
            bg, fg = BADGE_STYLE[b]
            out += f"<span class='badge' style='background:{bg};color:{fg};'>{BADGE_LABEL[b][LANG]}</span>"
    return out


def render_results(ranked):
    feasible = [r for r in ranked if r.get("feasible", True)]
    best = feasible[0]

    # ---- VERDICT banner ----
    via_map = {"sea": t("via_sea", LANG), "air": t("via_air", LANG),
               "multimodal": t("via_multi", LANG)}
    via = via_map[best["mode"]]
    others = feasible[1:]
    alt_costs = "، ".join(f"${r['cost']['total']:,.0f}" for r in others) if RTL else \
                ", ".join(f"${r['cost']['total']:,.0f}" for r in others)
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#6E1E2A,#8B2635 55%,#3D2419);
         border:2px solid #C9A24B;border-radius:14px;padding:20px 24px;margin:6px 0 16px 0;
         box-shadow:0 4px 24px rgba(201,162,75,0.20);'>
      <div style='font-size:13px;color:#E8C874;font-weight:700;letter-spacing:1px;'>
        ★ {t('verdict_title',LANG)}</div>
      <div style='font-size:24px;font-weight:800;color:#F0E6D2;margin:6px 0;'>
        {via} · {best['origin']['flag']} {name_of(best['origin'],LANG)}
        → {best['port']['flag']} {name_of(best['port'],LANG)}</div>
      <div style='font-size:14px;color:#F0E6D2;opacity:0.9;'>
        {t('verdict_because',LANG)} <b style='color:#E8C874;'>${best['cost']['total']:,.0f}</b>
        {t('vs_others',LANG)}: <span style='color:#E8C874;'>{alt_costs}</span></div>
    </div>""", unsafe_allow_html=True)

    # ---- KPI summary ----
    st.markdown(f"### 📊 {t('summary',LANG)}")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"<div class='kpi'><div class='l'>{t('best_route',LANG)}</div>"
                    f"<div class='v' style='font-size:15px;'>{best['origin']['flag']} "
                    f"{name_of(best['origin'],LANG)}</div></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='kpi'><div class='l'>{t('lowest_cost',LANG)}</div>"
                    f"<div class='v'>${best['cost']['total']:,.0f}</div></div>", unsafe_allow_html=True)
    with k3:
        h = best['transit_h']
        disp = f"{h/24:.1f}{t('days',LANG)}" if h > 48 else f"{h:.0f}{t('hours',LANG)}"
        st.markdown(f"<div class='kpi'><div class='l'>{t('transit',LANG)}</div>"
                    f"<div class='v'>{disp}</div></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='kpi'><div class='l'>{t('topsis_score',LANG)}</div>"
                    f"<div class='v'>{best['cc_score']:.3f}</div></div>", unsafe_allow_html=True)
    with k5:
        st.markdown(f"<div class='kpi'><div class='l'>{t('confidence',LANG)}</div>"
                    f"<div class='v'>{best.get('confidence',0)}%</div></div>", unsafe_allow_html=True)

    # ---- AI recommendation ----
    st.markdown(f"### 🧠 {t('recommendation',LANG)}")
    rec = build_recommendation(ranked, LANG)
    st.markdown(f"<div style='background:#241812;border-{'right' if RTL else 'left'}:4px solid #C9A24B;"
                f"border-radius:8px;padding:14px 18px;'>{rec}</div>", unsafe_allow_html=True)

    # ---- all options ranked ----
    st.markdown(f"### 🗺️ {t('all_options',LANG)}")
    for r in feasible:
        cls = "route-card route-best" if r["rank"] == 1 else "route-card"
        wx_lvl = t(RISK_LABEL[r["weather"]["level"]], LANG)
        st.markdown(f"""
        <div class='{cls}'>
          <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>
            <div style='font-size:16px;font-weight:700;'>
              #{r['rank']} · {r['origin']['flag']} {name_of(r['origin'],LANG)}
              → {r['port']['flag']} {name_of(r['port'],LANG)}
              <span style='color:#9A8A78;font-size:13px;'>· {t(MODE_LABEL[r['mode']],LANG)}</span>
            </div>
            <div>{badges_html(r.get('badges',[]))}</div>
          </div>
          <div style='display:flex;gap:22px;flex-wrap:wrap;margin-top:8px;font-size:13px;color:#9A8A78;'>
            <span>💵 <b style='color:#C9A24B;'>${r['cost']['total']:,.0f}</b></span>
            <span>📦 ${r['cost']['per_kg']:,.0f}/{ 'kg' } {t('freight',LANG)}</span>
            <span>⏱ {r['transit_h']:.0f}{t('hours',LANG)}</span>
            <span>📈 {r['cc_score']:.3f} {t('points',LANG)}</span>
            <span>🌦 {wx_lvl}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # ---- why chosen (detailed breakdown of best) ----
    st.markdown(f"### ✅ {t('why_chosen',LANG)}")
    _render_breakdown(best)

    # ---- comparison chart ----
    st.markdown(f"### 📊 {t('comparison',LANG)}")
    _render_comparison(feasible)

    # ---- radar ----
    st.markdown(f"### 🎯 {t('radar',LANG)}")
    _render_radar(feasible)

    # ---- export ----
    st.markdown("---")
    try:
        from pdf_export import generate_pdf
        pdf = generate_pdf(ranked, {
            "origin": name_of(best["origin"], "en"),
            "port": name_of(best["port"], "en"),
            "metal": name_of(METALS[metal], "en"),
            "carrier": name_of(SECURE_CARRIERS[carrier], "en"),
            "value_usd": value_usd,
            "depart": str(depart), "arrive": str(arrive),
        })
        st.download_button(t("export_pdf", LANG), data=pdf,
                           file_name="gold_route_report.pdf", mime="application/pdf")
        st.caption(t("export_note", LANG))
    except Exception as e:
        st.caption(f"PDF: {e}")


def _render_breakdown(r):
    car_name = name_of(SECURE_CARRIERS[r.get("carrier", "TRANSGUARD")], LANG)
    lm_label = (f"{t('last_mile_item',LANG)} · {car_name} "
                f"({r.get('last_mile_km','?')} {t('km',LANG)})")
    items = [
        (t("freight", LANG), r["cost"]["freight"]),
        (t("war_risk_ins", LANG), r["cost"]["war_ins"]),
        (t("insurance_item", LANG), r["cost"]["cargo_ins"]),
        (t("customs_item", LANG), r["cost"]["customs"]),
        (t("security_item", LANG), r["cost"]["security"]),
        (lm_label, r["cost"]["last_mile"]),
        (t("waiting_item", LANG), r["cost"]["waiting"]),
    ]
    rows = ""
    for label, val in items:
        pct = val / r["cost"]["total"] * 100 if r["cost"]["total"] else 0
        rows += (f"<tr><td style='padding:6px 10px;'>{label}</td>"
                 f"<td style='padding:6px 10px;text-align:{'left' if RTL else 'right'};"
                 f"color:#C9A24B;font-weight:600;'>${val:,.0f}</td>"
                 f"<td style='padding:6px 10px;color:#9A8A78;text-align:{'left' if RTL else 'right'};'>"
                 f"{pct:.0f}%</td></tr>")
    st.markdown(f"""
    <table style='width:100%;background:#241812;border-radius:10px;border-collapse:collapse;'>
      <tr style='border-bottom:2px solid #C9A24B;'>
        <th style='padding:8px 10px;text-align:{ALIGN};color:#F0E6D2;'>{t('cost_breakdown',LANG)}</th>
        <th style='padding:8px 10px;text-align:{'left' if RTL else 'right'};color:#F0E6D2;'>USD</th>
        <th style='padding:8px 10px;text-align:{'left' if RTL else 'right'};color:#F0E6D2;'>%</th>
      </tr>
      {rows}
      <tr style='border-top:2px solid #C9A24B;'>
        <td style='padding:8px 10px;font-weight:800;'>{t('total',LANG)}</td>
        <td style='padding:8px 10px;text-align:{'left' if RTL else 'right'};color:#4ADE80;
            font-weight:800;'>${r['cost']['total']:,.0f}</td><td></td>
      </tr>
    </table>""", unsafe_allow_html=True)


def _render_comparison(feasible):
    names = [f"{name_of(r['origin'],LANG)}·{t(MODE_LABEL[r['mode']],LANG)}" for r in feasible]
    totals = [r["cost"]["total"] for r in feasible]
    colors = ["#C9A24B" if r["rank"] == 1 else "#8B6F3A" for r in feasible]
    fig = go.Figure(go.Bar(x=names, y=totals, marker_color=colors,
                           text=[f"${v:,.0f}" for v in totals], textposition="outside"))
    fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#F0E6D2", margin=dict(t=20, b=40, l=40, r=20),
                      yaxis=dict(gridcolor="#3D2419"))
    st.plotly_chart(fig, use_container_width=True)


def _render_radar(feasible):
    cats_keys = ["freight", "transit", "security_item", "customs_item", "weather", "war_risk_ins"]
    cats = [t(k, LANG) for k in cats_keys]
    fig = go.Figure()
    palette = ["#C9A24B", "#8B2635", "#E8C874", "#A84860"]
    fills = ["rgba(201,162,75,0.20)", "rgba(139,38,53,0.20)",
             "rgba(232,200,116,0.16)", "rgba(168,72,96,0.18)"]
    for i, r in enumerate(feasible[:4]):
        m = r["metrics"]
        norm = [
            1 - min(m["shipping_cost"] / 400000, 1),
            1 - min(m["transit_time"] / 600, 1),
            1 - min(m["security"] / 10000, 1),
            1 - min(m["customs"] / 60000, 1),
            1 - min(m["weather_risk"] / 5000, 1),
            1 - min(m["war_risk"] / 20000, 1),
        ]
        fig.add_trace(go.Scatterpolar(
            r=norm + [norm[0]], theta=cats + [cats[0]], fill="toself",
            name=f"{name_of(r['origin'],LANG)}·{t(MODE_LABEL[r['mode']],LANG)}",
            line_color=palette[i % 4], fillcolor=fills[i % 4]))
    fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                      font_color="#F0E6D2", margin=dict(t=30, b=30),
                      polar=dict(bgcolor="rgba(26,37,53,0.5)",
                                 radialaxis=dict(visible=True, range=[0, 1], gridcolor="#3D2419")))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════
if analyze_clicked:
    with st.spinner("..."):
        ranked = analyze(origin_code, pref_port, pref_airport, value_usd, qty,
                         unit_key, escort, full_ins, urgency, carrier)
    st.session_state.ranked = ranked

if "ranked" in st.session_state:
    render_results(st.session_state.ranked)
else:
    st.markdown(f"""
    <div style='text-align:center;padding:50px 20px;'>
      <div style='font-size:52px;'>⚡</div>
      <h3 style='color:#F0E6D2;'>{t('welcome_title',LANG)}</h3>
      <p style='color:#9A8A78;max-width:560px;margin:0 auto;'>{t('welcome_body',LANG)}</p>
    </div>""", unsafe_allow_html=True)
