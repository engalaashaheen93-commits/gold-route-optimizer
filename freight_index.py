"""
freight_index.py — أسعار الشحن البحري الحيّة من مصادر رسمية مجانية

المصدر الرئيسي: بورصة شنغهاي للشحن (Shanghai Shipping Exchange - SSE)
    الرابط: https://en.sse.net.cn/indices/scfinew.jsp
    المؤشر: SCFI (Shanghai Containerized Freight Index)
    - يغطي 13 مساراً من شنغهاي، من ضمنها "Persian Gulf" (الخليج العربي / دبي)
    - الوحدة: دولار أمريكي / TEU  ← أسعار فعلية لا مجرد أرقام قياسية
    - يشمل: أجرة الشحن + رسوم إضافية منها:
        • PCS — رسم ازدحام الميناء (Port Congestion Surcharge)
        • WRS — رسم مخاطر الحرب (War Risk Surcharge)
        • BAF/LSS — رسوم الوقود
    - المصدر: تقارير 22 شركة خطوط ملاحية (Maersk, MSC, CMA-CGM, COSCO...)
      و26 شركة شحن ووساطة
    - يُنشر كل جمعة الساعة 15:00 بتوقيت بكين
    - مؤشر متوافق مع IOSCO ومتداول كعقود آجلة في سنغافورة وشيكاغو

ملاحظة منهجية للرسالة:
    رسم ازدحام الميناء (PCS) مُدرج ضمن المؤشر، أي أن السعر يعكس
    حالة الميناء التشغيلية ضمنياً — وهو ما يخدم متغيّر "حالة الموانئ"
    في نموذج القرار.

جميع الدوال تفشل بأمان وتُرجع None عند أي خطأ،
فيرجع التطبيق تلقائياً إلى البيانات التقديرية.
"""
import re
import requests

TIMEOUT = 10
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

SSE_SCFI_PAGE = "https://en.sse.net.cn/indices/scfinew.jsp"

# أسماء المسارات كما تظهر في جدول البورصة → رمز المسار في تطبيقنا
ROUTE_KEYWORDS = {
    "PVG": ["persian gulf", "gulf", "dubai"],          # شنغهاي → الخليج (دبي)
    "SIN": ["southeast asia", "singapore"],            # شنغهاι → جنوب شرق آسيا
    "HKG": ["hong kong", "hongkong"],                  # شنغهاي → هونغ كونغ
}


def _to_float(txt: str):
    """يحوّل نصاً إلى رقم مع تنظيف الفواصل والمسافات."""
    if not txt:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", str(txt))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def fetch_scfi_table() -> dict | None:
    """
    يجلب جدول SCFI من موقع بورصة شنغهاي ويستخرج أسعار المسارات.

    يُرجع:
        {
          "composite": 3239.64,
          "routes": {"Persian Gulf": 1234.0, ...},
          "source": "live",
          "provider": "Shanghai Shipping Exchange (SCFI)"
        }
      أو None عند الفشل.
    """
    try:
        r = requests.get(SSE_SCFI_PAGE, timeout=TIMEOUT, headers=UA)
        if r.status_code != 200:
            return None

        html = r.text
        # الصفحة قد تكون بترميز صيني
        try:
            html = r.content.decode("utf-8", errors="ignore")
        except Exception:
            pass

        routes = {}
        composite = None

        # ── استخراج صفوف الجدول ──────────────────────────────────
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I)
        for row in rows:
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)
            if len(cells) < 2:
                continue
            # تنظيف الوسوم من كل خلية
            clean = [re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ").strip()
                     for c in cells]
            label = clean[0].lower()

            # المؤشر المركّب — نأخذ آخر رقم في الصف (المؤشر الحالي لا السابق)
            if "comprehensive" in label or "composite" in label:
                for c in reversed(clean[1:]):
                    v = _to_float(c)
                    if v and v > 100:
                        composite = v
                        break

            # المسارات المفردة — نأخذ آخر رقم معقول في الصف (المؤشر الحالي)
            for code, keys in ROUTE_KEYWORDS.items():
                if any(k in label for k in keys):
                    for c in reversed(clean[1:]):
                        v = _to_float(c)
                        if v and v > 10:
                            routes[clean[0].strip()] = v
                            break

        if composite or routes:
            return {
                "composite": composite,
                "routes": routes,
                "source": "live",
                "provider": "Shanghai Shipping Exchange (SCFI)",
                "url": SSE_SCFI_PAGE,
            }
        return None

    except Exception:
        return None


def get_gulf_freight_rate() -> dict | None:
    """
    سعر الشحن على مسار شنغهاي → الخليج العربي (دبي) بالدولار لكل TEU.
    هذا هو المسار الأوثق صلة برسالتنا.
    """
    data = fetch_scfi_table()
    if not data:
        return None

    for name, val in data.get("routes", {}).items():
        if any(k in name.lower() for k in ("gulf", "persian", "dubai")):
            return {
                "route":        "شنغهاي ← الخليج العربي (دبي)",
                "rate_usd_teu": val,
                "provider":     data["provider"],
                "source":       "live",
            }

    # المسار غير موجود لكن المؤشر المركّب متاح
    if data.get("composite"):
        return {
            "route":        "المؤشر المركّب (جميع المسارات)",
            "composite":    data["composite"],
            "provider":     data["provider"],
            "source":       "live",
        }
    return None


def get_market_pressure() -> float | None:
    """
    مُعامل ضغط السوق: نسبة المؤشر المركّب الحالي إلى قيمة مرجعية.

    يُستخدم لتعديل تقديرات أسعار الشحن الداخلية بحيث تعكس
    اتجاه السوق الفعلي بدل أن تبقى ثابتة.

    > 1.0  ← السوق أغلى من المرجع
    < 1.0  ← السوق أرخص من المرجع
    """
    data = fetch_scfi_table()
    if not data or not data.get("composite"):
        return None
    BASELINE = 2000.0   # قيمة مرجعية تقريبية للمؤشر المركّب
    ratio = data["composite"] / BASELINE
    # نحصر المعامل في نطاق معقول تفادياً للقيم الشاذة
    return round(max(0.5, min(ratio, 2.5)), 3)


if __name__ == "__main__":
    print("جدول SCFI:", fetch_scfi_table())
    print("مسار الخليج:", get_gulf_freight_rate())
    print("ضغط السوق:", get_market_pressure())
