"""
weight_elicitation.py — Deriving TOPSIS criterion weights from natural language.

Why this module exists
----------------------
A standing problem in multi-criteria decision analysis (MCDM) is where the
criterion weights come from. They are usually fixed by the analyst in advance,
which forces every user into one predetermined trade-off — even though real
shipments differ: one is urgent, another is cost-sensitive, a third is moving
through a tense corridor.

This module lets the decision-maker state the priority for THIS shipment in
plain language ("urgent delivery for a key client, cost is secondary"), and
uses a large language model to convert that statement into a quantitative
weight vector that TOPSIS then consumes.

The AI therefore participates in FORMING the decision function, not merely in
explaining its result. Everything downstream — the ranking, the recommended
route — changes with it.

Safeguards
----------
Because a language model output is driving a numeric decision, the result is
never trusted blindly:
  * the returned object must contain exactly the expected criteria;
  * every weight must be a number within [0, 1];
  * weights are renormalised so they sum to 1 (a TOPSIS requirement);
  * any failure — no API key, malformed reply, network error — falls back
    silently to the default weights, so the system always produces a result.
The user is shown both vectors side by side and may reject the derived one.
"""
import json
from config import TOPSIS_WEIGHTS, ANTHROPIC_API_KEY

CRITERIA = list(TOPSIS_WEIGHTS.keys())

# Human-readable meaning of each criterion, sent to the model so it can map
# a free-text priority onto the right axis.
CRITERION_MEANING = {
    "total_cost":   "total landed cost of the shipment, door to the Gold Souk",
    "transit_time": "total elapsed transit time from departure to arrival",
    "geopolitical": "geopolitical instability along the route (conflict zones, sensitive straits)",
    "weather_risk": "adverse weather at any point on the route",
    "war_risk":     "war-risk exposure and its insurance premium",
}

MIN_W, MAX_W = 0.02, 0.70      # no criterion may vanish or dominate entirely


def _validate(raw: dict) -> dict | None:
    """
    Check the model's reply and coerce it into a usable weight vector.
    Returns None if the reply cannot be trusted.
    """
    if not isinstance(raw, dict):
        return None
    weights = raw.get("weights")
    if not isinstance(weights, dict):
        return None

    clean = {}
    for c in CRITERIA:
        v = weights.get(c)
        if not isinstance(v, (int, float)):
            return None                     # a missing criterion invalidates the set
        v = float(v)
        if v < 0 or v > 1:
            return None
        clean[c] = min(max(v, MIN_W), MAX_W)

    total = sum(clean.values())
    if total <= 0:
        return None
    return {c: v / total for c, v in clean.items()}     # renormalise to 1.0


def _prompt(text: str) -> str:
    lines = "\n".join(f'  "{c}": {CRITERION_MEANING[c]}' for c in CRITERIA)
    return (
        "You assign criterion weights for a TOPSIS decision model that ranks "
        "shipping routes for precious metals from Asia to Dubai.\n\n"
        "The criteria are:\n" + lines + "\n\n"
        "The decision-maker describes their priority for one specific shipment "
        "below. Translate that priority into weights.\n\n"
        "Rules:\n"
        "- Return ALL five criteria.\n"
        "- Each weight is a decimal between 0.02 and 0.70.\n"
        "- The five weights must sum to approximately 1.0.\n"
        "- A priority the user stresses gets a higher weight; one they call "
        "secondary gets a lower weight; anything unmentioned stays near its "
        "default.\n"
        "- Default weights are: " +
        ", ".join(f"{c} {TOPSIS_WEIGHTS[c]:.2f}" for c in CRITERIA) + ".\n\n"
        "Reply with ONLY a JSON object, no preamble and no markdown fences:\n"
        '{"weights": {"total_cost": 0.0, "transit_time": 0.0, "geopolitical": 0.0, '
        '"weather_risk": 0.0, "war_risk": 0.0}, '
        '"rationale": "one short sentence, in the same language the user wrote in"}\n\n'
        f"Decision-maker's priority:\n{text.strip()}"
    )


def derive(text: str) -> dict:
    """
    Convert a free-text priority statement into TOPSIS weights.

    Returns:
      {
        "weights":   dict,          # always usable (derived or default)
        "source":    "ai" | "default",
        "rationale": str,           # model's justification, or "" 
        "changed":   dict,          # per-criterion delta vs the defaults
        "error":     str | None,    # why the fallback was used, if it was
      }
    """
    default = {"weights": dict(TOPSIS_WEIGHTS), "source": "default",
               "rationale": "", "changed": {}, "error": None}

    if not text or not text.strip():
        return default
    if not ANTHROPIC_API_KEY:
        default["error"] = "no_api_key"
        return default

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": _prompt(text)}],
        )
        reply = msg.content[0].text.strip()
        # strip accidental code fences
        if reply.startswith("```"):
            reply = reply.split("```")[1]
            reply = reply[4:] if reply.lower().startswith("json") else reply
        parsed = json.loads(reply)
        weights = _validate(parsed)
        if weights is None:
            default["error"] = "invalid_reply"
            return default
        changed = {c: round(weights[c] - TOPSIS_WEIGHTS[c], 4) for c in CRITERIA}
        return {"weights": weights, "source": "ai",
                "rationale": str(parsed.get("rationale", ""))[:400],
                "changed": changed, "error": None}
    except Exception as e:
        default["error"] = type(e).__name__
        return default


def describe(result: dict, lang: str = "en") -> list:
    """Rows for a side-by-side default-vs-derived comparison table."""
    w = result["weights"]
    rows = []
    for c in CRITERIA:
        d = TOPSIS_WEIGHTS[c]
        n = w[c]
        arrow = "=" if abs(n - d) < 0.005 else ("^" if n > d else "v")
        rows.append({"criterion": c,
                     "default_pct": round(d * 100, 1),
                     "derived_pct": round(n * 100, 1),
                     "direction": arrow})
    return rows
