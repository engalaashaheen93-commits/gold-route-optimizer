"""
Gold Route Optimizer — bilingual (EN/AR) Streamlit app.
Compares every origin×mode to a chosen Dubai port using TOPSIS.
"""
import streamlit as st
from datetime import date, timedelta
import plotly.graph_objects as go

from config import (ORIGINS, DEST_POINTS, METALS, WEIGHT_UNITS, APP_MODE,
                    DEFAULT_LANG, TOPSIS_WEIGHTS, SECURE_CARRIERS,
                    shipment_value, PACKAGING_OPTIONS, t, name_of)
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

/* ── dropdown / calendar popovers ──
   These render in a portal OUTSIDE the themed container, so on mobile they
   fell back to a white background with gold text (invisible). Force the dark
   theme on every popover layer. */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
div[data-baseweb="menu"] ul,
ul[data-baseweb="menu"],
div[data-baseweb="calendar"],
div[data-baseweb="datepicker"],
[data-baseweb="layer"] div[role="listbox"],
[data-baseweb="layer"] div[role="dialog"] {{
  background:#241812 !important; color:#F0E6D2 !important;
  border:1px solid #8B6F3A !important; }}

/* each option row */
li[role="option"], div[role="option"],
ul[data-baseweb="menu"] li {{
  background:#241812 !important; color:#F0E6D2 !important; }}

/* hovered / highlighted / selected option */
li[role="option"]:hover, div[role="option"]:hover,
li[role="option"][aria-selected="true"],
div[role="option"][aria-selected="true"],
ul[data-baseweb="menu"] li:hover {{
  background:#8B2635 !important; color:#F0E6D2 !important; }}

/* calendar day cells */
div[data-baseweb="calendar"] * {{ color:#F0E6D2 !important; }}
div[data-baseweb="calendar"] [aria-selected="true"] {{
  background:#C9A24B !important; color:#0D0A08 !important; }}

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

/* keep every widget label the same height so columns line up */
[data-testid="stWidgetLabel"] p {{
  min-height:2.4em; display:flex; align-items:flex-end; margin-bottom:0; }}

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
    src_row(t("src_freight", LANG), APP_MODE in ("live", "hybrid"), "Freightos")
    # required Freightos attribution
    st.markdown(
        "<div style='font-size:10px;color:#9A8A78;margin-top:2px;'>"
        "Freight data by <a href='https://ship.freightos.com' target='_blank' "
        "style='color:#C9A24B;'>Freightos</a></div>", unsafe_allow_html=True)

    st.markdown(f"### ⚖️ {t('topsis_weights',LANG)}")
    for c, w in TOPSIS_WEIGHTS.items():
        st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:12px;"
                    f"color:#9A8A78;'><span>{c}</span><span style='color:#C9A24B;'>{int(w*100)}%</span></div>",
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# INPUT FORM
# ══════════════════════════════════════════════════════════════════
st.markdown(f"### 📦 {t('shipment',LANG)}")

# ── Row 1: Metal · Quantity · Unit · Packaging ──
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    metal = st.selectbox(t("metal", LANG), list(METALS.keys()),
                         format_func=lambda k: name_of(METALS[k], LANG))
with r1c2:
    qty = st.number_input(t("weight_qty", LANG), min_value=0.1, value=50.0, step=0.5)
with r1c3:
    unit_key = st.selectbox(t("weight_unit", LANG), list(WEIGHT_UNITS.keys()),
                            format_func=lambda k: name_of(WEIGHT_UNITS[k], LANG))
with r1c4:
    packaging = st.selectbox(
        t("packaging_type", LANG), list(PACKAGING_OPTIONS.keys()),
        index=list(PACKAGING_OPTIONS.keys()).index("standard"),
        format_func=lambda k: name_of(PACKAGING_OPTIONS[k], LANG),
        help=t("packaging_help", LANG))
w = compute_weight(qty, unit_key, packaging)
pk = PACKAGING_OPTIONS[packaging]
st.markdown(
    f"<div style='background:#241812;border-{'right' if RTL else 'left'}:4px solid #8B6F3A;"
    f"border-radius:8px;padding:10px 14px;margin:6px 0;color:#F0E6D2;font-size:13px;'>"
    f"⚖️ {t('net_weight',LANG)}: <b>{w['net_kg']:.3f} kg</b> · "
    f"{t('packaging',LANG)}: <b>+{w['packaging_kg']:.3f} kg</b> → "
    f"{t('gross_weight',LANG)}: <b style='color:#E8C874;'>{w['gross_kg']:.3f} kg</b>"
    f"<div style='color:#9A8A78;font-size:11px;margin-top:4px;'>"
    f"{name_of(pk,LANG)} — {pk['note_'+LANG]} · {t('weight_note',LANG)}</div>"
    f"</div>", unsafe_allow_html=True)

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

# ── Row 3: Urgency · Carrier mode ──
r3c1, r3c2, r3c3 = st.columns(3)
with r3c1:
    urg_map = {"normal": t("urg_normal", LANG), "express": t("urg_express", LANG),
               "urgent": t("urg_urgent", LANG)}
    urgency = st.selectbox(t("urgency", LANG), list(urg_map.keys()),
                           format_func=lambda k: urg_map[k])
with r3c2:
    # carrier: auto (cheapest) or a specific company
    carrier_opts = ["auto"] + list(SECURE_CARRIERS.keys())
    carrier_mode = st.selectbox(
        t("carrier", LANG), carrier_opts,
        format_func=lambda k: (t("auto_cheapest", LANG) if k == "auto"
                               else name_of(SECURE_CARRIERS[k], LANG)))
with r3c3:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    st.caption(f"🛡️ {t('carrier_help', LANG)}")

# ── Row 4: Pricing inputs (fix price · premium/discount · extra charges) ──
st.markdown(f"##### 💵 {t('pricing',LANG)}")
p1, p2, p3 = st.columns(3)
with p1:
    fix_price = st.number_input(t("fix_price", LANG), min_value=0.0, value=4030.0,
                                step=1.0, format="%.3f", help=t("fix_help", LANG))
with p2:
    premium = st.number_input(t("premium", LANG), value=0.0, step=0.5,
                              format="%.3f", help=t("premium_help", LANG))
with p3:
    extra_charges = st.number_input(t("extras", LANG), min_value=0.0, value=0.0,
                                    step=50.0, format="%.2f", help=t("extras_help", LANG))

# compute shipment value from the trade's own pricing formula
val = shipment_value(qty, unit_key, fix_price, premium, extra_charges)
value_usd = val["total_value"]

st.markdown(
    f"<div style='background:#241812;border-{'right' if RTL else 'left'}:4px solid #C9A24B;"
    f"border-radius:8px;padding:10px 14px;margin:6px 0;color:#F0E6D2;font-size:13px;'>"
    f"📊 {val['ounces']:,.3f} {t('oz_unit',LANG)} × ${val['unit_price']:,.3f} "
    f"= <b style='color:#E8C874;'>${val['metal_value']:,.2f}</b>"
    + (f" + ${val['extra_charges']:,.2f} {t('extras',LANG)}" if val['extra_charges'] else "")
    + f" → <b style='color:#4ADE80;'>${val['total_value']:,.2f}</b></div>",
    unsafe_allow_html=True)

# ── Row 5 (centered): Insurance · Escort toggles ──
_, tc1, tc2, _ = st.columns([1, 1, 1, 1])
with tc1:
    full_ins = st.toggle(t("full_insurance", LANG), value=True)
with tc2:
    escort = st.toggle(t("escort", LANG), value=True)

# ── Row 6: stated priority → AI-derived criterion weights ──
st.markdown(f"##### 🧭 {t('priority_hdr',LANG)}")
priority_text = st.text_area(
    t("priority_label", LANG), value="", height=80,
    placeholder=t("priority_ph", LANG), help=t("priority_help", LANG))

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


def carrier_label(r):
    """Display label for the inland carrier / service type."""
    c = r.get("carrier", "TRANSGUARD")
    svc = r.get("service")
    if c == "INCLUDED" or svc == "door_to_door":
        return f"{t('svc_d2d',LANG)} ({t('svc_included',LANG)})"
    if c == "FLAT95" or svc == "door_to_airport":
        return f"{t('svc_d2a',LANG)} ({t('svc_flat',LANG)})"
    return name_of(SECURE_CARRIERS[c], LANG)


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
    others = feasible[1:4]
    alt_costs = "، ".join(f"${r['cost']['total']:,.0f}" for r in others) if RTL else \
                ", ".join(f"${r['cost']['total']:,.0f}" for r in others)
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#6E1E2A,#8B2635 55%,#3D2419);
         border:2px solid #C9A24B;border-radius:14px;padding:20px 24px;margin:6px 0 16px 0;
         box-shadow:0 4px 24px rgba(201,162,75,0.20);'>
      <div style='font-size:13px;color:#E8C874;font-weight:700;letter-spacing:1px;'>
        ★ {t('verdict_title',LANG)}</div>
      <div style='font-size:22px;font-weight:800;color:#F0E6D2;margin:6px 0;'>
        {via} · {best['origin']['flag']} {name_of(best['origin'],LANG)}{best.get('hub_txt','')}
        → {best['port']['flag']} {name_of(best['port'],LANG)}</div>
      <div style='font-size:13px;color:#E8C874;margin-bottom:4px;'>
        🚚 {carrier_label(best)} · {best['last_mile_km']} {t('km',LANG)} → {t('last_mile_full',LANG)}</div>
      <div style='font-size:14px;color:#F0E6D2;opacity:0.9;'>
        {t('verdict_because',LANG)} <b style='color:#E8C874;'>${best['cost']['total']:,.0f}</b>
        {t('vs_others',LANG)}: <span style='color:#E8C874;'>{alt_costs}</span></div>
      <div style='font-size:11px;color:#9A8A78;margin-top:6px;'>
        {len(feasible)} {t('routes_compared',LANG)}</div>
    </div>""", unsafe_allow_html=True)

    # ---- HAZARD ALERTS for best route ----
    hz = best.get("hazards", [])
    if hz:
        rows = ""
        for h in hz:
            icon = "🌪️" if h["type"] == "weather" else "⚠️"
            label = t("hz_weather", LANG) if h["type"] == "weather" else t("hz_geo", LANG)
            lvl = t("hz_high", LANG) if h["level"] == "high" else t("hz_med", LANG)
            color = "#8B2635" if h["level"] == "high" else "#8B6F3A"
            rows += (f"<div style='display:flex;gap:10px;align-items:center;margin:4px 0;'>"
                     f"<span style='font-size:16px;'>{icon}</span>"
                     f"<span style='background:{color};color:#F0E6D2;padding:1px 8px;"
                     f"border-radius:8px;font-size:11px;font-weight:700;'>{lvl}</span>"
                     f"<span style='color:#F0E6D2;font-size:13px;'>{label} {t('hz_at',LANG)} "
                     f"<b>{h['where']}</b></span></div>")
        st.markdown(
            f"<div style='background:#241812;border:1px solid #8B2635;border-radius:12px;"
            f"padding:12px 16px;margin-bottom:12px;'>"
            f"<div style='color:#E8C874;font-weight:700;font-size:13px;margin-bottom:6px;'>"
            f"🚨 {t('hazards',LANG)}</div>{rows}</div>", unsafe_allow_html=True)

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

    # ---- all options ranked (top 8 of many) ----
    st.markdown(f"### 🗺️ {t('all_options',LANG)}")
    for r in feasible[:8]:
        cls = "route-card route-best" if r["rank"] == 1 else "route-card"
        wx_lvl = t(RISK_LABEL[r["weather"]["level"]], LANG)
        st.markdown(f"""
        <div class='{cls}'>
          <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>
            <div style='font-size:16px;font-weight:700;'>
              #{r['rank']} · {r['origin']['flag']} {name_of(r['origin'],LANG)}{r.get('hub_txt','')}
              → {r['port']['flag']} {name_of(r['port'],LANG)}
              <span style='color:#9A8A78;font-size:13px;'>· {t(MODE_LABEL[r['mode']],LANG)} · 🚚 {carrier_label(r)}</span>
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
    st.markdown(f"### 📊 {t('chart_tradeoff',LANG)}")
    _render_cost_time(feasible)

    st.markdown(f"### 📉 {t('chart_topn',LANG)}")
    _render_topN(feasible)

    st.markdown(f"### 🎯 {t('chart_score',LANG)}")
    _render_score_stack(feasible)

    # ---- robustness / sensitivity ----
    # ---- AI-derived weights (only when a priority was stated) ----
    _render_derived_weights()

    st.markdown(f"### 🛡️ {t('robust_hdr',LANG)}")
    _render_robustness(feasible)

    # ---- export ----
    st.markdown("---")
    try:
        from pdf_export import generate_pdf
        pdf = generate_pdf(ranked, {
            "origin": name_of(best["origin"], "en"),
            "port": name_of(best["port"], "en"),
            "metal": name_of(METALS[metal], "en"),
            "carrier": (name_of(SECURE_CARRIERS[best["carrier"]], "en")
                        if best["carrier"] in SECURE_CARRIERS
                        else ("All-inclusive (Door-to-Door)" if best.get("service") == "door_to_door"
                              else "Door-to-Airport + inland secure leg")),
            "value_usd": value_usd,
            "depart": str(depart), "arrive": str(arrive),
        })
        st.download_button(t("export_pdf", LANG), data=pdf,
                           file_name="gold_route_report.pdf", mime="application/pdf")
        st.caption(t("export_note", LANG))
    except Exception as e:
        st.caption(f"PDF: {e}")

    # precious-metals cost-structure note
    st.markdown(
        f"<div style='background:#241812;border-{'right' if RTL else 'left'}:4px solid #8B2635;"
        f"border-radius:8px;padding:12px 16px;margin-top:14px;color:#F0E6D2;font-size:13px;'>"
        f"💡 {t('pm_note',LANG)}</div>", unsafe_allow_html=True)


def _render_breakdown(r):
    car_name = carrier_label(r)
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


def _route_label(r):
    """Short, unique label: mode + service + hub + arrival."""
    mode = t(MODE_LABEL[r["mode"]], LANG)
    hub = r.get("hub_txt", "").replace(" via ", "")
    svc = ""
    if r.get("service") == "door_to_door":
        svc = " D2D"
    elif r.get("service") == "door_to_airport":
        svc = " D2A"
    port = name_of(r["port"], LANG)
    return f"#{r['rank']} {mode}{svc} → {port}" + (f" ({hub})" if hub else "")


def _render_cost_time(feasible):
    """Scatter: cost vs time. Shows the trade-off and where the winner sits."""
    fig = go.Figure()
    for r in feasible:
        is_best = r["rank"] == 1
        fig.add_trace(go.Scatter(
            x=[r["transit_h"]], y=[r["cost"]["total"]], mode="markers",
            marker=dict(size=18 if is_best else 10,
                        color="#C9A24B" if is_best else "#8B2635",
                        line=dict(width=2 if is_best else 0, color="#E8C874"),
                        symbol="star" if is_best else "circle"),
            name=_route_label(r), showlegend=False,
            hovertemplate=(f"<b>{_route_label(r)}</b><br>"
                           f"{t('total',LANG)}: ${r['cost']['total']:,.0f}<br>"
                           f"{t('transit',LANG)}: {r['transit_h']:.0f}h<extra></extra>")))
    fig.update_layout(
        height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,10,8,0.35)",
        font_color="#F0E6D2", margin=dict(t=30, b=50, l=60, r=20),
        xaxis=dict(title=t("transit", LANG) + " (h)", gridcolor="#3D2419", zeroline=False),
        yaxis=dict(title=t("total", LANG) + " (USD)", gridcolor="#3D2419", zeroline=False))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t("chart_hint_scatter", LANG))


def _render_topN(feasible, n=8):
    """Horizontal bar of total cost for the top N — labels stay readable."""
    top = feasible[:n][::-1]          # reverse so #1 sits on top
    labels = [_route_label(r) for r in top]
    totals = [r["cost"]["total"] for r in top]
    colors = ["#C9A24B" if r["rank"] == 1 else "#8B6F3A" for r in top]
    fig = go.Figure(go.Bar(
        x=totals, y=labels, orientation="h", marker_color=colors,
        text=[f"${v:,.0f}" for v in totals], textposition="auto",
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"))
    fig.update_layout(
        height=max(300, 42 * len(top)), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,10,8,0.35)", font_color="#F0E6D2",
        margin=dict(t=20, b=40, l=10, r=20),
        xaxis=dict(title=t("total", LANG) + " (USD)", gridcolor="#3D2419"),
        yaxis=dict(automargin=True))
    st.plotly_chart(fig, use_container_width=True)


def _render_derived_weights():
    """Show default vs AI-derived criterion weights, when a priority was given."""
    wres = st.session_state.get("wres")
    if not wres or wres.get("source") != "ai":
        if wres and wres.get("error") == "invalid_reply":
            st.info(t("weights_invalid", LANG))
        return

    import weight_elicitation
    st.markdown(f"### 🧭 {t('weights_hdr',LANG)}")
    if wres.get("rationale"):
        st.markdown(
            f"<div style='background:#241812;border-{'right' if RTL else 'left'}:4px solid #C9A24B;"
            f"border-radius:8px;padding:12px 16px;margin:6px 0;color:#F0E6D2;font-size:13px;'>"
            f"💬 {wres['rationale']}</div>", unsafe_allow_html=True)

    rows = weight_elicitation.describe(wres, LANG)
    LBL = {"total_cost": t("total", LANG), "transit_time": t("transit", LANG),
           "geopolitical": t("hz_geo", LANG), "weather_risk": t("weather", LANG),
           "war_risk": t("war_risk_ins", LANG)}
    ARROW = {"^": "🔺", "v": "🔻", "=": "▪️"}
    head = (f"| {t('criterion_col',LANG)} | {t('weights_default',LANG)} | "
            f"{t('weights_derived',LANG)} | |\n|---|---:|---:|:--:|\n")
    body_rows = "".join(
        f"| {LBL.get(r['criterion'], r['criterion'])} | {r['default_pct']}% | "
        f"**{r['derived_pct']}%** | {ARROW[r['direction']]} |\n" for r in rows)
    st.markdown(head + body_rows)
    st.caption(t("weights_note", LANG))


def _render_robustness(feasible):
    """Sensitivity analysis: does the recommendation survive perturbation?"""
    import sensitivity
    s = sensitivity.analyse(feasible)
    if not s.get("total_scenarios"):
        return
    m = sensitivity.margin_analysis(feasible)
    be = sensitivity.breakeven_cost(feasible)

    pct = s["robustness_pct"]
    colour = ("#2E7D32" if s["verdict"] == "high"
              else "#C9A24B" if s["verdict"] == "moderate" else "#8B2635")
    verdict_txt = t(f"robust_{s['verdict']}", LANG)

    st.markdown(
        f"<div style='background:#241812;border:1px solid {colour};border-radius:12px;"
        f"padding:16px 18px;margin:8px 0;'>"
        f"<div style='color:#E8C874;font-size:30px;font-weight:800;'>{pct}%</div>"
        f"<div style='color:#F0E6D2;font-size:14px;margin-bottom:6px;'>"
        f"{t('robust_line',LANG).format(wins=s['wins'], total=s['total_scenarios'])}</div>"
        f"<div style='color:{colour};font-weight:700;font-size:13px;'>{verdict_txt}</div>"
        f"</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(t("robust_weights", LANG),
                  f"{s['by_family'].get('weights',{}).get('pct',0)}%")
    with c2:
        st.metric(t("robust_cost", LANG),
                  f"{s['by_family'].get('cost',{}).get('pct',0)}%")
    with c3:
        st.metric(t("robust_time", LANG),
                  f"{s['by_family'].get('time',{}).get('pct',0)}%")

    # margin vs runner-up + break-even headroom
    bits = []
    if m:
        bits.append(t("margin_line", LANG).format(
            gap=f"{m['score_gap']:.4f}", cost=f"${m['cost_gap']:,.0f}",
            time=f"{m['time_gap']:.0f}"))
        if not m["decisive"]:
            bits.append(t("margin_thin", LANG))
    if be:
        bits.append(t("breakeven_line", LANG).format(pct=f"{(be-1)*100:.0f}"))
    else:
        bits.append(t("breakeven_none", LANG))
    st.caption(" · ".join(bits))

    if s["flips"]:
        with st.expander(t("robust_flips", LANG).format(n=len(s["flips"]))):
            for f in s["flips"][:12]:
                st.markdown(
                    f"- **{f['scenario']}** → {f['new_winner']} "
                    f"(${f['new_cost']:,.0f} · {f['new_time']:.0f}h)")
    st.caption(t("robust_note", LANG))


def _render_score_stack(feasible, n=8):
    """Stacked bar: how each criterion contributed to the final score."""
    top = feasible[:n][::-1]
    labels = [_route_label(r) for r in top]
    crit_order = ["total_cost", "transit_time", "geopolitical", "weather_risk", "war_risk"]
    crit_name = {"total_cost": t("total", LANG), "transit_time": t("transit", LANG),
                 "geopolitical": t("hz_geo", LANG), "weather_risk": t("weather", LANG),
                 "war_risk": t("war_risk_ins", LANG)}
    palette = {"total_cost": "#C9A24B", "transit_time": "#E8C874",
               "geopolitical": "#8B2635", "weather_risk": "#A84860", "war_risk": "#8B6F3A"}
    fig = go.Figure()
    for c in crit_order:
        vals = [r.get("criteria_detail", {}).get(c, {}).get("weighted", 0) for r in top]
        fig.add_trace(go.Bar(
            x=vals, y=labels, orientation="h", name=crit_name[c],
            marker_color=palette[c],
            hovertemplate="%{y}<br>" + crit_name[c] + ": %{x:.3f}<extra></extra>"))
    fig.update_layout(
        barmode="stack", height=max(300, 42 * len(top)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,10,8,0.35)",
        font_color="#F0E6D2", margin=dict(t=20, b=40, l=10, r=20),
        xaxis=dict(title=t("topsis_score", LANG), gridcolor="#3D2419"),
        yaxis=dict(automargin=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(t("chart_hint_stack", LANG))


# ══════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════
if analyze_clicked:
    with st.spinner("..."):
        import weight_elicitation
        wres = weight_elicitation.derive(priority_text)
        ranked = analyze(origin_code, value_usd, qty, unit_key,
                         escort, full_ins, urgency, carrier_mode, packaging,
                         weights_override=(wres["weights"] if wres["source"] == "ai" else None))
    st.session_state.ranked = ranked
    st.session_state.wres = wres

if "ranked" in st.session_state:
    render_results(st.session_state.ranked)
else:
    st.markdown(f"""
    <div style='text-align:center;padding:50px 20px;'>
      <div style='font-size:52px;'>⚡</div>
      <h3 style='color:#F0E6D2;'>{t('welcome_title',LANG)}</h3>
      <p style='color:#9A8A78;max-width:560px;margin:0 auto;'>{t('welcome_body',LANG)}</p>
    </div>""", unsafe_allow_html=True)
