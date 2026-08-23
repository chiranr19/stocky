"""The reading layer: turn numbers into plain-English interpretation.

Answers the question a beginner actually has in front of a chart — *the line is
going up, is that good or is that risky?* — with deterministic rules over the
metrics we already compute.

Rules of the house, enforced by tests:
  * Every reading names what the data says, what a veteran does with it, and
    what would make that reading wrong (``caveat`` is never empty).
  * Every reading also carries an everyday-life ``analogy`` — the metaphor a
    beginner remembers when the jargon slides off. Never empty either.
  * Tone is limited to constructive / caution / neutral. Nothing here says buy,
    sell, or should — these are interpretations, not instructions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import StockMetrics

TONES = ("constructive", "caution", "neutral")


@dataclass(frozen=True)
class Reading:
    aspect: str  # 'trend' | 'rsi' | 'volatility' | 'position' | 'volume' | ...
    headline: str
    detail: str
    tone: str
    caveat: str
    analogy: str = ""  # everyday-life metaphor; effectively required (see tests)


# --------------------------------------------------------------------------- #
# Per-stock readings
# --------------------------------------------------------------------------- #
def _trend_reading(m: StockMetrics, depth_pct: float | None) -> Reading:
    """The headline question: what does the shape of this chart mean?"""
    ret_3m = m.ret_3m or 0.0

    if m.above_ma50 and m.above_ma200:
        if depth_pct is not None and depth_pct >= 5.0:
            return Reading(
                aspect="trend",
                headline=f"Rising trend, currently {depth_pct:.0f}% off its recent high",
                detail=(
                    "Both the 50- and 200-day averages are below price, so the uptrend "
                    "is intact — but it has pulled back. This is the shape veterans "
                    "actually shop in: the trend still works, the price is cheaper than "
                    "it was, and the crowd has cooled off."
                ),
                tone="constructive",
                caveat=(
                    "A pullback only stays a pullback while the trend holds. If price "
                    "loses the 200-day average, the same chart becomes a downtrend — "
                    "check the historical dip stats below for how deep this stock "
                    "usually goes."
                ),
                analogy=(
                    "Like your favourite store running a sale while it's still busy and "
                    "well-stocked. The lights are on, the shelves are full — it just "
                    "happens to be cheaper this week than last."
                ),
            )
        return Reading(
            aspect="trend",
            headline="Rising and near its highs — strength, not a guarantee",
            detail=(
                "Price sits above both the 50- and 200-day averages, the textbook "
                "definition of an uptrend. An upward chart is generally a *good* sign: "
                "momentum tends to persist more often than it reverses. Vets read it as "
                "'this is working', not as 'I've missed it'."
            ),
            tone="constructive",
            caveat=(
                "Buying at the highs means paying full price with no discount — your "
                "downside is the whole gap back to support. Rising charts also make it "
                "easy to confuse a good company with a good entry."
            ),
            analogy=(
                "Like a runner in the lead with a mile still to go. Being out front is a "
                "good sign, not a finish line — but there's no slack in the price if they "
                "stumble."
            ),
        )

    if m.above_ma200 and not m.above_ma50:
        return Reading(
            aspect="trend",
            headline="Long trend intact, short-term stumbling",
            detail=(
                "Price slipped under the 50-day average but is still above the 200-day. "
                "This is the most common shape in a healthy stock — a wobble inside a "
                "bigger rise. Veterans watch whether the 200-day holds."
            ),
            tone="neutral",
            caveat=(
                "Every big decline also starts exactly like this. The 200-day is the "
                "line that decides which one this turns out to be."
            ),
            analogy=(
                "Like a road-trip that's off the highway but still pointed the right way. "
                "A wrong turn or a scenic detour both look identical at the first "
                "junction — the 200-day is the sign that tells you which."
            ),
        )

    if not m.above_ma200 and m.above_ma50:
        return Reading(
            aspect="trend",
            headline="Bouncing, but the long trend is still broken",
            detail=(
                "Price has climbed back over the 50-day average while remaining below "
                "the 200-day. That's an early sign of repair — the kind of bounce that "
                "either becomes a real recovery or fades back into the downtrend."
            ),
            tone="neutral",
            caveat=(
                "Downtrends are full of sharp bounces that fail. Until the 200-day is "
                "reclaimed, this is a rally inside a decline."
            ),
            analogy=(
                "Like a warm afternoon in the middle of winter. It might be the first "
                "day of spring, or it might just be a warm afternoon — one nice day "
                "doesn't end the season."
            ),
        )

    return Reading(
        aspect="trend",
        headline=f"Falling — below both averages{f', {ret_3m:.0f}% over 3 months' if ret_3m else ''}",
        detail=(
            "Price is under both the 50- and 200-day averages: a downtrend. A falling "
            "chart is not automatically a bargain. This is what the phrase 'falling "
            "knife' describes — cheap keeps getting cheaper more often than beginners "
            "expect, because something is usually wrong underneath."
        ),
        tone="caution",
        caveat=(
            "Downtrends do end, and the biggest winners often come off broken charts — "
            "but nobody can time that from the chart alone. Waiting for price to "
            "reclaim the 200-day costs you some upside and avoids most of the pain."
        ),
        analogy=(
            "Like a down escalator: each step looks cheap next to the one above it, and "
            "the escalator does not care. The 200-day line is the floor where it stops "
            "being an escalator."
        ),
    )


def _rsi_reading(m: StockMetrics) -> Reading | None:
    if m.rsi14 is None:
        return None
    r = m.rsi14
    if r >= 70:
        return Reading(
            aspect="rsi",
            headline=f"RSI {r:.0f} — stretched to the upside",
            detail=(
                "RSI measures how one-sided recent moves have been. Above 70 means "
                "buyers have been in near-total control, so the easy part of the move "
                "is likely behind it. Vets treat it as a reason to be patient rather "
                "than to chase."
            ),
            tone="caution",
            caveat=(
                "Overbought is a feature of strong stocks, not a countdown. The best "
                "performers can hold RSI above 70 for weeks — selling on that alone has "
                "cost people entire trends."
            ),
            analogy=(
                "Like a car that's been flooring the accelerator uphill. It's clearly "
                "got a strong engine — but it's been running hot, and the easy stretch "
                "of road is probably behind it."
            ),
        )
    if r <= 30:
        return Reading(
            aspect="rsi",
            headline=f"RSI {r:.0f} — washed out to the downside",
            detail=(
                "Sellers have dominated recent sessions. Historically, extremes like "
                "this are where bounces start in stocks whose longer trend is still "
                "healthy — the reason RSI pairs with the trend reading above."
            ),
            tone="neutral",
            caveat=(
                "In a genuine downtrend RSI can sit under 30 for a long time, printing "
                "'oversold' the whole way down. Oversold alone is not a floor."
            ),
            analogy=(
                "Like a rubber band stretched hard in one direction. In a healthy stock "
                "it tends to snap back — but a band that's already snapped just keeps "
                "hanging slack, so it only means something when the trend is still whole."
            ),
        )
    return Reading(
        aspect="rsi",
        headline=f"RSI {r:.0f} — neither stretched nor washed out",
        detail=(
            "Momentum is in its normal band, so RSI isn't the interesting variable "
            "right now. The trend and the pullback depth carry more information here."
        ),
        tone="neutral",
        caveat="A mid-range RSI says nothing about direction — it's simply quiet.",
        analogy=(
            "Like a thermometer reading room temperature: nothing's overheating, nothing's "
            "frozen. It just isn't the gauge worth staring at right now."
        ),
    )


def _volatility_reading(m: StockMetrics) -> Reading | None:
    if m.vol_90d is None:
        return None
    v = m.vol_90d
    weekly = v / (52**0.5)
    if v >= 45:
        tone, label = "caution", "high"
        extra = (
            "Position size is the lever vets pull here: the same dollar amount in a "
            "wild stock is a much bigger bet than in a calm one."
        )
        analogy = (
            "Volatility is the sea state, not the destination. High seas mean the same "
            "voyage with far more seasickness — and far more passengers who jump "
            "overboard at exactly the wrong moment."
        )
    elif v >= 25:
        tone, label = "neutral", "typical for a single stock"
        extra = "Roughly in line with what an individual large-cap normally does."
        analogy = (
            "Like normal highway driving: the odd bump and lane change, nothing that "
            "throws you out of your seat. Ordinary weather for one company's stock."
        )
    else:
        tone, label = "constructive", "calm"
        extra = "Quiet stocks are easier to hold through bad news, which matters more than it sounds."
        analogy = (
            "Like a smooth-riding sedan versus a dirt bike. A calmer ride is far easier "
            "to stay seated on when the road turns bad — which is usually when it counts."
        )
    return Reading(
        aspect="volatility",
        headline=f"Volatility {v:.0f}% — {label}",
        detail=(
            f"Annualized volatility of {v:.0f}% means a typical week swings roughly "
            f"±{weekly:.1f}%. {extra}"
        ),
        tone=tone,
        caveat=(
            "Volatility is measured on the last 90 days and changes fast — it spikes "
            "*after* trouble starts, so a calm reading is not a promise of a calm future."
        ),
        analogy=analogy,
    )


def _position_reading(m: StockMetrics) -> Reading | None:
    p = m.range_52w_position
    if p >= 0.95:
        return Reading(
            aspect="position",
            headline="Sitting at the top of its 52-week range",
            detail=(
                "Price is at or near its highest point of the past year. New highs are "
                "a strength signal — there's nobody left holding a loss to sell into a "
                "rally, which is why breakouts can run."
            ),
            tone="constructive",
            caveat=(
                "It also means every buyer today is paying more than everyone did all "
                "year. There's no support directly beneath a new high."
            ),
            analogy=(
                "Like climbing above the tree line: nobody above you is stuck holding a "
                "loss, so the air is clear — but there's also nothing underfoot to catch "
                "you if you slip."
            ),
        )
    if p <= 0.10:
        return Reading(
            aspect="position",
            headline="Near the bottom of its 52-week range",
            detail=(
                "Price is close to its lowest point in a year. This is where value "
                "hunters look and where value traps live — the two are only "
                "distinguishable by whether the longer trend and the business are "
                "stabilizing."
            ),
            tone="caution",
            caveat=(
                "'Down a lot' says nothing about how much further it can fall. A stock "
                "that has dropped 50% can drop another 50%."
            ),
            analogy=(
                "Like a clearance rack: sometimes it's a genuine bargain, sometimes it's "
                "there because nobody wants it. The only way to tell them apart is "
                "whether the trend and the business have stopped sliding."
            ),
        )
    return None


def _drawdown_reading(m: StockMetrics) -> Reading:
    dd = abs(m.max_drawdown_1y)
    return Reading(
        aspect="drawdown",
        headline=f"Worst drop in the past year: −{dd:.0f}%",
        detail=(
            f"At some point over the last 12 months, holding this would have meant "
            f"watching it fall {dd:.0f}% from a peak. The honest test before owning "
            f"anything: could you have sat through that without selling?"
        ),
        tone="caution" if dd >= 30 else "neutral",
        caveat=(
            "This is the worst of the *past* year only. A calmer year doesn't cap what "
            "the next one can do — 2020 and 2022 both produced far deeper drops."
        ),
        analogy=(
            "The deepest pothole on the road already driven. Owning this meant riding "
            "through it — the honest question is whether your hands stay on the wheel "
            "the next time one shows up."
        ),
    )


def _volume_reading(m: StockMetrics) -> Reading | None:
    if m.volume_ratio < 1.5:
        return None
    return Reading(
        aspect="volume",
        headline=f"Volume {m.volume_ratio:.1f}× its 30-day average",
        detail=(
            "Far more shares changed hands than usual, which means something happened: "
            "earnings, news, an analyst move, or an index change. Vets check volume "
            "because a price move on heavy volume carries more conviction than the same "
            "move on a quiet day."
        ),
        tone="neutral",
        caveat=(
            "Volume tells you people acted, not who was right. Heavy volume appears at "
            "both panic bottoms and euphoric tops."
        ),
        analogy=(
            "Like a sudden crowd outside a shop. Something drew them — a sale, a scare, a "
            "rumour — and a price move made in a crowd carries more weight than one made "
            "in an empty street. The crowd just doesn't tell you who's right."
        ),
    )


def _cross_reading(m: StockMetrics) -> Reading | None:
    if m.cross == "golden":
        return Reading(
            aspect="cross",
            headline="Fresh golden cross (50-day crossed above the 200-day)",
            detail=(
                "A widely-watched trend-confirmation signal. Its power is partly "
                "self-fulfilling: enough people watch it that it can attract buyers."
            ),
            tone="constructive",
            caveat=(
                "It is a lagging signal built from averages — by the time it fires, a "
                "large part of the move has already happened, and it produces false "
                "starts in choppy markets."
            ),
            analogy=(
                "Like a weather forecast that turns sunny only after you've noticed it's "
                "warm out. Widely watched enough to be partly self-fulfilling — and "
                "always a step behind the actual weather."
            ),
        )
    if m.cross == "death":
        return Reading(
            aspect="cross",
            headline="Fresh death cross (50-day crossed below the 200-day)",
            detail=(
                "The bearish mirror image, read as confirmation that the trend has "
                "turned down."
            ),
            tone="caution",
            caveat=(
                "Famously prone to firing near bottoms — it lags, so it often confirms "
                "a decline that is already mostly over."
            ),
            analogy=(
                "The same late forecast, now calling for rain — often just as the storm "
                "is clearing. It confirms the downturn rather than warning of it."
            ),
        )
    return None


def stock_readings(m: StockMetrics, depth_pct: float | None = None) -> list[Reading]:
    """Ordered interpretation of one stock's current situation."""
    readings: list[Reading | None] = [
        _trend_reading(m, depth_pct),
        _rsi_reading(m),
        _position_reading(m),
        _volatility_reading(m),
        _drawdown_reading(m),
        _cross_reading(m),
        _volume_reading(m),
    ]
    return [r for r in readings if r is not None]


# --------------------------------------------------------------------------- #
# Market-level readings
# --------------------------------------------------------------------------- #
def vix_reading(level: float) -> Reading:
    if level < 15:
        return Reading(
            aspect="vix",
            headline=f"VIX {level:.1f} — calm",
            detail=(
                "The market expects small daily moves over the next month. Calm markets "
                "drift upward more often than not, and protection is cheap when nobody "
                "wants it."
            ),
            tone="constructive",
            caveat=(
                "Calm is when complacency builds. Volatility spikes start from low "
                "levels, never from high ones."
            ),
            analogy=(
                "Umbrella insurance is cheapest on a sunny day — which is also when "
                "everyone stops carrying one. The VIX is that price of protection."
            ),
        )
    if level <= 25:
        return Reading(
            aspect="vix",
            headline=f"VIX {level:.1f} — normal",
            detail=(
                "Expected swings are in their usual range: ordinary market weather, "
                "neither fearful nor euphoric."
            ),
            tone="neutral",
            caveat="A normal VIX gives no directional information at all.",
            analogy=(
                "A partly-cloudy forecast: might rain, might not. You carry an umbrella "
                "out of habit, not fear. Ordinary market weather."
            ),
        )
    return Reading(
        aspect="vix",
        headline=f"VIX {level:.1f} — stressed",
        detail=(
            "Traders are paying up for protection, which means bigger daily swings are "
            "expected. Historically, high-fear readings have marked better entry points "
            "than calm ones — precisely because they feel awful."
        ),
        tone="caution",
        caveat=(
            "High fear can go far higher, and 'stressed' has preceded plenty of further "
            "declines. It measures expected movement, not direction."
        ),
        analogy=(
            "Umbrella prices spiking as the sky darkens: everyone wants cover at once, so "
            "it costs the most exactly when it feels most needed. Storms this loud have "
            "often marked better entry points than the sunny days — because they feel awful."
        ),
    )


def breadth_reading(pct_above_ma50: float, advancers: int, decliners: int) -> Reading:
    if pct_above_ma50 >= 55:
        return Reading(
            aspect="breadth",
            headline=f"Broad participation — {pct_above_ma50:.0f}% above their 50-day",
            detail=(
                "Most stocks are joining the move, not just a handful of giants. Broad "
                "rallies are historically more durable because they don't depend on a "
                "few names holding up the index."
            ),
            tone="constructive",
            caveat=(
                "Breadth is a snapshot that can deteriorate quickly, and it says "
                "nothing about valuation."
            ),
            analogy=(
                "Like a party where the whole room is dancing, not just the DJ. A crowd "
                "that's all in tends to keep the night going longer than a floor propped "
                "up by a few show-offs."
            ),
        )
    if pct_above_ma50 >= 45:
        return Reading(
            aspect="breadth",
            headline=f"Mixed participation — {pct_above_ma50:.0f}% above their 50-day",
            detail=(
                f"Roughly half the market is trending up ({advancers} advancing vs "
                f"{decliners} declining today). No strong signal either way."
            ),
            tone="neutral",
            caveat="Mixed breadth resolves in either direction — it's a wait-and-see state.",
            analogy=(
                "Half the room is dancing, half is checking their coats. The night could "
                "warm up or wind down — the floor hasn't decided yet."
            ),
        )
    return Reading(
        aspect="breadth",
        headline=f"Narrow market — only {pct_above_ma50:.0f}% above their 50-day",
        detail=(
            "Most stocks are below their own 50-day averages. When an index rises on "
            "narrow breadth, a few large companies are masking widespread weakness — "
            "one of the oldest warning patterns vets watch."
        ),
        tone="caution",
        caveat=(
            "Narrow markets can stay narrow for a long time, and the leaders sometimes "
            "keep leading. It's a risk flag, not a timing tool."
        ),
        analogy=(
            "Like a parade carried by a few tall floats while the marchers behind have "
            "stopped. From the front row it still looks like a parade — but the crowd has "
            "quietly thinned out."
        ),
    )


def yield_reading(level: float, change_pct: float) -> Reading:
    direction = "rising" if change_pct > 0 else "falling" if change_pct < 0 else "flat"
    return Reading(
        aspect="tnx",
        headline=f"10-year yield {level:.2f}% — {direction}",
        detail=(
            "The 10-year Treasury yield is the market's baseline 'risk-free' return. "
            "When it rises, safe bonds compete harder with stocks and long-duration "
            "growth names tend to feel it most; when it falls, the opposite."
        ),
        tone="neutral",
        caveat=(
            "The stock/yield relationship is loose and flips depending on *why* yields "
            "are moving — growth optimism and inflation fear look identical on this tile."
        ),
        analogy=(
            "The 10-year yield is the interest a totally safe savings account pays. When "
            "it rises, that safe account competes harder for your money, and the priciest "
            "growth stocks — the ones promising payoffs far in the future — feel it most."
        ),
    )
