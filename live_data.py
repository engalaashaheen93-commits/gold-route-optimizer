"""
live_data.py — مصادر بيانات حيّة مجانية بالكامل (بدون مفاتيح ولا تسجيل)

المصادر:
  1. gold-api.com   → أسعار المعادن الفورية (XAU/XAG/XPT) — مجاني، بدون مفتاح، بدون حد
  2. Open-Meteo     → الطقس اللحظي على المسارات — مجاني، بدون مفتاح، 10k طلب/يوم
  3. Frankfurter    → أسعار الصرف (ECB) — مجاني، بدون مفتاح

كل دالة تفشل بأمان (fail-safe) وترجع None عند أي خطأ،
فيرجع التطبيق تلقائياً إلى بيانات المحاكاة.
"""
import requests

TIMEOUT = 8

# ── إحداثيات مدن المسارات ──────────────────────────────────────────
CITY_COORDS = {
    "Singapore": (1.3521, 103.8198),
    "Hong Kong": (22.3193, 114.1694),
    "Shanghai":  (31.2304, 121.4737),
    "Mumbai":    (19.0760, 72.8777),
    "Istanbul":  (41.0082, 28.9784),
    "Dubai":     (25.2048, 55.2708),
}

# رموز الطقس (WMO) → مستوى المخاطرة
_SEVERE = {95, 96, 99, 65, 67, 75, 82, 86}     # عواصف رعدية / مطر غزير / ثلج كثيف
_MODERATE = {51, 53, 55, 61, 63, 71, 73, 80, 81, 45, 48}  # رذاذ / مطر / ضباب


def get_live_metal_price(symbol: str = "XAU") -> dict | None:
    """
    السعر الفوري للمعدن بالدولار للأونصة.
    symbol: XAU (ذهب) | XAG (فضة) | XPT (بلاتين)
    """
    try:
        r = requests.get(f"https://api.gold-api.com/price/{symbol}", timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        d = r.json()
        price = d.get("price")
        if not price:
            return None
        return {
            "symbol":       d.get("symbol", symbol),
            "name":         d.get("name", ""),
            "price_usd_oz": float(price),
            "price_usd_kg": round(float(price) * 32.1507, 2),  # أونصة تروي → كغ
            "updated":      d.get("updatedAt", ""),
            "source":       "live",
        }
    except Exception:
        return None


def get_live_weather(city: str) -> dict | None:
    """حالة الطقس اللحظية وتحويلها إلى درجة مخاطرة للشحن."""
    coords = CITY_COORDS.get(city)
    if not coords:
        return None
    lat, lon = coords
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,wind_speed_10m,weather_code,precipitation"
        )
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        cur = r.json().get("current", {})

        wind = float(cur.get("wind_speed_10m", 0))   # كم/ساعة
        code = int(cur.get("weather_code", 0))
        temp = cur.get("temperature_2m")

        # حساب درجة المخاطرة 0..1
        score = 0.05
        if code in _SEVERE:
            score += 0.55
        elif code in _MODERATE:
            score += 0.25
        if wind > 50:
            score += 0.30
        elif wind > 30:
            score += 0.15
        score = round(min(score, 1.0), 2)

        risk = "مرتفع" if score > 0.55 else ("متوسط" if score > 0.25 else "منخفض")

        desc = _describe(code)
        return {
            "risk":        risk,
            "score":       score,
            "description": f"{desc} — {temp}°م، رياح {wind:.0f} كم/س",
            "source":      "live",
        }
    except Exception:
        return None


def _describe(code: int) -> str:
    """وصف عربي مبسّط لرمز الطقس WMO."""
    if code == 0:
        return "صافٍ"
    if code in (1, 2, 3):
        return "غائم جزئياً"
    if code in (45, 48):
        return "ضباب"
    if code in (51, 53, 55):
        return "رذاذ"
    if code in (61, 63, 65, 80, 81, 82):
        return "أمطار"
    if code in (71, 73, 75, 85, 86):
        return "ثلوج"
    if code in (95, 96, 99):
        return "عواصف رعدية"
    return "غير محدد"


def get_usd_aed_rate() -> float | None:
    """سعر صرف الدولار مقابل الدرهم الإماراتي (مرجعي)."""
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=AED", timeout=TIMEOUT
        )
        if r.status_code != 200:
            return None
        return float(r.json()["rates"]["AED"])
    except Exception:
        return None


# ── اختبار سريع من سطر الأوامر ─────────────────────────────────────
if __name__ == "__main__":
    print("سعر الذهب:", get_live_metal_price("XAU"))
    print("طقس سنغافورة:", get_live_weather("Singapore"))
    print("سعر الصرف:", get_usd_aed_rate())
