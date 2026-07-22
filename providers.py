"""
Data providers — live where free, realistic simulation otherwise.
Every function fails safe (returns mock) so the app never crashes.
"""
import random
import requests
from config import APP_MODE, OPENWEATHER_API_KEY

TIMEOUT = 8
random.seed()   # real variance each run

# ══════════════════════════════════════════════════════════════════
# BASE FREIGHT TABLE  (origin → Dubai)  — USD per kg (air) / per kg (sea)
# realistic estimates, editable
# ══════════════════════════════════════════════════════════════════
BASE_FREIGHT = {
    "PVG": {"air": 4.30, "sea": 0.75, "air_h": 9,  "sea_d": 18},   # Shanghai
    "HKG": {"air": 4.05, "sea": 0.80, "air_h": 8,  "sea_d": 16},   # Hong Kong
    "SIN": {"air": 4.80, "sea": 0.70, "air_h": 8,  "sea_d": 14},   # Singapore
    "IST": {"air": 3.60, "sea": 1.05, "air_h": 6,  "sea_d": 11},   # Istanbul
}

# customs for INVESTMENT GOLD into Dubai (DMCC/free-zone):
# investment-grade bullion is largely duty-exempt in the UAE; only a small
# clearance/handling + documentation fee applies. rate is a tiny nominal %.
CUSTOMS = {
    "CN": {"rate": 0.0000, "complexity": 4, "handling": 850},
    "HK": {"rate": 0.0000, "complexity": 2, "handling": 500},
    "SG": {"rate": 0.0000, "complexity": 2, "handling": 600},
    "TR": {"rate": 0.0005, "complexity": 3, "handling": 700},
}

# geopolitical corridor score 0..1 (higher = riskier) + war-risk premium %
# war-risk insurance = 0.1% of shipment value (real market rate, flat).
# geo scores are kept only for hazard flagging, NOT for the war premium.
CORRIDOR = {
    "PVG": {"geo": 0.20, "war": 0.0010},
    "HKG": {"geo": 0.18, "war": 0.0010},
    "SIN": {"geo": 0.12, "war": 0.0010},
    "IST": {"geo": 0.45, "war": 0.0010},
}

CITY_COORDS = {
    "Shanghai": (31.2304, 121.4737),
    "Hong Kong": (22.3193, 114.1694),
    "Singapore": (1.3521, 103.8198),
    "Istanbul": (41.0082, 28.9784),
    "Dubai": (25.2048, 55.2708),
}

MOCK_WEATHER = {
    "Shanghai":  {"level": "med",  "score": 0.35},
    "Hong Kong": {"level": "med",  "score": 0.40},
    "Singapore": {"level": "high", "score": 0.55},
    "Istanbul":  {"level": "low",  "score": 0.20},
    "Dubai":     {"level": "low",  "score": 0.15},
}


# ══════════════════════════════════════════════════════════════════
# METAL SPOT PRICE  (live: gold-api.com — free, no key)
# ══════════════════════════════════════════════════════════════════
def get_metal_price(symbol: str) -> dict:
    if APP_MODE in ("live", "hybrid"):
        try:
            r = requests.get(f"https://api.gold-api.com/price/{symbol}", timeout=TIMEOUT)
            if r.status_code == 200:
                d = r.json()
                if d.get("price"):
                    return {"symbol": symbol, "price_oz": float(d["price"]),
                            "price_g": float(d["price"]) / 31.1035, "source": "live"}
        except Exception:
            pass
    # fallback mock spot prices (USD/oz)
    mock = {"XAU": 4030.0, "XAG": 48.5, "XPT": 1010.0, "XPD": 1150.0}
    p = mock.get(symbol, 4030.0)
    return {"symbol": symbol, "price_oz": p, "price_g": p / 31.1035, "source": "mock"}


# ══════════════════════════════════════════════════════════════════
# WEATHER  (live: Open-Meteo — free, no key)
# ══════════════════════════════════════════════════════════════════
_SEVERE = {95, 96, 99, 65, 67, 75, 82, 86}
_MODER = {51, 53, 55, 61, 63, 71, 73, 80, 81, 45, 48}


def get_weather(city: str) -> dict:
    if APP_MODE in ("live", "hybrid"):
        coords = CITY_COORDS.get(city)
        if coords:
            try:
                lat, lon = coords
                url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}"
                       f"&longitude={lon}&current=temperature_2m,wind_speed_10m,weather_code")
                r = requests.get(url, timeout=TIMEOUT)
                if r.status_code == 200:
                    cur = r.json().get("current", {})
                    wind = float(cur.get("wind_speed_10m", 0))
                    code = int(cur.get("weather_code", 0))
                    score = 0.05
                    if code in _SEVERE: score += 0.55
                    elif code in _MODER: score += 0.25
                    if wind > 50: score += 0.30
                    elif wind > 30: score += 0.15
                    score = round(min(score, 1.0), 2)
                    lvl = "high" if score > 0.55 else ("med" if score > 0.25 else "low")
                    return {"level": lvl, "score": score, "source": "live"}
            except Exception:
                pass
    m = MOCK_WEATHER.get(city, {"level": "med", "score": 0.3})
    return {**m, "source": "mock"}


# ══════════════════════════════════════════════════════════════════
# FREIGHT  (per origin, per mode) with SCFI market-pressure if available
# ══════════════════════════════════════════════════════════════════
def _market_pressure() -> tuple[float, str]:
    if APP_MODE in ("live", "hybrid"):
        try:
            from freight_index import get_market_pressure
            p = get_market_pressure()
            if p:
                return p, "live"
        except Exception:
            pass
    return 1.0, "mock"


def get_freight(origin_code: str, gross_kg: float, mode: str) -> dict:
    base = BASE_FREIGHT.get(origin_code, {"air": 4.5, "sea": 0.85, "air_h": 8, "sea_d": 16})
    pressure, src = _market_pressure()
    variance = random.uniform(0.94, 1.06)

    if mode == "air":
        cost = base["air"] * gross_kg * variance * pressure
        hours = base["air_h"]
    elif mode == "sea":
        cost = base["sea"] * gross_kg * variance * pressure
        hours = base["sea_d"] * 24
    else:  # multimodal — blend
        cost = ((base["air"] + base["sea"]) / 1.7) * gross_kg * variance * pressure
        hours = ((base["air_h"] + base["sea_d"] * 24) / 2.3)

    freight_source = src
    live_range = None

    # ── LIVE freight from Freightos (free, no key) ──
    if APP_MODE in ("live", "hybrid"):
        try:
            from freightos_rates import get_freight_quote
            q = get_freight_quote(origin_code, gross_kg, mode)
            if q and q["usd"] > 0:
                cost = q["usd"]
                freight_source = "live"
                live_range = (q["min"], q["max"])
        except Exception:
            pass

    return {
        "freight_usd": round(cost, 2),
        "transit_h": round(hours, 1),
        "per_kg": round(cost / gross_kg, 2) if gross_kg else 0,
        "market_pressure": pressure,
        "live_range": live_range,
        "source": freight_source,
    }


# ══════════════════════════════════════════════════════════════════
# CUSTOMS
# ══════════════════════════════════════════════════════════════════
def get_customs(country: str, value_usd: float, gross_kg: float) -> dict:
    c = CUSTOMS.get(country, {"rate": 0.008, "complexity": 3, "handling": 700})
    duty = value_usd * c["rate"]
    total = duty + c["handling"]
    return {"total_usd": round(total, 2), "complexity": c["complexity"],
            "rate": c["rate"], "handling": c["handling"]}


# ══════════════════════════════════════════════════════════════════
# SECURITY
# ══════════════════════════════════════════════════════════════════
def get_security(origin_code: str, escort: bool, value_usd: float) -> dict:
    base = 1500 if escort else 400
    # scale a little with value
    scaled = base + value_usd * 0.00015
    risk = 0.25 if escort else 0.55
    return {"escort_usd": round(scaled, 2), "risk_score": risk}


# ══════════════════════════════════════════════════════════════════
# INSURANCE  (cargo + war-risk)
# ══════════════════════════════════════════════════════════════════
def get_insurance(value_usd: float, full_cover: bool, origin_code: str) -> dict:
    cargo_rate = 0.0018 if full_cover else 0.0010
    cargo = value_usd * cargo_rate
    war_rate = CORRIDOR.get(origin_code, {}).get("war", 0.0010)
    war = value_usd * war_rate
    return {"cargo_usd": round(cargo, 2), "war_usd": round(war, 2), "war_rate": war_rate}


# ══════════════════════════════════════════════════════════════════
# GEOPOLITICAL
# ══════════════════════════════════════════════════════════════════
def get_geopolitical(origin_code: str) -> dict:
    g = CORRIDOR.get(origin_code, {"geo": 0.25})
    return {"score": g["geo"]}


# ══════════════════════════════════════════════════════════════════
# PORT WAITING  (Dubai side)
# ══════════════════════════════════════════════════════════════════
def get_port_wait(port_code: str) -> dict:
    waits = {"JEA": 6, "HAM": 4, "SHJP": 4, "KHL": 5, "ZYD": 5,
             "KHR": 3, "FUJ": 3, "DXB": 1, "SHJ": 1, "AUH": 1}
    h = waits.get(port_code, 4) * random.uniform(0.8, 1.3)
    return {"wait_h": round(h, 1)}
