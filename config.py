"""
Configuration + bilingual (EN/AR) strings for Gold Route Optimizer.
Works locally (.env) and on Streamlit Cloud (st.secrets).
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _get(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


ANTHROPIC_API_KEY   = _get("ANTHROPIC_API_KEY")
OPENWEATHER_API_KEY = _get("OPENWEATHER_API_KEY")
APP_MODE            = _get("APP_MODE", "hybrid")   # mock | hybrid | live
DEFAULT_LANG        = _get("DEFAULT_LANG", "en")   # en | ar

# ══════════════════════════════════════════════════════════════════
# ORIGINS (Asia → Dubai)
# ══════════════════════════════════════════════════════════════════
ORIGINS = {
    "PVG": {"en": "Shanghai",  "ar": "شنغهاي",    "city": "Shanghai",  "country": "CN", "flag": "🇨🇳"},
    "HKG": {"en": "Hong Kong", "ar": "هونغ كونغ", "city": "Hong Kong", "country": "HK", "flag": "🇭🇰"},
    "SIN": {"en": "Singapore", "ar": "سنغافورة",  "city": "Singapore", "country": "SG", "flag": "🇸🇬"},
    "IST": {"en": "Istanbul",  "ar": "إسطنبول",   "city": "Istanbul",  "country": "TR", "flag": "🇹🇷"},
}

# ══════════════════════════════════════════════════════════════════
# TRANSIT HUBS (transshipment points between origin and UAE)
# sea + air hubs where cargo can be re-consolidated before Dubai.
# ══════════════════════════════════════════════════════════════════
TRANSIT_SEA = {
    "SIN": {"en": "Singapore",   "ar": "سنغافورة",   "flag": "🇸🇬"},
    "PUS": {"en": "Busan",       "ar": "بوسان",      "flag": "🇰🇷"},
    "HKG": {"en": "Hong Kong",   "ar": "هونغ كونغ",  "flag": "🇭🇰"},
    "CMB": {"en": "Colombo",     "ar": "كولومبو",    "flag": "🇱🇰"},
    "PKG": {"en": "Port Klang",  "ar": "بورت كلانغ", "flag": "🇲🇾"},
}
TRANSIT_AIR = {
    "SIN": {"en": "Singapore",   "ar": "سنغافورة",  "flag": "🇸🇬"},
    "HKG": {"en": "Hong Kong",   "ar": "هونغ كونغ", "flag": "🇭🇰"},
    "ICN": {"en": "Incheon",     "ar": "إنتشون",    "flag": "🇰🇷"},
    "NRT": {"en": "Tokyo",       "ar": "طوكيو",     "flag": "🇯🇵"},
}

# ══════════════════════════════════════════════════════════════════
# GEOPOLITICAL RISK by location (0=safe .. 1=high risk)
# reflects corridor stability, conflict proximity, chokepoints.
# Used to flag hazards and feed the decision.
# ══════════════════════════════════════════════════════════════════
GEO_RISK = {
    # origins
    "PVG": 0.20, "HKG": 0.22, "SIN": 0.10, "IST": 0.45,
    # transit hubs
    "PUS": 0.18, "CMB": 0.30, "PKG": 0.15, "ICN": 0.25, "NRT": 0.15,
    # UAE arrival points (Strait of Hormuz proximity)
    "JEA": 0.28, "HAM": 0.28, "SHJP": 0.28, "KHL": 0.24, "ZYD": 0.24,
    "KHR": 0.20, "FUJ": 0.20,
    "DXB": 0.25, "SHJ": 0.25, "AUH": 0.22,
}

# cities to check live weather for each routing node
NODE_CITY = {
    "PVG": "Shanghai", "HKG": "Hong Kong", "SIN": "Singapore", "IST": "Istanbul",
    "PUS": "Busan", "CMB": "Colombo", "PKG": "Kuala Lumpur", "ICN": "Seoul", "NRT": "Tokyo",
    "JEA": "Dubai", "HAM": "Dubai", "SHJP": "Dubai", "KHL": "Dubai", "ZYD": "Dubai",
    "KHR": "Dubai", "FUJ": "Dubai",
    "DXB": "Dubai", "SHJ": "Dubai", "AUH": "Dubai",
}

# ══════════════════════════════════════════════════════════════════
# DUBAI DESTINATION PORTS + onward delivery to Gold Souk (Deira)
# last-mile cost is an estimate (USD) — editable
# ══════════════════════════════════════════════════════════════════
DEST_POINTS = {
    # ── Sea ports ──
    "JEA": {"en": "Jebel Ali Port",  "ar": "ميناء جبل علي", "type": "sea",
            "souk_km": 45, "flag": "🚢"},
    "HAM": {"en": "Hamriyah Port",   "ar": "ميناء الحمرية", "type": "sea",
            "souk_km": 28, "flag": "🚢"},
    "SHJP": {"en": "Sharjah Port",   "ar": "ميناء الشارقة", "type": "sea",
            "souk_km": 35, "flag": "🚢"},
    "KHL": {"en": "Khalifa Port",    "ar": "ميناء خليفة",   "type": "sea",
            "souk_km": 130, "flag": "🚢"},
    "ZYD": {"en": "Zayed Port",      "ar": "ميناء زايد",    "type": "sea",
            "souk_km": 150, "flag": "🚢"},
    "KHR": {"en": "Khorfakkan Port", "ar": "ميناء خورفكان", "type": "sea",
            "souk_km": 130, "flag": "🚢"},
    "FUJ": {"en": "Fujairah Port",   "ar": "ميناء الفجيرة", "type": "sea",
            "souk_km": 140, "flag": "🚢"},
    # ── Airports ──
    "DXB": {"en": "Dubai Intl Airport",   "ar": "مطار دبي الدولي",    "type": "air",
            "souk_km": 8,  "flag": "✈️"},
    "SHJ": {"en": "Sharjah Airport",      "ar": "مطار الشارقة",       "type": "air",
            "souk_km": 22, "flag": "✈️"},
    "AUH": {"en": "Zayed Intl (Abu Dhabi)", "ar": "مطار زايد (أبوظبي)", "type": "air",
            "souk_km": 155, "flag": "✈️"},
}
# keep old name as alias so nothing breaks
DUBAI_PORTS = DEST_POINTS

# ══════════════════════════════════════════════════════════════════
# SECURE INLAND CARRIERS (airport/port → Dubai Gold Souk)
# specialised precious-metals transport & armed escort.
# base_usd = fixed dispatch; per_km = armored-route rate;
# per_100k_value = value-based security surcharge (per $100k insured).
# Figures are realistic ESTIMATES — precise quotes are confidential.
# ══════════════════════════════════════════════════════════════════
SECURE_CARRIERS = {
    "TRANSGUARD": {
        "en": "Transguard", "ar": "ترانسجارد",
        "base_usd": 260, "per_km": 6.5, "per_100k_value": 55,
        "note_en": "Emirates Group · sole escort-authorised at DXB",
        "note_ar": "مجموعة الإمارات · المرخّصة حصرياً في مطار دبي",
    },
    "BRINKS": {
        "en": "Brink's", "ar": "برينكس",
        "base_usd": 310, "per_km": 7.2, "per_100k_value": 62,
        "note_en": "Global network · operates DMCC/Almas vault",
        "note_ar": "شبكة عالمية · تدير خزائن DMCC/الماس",
    },
    "LOOMIS": {
        "en": "Loomis", "ar": "لوميس",
        "base_usd": 240, "per_km": 6.0, "per_100k_value": 50,
        "note_en": "Bonded storage · DAFZA vault",
        "note_ar": "تخزين جمركي · خزنة منطقة مطار دبي الحرة",
    },
    "ERBAY": {
        "en": "Erbay", "ar": "إرباي",
        "base_usd": 220, "per_km": 5.6, "per_100k_value": 46,
        "note_en": "Regional secure logistics · competitive rates",
        "note_ar": "خدمات لوجستية آمنة إقليمية · أسعار تنافسية",
    },
}

# ══════════════════════════════════════════════════════════════════
# 3-TIER SECURITY / HANDLING MODEL  (per uploaded matrix)
# Amounts in USD (converted from AED at ~3.67).
# The tier is auto-selected from shipment value & escort choice, and
# drives insurance %, fixed security fee, per-kg handling, and
# in-UAE destination handling fee.
# ══════════════════════════════════════════════════════════════════
AED = 3.6725   # USD per AED divisor  (1 USD ≈ 3.6725 AED)

SECURITY_TIERS = {
    "low": {
        "en": "Low",  "ar": "منخفض",
        "when_en": "Gold/Silver, organised delivery, no special escort",
        "when_ar": "ذهب/فضة، تسليم منظّم، بدون حراسة خاصة",
        "insurance_pct": 0.0015,          # lower bound of 0.15–0.25%
        "security_fixed_aed": 275,
        "handling_per_kg_aed": 13,
        "dest_handling_aed": 75,
    },
    "medium": {
        "en": "Medium", "ar": "متوسط",
        "when_en": "Higher value, airport/vault, secure handling",
        "when_ar": "قيمة أعلى، مطار/مخزن، مناولة آمنة",
        "insurance_pct": 0.0025,          # lower bound of 0.25–0.45%
        "security_fixed_aed": 600,
        "handling_per_kg_aed": 22,
        "dest_handling_aed": 200,
    },
    "high": {
        "en": "High", "ar": "عالي",
        "when_en": "High-value cargo, escort/vault/armored service",
        "when_ar": "شحنة عالية القيمة، حراسة/خزنة/نقل مصفّح",
        "insurance_pct": 0.0045,          # lower bound of 0.45–0.90%
        "security_fixed_aed": 1150,
        "handling_per_kg_aed": 35,
        "dest_handling_aed": 425,
    },
}


def select_tier(value_usd: float, escort: bool, full_insurance: bool) -> str:
    """Auto-pick the security tier from shipment profile."""
    if escort or value_usd >= 5_000_000:
        return "high"
    if full_insurance or value_usd >= 1_000_000:
        return "medium"
    return "low"

# ══════════════════════════════════════════════════════════════════
# METALS
# ══════════════════════════════════════════════════════════════════
METALS = {
    "XAU": {"en": "Gold",      "ar": "ذهب",       "symbol": "XAU"},
    "XAG": {"en": "Silver",    "ar": "فضة",       "symbol": "XAG"},
    "XPT": {"en": "Platinum",  "ar": "بلاتينيوم", "symbol": "XPT"},
    "XPD": {"en": "Palladium", "ar": "بالاديوم",  "symbol": "XPD"},
}

# ══════════════════════════════════════════════════════════════════
# WEIGHT UNITS → grams
# ══════════════════════════════════════════════════════════════════
WEIGHT_UNITS = {
    "oz":      {"en": "Troy Ounce",    "ar": "أونصة",         "grams": 31.1035, "purity": 0.9999},
    "kg995":   {"en": "Kilogram 995",  "ar": "كيلوغرام 995",  "grams": 1000.0,  "purity": 0.995},
    "kg_pure": {"en": "Kilogram Pure", "ar": "كيلوغرام خالص", "grams": 1000.0,  "purity": 0.9999},
    "g":       {"en": "Gram",          "ar": "غرام",          "grams": 1.0,     "purity": 0.9999},
}

# ══════════════════════════════════════════════════════════════════
# TRANSPORT MODES — app compares ALL by default
# ══════════════════════════════════════════════════════════════════
MODES = ["air", "sea", "multimodal"]

# ══════════════════════════════════════════════════════════════════
# MARKET AIR-FREIGHT PRICING (per troy ounce) — real industry rates.
# Two service types:
#   door_to_door    = all-inclusive (freight + inland transport + guard + insurance)
#   door_to_airport = to the airport only; inland guard/insurance added separately
# Rate decreases as quantity grows (a single truck carries the gold regardless).
# ══════════════════════════════════════════════════════════════════
GRAMS_PER_OZ = 31.1035

# Market convention for ounces per kilogram (used for pricing, not physics):
#   pure (999.9) → 32.148 oz/kg
#   995          → 31.99  oz/kg
OZ_PER_KG_PURE = 32.148
OZ_PER_KG_995  = 31.99

# Market-standard ounces per kilogram, by purity (industry convention).
# Used to convert a kg-entered quantity into billable/priced troy ounces.
OZ_PER_KG = {
    "pure": 32.148,    # 999.9 fine
    "995":  31.990,    # 995 fine
}

# Packaging overhead: cartons, tape, plastic bags, sealing materials.
# Carriers bill the FULL gross weight (packaging is charged as if it were gold).
# Field figures for a 50 kg shipment:
#   light   : security bags/envelopes + tape + dividers → 200–800 g  (~1%)
#   standard: strong outer cartons + extra protection   → 300 g–1.5 kg (~1.8%)
#   heavy   : wooden crate / special security packing   → 2–3 kg     (~5%)
PACKAGING_OPTIONS = {
    "light": {
        "en": "Security bags + tape + dividers",
        "ar": "أكياس أمان + لاصق + فواصل داخلية",
        "factor": 1.010,     # ~1%
        "note_en": "≈ 200–800 g on a 50 kg shipment",
        "note_ar": "≈ 200–800 غ على شحنة 50 كغ",
    },
    "standard": {
        "en": "Strong outer cartons + extra protection",
        "ar": "كراتين خارجية قوية + حماية إضافية",
        "factor": 1.018,     # ~1.8%
        "note_en": "≈ 300 g – 1.5 kg on a 50 kg shipment",
        "note_ar": "≈ 300 غ – 1.5 كغ على شحنة 50 كغ",
    },
    "heavy": {
        "en": "Wooden crate / special security packing",
        "ar": "صندوق خشبي / تغليف أمني خاص",
        "factor": 1.050,     # ~5%
        "note_en": "≈ 2–3 kg on a 50 kg shipment",
        "note_ar": "≈ 2–3 كغ على شحنة 50 كغ",
    },
}
DEFAULT_PACKAGING = "standard"
PACKAGING_FACTOR = PACKAGING_OPTIONS[DEFAULT_PACKAGING]["factor"]

AIR_OZ_PRICING = [
    # (max_gross_kg, door_to_door $/oz, door_to_airport $/oz)
    (50.0,  2.00, 1.50),
    (75.0,  1.50, 1.00),
    (9e9,   1.20, 0.80),   # above 75 kg
]

# Door-to-Airport adds a flat inland secure leg (transport + guard + insurance)
# to reach the Gold Souk. Flat because one armoured truck covers the load.
INLAND_SECURE_FLAT_USD = 95.0


def air_oz_rate(gross_kg: float, service: str) -> float:
    """Return $/oz for the given weight tier and service type."""
    for max_kg, dtd, dta in AIR_OZ_PRICING:
        if gross_kg <= max_kg:
            return dtd if service == "door_to_door" else dta
    return AIR_OZ_PRICING[-1][1 if service == "door_to_door" else 2]


def priced_ounces(qty: float, unit_key: str) -> float:
    """
    Convert the user's quantity into PRICEABLE troy ounces using the
    market convention (32.148 oz/kg pure, 31.99 oz/kg for 995).
    """
    u = WEIGHT_UNITS[unit_key]
    if unit_key == "oz":
        return qty
    if unit_key == "kg995":
        return qty * OZ_PER_KG_995
    if unit_key == "kg_pure":
        return qty * OZ_PER_KG_PURE
    if unit_key == "g":
        return (qty / 1000.0) * OZ_PER_KG_PURE
    # fallback: physical conversion
    return (qty * u["grams"]) / GRAMS_PER_OZ


def shipment_value(qty: float, unit_key: str, fixing_per_oz: float,
                   premium_per_oz: float = 0.0, extra_charges: float = 0.0) -> dict:
    """
    Shipment value = ounces x (fixing price + premium/discount) + extra charges.
    premium_per_oz may be negative (a discount off the fixing).
    """
    oz = priced_ounces(qty, unit_key)
    unit_price = fixing_per_oz + premium_per_oz
    metal_value = oz * unit_price
    total = metal_value + extra_charges
    return {
        "ounces": round(oz, 3),
        "unit_price": round(unit_price, 3),
        "metal_value": round(metal_value, 2),
        "extra_charges": round(extra_charges, 2),
        "total_value": round(total, 2),
    }


def priced_ounces(qty: float, unit_key: str) -> float:
    """
    Convert the user's entered quantity into PRICED troy ounces,
    using the market conversion for the chosen unit/purity.
    """
    if unit_key == "kg995":
        return qty * OZ_PER_KG["995"]
    if unit_key == "kg_pure":
        return qty * OZ_PER_KG["pure"]
    if unit_key == "g":
        return (qty / 1000.0) * OZ_PER_KG["pure"]
    return qty          # already in troy ounces


def shipment_value(qty: float, unit_key: str, fix_price_oz: float,
                   premium_oz: float = 0.0, extra_charges: float = 0.0) -> dict:
    """
    Total shipment value the way the trade prices it:
        ounces x (fix price + premium/discount per oz) + extra charges
    premium_oz may be negative (a discount to the fix).
    """
    oz = priced_ounces(qty, unit_key)
    unit_price = fix_price_oz + premium_oz
    metal_value = oz * unit_price
    total = metal_value + extra_charges
    return {
        "ounces": round(oz, 3),
        "unit_price": round(unit_price, 3),
        "metal_value": round(metal_value, 2),
        "extra_charges": round(extra_charges, 2),
        "total_value": round(total, 2),
    }

# ══════════════════════════════════════════════════════════════════
# TOPSIS weights
# ══════════════════════════════════════════════════════════════════
TOPSIS_WEIGHTS = {
    "shipping_cost":  0.24,
    "insurance":      0.14,
    "customs":        0.10,
    "security":       0.14,
    "transit_time":   0.20,
    "war_risk":       0.05,
    "weather_risk":   0.04,
    "geopolitical":   0.05,
    "last_mile":      0.04,
}

# ══════════════════════════════════════════════════════════════════
# i18n — every UI string in EN + AR
# ══════════════════════════════════════════════════════════════════
T = {
    "app_title":       {"en": "Gold Route Optimizer",            "ar": "محسّن مسارات الذهب"},
    "app_subtitle":    {"en": "AI-powered route selection for precious-metals shipping · Asia to Dubai",
                        "ar": "اختيار مسارات شحن المعادن الثمينة بالذكاء الاصطناعي · آسيا إلى دبي"},
    "lang_button":     {"en": "🌐 العربية",                       "ar": "🌐 English"},
    "mode_badge":      {"en": "Mode",                            "ar": "الوضع"},

    "shipment":        {"en": "Shipment Details",                "ar": "بيانات الشحنة"},
    "origin":          {"en": "Origin",                          "ar": "مصدر الشحنة"},
    "destination":     {"en": "Dubai Destination Port",          "ar": "ميناء الوصول في دبي"},
    "metal":           {"en": "Metal",                           "ar": "المعدن"},
    "weight_qty":      {"en": "Quantity",                        "ar": "الكمية"},
    "weight_unit":     {"en": "Unit",                            "ar": "الوحدة"},
    "value":           {"en": "Shipment Value (USD)",            "ar": "قيمة الشحنة (دولار)"},
    "value_help":      {"en": "Enter the insured value of the shipment",
                        "ar": "أدخل القيمة المؤمّنة للشحنة"},
    "depart_date":     {"en": "Departure Date",                  "ar": "تاريخ الانطلاق"},
    "arrive_date":     {"en": "Arrival Date",                    "ar": "تاريخ الاستلام"},
    "urgency":         {"en": "Urgency Level",                   "ar": "مستوى الاستعجال"},
    "escort":          {"en": "Armed Escort",                    "ar": "حراسة مسلحة"},
    "full_insurance":  {"en": "Full Insurance Coverage",         "ar": "تغطية تأمينية كاملة"},
    "analyze":         {"en": "🔍 Analyze All Routes",           "ar": "🔍 حلّل جميع المسارات"},

    "urg_normal":      {"en": "Normal (7+ days)",                "ar": "عادي (7+ أيام)"},
    "urg_express":     {"en": "Express (3-7 days)",              "ar": "مستعجل (3-7 أيام)"},
    "urg_urgent":      {"en": "Critical (<48 h)",               "ar": "عاجل جداً (<48 ساعة)"},

    "mode_air":        {"en": "Air",                             "ar": "جوي"},
    "mode_sea":        {"en": "Sea",                             "ar": "بحري"},
    "mode_multi":      {"en": "Multimodal",                      "ar": "متعدد الوسائط"},

    "results":         {"en": "Results",                        "ar": "النتائج"},
    "summary":         {"en": "Summary",                        "ar": "الملخص"},
    "best_route":      {"en": "Best Route",                     "ar": "أفضل مسار"},
    "lowest_cost":     {"en": "Lowest Cost",                    "ar": "أقل تكلفة"},
    "transit":         {"en": "Transit Time",                   "ar": "زمن العبور"},
    "topsis_score":    {"en": "TOPSIS Score",                   "ar": "درجة TOPSIS"},
    "confidence":      {"en": "Confidence",                     "ar": "درجة الثقة"},
    "all_options":     {"en": "All Route Options (ranked)",     "ar": "جميع الخيارات (مرتّبة)"},
    "why_chosen":      {"en": "Why this route?",                "ar": "لماذا هذا المسار؟"},
    "recommendation":  {"en": "AI Recommendation",              "ar": "توصية الذكاء الاصطناعي"},
    "cost_breakdown":  {"en": "Cost Breakdown",                 "ar": "تفصيل التكلفة"},
    "comparison":      {"en": "Route Comparison",               "ar": "مقارنة المسارات"},
    "radar":           {"en": "Multi-Criteria Profile",        "ar": "الملف متعدد المعايير"},

    "freight":         {"en": "Freight",                        "ar": "الشحن"},
    "war_risk_ins":    {"en": "War-Risk Insurance",             "ar": "تأمين مخاطر الحرب"},
    "insurance_item":  {"en": "Cargo Insurance",                "ar": "تأمين الشحنة"},
    "customs_item":    {"en": "Customs & Clearance",            "ar": "الجمارك والتخليص"},
    "security_item":   {"en": "Security & Escort",              "ar": "الأمن والحراسة"},
    "last_mile_item":  {"en": "Delivery to Gold Souk",          "ar": "التوصيل لسوق الذهب"},
    "waiting_item":    {"en": "Port Waiting",                   "ar": "انتظار الميناء"},
    "total":           {"en": "Total",                          "ar": "الإجمالي"},
    "per_kg":          {"en": "per kg",                         "ar": "لكل كغ"},
    "hours":           {"en": "h",                              "ar": "ساعة"},
    "days":            {"en": "d",                              "ar": "يوم"},
    "points":          {"en": "pts",                            "ar": "نقطة"},
    "rank":            {"en": "Rank",                           "ar": "الترتيب"},
    "route_col":       {"en": "Route",                          "ar": "المسار"},
    "mode_col":        {"en": "Mode",                           "ar": "الوسيلة"},
    "weather":         {"en": "Weather",                        "ar": "الطقس"},

    "risk_low":        {"en": "Low",                            "ar": "منخفض"},
    "risk_med":        {"en": "Medium",                         "ar": "متوسط"},
    "risk_high":       {"en": "High",                           "ar": "مرتفع"},

    "data_sources":    {"en": "Data Sources",                   "ar": "مصادر البيانات"},
    "live":            {"en": "LIVE",                           "ar": "حيّ"},
    "estimated":       {"en": "Estimated",                      "ar": "تقديري"},
    "src_metals":      {"en": "Metal Prices",                   "ar": "أسعار المعادن"},
    "src_weather":     {"en": "Weather",                        "ar": "الطقس"},
    "src_freight":     {"en": "Freight & Ports",                "ar": "الشحن والموانئ"},
    "src_freight_note":{"en": "Commercial providers - simulated",
                        "ar": "مزوّدوها تجاريون - محاكاة"},

    "topsis_weights":  {"en": "TOPSIS Weights",                 "ar": "أوزان TOPSIS"},

    "welcome_title":   {"en": "Start by entering shipment details",
                        "ar": "ابدأ بإدخال بيانات الشحنة"},
    "welcome_body":    {"en": "Fill in the form above and press Analyze. The system compares every route and mode using TOPSIS.",
                        "ar": "املأ النموذج أعلاه واضغط تحليل. يقارن النظام كل المسارات والوسائل باستخدام TOPSIS."},

    "export_pdf":      {"en": "📄 Export Report (PDF)",         "ar": "📄 تصدير التقرير (PDF)"},
    "export_note":     {"en": "Report is generated in English.",
                        "ar": "التقرير يُنشأ باللغة الإنجليزية."},

    "gross_weight":    {"en": "Billable weight",                "ar": "الوزن المحتسب"},
    "net_weight":      {"en": "Net metal",                      "ar": "المعدن الصافي"},
    "packaging":       {"en": "Packaging",                      "ar": "التغليف"},
    "packaging_type":  {"en": "Packaging Type",                 "ar": "نوع التغليف"},
    "packaging_help":  {"en": "Packaging weight is billed as if it were metal",
                        "ar": "وزن التغليف يُحتسب كأنه معدن"},
    "weight_note":     {"en": "Carriers bill the packed weight — cartons, tape and sealing are charged as if they were metal.",
                        "ar": "الناقل يحتسب الوزن بعد التغليف — الكراتين واللاصق ومواد الإغلاق تُحسب كأنها معدن."},

    # pricing inputs
    "pricing":         {"en": "Shipment Pricing",               "ar": "تسعير الشحنة"},
    "fix_price":       {"en": "Fix Price",                    "ar": "سعر التثبيت"},
    "fix_help":        {"en": "Fixing price in USD per troy ounce", "ar": "سعر التثبيت بالدولار لكل أونصة"},
    "premium":         {"en": "Premium / Discount",           "ar": "البريميوم / الخصم"},
    "premium_help":    {"en": "USD per ounce added to (or subtracted from) the fix price", "ar": "دولار لكل أونصة يُضاف إلى سعر التثبيت أو يُطرح منه"},
    "extras":          {"en": "Extra Charges",                "ar": "رسوم إضافية"},
    "extras_help":     {"en": "One-off charges for the whole shipment (USD)", "ar": "رسوم لمرة واحدة على كامل الشحنة (دولار)"},
    "oz_unit":         {"en": "oz",                             "ar": "أونصة"},
    "pure_weight":     {"en": "Pure content",                   "ar": "المحتوى الصافي"},

    # secure carrier
    "carrier":         {"en": "Secure Carrier",               "ar": "شركة النقل الآمن"},
    "carrier_help":    {"en": "Specialised precious-metals transport & armed escort to the Gold Souk",
                        "ar": "نقل مخصص للمعادن الثمينة مع حراسة مسلحة حتى سوق الذهب"},
    "last_mile_full":  {"en": "Secure Delivery to Gold Souk",   "ar": "التوصيل الآمن لسوق الذهب"},
    "distance":        {"en": "Distance",                       "ar": "المسافة"},
    "km":              {"en": "km",                             "ar": "كم"},

    # dual destination
    "pref_port":       {"en": "Preferred Sea Port",             "ar": "ميناء الاستلام المرغوب"},
    "pref_airport":    {"en": "Preferred Airport",              "ar": "مطار الاستلام المرغوب"},
    "arrival_point":   {"en": "Arrival Point",                  "ar": "نقطة الوصول"},

    # security tier
    "sec_tier":        {"en": "Security Tier",                  "ar": "مستوى الأمان"},
    "tier_low":        {"en": "Low",                            "ar": "منخفض"},
    "tier_medium":     {"en": "Medium",                         "ar": "متوسط"},
    "tier_high":       {"en": "High",                           "ar": "عالي"},
    "auto_selected":   {"en": "auto-selected",                  "ar": "محدّد تلقائياً"},
    "auto_cheapest":   {"en": "Auto (cheapest carrier)",        "ar": "تلقائي (الأوفر)"},
    "via_hub":         {"en": "via",                            "ar": "عبر"},
    "direct":          {"en": "Direct",                         "ar": "مباشر"},
    "routes_compared": {"en": "routes compared",                "ar": "مسار تمت مقارنته"},
    "svc_d2d":         {"en": "Door-to-Door",                   "ar": "من الباب للباب"},
    "svc_d2a":         {"en": "Door-to-Airport",                "ar": "من الباب للمطار"},
    "svc_included":    {"en": "all-inclusive",                  "ar": "شامل كل شي"},
    "svc_flat":        {"en": "+ inland secure leg",            "ar": "+ نقل داخلي آمن"},

    # verdict banner
    "verdict_title":   {"en": "Best Route Found",               "ar": "أفضل مسار"},
    "via_sea":         {"en": "by SEA",                         "ar": "بحراً"},
    "via_air":         {"en": "by AIR",                         "ar": "جواً"},
    "via_multi":       {"en": "MULTIMODAL",                     "ar": "متعدد الوسائط"},
    "verdict_because": {"en": "because its total cost is",      "ar": "لأن تكلفته الإجمالية"},
    "vs_others":       {"en": "versus the alternatives",        "ar": "مقارنةً بالبدائل"},
    "report_all":      {"en": "Full Report — All Options Analysed",
                        "ar": "التقرير الكامل — دراسة كل الخيارات"},
    "not_chosen":      {"en": "Alternatives not selected by the AI",
                        "ar": "البدائل التي لم يخترها الذكاء الاصطناعي"},
    "pm_note":         {"en": "Note: base freight is inherently low for small, high-value parcels; "
                              "the bulk of the cost lies in insurance and security — a defining "
                              "characteristic of precious-metals logistics.",
                        "ar": "ملاحظة: تكلفة الشحن الأساسية منخفضة بطبيعتها للطرود الصغيرة عالية القيمة؛ "
                              "الجزء الأكبر من التكلفة يقع في التأمين والأمان — وهي خصيصة المعادن الثمينة."},

    # hazards
    "hazards":         {"en": "Risk Alerts",                    "ar": "تنبيهات المخاطر"},
    "hz_geo":          {"en": "Geopolitical risk",              "ar": "خطر جيوسياسي"},
    "hz_weather":      {"en": "Severe weather",                 "ar": "طقس سيّئ"},
    "hz_none":         {"en": "No significant hazards on this route.",
                        "ar": "لا مخاطر جوهرية على هذا المسار."},
    "hz_at":           {"en": "at",                             "ar": "في"},
    "hz_high":         {"en": "HIGH",                           "ar": "مرتفع"},
    "hz_med":          {"en": "MODERATE",                       "ar": "متوسط"},
}


def t(key: str, lang: str) -> str:
    return T.get(key, {}).get(lang, T.get(key, {}).get("en", key))


def name_of(d: dict, lang: str) -> str:
    return d.get(lang, d.get("en", "?"))


def last_mile_cost(dest_code: str, carrier_key: str, value_usd: float, tier: str) -> dict:
    """
    Secure inland transport from arrival point to Dubai Gold Souk,
    using the chosen carrier + tier-based destination handling fee.
    """
    dest = DEST_POINTS[dest_code]
    car = SECURE_CARRIERS[carrier_key]
    tinfo = SECURITY_TIERS[tier]
    km = dest["souk_km"]
    transport = (car["base_usd"]
                 + car["per_km"] * km
                 + car["per_100k_value"] * (value_usd / 100_000))
    dest_handling = tinfo["dest_handling_aed"] / AED
    return {"cost_usd": round(transport + dest_handling, 2),
            "transport_usd": round(transport, 2),
            "dest_handling_usd": round(dest_handling, 2),
            "km": km, "carrier": carrier_key}


def tier_security(gross_kg: float, tier: str) -> dict:
    """Fixed security fee + per-kg handling for a tier (USD)."""
    tinfo = SECURITY_TIERS[tier]
    fixed = tinfo["security_fixed_aed"] / AED
    handling = tinfo["handling_per_kg_aed"] * gross_kg / AED
    return {"security_usd": round(fixed + handling, 2),
            "fixed_usd": round(fixed, 2),
            "handling_usd": round(handling, 2)}


def tier_insurance(value_usd: float, tier: str) -> float:
    """Cargo insurance premium for a tier (USD)."""
    return round(value_usd * SECURITY_TIERS[tier]["insurance_pct"], 2)
