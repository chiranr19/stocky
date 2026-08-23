# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Named patterns that make a setup good or bad — the showcase for both sides.

The Entry Radar answers "which dips are worth studying". This module answers
the other half a beginner needs: **what does a bad setup look like, and why is
it bad?** Each flag is a specific, named, recognizable pattern with the reason
it matters and what veterans actually do about it.

Two polarities:
  * ``risk``     — patterns that have historically hurt people (falling knives,
                   value traps, paying in volatility for nothing).
  * ``strength`` — patterns that describe a durable setup.

Pure and deterministic over ``StockMetrics`` so it unit-tests cleanly. Nothing
here is advice: risk flags describe hazards to recognize, not instructions to
sell, and strength flags describe quality, not a reason to buy.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import MIN_DOLLAR_VOLUME
from .metrics import StockMetrics

# Severity → how much it counts toward the "poor setup" ranking.
SEVERITY_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}


@dataclass(frozen=True)
class Flag:
    code: str
    label: str
    kind: str  # 'risk' | 'strength'
    severity: str  # 'high' | 'medium' | 'low'
    why: str  # what the pattern means
    what_vets_do: str  # how an experienced investor treats it


# --------------------------------------------------------------------------- #
# Risk patterns — the "bad picks" showcase
# --------------------------------------------------------------------------- #
def _risk_flags(m: StockMetrics, depth_pct: float | None) -> list[Flag]:
    out: list[Flag] = []
    ret_1y = m.ret_1y if m.ret_1y is not None else 0.0
    ret_3m = m.ret_3m if m.ret_3m is not None else 0.0
    vol = m.vol_90d if m.vol_90d is not None else 0.0

    # The classic beginner trap: buying something only because it fell a lot.
    if not m.above_ma200 and (depth_pct or 0) >= 15.0 and ret_3m <= -10.0:
        out.append(
            Flag(
                code="falling_knife",
                label="Falling knife",
                kind="risk",
                severity="high",
                why=(
                    f"Down {abs(ret_3m):.0f}% over three months and trading below its "
                    "200-day average. The trend is broken, not merely dipping — the "
                    "cheap price keeps getting cheaper."
                ),
                what_vets_do=(
                    "Wait for the price to reclaim the 200-day average before treating "
                    "it as a setup. Missing the exact bottom costs far less than "
                    "catching the knife."
                ),
            )
        )
    elif not m.above_ma200:
        out.append(
            Flag(
                code="broken_trend",
                label="Trend broken",
                kind="risk",
                severity="high",
                why=(
                    "Price sits below its 200-day average — the single line most "
                    "investors use to separate an uptrend from a downtrend."
                ),
                what_vets_do=(
                    "Treat everything else about the stock as secondary until this "
                    "repairs. Most rules that work in uptrends fail here."
                ),
            )
        )

    # Cheap for a reason: at the lows, trend broken, and a losing year.
    if m.range_52w_position <= 0.15 and not m.above_ma200 and ret_1y < 0:
        out.append(
            Flag(
                code="value_trap",
                label="Possible value trap",
                kind="risk",
                severity="high",
                why=(
                    f"Near its 52-week low, below the 200-day average, and down "
                    f"{abs(ret_1y):.0f}% over the year. 'Cheap' here reflects a market "
                    "verdict, not a discount."
                ),
                what_vets_do=(
                    "Demand a reason the business is turning before the chart does. "
                    "Without one, low prices tend to get lower."
                ),
            )
        )

    # The worst quadrant of the risk map: paid in swings, got nothing back.
    if vol >= 40.0 and ret_1y < 0:
        out.append(
            Flag(
                code="volatility_trap",
                label="Paid in volatility, not returns",
                kind="risk",
                severity="high",
                why=(
                    f"{vol:.0f}% annualized volatility with a {ret_1y:.0f}% year — a "
                    "wild ride that went nowhere. This is the bottom-right corner of "
                    "the risk-vs-reward map."
                ),
                what_vets_do=(
                    "Compare it against simply owning the index: same or better return "
                    "with a fraction of the stress is the benchmark to beat."
                ),
            )
        )
    elif vol >= 60.0:
        out.append(
            Flag(
                code="very_high_volatility",
                label="Very high volatility",
                kind="risk",
                severity="medium",
                why=(
                    f"{vol:.0f}% annualized means roughly ±{vol / (52**0.5):.0f}% "
                    "swings in a typical week. Position size matters more than the "
                    "pick here."
                ),
                what_vets_do=(
                    "Size the position so a bad week is survivable, rather than "
                    "avoiding volatility outright."
                ),
            )
        )

    # Chasing risk: stretched and at the highs.
    if (m.rsi14 or 0) >= 75.0 and m.range_52w_position >= 0.95:
        out.append(
            Flag(
                code="overextended",
                label="Overextended",
                kind="risk",
                severity="medium",
                why=(
                    f"RSI {m.rsi14:.0f} at the top of its 52-week range. Buyers have "
                    "been in complete control, which is exactly when entries get "
                    "expensive and pullbacks get sharp."
                ),
                what_vets_do=(
                    "Let it cool off rather than chase. Strong stocks give better "
                    "entries to the patient — that's the whole premise of the radar."
                ),
            )
        )

    if m.cross == "death":
        out.append(
            Flag(
                code="death_cross",
                label="Recent death cross",
                kind="risk",
                severity="medium",
                why=(
                    "The 50-day average just crossed below the 200-day — a widely "
                    "watched confirmation that momentum has turned down."
                ),
                what_vets_do=(
                    "Note it, but don't act on it alone: it lags badly and has a "
                    "reputation for firing near bottoms."
                ),
            )
        )

    if abs(m.max_drawdown_1y) >= 40.0:
        out.append(
            Flag(
                code="severe_drawdown",
                label=f"Fell {abs(m.max_drawdown_1y):.0f}% within the year",
                kind="risk",
                severity="medium",
                why=(
                    "It has already demonstrated it can drop this hard in twelve "
                    "months. That's the ride you'd be signing up for."
                ),
                what_vets_do=(
                    "Ask honestly whether you'd have held through it. Most people "
                    "overestimate their tolerance until it happens."
                ),
            )
        )

    if m.avg_dollar_volume_20d < MIN_DOLLAR_VOLUME:
        out.append(
            Flag(
                code="thin_liquidity",
                label="Thinly traded",
                kind="risk",
                severity="medium",
                why=(
                    "Low dollar volume means fewer buyers and sellers, so the gap "
                    "between the buy and sell price widens and larger orders move the "
                    "price against you."
                ),
                what_vets_do=(
                    "Stick to liquid names while learning — you want getting out to be "
                    "the easy part."
                ),
            )
        )

    return out


# --------------------------------------------------------------------------- #
# Strength patterns — what makes the good picks good
# --------------------------------------------------------------------------- #
def _strength_flags(m: StockMetrics, depth_pct: float | None) -> list[Flag]:
    out: list[Flag] = []
    ret_1y = m.ret_1y if m.ret_1y is not None else 0.0
    vol = m.vol_90d if m.vol_90d is not None else 0.0

    if m.above_ma50 and m.above_ma200:
        out.append(
            Flag(
                code="trend_intact",
                label="Trend intact",
                kind="strength",
                severity="high",
                why=(
                    "Price holds above both the 50- and 200-day averages: the textbook "
                    "definition of an uptrend, and the condition under which most "
                    "technical patterns actually work."
                ),
                what_vets_do=(
                    "Treat this as the entry ticket — most vets simply won't study a "
                    "setup without it."
                ),
            )
        )

    if (depth_pct or 0) >= 8.0 and m.above_ma200:
        out.append(
            Flag(
                code="constructive_pullback",
                label="Pullback in an uptrend",
                kind="strength",
                severity="high",
                why=(
                    f"{depth_pct:.0f}% below its recent high while the long trend still "
                    "holds — a discount without a broken chart."
                ),
                what_vets_do=(
                    "This is the shape they shop in, sized small and checked against "
                    "the stock's own history of similar dips."
                ),
            )
        )

    if vol and vol <= 25.0 and ret_1y > 0:
        out.append(
            Flag(
                code="calm_compounder",
                label="Calm and positive",
                kind="strength",
                severity="medium",
                why=(
                    f"A {ret_1y:.0f}% year with only {vol:.0f}% volatility — return "
                    "without a punishing ride."
                ),
                what_vets_do=(
                    "Value the smooth ride: the easiest portfolio to hold through a "
                    "scare is the one you actually keep."
                ),
            )
        )

    if abs(m.max_drawdown_1y) <= 15.0:
        out.append(
            Flag(
                code="shallow_drawdown",
                label="Shallow worst drop",
                kind="strength",
                severity="medium",
                why=(
                    f"Its deepest fall in the past year was only "
                    f"{abs(m.max_drawdown_1y):.0f}% — it has held together under "
                    "pressure."
                ),
                what_vets_do=(
                    "Read it as resilience, while remembering one calm year proves "
                    "nothing about the next."
                ),
            )
        )

    if m.avg_dollar_volume_20d >= MIN_DOLLAR_VOLUME * 10:
        out.append(
            Flag(
                code="deep_liquidity",
                label="Highly liquid",
                kind="strength",
                severity="low",
                why=(
                    "Heavy dollar volume: tight spreads, and you can get in or out "
                    "without moving the price."
                ),
                what_vets_do="Prefer it, especially for anything held in size.",
            )
        )

    if m.cross == "golden":
        out.append(
            Flag(
                code="golden_cross",
                label="Recent golden cross",
                kind="strength",
                severity="low",
                why=(
                    "The 50-day average crossed above the 200-day, a widely watched "
                    "trend confirmation that can attract buyers on its own."
                ),
                what_vets_do=(
                    "Take it as confirmation of a trend they already identified — "
                    "never as the reason by itself, since it lags."
                ),
            )
        )

    return out


# --------------------------------------------------------------------------- #
# Glossary — the generic pattern behind each flag code, for legends/digests.
# Instance flags carry stock-specific numbers in ``why``; this carries the
# pattern itself. test_flags keeps it in sync with what evaluate() can emit.
# --------------------------------------------------------------------------- #
GLOSSARY: dict[str, dict[str, str]] = {
    "falling_knife": {
        "label": "Falling knife",
        "kind": "risk",
        "meaning": "A steep decline that is still in progress: well below the 200-day "
                   "average and down hard over recent months. The trend is broken, not "
                   "dipping — cheap has been getting cheaper.",
        "vets": "Wait for the price to reclaim the 200-day average before studying it "
                "as a setup; missing the exact bottom costs less than catching the knife.",
        "analogy": "A kitchen knife slipping off the counter: the safe move is to let it "
                   "hit the floor — the 200-day line — and pick it up afterward. Costs a "
                   "second of lateness, spares the fingers.",
    },
    "broken_trend": {
        "label": "Trend broken",
        "kind": "risk",
        "meaning": "Price below its 200-day average — the most-watched line separating "
                   "an uptrend from a downtrend.",
        "vets": "Treat everything else about the stock as secondary until this repairs.",
        "analogy": "A river that's changed direction. Every other feature of the "
                   "landscape matters less than which way the water is now flowing.",
    },
    "value_trap": {
        "label": "Possible value trap",
        "kind": "risk",
        "meaning": "Near the 52-week low with a broken trend and a losing year. 'Cheap' "
                   "here reflects a market verdict, not a discount.",
        "vets": "Demand a reason the business is turning before the chart does.",
        "analogy": "The cheap hotel room with the great price and the smell you find out "
                   "about later. The low number is the market's verdict, not a coupon.",
    },
    "volatility_trap": {
        "label": "Paid in volatility, not returns",
        "kind": "risk",
        "meaning": "High volatility paired with a negative year — a wild ride that went "
                   "nowhere. The worst quadrant of the risk-vs-reward map.",
        "vets": "Compare it against simply owning the index before spending attention on it.",
        "analogy": "A rollercoaster that unloads you lower than it picked you up: all the "
                   "screaming, none of the view.",
    },
    "very_high_volatility": {
        "label": "Very high volatility",
        "kind": "risk",
        "meaning": "Swings large enough that position size matters more than the pick.",
        "vets": "Size the position so a bad week is survivable.",
        "analogy": "A chainsaw versus a butter knife: it can do far more in either "
                   "direction, so how you hold it matters more than which one it is.",
    },
    "overextended": {
        "label": "Overextended",
        "kind": "risk",
        "meaning": "Hot RSI at the very top of the 52-week range — entries here are "
                   "expensive and pullbacks from here are sharp.",
        "vets": "Let it cool rather than chase; strong stocks give better entries to "
                "the patient.",
        "analogy": "A sprinter at full stretch leaning past the tape. Impressive — and "
                   "about to need a breather.",
    },
    "death_cross": {
        "label": "Recent death cross",
        "kind": "risk",
        "meaning": "The 50-day average crossed below the 200-day — a widely watched "
                   "confirmation that momentum turned down. It lags badly.",
        "vets": "Note it, but never act on it alone; it has a reputation for firing "
                "near bottoms.",
        "analogy": "A weather app that finally says 'rain' as the clouds are breaking. "
                   "Real, but late enough to be nearly useless on its own.",
    },
    "severe_drawdown": {
        "label": "Severe drawdown within the year",
        "kind": "risk",
        "meaning": "The stock already demonstrated it can fall 40%+ inside twelve "
                   "months — that is the ride on offer.",
        "vets": "Ask honestly whether they'd have held through it.",
        "analogy": "A theme-park ride with a warning sign it has already earned. The "
                   "sign is describing a drop it really did take, not a hypothetical one.",
    },
    "thin_liquidity": {
        "label": "Thinly traded",
        "kind": "risk",
        "meaning": "Low dollar volume: wider spreads, and larger orders move the price "
                   "against you.",
        "vets": "Stick to liquid names while learning — getting out stays the easy part.",
        "analogy": "A tiny exit door in a crowded room. Fine until everyone wants out at "
                   "once — then the doorway itself becomes the problem.",
    },
    "trend_intact": {
        "label": "Trend intact",
        "kind": "strength",
        "meaning": "Above both the 50- and 200-day averages — the textbook uptrend, and "
                   "the condition under which most technical patterns actually work.",
        "vets": "Treat it as the entry ticket for studying a setup at all.",
        "analogy": "A swimmer moving with the current, not against it. Everything else in "
                   "the water is easier when the flow is already on your side.",
    },
    "constructive_pullback": {
        "label": "Pullback in an uptrend",
        "kind": "strength",
        "meaning": "Meaningfully below its recent high while the long trend still holds "
                   "— a discount without a broken chart.",
        "vets": "This is the shape veterans shop in, checked against the stock's own "
                "history of similar dips.",
        "analogy": "A well-run shop with a sale on: still busy, still stocked, just "
                   "cheaper this week than last.",
    },
    "calm_compounder": {
        "label": "Calm and positive",
        "kind": "strength",
        "meaning": "A positive year delivered with low volatility — return without a "
                   "punishing ride.",
        "vets": "Value the smooth ride; the easiest portfolio to hold is the one you keep.",
        "analogy": "A dependable commuter train — not thrilling, rarely late, and the "
                   "ride you actually keep taking.",
    },
    "shallow_drawdown": {
        "label": "Shallow worst drop",
        "kind": "strength",
        "meaning": "Its deepest fall in the past year stayed modest — it has held "
                   "together under pressure.",
        "vets": "Read it as resilience, remembering one calm year proves nothing about "
                "the next.",
        "analogy": "A boat that stayed steady through last year's roughest patch. "
                   "Reassuring — though last year's storms don't set next year's ceiling.",
    },
    "deep_liquidity": {
        "label": "Highly liquid",
        "kind": "strength",
        "meaning": "Heavy dollar volume: tight spreads, easy entry and exit at the "
                   "quoted price.",
        "vets": "Prefer it, especially for anything held in size.",
        "analogy": "A wide, well-lit doorway: you can walk in or out at the marked price "
                   "without a scramble.",
    },
    "golden_cross": {
        "label": "Recent golden cross",
        "kind": "strength",
        "meaning": "The 50-day average crossed above the 200-day — a widely watched "
                   "trend confirmation that can attract buyers on its own. It lags.",
        "vets": "Take it as confirmation of a trend already identified, never as the "
                "reason by itself.",
        "analogy": "A weather app turning sunny after you already felt the warmth. Nice "
                   "confirmation — just don't mistake it for the forecast.",
    },
}


def flag_analogy(flag_code: str) -> str:
    """Everyday-life picture of a pattern, for UI popovers and the digest legend."""
    return GLOSSARY.get(flag_code, {}).get("analogy", "")


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def evaluate(m: StockMetrics, depth_pct: float | None = None) -> list[Flag]:
    """All flags for one stock, risks first (worst-severity first within each)."""
    order = {"high": 0, "medium": 1, "low": 2}
    risks = sorted(_risk_flags(m, depth_pct), key=lambda f: (order[f.severity], f.code))
    strengths = sorted(
        _strength_flags(m, depth_pct), key=lambda f: (order[f.severity], f.code)
    )
    return risks + strengths


def risk_score(flags: list[Flag]) -> float:
    """Weighted severity of the risk flags — higher means a poorer setup."""
    return round(
        sum(SEVERITY_WEIGHT[f.severity] for f in flags if f.kind == "risk"), 1
    )
