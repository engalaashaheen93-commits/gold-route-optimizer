"""
Recommendation text generator.
Uses Claude API when a key is set; otherwise a bilingual rule-based fallback.
"""
from config import ANTHROPIC_API_KEY, name_of


def build_recommendation(ranked: list, lang: str) -> str:
    best = ranked[0]
    # try Claude
    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            prompt = _make_prompt(ranked, lang)
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            pass
    return _fallback(ranked, lang)


def _make_prompt(ranked, lang):
    best = ranked[0]
    lines = []
    for r in ranked[:4]:
        if not r.get("feasible", True):
            continue
        lines.append(f"- {name_of(r['origin'],'en')} via {r['mode']}: "
                     f"score {r['cc_score']}, total ${r['cost']['total']:,.0f}, "
                     f"{r['transit_h']}h transit")
    tbl = "\n".join(lines)
    langname = "Arabic" if lang == "ar" else "English"
    return (f"You are a logistics advisor for precious-metals shipping to Dubai. "
            f"In {langname}, write a concise 3-4 sentence recommendation explaining why the "
            f"top route was chosen over the alternatives. Be specific about cost, time and risk.\n\n"
            f"Ranked options:\n{tbl}\n\nRecommended: {name_of(best['origin'],'en')} via {best['mode']}.")


def _fallback(ranked, lang):
    best = ranked[0]
    feasible = [r for r in ranked if r.get("feasible", True)]
    alt = feasible[1] if len(feasible) > 1 else None

    o_name = name_of(best["origin"], lang)
    p_name = name_of(best["port"], lang)
    mode_map = {"air": {"en": "air", "ar": "الجوي"},
                "sea": {"en": "sea", "ar": "البحري"},
                "multimodal": {"en": "multimodal", "ar": "متعدد الوسائط"}}
    m_name = mode_map[best["mode"]][lang]

    if lang == "ar":
        txt = (f"المسار الموصى به هو **{o_name} ← {p_name}** عبر الشحن {m_name}، "
               f"إذ حصل على أعلى درجة تقييم ({best['cc_score']}) بتكلفة إجمالية "
               f"{best['cost']['total']:,.0f} دولار وزمن عبور {best['transit_h']} ساعة. ")
        if alt:
            diff = alt["cost"]["total"] - best["cost"]["total"]
            txt += (f"مقارنةً بالبديل التالي ({name_of(alt['origin'],'ar')} عبر "
                    f"{mode_map[alt['mode']]['ar']})، يوفّر هذا المسار "
                    f"{abs(diff):,.0f} دولار. ")
        badges = best.get("badges", [])
        if "cheapest" in badges: txt += "وهو الأقل تكلفةً بين كل الخيارات. "
        if "fastest" in badges: txt += "وهو الأسرع أيضاً. "
        if "safest" in badges: txt += "ويتمتع بأدنى درجة مخاطرة أمنية. "
        return txt

    txt = (f"The recommended route is **{o_name} → {p_name}** via {m_name} shipping, "
           f"achieving the highest TOPSIS score ({best['cc_score']}) with a total landed "
           f"cost of ${best['cost']['total']:,.0f} and {best['transit_h']}h transit. ")
    if alt:
        diff = alt["cost"]["total"] - best["cost"]["total"]
        txt += (f"Compared to the next alternative ({name_of(alt['origin'],'en')} via "
                f"{alt['mode']}), it saves ${abs(diff):,.0f}. ")
    badges = best.get("badges", [])
    if "cheapest" in badges: txt += "It is the lowest-cost option overall. "
    if "fastest" in badges: txt += "It is also the fastest. "
    if "safest" in badges: txt += "It carries the lowest security risk. "
    return txt
