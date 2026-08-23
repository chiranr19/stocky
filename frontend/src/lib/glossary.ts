// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
// Plain-English explanations for every metric and term Stocky surfaces.
// Tone: second person, honest about limits. `whenItLies` is the point — a metric
// you can't be fooled by is a metric you actually understand. `analogy` is the
// everyday-life picture a beginner remembers when the jargon slides off; it is
// required on every entry so the metaphor layer can never be half-finished.

export interface GlossaryEntry {
  term: string;
  what: string;
  whyVetsWatchIt: string;
  whenItLies: string;
  analogy: string;
}

export const GLOSSARY: Record<string, GlossaryEntry> = {
  voo: {
    term: "VOO",
    what: "A fund (ETF) from Vanguard that holds all 500 companies in the S&P 500 at once. Buy one share and you own a tiny slice of the whole U.S. large-cap market.",
    whyVetsWatchIt:
      "It's the default 'boring' benchmark. Any single stock you pick should be measured against 'what if I'd just bought VOO instead?' — most active bets fail to beat it.",
    whenItLies:
      "VOO is ~30% big tech, so it's less diversified than it looks. It also only covers large U.S. companies — no small caps, no international.",
    analogy:
      "Owning the whole cinema instead of betting on one film. Some films flop, some are hits, and you quietly collect the average of the night.",
  },
  etf: {
    term: "ETF",
    what: "Exchange-Traded Fund — a basket of many stocks (or bonds) that trades like a single stock. One purchase spreads your money across everything inside it.",
    whyVetsWatchIt:
      "ETFs are the cheapest, simplest way to diversify. Sector ETFs (like XLK for tech) also act as a clean thermometer for how a whole slice of the market moved.",
    whenItLies:
      "A 'diversified' ETF can still be concentrated — a few giant holdings can drive most of its move. Always check what's actually inside.",
    analogy:
      "A grocery basket instead of a single apple: one trip, many items. Though a 'mixed' basket can still turn out to be mostly one thing.",
  },
  benchmark: {
    term: "benchmark",
    what: "The yardstick you compare a stock against — here it's always VOO (the S&P 500).",
    whyVetsWatchIt:
      "Returns mean nothing in isolation. +20% sounds great until you learn the market did +25%. Beating the benchmark is the whole job of active picking.",
    whenItLies:
      "Beating the benchmark over one lucky window isn't skill. And a riskier stock 'should' beat a calm index in good years — the question is what it does in bad ones.",
    analogy:
      "The pace car in a race. Your finishing time only means something next to the car everyone else is chasing.",
  },
  ticker: {
    term: "ticker",
    what: "The short symbol a stock trades under — AAPL for Apple, NVDA for NVIDIA.",
    whyVetsWatchIt: "It's the universal ID. Every quote, chart, and order uses it.",
    whenItLies:
      "Symbols get reused and companies rebrand. Class shares differ (GOOGL vs GOOG) with different voting rights.",
    analogy:
      "A stock's phone number: short, unique, and how everything reaches it. Just double-check you dialled the right one (GOOGL vs GOOG).",
  },
  sector: {
    term: "sector",
    what: "A grouping of companies in the same line of business — Technology, Health Care, Energy, and so on. There are 11.",
    whyVetsWatchIt:
      "Stocks in a sector tend to move together on the same news. Watching sectors shows you where money is rotating in or out.",
    whenItLies:
      "A company's official sector can be misleading — Amazon is 'Consumer Discretionary' but trades like a tech stock.",
    analogy:
      "Neighbourhoods in a city. Houses on the same street tend to flood or boom together when the weather over that street changes.",
  },
  market_cap: {
    term: "market cap",
    what: "The total value of a company: share price × number of shares. It's the real 'size' of the company.",
    whyVetsWatchIt:
      "Size drives behavior. Mega-caps are steadier; small caps swing harder. It's how you compare companies, not share price.",
    whenItLies:
      "A high share price doesn't mean a big company, and a low one doesn't mean cheap — only cap tells you size.",
    analogy:
      "The size of the whole pizza, not the price of one slice. A pricey slice can still come off a small pizza.",
  },
  share_price: {
    term: "share price",
    what: "The cost of one share. This is what your $200 budget filters on — how much a single share costs today.",
    whyVetsWatchIt:
      "It sets what you can afford in whole shares. A $50 stock and a $5,000 stock can be equally 'expensive' as companies.",
    whenItLies:
      "Price alone says nothing about value or size. A $10 stock isn't 'cheaper' than a $1,000 one in any meaningful sense.",
    analogy:
      "The cost of one ticket, not the size of the venue. A $10 ticket isn't 'cheaper' than a $1,000 one in any way that matters.",
  },
  volume: {
    term: "volume",
    what: "How many shares changed hands today.",
    whyVetsWatchIt:
      "Volume is conviction. A big price move on heavy volume is more believable than the same move on light volume.",
    whenItLies:
      "Volume spikes around index rebalances or options expiry that have nothing to do with the company.",
    analogy:
      "The size of the crowd behind a move. A shove from a packed stadium carries more than the same shove from an empty room.",
  },
  dollar_volume: {
    term: "dollar volume",
    what: "Volume in money terms: shares traded × price. How many dollars flow through the stock in a day.",
    whyVetsWatchIt:
      "It's the real measure of liquidity — whether you can get in and out without moving the price. Stocky requires ≥ $5M/day.",
    whenItLies:
      "A single block trade can inflate a day's dollar volume without meaning the stock is normally liquid.",
    analogy:
      "How wide the doorway is, measured in dollars. A wide door lets you slip in and out without a scramble.",
  },
  liquidity: {
    term: "liquidity",
    what: "How easily you can buy or sell without pushing the price around.",
    whyVetsWatchIt:
      "Illiquid stocks trap you — wide spreads on the way in, no buyers on the way out. Liquidity is a safety gate.",
    whenItLies:
      "Liquidity evaporates exactly when you need it — in a panic, the calm-day volume disappears.",
    analogy:
      "How easy it is to leave the party. Some rooms have a wide exit; others jam the moment everyone rushes the door at once.",
  },
  range_52w: {
    term: "52-week range",
    what: "The lowest and highest price over the past year, and where today sits between them (0% = at the low, 100% = at the high).",
    whyVetsWatchIt:
      "Quick read on trend and sentiment. Near the highs = strength; near the lows = out of favor (or a bargain).",
    whenItLies:
      "'Near its low' can mean cheap OR falling knife. 'Near its high' can mean momentum OR overextended. Position isn't a verdict.",
    analogy:
      "Where you're standing on a hill you climbed all year — near the peak, near the bottom, or halfway. The spot alone doesn't say which way you'll walk next.",
  },
  moving_average: {
    term: "moving average",
    what: "The average closing price over the last N days (MA50 = 50 days, MA200 = 200 days), redrawn each day into a smooth line.",
    whyVetsWatchIt:
      "It filters daily noise to show the trend. Price above its MA200 is a common definition of 'in an uptrend'.",
    whenItLies:
      "It lags — by definition it's history. In choppy markets price whipsaws across the average, firing false signals.",
    analogy:
      "The smoothed line a runner traces, ignoring every stumble and sprint. It shows the direction — always a step behind the runner.",
  },
  golden_cross: {
    term: "golden cross",
    what: "When the 50-day moving average crosses ABOVE the 200-day — a widely-watched bullish trend signal.",
    whyVetsWatchIt:
      "It marks a shift from short-term to long-term strength. Enough traders act on it that it can be partly self-fulfilling.",
    whenItLies:
      "It's a lagging signal built from averages — the cross often happens well after the low, sometimes right before a pullback.",
    analogy:
      "A weather app switching to sunny after you already felt the warmth. Nice confirmation, always a little late.",
  },
  death_cross: {
    term: "death cross",
    what: "When the 50-day moving average crosses BELOW the 200-day — the bearish mirror of a golden cross.",
    whyVetsWatchIt:
      "It flags deteriorating momentum and often precedes or confirms a downtrend.",
    whenItLies:
      "Famous for firing near bottoms. Because it lags, the worst of the drop is frequently already over when it triggers.",
    analogy:
      "The same late weather app, now calling for rain — often just as the clouds are starting to break.",
  },
  rsi: {
    term: "RSI",
    what: "Relative Strength Index (0–100) — measures how fast and how far a price has moved recently. Above 70 = 'overbought', below 30 = 'oversold'.",
    whyVetsWatchIt:
      "It hints when a move is stretched and due for a breather, and flags momentum divergences.",
    whenItLies:
      "A strong stock can stay 'overbought' for months. RSI is a caution flag, never a sell button.",
    analogy:
      "A car's temperature gauge. In the red means it's been running hard, not that the engine is about to quit.",
  },
  momentum: {
    term: "momentum",
    what: "The tendency of recent winners to keep winning (and losers to keep losing) for a while. Here: 3-month return, trend-confirmed by the moving averages.",
    whyVetsWatchIt:
      "Momentum is one of the most durable, well-documented market effects. It's the biggest weight (40%) in Stocky's score.",
    whenItLies:
      "Momentum reverses hard and without warning. The best performers going in are often the worst in a sharp rotation.",
    analogy:
      "A ball rolling downhill: it tends to keep rolling — right up until the hill quietly runs out.",
  },
  volatility: {
    term: "volatility",
    what: "How much a stock's price bounces around, annualized into a percent. Higher = wilder ride.",
    whyVetsWatchIt:
      "It's the plain-English version of 'risk'. Two stocks with the same return but different volatility are NOT the same bet.",
    whenItLies:
      "Past volatility doesn't predict the next shock. Calm stocks can gap violently on a single headline.",
    analogy:
      "The sea state of the voyage. Same destination either way, but rough seas mean far more seasickness on the trip.",
  },
  vix: {
    term: "VIX",
    what: "The market's 'fear gauge' — expected S&P 500 volatility over the next 30 days, derived from options prices.",
    whyVetsWatchIt:
      "Low VIX = complacency, high VIX = fear. Spikes mark stress; extreme readings often coincide with market bottoms.",
    whenItLies:
      "VIX measures expected, not realized, moves. A low VIX can persist right up until it doesn't.",
    analogy:
      "The price of umbrellas across the whole town — cheap on sunny days, spiking the moment the sky darkens.",
  },
  tnx: {
    term: "10-year yield",
    what: "The interest rate on 10-year U.S. government bonds — the closest thing to the 'price of money' for the whole economy.",
    whyVetsWatchIt:
      "Rising yields pressure stock valuations (especially growth/tech); falling yields tend to lift them. It's macro gravity.",
    whenItLies:
      "The stock-vs-yield relationship isn't mechanical — it flips depending on why yields are moving (growth vs inflation).",
    analogy:
      "The interest a totally safe savings account pays. When it climbs, that safe account competes harder for everyone's money.",
  },
  drawdown: {
    term: "max drawdown",
    what: "The biggest peak-to-trough drop along the way — how much you'd have been down at the worst point.",
    whyVetsWatchIt:
      "It's the pain test. A great long-run return is worthless if the drawdown would've shaken you out before the recovery.",
    whenItLies:
      "Past max drawdown is a floor, not a ceiling — the next one can be deeper. It also says nothing about how long recovery took.",
    analogy:
      "The deepest valley on a hike you already finished. The view from the top is nice; the real test is whether you'd have turned back down in the valley.",
  },
  total_return: {
    term: "total return",
    what: "Your gain including dividends reinvested, not just the price change.",
    whyVetsWatchIt:
      "It's the honest number. For dividend payers, price-only return understates what you actually earned.",
    whenItLies:
      "Total return assumes you reinvested every dividend perfectly and ignores taxes and fees.",
    analogy:
      "Counting the apples you ate AND the ones the tree kept dropping in your basket — not just the apples still on the branch.",
  },
  annualized_return: {
    term: "annualized return",
    what: "Total return restated as a smooth per-year rate, so you can compare a 3-year and a 10-year hold fairly.",
    whyVetsWatchIt:
      "It normalizes for time. +100% over 2 years and +100% over 10 years are very different — annualizing shows it.",
    whenItLies:
      "It smooths away the bumps. A calm 12%/yr and a terrifying 12%/yr look identical on this number alone.",
    analogy:
      "Restating a road trip as miles per hour, so a short sprint and a long haul can finally be compared on the same terms.",
  },
  dividends: {
    term: "dividends",
    what: "Cash a company pays shareholders out of profits, usually quarterly.",
    whyVetsWatchIt:
      "Reinvested dividends compound into a huge share of long-run returns. They also signal management confidence.",
    whenItLies:
      "A sky-high dividend yield is often a warning — it usually means the price crashed, and the payout may get cut.",
    analogy:
      "The tree dropping fruit into your basket each season while you still own the tree. A suspiciously huge harvest can mean the tree is sick.",
  },
  breadth: {
    term: "breadth",
    what: "How many stocks are participating in a move — e.g. the % of the S&P above its 50-day average, or advancers vs decliners.",
    whyVetsWatchIt:
      "A rally led by a handful of giants (narrow breadth) is fragile. Broad participation is a healthier, more durable move.",
    whenItLies:
      "Breadth can stay weak for a long time in a mega-cap-led market without the index breaking. It's context, not a trigger.",
    analogy:
      "How much of the parade is actually marching. A few tall floats can hide a street that's gone quiet behind them.",
  },
  advancers: {
    term: "advancers vs decliners",
    what: "How many stocks rose versus fell today. A simple, direct breadth reading.",
    whyVetsWatchIt:
      "It tells you whether green on the index is real or just a few big names masking a weak day underneath.",
    whenItLies:
      "One day of advancers/decliners is noise. The trend over weeks is what carries signal.",
    analogy:
      "A show of hands in the room: more up than down today. One vote is noise — the pattern over weeks is the signal.",
  },
  gap: {
    term: "gap",
    what: "When a stock opens well above or below where it closed yesterday — usually on overnight news like earnings.",
    whyVetsWatchIt:
      "Gaps mark where sentiment reset hard. Traders watch whether gaps 'fill' (price returns to close the gap) or run.",
    whenItLies:
      "Not every gap is meaningful — ex-dividend dates and index changes create gaps with no real information.",
    analogy:
      "Waking up to find the price teleported overnight — usually because news arrived while the market was asleep.",
  },
  correlation: {
    term: "correlation",
    what: "How closely two stocks move together, from +1 (in lockstep) to −1 (opposite) to 0 (unrelated).",
    whyVetsWatchIt:
      "It's the math behind diversification. Owning five stocks that all move together is really owning one bet five times.",
    whenItLies:
      "Correlations spike toward +1 in a crash — the moment diversification matters most is when it stops working.",
    analogy:
      "Four umbrellas from the same shop: in a real storm they all leak in the same seam. Correlation measures how 'same-shop' two stocks are.",
  },
  diversification: {
    term: "diversification",
    what: "Spreading money across things that don't all move together, so no single bad bet sinks you.",
    whyVetsWatchIt:
      "It's the only real 'free lunch' in investing — you can cut risk without necessarily cutting expected return.",
    whenItLies:
      "Over-diversifying just recreates the index (so why not buy VOO?). And correlations converge in panics.",
    analogy:
      "Not every egg in one basket — and, just as important, not two baskets that always trip over the same crack.",
  },
  beta: {
    term: "beta",
    what: "How much a stock moves relative to the market. Beta 1 = moves with the S&P; 2 = twice as much; 0.5 = half.",
    whyVetsWatchIt:
      "A fast read on how aggressive a stock is. High beta amplifies both the up and the down.",
    whenItLies:
      "Beta is backward-looking and unstable — a stock's beta can change completely as its story changes.",
    analogy:
      "The volume knob on a stock versus the market's music. Beta 2 plays every move twice as loud, up and down alike.",
  },
  pe_ratio: {
    term: "P/E ratio",
    what: "Price-to-Earnings — share price divided by earnings per share. Roughly, how many dollars you pay per dollar of annual profit.",
    whyVetsWatchIt:
      "The classic 'expensive vs cheap' gauge. A high P/E means the market expects fast growth.",
    whenItLies:
      "A low P/E can be a value trap (cheap for a reason); a high P/E can be justified by growth. Earnings can also be manipulated.",
    analogy:
      "The years of profit you're prepaying for. A high number is a big tab run up on the promise of fast growth.",
  },
  score: {
    term: "Stocky score",
    what: "A 0–100 blend of four factors — Momentum (40%), Stability (30%), Resilience (20%), Liquidity (10%) — ranked WITHIN each sector.",
    whyVetsWatchIt:
      "It's a transparent starting point: every input is shown, nothing is hidden. Use it to explore, not to obey.",
    whenItLies:
      "It's a backward-looking ranking, not a prediction. It rewards what has worked, which is exactly what reverses in a rotation. NOT a recommendation.",
    analogy:
      "A cover band's rating from last night's setlist — it tells you what played well then, not what tonight's crowd will love.",
  },
  fractional_shares: {
    term: "fractional shares",
    what: "Buying a slice of a share — $50 of a $500 stock — offered by many brokers now.",
    whyVetsWatchIt:
      "They make share price almost irrelevant to affordability, so you can own expensive names in small amounts.",
    whenItLies:
      "Stocky's $200 filter is about WHOLE-share affordability. With fractional shares the price cap matters far less.",
    analogy:
      "Buying a slice of the cake instead of the whole cake, so the sticker price stops deciding what you get to taste.",
  },
  opportunity_cost: {
    term: "opportunity cost",
    what: "What you gave up by choosing this bet instead of the next-best one — usually, instead of just buying VOO.",
    whyVetsWatchIt:
      "It reframes every pick: the real question isn't 'did I make money?' but 'did I beat the boring alternative?'",
    whenItLies:
      "It's easy to cherry-pick the comparison after the fact. Decide your benchmark before you invest, not after.",
    analogy:
      "The date you didn't go on. The real question isn't whether tonight was fun, but whether it beat the plan you skipped.",
  },
  pullback: {
    term: "pullback",
    what: "How far a stock trades below its recent high — e.g. 12% under its 3-month peak.",
    whyVetsWatchIt:
      "Strong stocks regularly dip 5–15% on the way up. Vets shop during pullbacks instead of chasing highs — better prices, same company.",
    whenItLies:
      "Not every dip recovers. A pullback in a broken trend is just the start of a bigger decline — always check the trend first.",
    analogy:
      "A strong hiker pausing on a switchback. A breather on the way up can look a lot like the start of a descent — the trend tells you which.",
  },
  falling_knife: {
    term: "falling knife",
    what: "A stock dropping hard and fast, with its longer trend broken (below the 200-day average).",
    whyVetsWatchIt:
      "'Never catch a falling knife' — buying just because something fell is how beginners get hurt. The cheap stock keeps getting cheaper.",
    whenItLies:
      "Occasionally the knife IS the bottom and the brave get rewarded. You only know afterwards — which is exactly the problem.",
    analogy:
      "A knife slipping off the counter. The safe move is letting it hit the floor and picking it up — not grabbing at the blade mid-air.",
  },
  mean_reversion: {
    term: "mean reversion",
    what: "The tendency of stretched prices to snap back toward their average.",
    whyVetsWatchIt:
      "It's the logic behind buying dips: unusually deep pullbacks in healthy stocks have often bounced. Note the word 'often'.",
    whenItLies:
      "Regimes change. A stock can revert to a NEW, lower average. Mean reversion works until the mean itself moves.",
    analogy:
      "A stretched rubber band snapping back toward its resting shape — until the day the resting shape itself quietly moves.",
  },
  base_rate: {
    term: "base rate",
    what: "How often something actually happened historically — e.g. '7 of 9 similar dips were higher a month later.'",
    whyVetsWatchIt:
      "Base rates replace gut feel with counted history. It's the only honest way to 'validate' a setup — and it's still not a promise.",
    whenItLies:
      "Small samples lie constantly. 9 past episodes is weak evidence; markets also change regime, making old episodes less comparable.",
    analogy:
      "Checking how the last dozen blind dates actually went before this one. Counted history beats a hopeful gut feeling — and still isn't a promise.",
  },
  win_rate: {
    term: "win rate",
    what: "The share of past setups that ended with a positive return over the horizon.",
    whyVetsWatchIt:
      "Alongside the typical move it sketches the odds. A 70% win rate with a brutal worst case is still a dangerous bet.",
    whenItLies:
      "Win rate says nothing about SIZE of wins vs losses. Always read it next to the worst case, never alone.",
    analogy:
      "How often past attempts landed in the win column. A high hit-rate with one catastrophic miss is still a dangerous game.",
  },
  forward_return: {
    term: "forward return",
    what: "What the stock did over the N sessions AFTER a given day — here, ~1 month after each past setup.",
    whyVetsWatchIt:
      "It's the honest way to test 'what happened next' — measuring from the setup forward, not cherry-picking afterwards.",
    whenItLies:
      "The next month is arbitrary. A setup can look bad at 1 month and great at 6, or vice versa.",
    analogy:
      "Reading the next chapter after each turning point, instead of skipping ahead to whichever ending flatters the story.",
  },
  sample_size: {
    term: "sample size (N)",
    what: "How many past episodes the stats are built on. Stocky refuses to show stats below N of 6.",
    whyVetsWatchIt:
      "Every stat is only as trustworthy as its N. Vets ignore any claim that doesn't disclose it.",
    whenItLies:
      "Even a decent N can mislead if all the episodes came from one market regime — 9 dips in a raging bull all look genius.",
    analogy:
      "How many coin flips you actually watched. Three heads in a row proves nothing; the count is what makes a pattern trustworthy.",
  },
  entry_score: {
    term: "entry score",
    what: "A 0–100 blend: pullback Depth (35%), Trend intact (30%), RSI washout (20%), 1-year Quality (15%).",
    whyVetsWatchIt:
      "It ranks which dips are worth STUDYING first — deep-but-unusual pullbacks in stocks whose long trend survived.",
    whenItLies:
      "It's a ranking of setups, not a prediction, and definitely not a buy list. The falling-knife filter and the base rates matter more than the number.",
    analogy:
      "A scout's rating on a prospect's setup — worth a closer look, never a signed contract.",
  },

  // --- Followed Filers (public disclosures) ---
  form_4: {
    term: "Form 4",
    what: "The filing a company insider (director, officer, or 10%+ owner) must send the SEC within two business days of buying or selling their own company's stock.",
    whyVetsWatchIt:
      "It's the fastest legal window into what the people closest to a business are doing with their own money — and it's public and free.",
    whenItLies:
      "Most insider activity is routine: shares granted as pay, sold for taxes or a house, or exercised options. An open-market purchase with real cash is the rarer, more telling event.",
    analogy:
      "A receipt the chef has to tape to the window every time they eat their own cooking — you still can't tell if it was hunger or habit.",
  },
  stock_act: {
    term: "STOCK Act",
    what: "A 2012 law requiring members of Congress to publicly disclose their stock trades (and their spouses') within 30–45 days.",
    whyVetsWatchIt:
      "It's the only legal window into the trading of people who sometimes vote on the industries they hold. The trades are public record.",
    whenItLies:
      "The 30–45 day lag means you always learn late, amounts are only disclosed as wide ranges, and many trades are made by financial advisors, not the member.",
    analogy:
      "A game where the players must show their cards — but only a month after the hand is over.",
  },
  ptr: {
    term: "PTR",
    what: "Periodic Transaction Report — the specific STOCK Act filing where a member of Congress lists each trade, its date, and a dollar *range*.",
    whyVetsWatchIt:
      "It's the raw record behind every 'congressman bought X' headline. Reading the source beats trusting the summary.",
    whenItLies:
      "Amounts are ranges ($1,001–$15,000, …), not exact figures, and a late or amended PTR can quietly rewrite what you thought you saw.",
    analogy:
      "An expense report with the amounts smudged into brackets — you know roughly, never exactly.",
  },
  tenb5_1: {
    term: "10b5-1 plan",
    what: "A pre-arranged trading plan an insider sets up in advance, so shares sell automatically on a schedule regardless of the news that day.",
    whyVetsWatchIt:
      "It's the cleanest way to tell a routine, pre-planned sale from a reactive one. A 10b5-1 sale usually says nothing about what the insider thinks today.",
    whenItLies:
      "Plans can still be started, cancelled, or amended opportunistically. The label tells you the timing was scheduled — not why the plan exists.",
    analogy:
      "A standing order at the bakery: a croissant every Friday whether you're hungry or not. The delivery isn't a verdict on the croissant.",
  },
  disclosure_lag: {
    term: "disclosure lag",
    what: "The gap between when a public figure traded and when you're legally allowed to know — two days for insiders, up to 30–45 for Congress.",
    whyVetsWatchIt:
      "It's the built-in cost of copying anyone famous: the price has already moved by the time the filing is public. We show that move on every row.",
    whenItLies:
      "Sometimes the price barely moves in the gap; sometimes it runs away entirely. The lag is a tax whose rate you only learn afterward.",
    analogy:
      "Getting last week's weather forecast today — accurate, and completely useless for deciding whether to pack an umbrella now.",
  },
  amount_range: {
    term: "amount range",
    what: "Congressional trades are disclosed only as broad dollar bands ($1,001–$15,000, $15,001–$50,000, and so on), never an exact figure.",
    whyVetsWatchIt:
      "It's a reminder to never treat these numbers as precise. Any honest total is itself a range, not a single figure.",
    whenItLies:
      "The bands are wide enough that a 'total' can be off by multiples. Adding midpoints invents precision the disclosure never provided.",
    analogy:
      "A menu that lists prices as '$ to $$$'. You can budget a rough range, but never tally an exact bill.",
  },
  survivorship_bias: {
    term: "survivorship bias",
    what: "The trap of judging a strategy only by the winners that survived, while the failures quietly vanish from view.",
    whyVetsWatchIt:
      "Track enough famous traders and a few will look brilliant by pure chance. Sample size and a benchmark are what separate skill from luck.",
    whenItLies:
      "A filer with a great-looking record over a handful of trades has told you almost nothing — small samples are mostly noise.",
    analogy:
      "Only interviewing lottery winners about their 'system' — everyone who lost with the same numbers isn't in the room.",
  },
  lag_tax: {
    term: "lag tax",
    what: "How much a stock already moved between the day a public figure traded and the day you could legally find out.",
    whyVetsWatchIt:
      "It's the single biggest reason copying disclosed trades underperforms the headline: you're buying at a different, usually worse, price.",
    whenItLies:
      "Occasionally the move during the lag is small or even favorable. It's an average cost, not a certainty.",
    analogy:
      "Buying concert tickets after the artist blew up — same seat, very different price than the early birds paid.",
  },
};

export function getTerm(key: string): GlossaryEntry | undefined {
  return GLOSSARY[key];
}
