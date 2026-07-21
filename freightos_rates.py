"""
freightos_rates.py — LIVE air/ocean freight price ranges from Freightos.

Uses the public Freightos shippingCalculator endpoint:
    https://ship.freightos.com/api/shippingCalculator
No API key required. Per Freightos terms, the app must show a visible
credit + link to https://ship.freightos.com (added in the sidebar/footer).

We query in "boxes" mode with the shipment's real weight, so the price
reflects a small parcel rather than a full container. Returns the mid-point
of the quoted range in USD, or None on any failure (→ app falls back to
its internal freight estimate). Insurance & security are NOT taken from
here — they use the agreed 3-tier model.
"""
import requests
import xml.etree.ElementTree as ET

TIMEOUT = 10
BASE = "https://ship.freightos.com/api/shippingCalculator"

# origin code → Freightos-friendly location string
ORIGIN_LOC = {
    "PVG": "Shanghai,China",
    "HKG": "HongKong,HongKong",
    "SIN": "Singapore,Singapore",
    "IST": "Istanbul,Turkey",
}
# Dubai as the UAE gateway (Freightos resolves to nearest port/airport)
DEST_LOC = "Dubai,UnitedArabEmirates"

# Freightos "mode" → our mode
# boxes = LCL/air parcel style pricing


def _parse(text: str):
    """Parse Freightos XML/JSON-ish response → (min,max,mode) list."""
    quotes = []
    try:
        root = ET.fromstring(text)
    except Exception:
        return quotes
    # response contains <mode> elements with price min/max
    for mode in root.iter():
        tag = mode.tag.lower()
        if tag.endswith("mode") or tag.endswith("service"):
            price_min = price_max = None
            mname = mode.get("name") or mode.get("mode") or ""
            for child in mode.iter():
                ct = child.tag.lower()
                if ct.endswith("min") and child.text:
                    try: price_min = float(child.text)
                    except: pass
                if ct.endswith("max") and child.text:
                    try: price_max = float(child.text)
                    except: pass
            if price_min or price_max:
                quotes.append({"mode": mname,
                               "min": price_min or price_max,
                               "max": price_max or price_min})
    return quotes


def get_freight_quote(origin_code: str, gross_kg: float, mode: str) -> dict | None:
    """
    Live freight price for a small shipment (boxes mode) origin → Dubai.
    mode: 'air' | 'sea' | 'multimodal' (multimodal treated as sea here).
    Returns {'usd': <mid>, 'min':..,'max':..,'source':'live'} or None.
    """
    origin = ORIGIN_LOC.get(origin_code)
    if not origin:
        return None

    # dimensions: assume a compact secured box; weight drives the quote
    params = {
        "loadtype": "boxes",
        "weight": max(int(gross_kg), 1),
        "width": 40, "length": 40, "height": 40,  # cm, compact bullion case
        "quantity": 1,
        "origin": origin,
        "destination": DEST_LOC,
        "format": "xml",
    }
    try:
        r = requests.get(BASE, params=params, timeout=TIMEOUT,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return None
        quotes = _parse(r.text)
        if not quotes:
            return None

        want_air = (mode == "air")
        picked = None
        for q in quotes:
            nm = q["mode"].lower()
            if want_air and ("air" in nm):
                picked = q; break
            if not want_air and ("ocean" in nm or "sea" in nm or "lcl" in nm):
                picked = q; break
        if not picked:
            picked = quotes[0]

        mid = (picked["min"] + picked["max"]) / 2
        return {"usd": round(mid, 2), "min": picked["min"],
                "max": picked["max"], "source": "live"}
    except Exception:
        return None


if __name__ == "__main__":
    for m in ("air", "sea"):
        print(m, get_freight_quote("PVG", 50, m))
