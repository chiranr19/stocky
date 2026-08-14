// Plain-English explanations for every metric and term Stocky surfaces.
// Tone: second person, honest about limits. `whenItLies` is the point — a metric
// you can't be fooled by is a metric you actually understand.

export interface GlossaryEntry {
  term: string;
  what: string;
  whyVetsWatchIt: string;
  whenItLies: string;
}

export const GLOSSARY: Record<string, GlossaryEntry> = {
  voo: {
    term: "VOO",
    what: "A fund (ETF) from Vanguard that holds all 500 companies in the S&P 500 at once. Buy one share and you own a tiny slice of the whole U.S. large-cap market.",
    whyVetsWatchIt:
      "It's the default 'boring' benchmark. Any single stock you pick should be measured against 'what if I'd just bought VOO instead?' — most active bets fail to beat it.",
    whenItLies:
      "VOO is ~30% big tech, so it's less diversified than it looks. It also only covers large U.S. companies — no small caps, no international.",
  },
  etf: {
    term: "ETF",
    what: "Exchange-Traded Fund — a basket of many stocks (or bonds) that trades like a single stock. One purchase spreads your money across everything inside it.",
    whyVetsWatchIt:
      "ETFs are the cheapest, simplest way to diversify. Sector ETFs (like XLK for tech) also act as a clean thermometer for how a whole slice of the market moved.",
    whenItLies:
      "A 'diversified' ETF can still be concentrated — a few giant holdings can drive most of its move. Always check what's actually inside.",
  },
  benchmark: {
    term: "benchmark",
    what: "The yardstick you compare a stock against — here it's always VOO (the S&P 500).",
    whyVetsWatchIt:
      "Returns mean nothing in isolation. +20% sounds great until you learn the market did +25%. Beating the benchmark is the whole job of active picking.",
    whenItLies:
      "Beating the benchmark over one lucky window isn't skill. And a riskier stock 'should' beat a calm index in good years — the question is what it does in bad ones.",
  },
  ticker: {
    term: "ticker",
    what: "The short symbol a stock trades under — AAPL for Apple, NVDA for NVIDIA.",
    whyVetsWatchIt: "It's the universal ID. Every quote, chart, and order uses it.",
    whenItLies:
      "Symbols get reused and companies rebrand. Class shares differ (GOOGL vs GOOG) with different voting rights.",
  },
  sector: {
    term: "sector",
    what: "A grouping of companies in the same line of business — Technology, Health Care, Energy, and so on. There are 11.",
    whyVetsWatchIt:
      "Stocks in a sector tend to move together on the same news. Watching sectors shows you where money is rotating in or out.",
    whenItLies:
      "A company's official sector can be misleading — Amazon is 'Consumer Discretionary' but trades like a tech stock.",
  },
  market_cap: {
    term: "market cap",
    what: "The total value of a company: share price × number of shares. It's the real 'size' of the company.",
    whyVetsWatchIt:
      "Size drives behavior. Mega-caps are steadier; small caps swing harder. It's how you compare companies, not share price.",
    whenItLies:
      "A high share price doesn't mean a big company, and a low one doesn't mean cheap — only cap tells you size.",
  },
  share_price: {
    term: "share price",
    what: "The cost of one share. This is what your $200 budget filters on — how much a single share costs today.",
    whyVetsWatchIt:
      "It sets what you can afford in whole shares. A $50 stock and a $5,000 stock can be equally 'expensive' as companies.",
    whenItLies:
      "Price alone says nothing about value or size. A $10 stock isn't 'cheaper' than a $1,000 one in any meaningful sense.",
  },
  volume: {
    term: "volume",
    what: "How many shares changed hands today.",
    whyVetsWatchIt:
      "Volume is conviction. A big price move on heavy volume is more believable than the same move on light volume.",
    whenItLies:
      "Volume spikes around index rebalances or options expiry that have nothing to do with the company.",
  },
  dollar_volume: {
    term: "dollar volume",
    what: "Volume in money terms: shares traded × price. How many dollars flow through the stock in a day.",
    whyVetsWatchIt:
      "It's the real measure of liquidity — whether you can get in and out without moving the price. Stocky requires ≥ $5M/day.",
    whenItLies:
      "A single block trade can inflate a day's dollar volume without meaning the stock is normally liquid.",
  },
  liquidity: {
    term: "liquidity",
    what: "How easily you can buy or sell without pushing the price around.",
    whyVetsWatchIt:
      "Illiquid stocks trap you — wide spreads on the way in, no buyers on the way out. Liquidity is a safety gate.",
    whenItLies:
      "Liquidity evaporates exactly when you need it — in a panic, the calm-day volume disappears.",
  },
  range_52w: {
    term: "52-week range",
    what: "The lowest and highest price over the past year, and where today sits between them (0% = at the low, 100% = at the high).",
    whyVetsWatchIt:
      "Quick read on trend and sentiment. Near the highs = strength; near the lows = out of favor (or a bargain).",
    whenItLies:
      "'Near its low' can mean cheap OR falling knife. 'Near its high' can mean momentum OR overextended. Position isn't a verdict.",
  },
  moving_average: {
    term: "moving average",
    what: "The average closing price over the last N days (MA50 = 50 days, MA200 = 200 days), redrawn each day into a smooth line.",
    whyVetsWatchIt:
      "It filters daily noise to show the trend. Price above its MA200 is a common definition of 'in an uptrend'.",
    whenItLies:
      "It lags — by definition it's history. In choppy markets price whipsaws across the average, firing false signals.",
  },
  golden_cross: {
    term: "golden cross",
    what: "When the 50-day moving average crosses ABOVE the 200-day — a widely-watched bullish trend signal.",
    whyVetsWatchIt:
      "It marks a shift from short-term to long-term strength. Enough traders act on it that it can be partly self-fulfilling.",
    whenItLies:
      "It's a lagging signal built from averages — the cross often happens well after the low, sometimes right before a pullback.",
  },
  death_cross: {
    term: "death cross",
    what: "When the 50-day moving average crosses BELOW the 200-day — the bearish mirror of a golden cross.",
    whyVetsWatchIt:
      "It flags deteriorating momentum and often precedes or confirms a downtrend.",
    whenItLies:
      "Famous for firing near bottoms. Because it lags, the worst of the drop is frequently already over when it triggers.",
  },
  rsi: {
    term: "RSI",
    what: "Relative Strength Index (0–100) — measures how fast and how far a price has moved recently. Above 70 = 'overbought', below 30 = 'oversold'.",
    whyVetsWatchIt:
      "It hints when a move is stretched and due for a breather, and flags momentum divergences.",
    whenItLies:
      "A strong stock can stay 'overbought' for months. RSI is a caution flag, never a sell button.",
  },
  momentum: {
    term: "momentum",
    what: "The tendency of recent winners to keep winning (and losers to keep losing) for a while. Here: 3-month return, trend-confirmed by the moving averages.",
    whyVetsWatchIt:
      "Momentum is one of the most durable, well-documented market effects. It's the biggest weight (40%) in Stocky's score.",
    whenItLies:
      "Momentum reverses hard and without warning. The best performers going in are often the worst in a sharp rotation.",
  },
  volatility: {
    term: "volatility",
    what: "How much a stock's price bounces around, annualized into a percent. Higher = wilder ride.",
    whyVetsWatchIt:
      "It's the plain-English version of 'risk'. Two stocks with the same return but different volatility are NOT the same bet.",
    whenItLies:
      "Past volatility doesn't predict the next shock. Calm stocks can gap violently on a single headline.",
  },
  vix: {
    term: "VIX",
    what: "The market's 'fear gauge' — expected S&P 500 volatility over the next 30 days, derived from options prices.",
    whyVetsWatchIt:
      "Low VIX = complacency, high VIX = fear. Spikes mark stress; extreme readings often coincide with market bottoms.",
    whenItLies:
      "VIX measures expected, not realized, moves. A low VIX can persist right up until it doesn't.",
  },
  tnx: {
    term: "10-year yield",
    what: "The interest rate on 10-year U.S. government bonds — the closest thing to the 'price of money' for the whole economy.",
    whyVetsWatchIt:
      "Rising yields pressure stock valuations (especially growth/tech); falling yields tend to lift them. It's macro gravity.",
    whenItLies:
      "The stock-vs-yield relationship isn't mechanical — it flips depending on why yields are moving (growth vs inflation).",
  },
  drawdown: {
    term: "max drawdown",
    what: "The biggest peak-to-trough drop along the way — how much you'd have been down at the worst point.",
    whyVetsWatchIt:
      "It's the pain test. A great long-run return is worthless if the drawdown would've shaken you out before the recovery.",
    whenItLies:
      "Past max drawdown is a floor, not a ceiling — the next one can be deeper. It also says nothing about how long recovery took.",
  },
  total_return: {
    term: "total return",
    what: "Your gain including dividends reinvested, not just the price change.",
    whyVetsWatchIt:
      "It's the honest number. For dividend payers, price-only return understates what you actually earned.",
    whenItLies:
      "Total return assumes you reinvested every dividend perfectly and ignores taxes and fees.",
  },
  annualized_return: {
    term: "annualized return",
    what: "Total return restated as a smooth per-year rate, so you can compare a 3-year and a 10-year hold fairly.",
    whyVetsWatchIt:
      "It normalizes for time. +100% over 2 years and +100% over 10 years are very different — annualizing shows it.",
    whenItLies:
      "It smooths away the bumps. A calm 12%/yr and a terrifying 12%/yr look identical on this number alone.",
  },
  dividends: {
    term: "dividends",
    what: "Cash a company pays shareholders out of profits, usually quarterly.",
    whyVetsWatchIt:
      "Reinvested dividends compound into a huge share of long-run returns. They also signal management confidence.",
    whenItLies:
      "A sky-high dividend yield is often a warning — it usually means the price crashed, and the payout may get cut.",
  },
  breadth: {
    term: "breadth",
    what: "How many stocks are participating in a move — e.g. the % of the S&P above its 50-day average, or advancers vs decliners.",
    whyVetsWatchIt:
      "A rally led by a handful of giants (narrow breadth) is fragile. Broad participation is a healthier, more durable move.",
    whenItLies:
      "Breadth can stay weak for a long time in a mega-cap-led market without the index breaking. It's context, not a trigger.",
  },
  advancers: {
    term: "advancers vs decliners",
    what: "How many stocks rose versus fell today. A simple, direct breadth reading.",
    whyVetsWatchIt:
      "It tells you whether green on the index is real or just a few big names masking a weak day underneath.",
    whenItLies:
      "One day of advancers/decliners is noise. The trend over weeks is what carries signal.",
  },
  gap: {
    term: "gap",
    what: "When a stock opens well above or below where it closed yesterday — usually on overnight news like earnings.",
    whyVetsWatchIt:
      "Gaps mark where sentiment reset hard. Traders watch whether gaps 'fill' (price returns to close the gap) or run.",
    whenItLies:
      "Not every gap is meaningful — ex-dividend dates and index changes create gaps with no real information.",
  },
  correlation: {
    term: "correlation",
    what: "How closely two stocks move together, from +1 (in lockstep) to −1 (opposite) to 0 (unrelated).",
    whyVetsWatchIt:
      "It's the math behind diversification. Owning five stocks that all move together is really owning one bet five times.",
    whenItLies:
      "Correlations spike toward +1 in a crash — the moment diversification matters most is when it stops working.",
  },
  diversification: {
    term: "diversification",
    what: "Spreading money across things that don't all move together, so no single bad bet sinks you.",
    whyVetsWatchIt:
      "It's the only real 'free lunch' in investing — you can cut risk without necessarily cutting expected return.",
    whenItLies:
      "Over-diversifying just recreates the index (so why not buy VOO?). And correlations converge in panics.",
  },
  beta: {
    term: "beta",
    what: "How much a stock moves relative to the market. Beta 1 = moves with the S&P; 2 = twice as much; 0.5 = half.",
    whyVetsWatchIt:
      "A fast read on how aggressive a stock is. High beta amplifies both the up and the down.",
    whenItLies:
      "Beta is backward-looking and unstable — a stock's beta can change completely as its story changes.",
  },
  pe_ratio: {
    term: "P/E ratio",
    what: "Price-to-Earnings — share price divided by earnings per share. Roughly, how many dollars you pay per dollar of annual profit.",
    whyVetsWatchIt:
      "The classic 'expensive vs cheap' gauge. A high P/E means the market expects fast growth.",
    whenItLies:
      "A low P/E can be a value trap (cheap for a reason); a high P/E can be justified by growth. Earnings can also be manipulated.",
  },
  score: {
    term: "Stocky score",
    what: "A 0–100 blend of four factors — Momentum (40%), Stability (30%), Resilience (20%), Liquidity (10%) — ranked WITHIN each sector.",
    whyVetsWatchIt:
      "It's a transparent starting point: every input is shown, nothing is hidden. Use it to explore, not to obey.",
    whenItLies:
      "It's a backward-looking ranking, not a prediction. It rewards what has worked, which is exactly what reverses in a rotation. NOT a recommendation.",
  },
  fractional_shares: {
    term: "fractional shares",
    what: "Buying a slice of a share — $50 of a $500 stock — offered by many brokers now.",
    whyVetsWatchIt:
      "They make share price almost irrelevant to affordability, so you can own expensive names in small amounts.",
    whenItLies:
      "Stocky's $200 filter is about WHOLE-share affordability. With fractional shares the price cap matters far less.",
  },
  opportunity_cost: {
    term: "opportunity cost",
    what: "What you gave up by choosing this bet instead of the next-best one — usually, instead of just buying VOO.",
    whyVetsWatchIt:
      "It reframes every pick: the real question isn't 'did I make money?' but 'did I beat the boring alternative?'",
    whenItLies:
      "It's easy to cherry-pick the comparison after the fact. Decide your benchmark before you invest, not after.",
  },
  pullback: {
    term: "pullback",
    what: "How far a stock trades below its recent high — e.g. 12% under its 3-month peak.",
    whyVetsWatchIt:
      "Strong stocks regularly dip 5–15% on the way up. Vets shop during pullbacks instead of chasing highs — better prices, same company.",
    whenItLies:
      "Not every dip recovers. A pullback in a broken trend is just the start of a bigger decline — always check the trend first.",
  },
  falling_knife: {
    term: "falling knife",
    what: "A stock dropping hard and fast, with its longer trend broken (below the 200-day average).",
    whyVetsWatchIt:
      "'Never catch a falling knife' — buying just because something fell is how beginners get hurt. The cheap stock keeps getting cheaper.",
    whenItLies:
      "Occasionally the knife IS the bottom and the brave get rewarded. You only know afterwards — which is exactly the problem.",
  },
  mean_reversion: {
    term: "mean reversion",
    what: "The tendency of stretched prices to snap back toward their average.",
    whyVetsWatchIt:
      "It's the logic behind buying dips: unusually deep pullbacks in healthy stocks have often bounced. Note the word 'often'.",
    whenItLies:
      "Regimes change. A stock can revert to a NEW, lower average. Mean reversion works until the mean itself moves.",
  },
  base_rate: {
    term: "base rate",
    what: "How often something actually happened historically — e.g. '7 of 9 similar dips were higher a month later.'",
    whyVetsWatchIt:
      "Base rates replace gut feel with counted history. It's the only honest way to 'validate' a setup — and it's still not a promise.",
    whenItLies:
      "Small samples lie constantly. 9 past episodes is weak evidence; markets also change regime, making old episodes less comparable.",
  },
  win_rate: {
    term: "win rate",
    what: "The share of past setups that ended with a positive return over the horizon.",
    whyVetsWatchIt:
      "Alongside the median move it sketches the odds. A 70% win rate with a brutal worst case is still a dangerous bet.",
    whenItLies:
      "Win rate says nothing about SIZE of wins vs losses. Always read it next to the worst case, never alone.",
  },
  forward_return: {
    term: "forward return",
    what: "What the stock did over the N sessions AFTER a given day — here, ~1 month after each past setup.",
    whyVetsWatchIt:
      "It's the honest way to test 'what happened next' — measuring from the setup forward, not cherry-picking afterwards.",
    whenItLies:
      "The next month is arbitrary. A setup can look bad at 1 month and great at 6, or vice versa.",
  },
  sample_size: {
    term: "sample size (N)",
    what: "How many past episodes the stats are built on. Stocky refuses to show stats below N of 6.",
    whyVetsWatchIt:
      "Every stat is only as trustworthy as its N. Vets ignore any claim that doesn't disclose it.",
    whenItLies:
      "Even a decent N can mislead if all the episodes came from one market regime — 9 dips in a raging bull all look genius.",
  },
  entry_score: {
    term: "entry score",
    what: "A 0–100 blend: pullback Depth (35%), Trend intact (30%), RSI washout (20%), 1-year Quality (15%).",
    whyVetsWatchIt:
      "It ranks which dips are worth STUDYING first — deep-but-unusual pullbacks in stocks whose long trend survived.",
    whenItLies:
      "It's a ranking of setups, not a prediction, and definitely not a buy list. The falling-knife filter and the base rates matter more than the number.",
  },
};

export function getTerm(key: string): GlossaryEntry | undefined {
  return GLOSSARY[key];
}
