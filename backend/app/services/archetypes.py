# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Auto-archetypes — a deterministic character for any uncurated ticker.

A user-added name (DVA, or whatever catches the eye) has no hand-written role,
so we derive one from its own numbers: a calm compounder, a rollercoaster, a
fallen star… Same teaching voice as the curated 16, same no-advice copy law,
and — crucially — the thresholds reuse the flags vocabulary (25/40/60 vol
bands, the 200-day line, the 52-week position) so the archetype and the flags
shown beside it can never contradict each other.

The registry is an ORDERED decision list: first predicate to match wins (mutual
exclusivity), and a final ``True`` catch-all guarantees totality — every stock
gets exactly one character. Curated JSON always wins over an archetype upstream.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass

from .metrics import StockMetrics

# The narrative group every archetype lands in — a name the user is scouting.
ARCHETYPE_GROUP = "scout"


@dataclass(frozen=True)
class Archetype:
    code: str
    role: str  # <= 40 chars, "The …" house style
    lesson: str
    story: Callable[[StockMetrics | None, int], str]


def _weekly(v: float) -> float:
    return v / (52 ** 0.5)


_UNWRITTEN = Archetype(
    code="unwritten_story",
    role="The unwritten story",
    lesson="Unmeasurable risk is not the same as no risk.",
    story=lambda m, s: (
        f"Only {s} sessions of public history — not enough to measure risk, "
        "correlation, or a full year. A blank past can't be graded, and that is "
        "itself the grade."
    ),
)

_ARCHETYPES: list[tuple[Callable[[StockMetrics | None, int], bool], Archetype]] = [
    (
        lambda m, s: m is None or s < 200 or m.ret_1y is None or m.vol_90d is None,
        _UNWRITTEN,
    ),
    (
        lambda m, s: m.vol_90d >= 60,
        Archetype(
            code="lottery_ticket",
            role="The lottery ticket",
            lesson="Size a wild bet so a bad week is survivable — the position matters more than the pick.",
            story=lambda m, s: (
                f"{m.vol_90d:.0f}% annualized volatility puts it in a class of its "
                f"own — roughly ±{_weekly(m.vol_90d):.0f}% in an ordinary week. A few "
                "of these change a life; most quietly don't."
            ),
        ),
    ),
    (
        lambda m, s: not m.above_ma200 and m.ret_1y <= -15,
        Archetype(
            code="fallen_star",
            role="The fallen star",
            lesson="A famous name is a memory, not a floor. The 200-day line is where a sale becomes a verdict.",
            story=lambda m, s: (
                f"Down {abs(m.ret_1y):.0f}% over the year and living below its "
                "200-day line — a name the market once told very differently. The "
                "poster is still on the wall; the price is the review."
            ),
        ),
    ),
    (
        lambda m, s: m.vol_90d >= 40,
        Archetype(
            code="rollercoaster",
            role="The rollercoaster",
            lesson="With swings this size, position size decides more than the pick does.",
            story=lambda m, s: (
                f"{m.vol_90d:.0f}% annualized volatility means roughly "
                f"±{_weekly(m.vol_90d):.0f}% in an ordinary week. Some weeks that "
                "pays for the ticket; the ride never asks whether your stomach agrees."
            ),
        ),
    ),
    (
        lambda m, s: m.range_52w_position >= 0.95 and (m.rsi14 or 0) >= 70,
        Archetype(
            code="hot_hand",
            role="The hot hand",
            lesson="Overbought is a feature of strong stocks, not a countdown — but there's no discount left at the top.",
            story=lambda m, s: (
                f"Pressed against its 52-week high with RSI up near "
                f"{(m.rsi14 or 0):.0f} — everything is working at once. The crowd is "
                "all on one side, which is its own kind of risk."
            ),
        ),
    ),
    (
        lambda m, s: m.above_ma200 and m.vol_90d <= 25 and m.ret_1y > 0,
        Archetype(
            code="calm_compounder",
            role="The calm compounder",
            lesson="The easiest ride to hold through a scare is the one that never threw you around in the first place.",
            story=lambda m, s: (
                f"A {m.ret_1y:.0f}% year delivered with only {m.vol_90d:.0f}% "
                "volatility — the dependable commuter train of the list. It rarely "
                "makes the front page, which is precisely how it keeps its passengers."
            ),
        ),
    ),
    (
        lambda m, s: m.vol_90d <= 25 and m.ret_1y <= 0,
        Archetype(
            code="sleeping_giant",
            role="The sleeping giant",
            lesson="A calm chart is comfortable; whether that comfort is patience or denial, only time settles.",
            story=lambda m, s: (
                f"Quiet ({m.vol_90d:.0f}% volatility) but going nowhere — a flat year "
                "on a calm chart. Boredom is cheap to hold and easy to ignore, which "
                "is how value hides, and how value traps hide too."
            ),
        ),
    ),
    (
        lambda m, s: m.above_ma200 and m.ret_1y > 0,
        Archetype(
            code="steady_climber",
            role="The steady climber",
            lesson="Most money is made in trends this ordinary, held longer than feels exciting.",
            story=lambda m, s: (
                f"Above its 200-day line with a {m.ret_1y:.0f}% year — the plain, "
                "unglamorous shape of an uptrend that keeps working. Nothing "
                "dramatic, which is usually the point."
            ),
        ),
    ),
    (
        lambda m, s: True,  # total catch-all: trend and tape disagree
        Archetype(
            code="crossroads",
            role="The crossroads",
            lesson="When the signals conflict, the honest read is 'undecided', not a forced call.",
            story=lambda m, s: (
                f"Trend and tape disagree right now — a {m.ret_1y:.0f}% year that "
                "doesn't square neatly with where the price sits. A name between "
                "chapters, waiting to pick a direction."
            ),
        ),
    ),
]

# For tests / legends: the full set (deduped, in declaration order).
ARCHETYPES: list[Archetype] = list(
    {a.code: a for _, a in [(None, _UNWRITTEN), *[(p, a) for p, a in _ARCHETYPES]]}.values()
)


def classify(m: StockMetrics | None, sessions: int) -> Archetype:
    """Exactly one archetype for a stock, first match wins."""
    for predicate, archetype in _ARCHETYPES:
        if predicate(m, sessions):
            return archetype
    return _UNWRITTEN  # unreachable (the last predicate is True), but total by construction


def assign(m: StockMetrics | None, sessions: int) -> dict[str, str]:
    """Role/group/story/lesson for an uncurated ticker, ready for a BasketMember."""
    a = classify(m, sessions)
    return {
        "role": a.role,
        "group": ARCHETYPE_GROUP,
        "story": a.story(m, sessions),
        "lesson": a.lesson,
    }


def assign_stale(ticker: str, data_ends: dt.date, latest: dt.date) -> dict[str, str]:
    """Same shape as assign(), for a name whose price feed stopped. Its metrics are
    withheld upstream, and without this it would read as a young listing ("only 0
    sessions"), which is false: the past is there, the present isn't."""
    return {
        "role": "The stopped clock",
        "group": ARCHETYPE_GROUP,
        "story": (
            f"{ticker}'s price data ends {data_ends:%Y-%m-%d}, while the market's latest "
            f"close is {latest:%Y-%m-%d}. A trading halt, a delisting, or a merger can "
            "each stop a feed. Its last numbers are frozen, so it sits out the map, the "
            "race, and the what-changed feed until fresh bars arrive."
        ),
        "lesson": "Check the date on a number before reading it — a frozen price looks just like a live one.",
    }
