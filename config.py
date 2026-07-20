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
# DUBAI DESTINATION PORTS + onward delivery to Gold Souk (Deira)
# last-mile cost is an estimate (USD) — editable
# ══════════════════════════════════════════════════════════════════
DEST_POINTS = {
    # ── Sea ports ──
    "JEA": {"en": "Jebel Ali Port",  "ar": "ميناء جبل علي", "type": "sea",
            "souk_km": 45, "flag": "🚢"},
    "RAS": {"en": "Port Rashid",     "ar": "ميناء راشد",    "type": "sea",
            "souk_km": 12, "flag": "🚢"},
    "HAM": {"en": "Hamriyah Port",   "ar": "ميناء الحمرية", "type": "sea",
            "souk_km": 28, "flag": "🚢"},
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
}

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
    "depart_date":     {"en": "Requested Departure Date",        "ar": "تاريخ الانطلاق المطلوب"},
    "arrive_date":     {"en": "Required Arrival Date",           "ar": "تاريخ الاستلام المطلوب"},
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

    "gross_weight":    {"en": "Gross weight",                   "ar": "الوزن الإجمالي"},
    "pure_weight":     {"en": "Pure content",                   "ar": "المحتوى الصافي"},

    # secure carrier
    "carrier":         {"en": "Secure Inland Carrier",          "ar": "شركة النقل الآمن الداخلي"},
    "carrier_help":    {"en": "Specialised precious-metals transport & armed escort to the Gold Souk",
                        "ar": "نقل مخصص للمعادن الثمينة مع حراسة مسلحة حتى سوق الذهب"},
    "last_mile_full":  {"en": "Secure Delivery to Gold Souk",   "ar": "التوصيل الآمن لسوق الذهب"},
    "distance":        {"en": "Distance",                       "ar": "المسافة"},
    "km":              {"en": "km",                             "ar": "كم"},
}


def t(key: str, lang: str) -> str:
    return T.get(key, {}).get(lang, T.get(key, {}).get("en", key))


def name_of(d: dict, lang: str) -> str:
    return d.get(lang, d.get("en", "?"))


def last_mile_cost(dest_code: str, carrier_key: str, value_usd: float) -> dict:
    """
    Secure inland transport cost from the arrival point to the Dubai Gold Souk,
    using the chosen specialised carrier.
    """
    dest = DEST_POINTS[dest_code]
    car = SECURE_CARRIERS[carrier_key]
    km = dest["souk_km"]
    cost = (car["base_usd"]
            + car["per_km"] * km
            + car["per_100k_value"] * (value_usd / 100_000))
    return {"cost_usd": round(cost, 2), "km": km, "carrier": carrier_key}
