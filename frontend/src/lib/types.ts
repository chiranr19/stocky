// Mirrors backend/app/models.py — keep in sync.

export interface WatchlistCard {
  ticker: string;
  name: string;
  price: number;
  change_abs: number;
  change_pct: number;
  range_52w_low: number;
  range_52w_high: number;
  range_52w_position: number;
  volume: number;
  avg_volume_30d: number;
  volume_ratio: number;
  unusual_volume: boolean;
  big_mover: boolean;
  sparkline: number[];
}

export interface SectorTile {
  etf: string;
  sector: string;
  change_pct: number;
  weight: number;
}

export interface PulseResponse {
  as_of: string;
  benchmark: string;
  sectors: SectorTile[];
  watchlist: WatchlistCard[];
}

// --- Time Machine ---
export interface PricePoint {
  date: string;
  value: number;
}
export interface DrawdownInfo {
  peak_date: string;
  trough_date: string;
  peak_value: number;
  trough_value: number;
  drawdown_pct: number;
}
export interface BenchmarkResult {
  ticker: string;
  end_value: number;
  total_return_pct: number;
  path: PricePoint[];
}
export interface TimeMachineResult {
  ticker: string;
  name: string;
  start_date: string;
  end_date: string;
  amount: number;
  shares: number;
  start_price: number;
  end_price: number;
  start_value: number;
  end_value: number;
  total_return_pct: number;
  annualized_return_pct: number | null;
  max_drawdown: DrawdownInfo;
  path: PricePoint[];
  benchmark: BenchmarkResult;
  outperformance_pct: number;
}

// --- System ---
export interface DataHealth {
  status: "warming" | "ready" | "idle";
  tickers_loaded: number;
  tickers_total: number;
  priority_total: number;
  warm_loaded: number;
  latest_trading_date: string | null;
  expected_session: string;
  sessions_behind: number;
  is_fresh: boolean;
  last_ingest_at: string | null;
  anomalies_count: number;
  failed_count: number;
  history_span_days: number | null;
  median_sessions: number | null;
  thinnest_ticker: string | null;
  thinnest_sessions: number | null;
  snapshot_date: string;
}
export interface UniverseItem {
  ticker: string;
  name: string;
  sector: string | null;
}

// --- Analytics: shared row ---
export interface StockRow {
  ticker: string;
  name: string;
  sector: string | null;
  price: number;
  change_pct: number;
  spark: number[];
  range_52w_position: number;
  avg_dollar_volume: number;
  above_ma50: boolean;
  above_ma200: boolean;
  rsi14: number | null;
  vol_90d: number | null;
  ret_1m: number | null;
  ret_3m: number | null;
  ret_1y: number | null;
  max_drawdown_1y: number;
  volume_ratio: number;
  gap_pct: number;
  cross: "golden" | "death" | null;
  cross_date: string | null;
  rsi_signal: "overbought" | "oversold" | null;
  score: number | null;
  factors: Record<string, number> | null;
}

// --- Overview ---
export interface IndexTile {
  ticker: string;
  label: string;
  name: string;
  value: number;
  change_pct: number;
  unit: "usd" | "level" | "percent";
  spark: number[];
}
export interface BreadthStats {
  members: number;
  pct_above_ma50: number;
  pct_above_ma200: number;
  advancers: number;
  decliners: number;
  new_highs_52w: number;
  new_lows_52w: number;
}
export interface OverviewResponse {
  as_of: string;
  tiles: IndexTile[];
  breadth: BreadthStats;
  readings: Reading[];
}

// --- Sectors ---
export interface SectorPanel {
  gics: string;
  label: string;
  etf: string;
  etf_change_pct: number;
  members_total: number;
  members_affordable: number;
  breadth_pct_up: number;
  avg_change_pct: number;
  top: StockRow[];
}
export interface SectorsResponse {
  as_of: string;
  budget: number | null;
  weights: Record<string, number>;
  sectors: SectorPanel[];
}

// --- Risk map ---
export interface RiskPoint {
  ticker: string;
  name: string;
  sector: string;
  vol_90d: number;
  ret_1y: number;
  price: number;
  score: number | null;
}
export interface RiskMapResponse {
  as_of: string;
  budget: number | null;
  points: RiskPoint[];
  benchmark: RiskPoint | null;
}

// --- Signals ---
export interface SignalsResponse {
  as_of: string;
  budget: number | null;
  golden_crosses: StockRow[];
  death_crosses: StockRow[];
  overbought: StockRow[];
  oversold: StockRow[];
}

// --- Entry Radar ---
export interface EchoStats {
  n: number;
  median_fwd_pct: number;
  win_rate: number; // 0-1
  worst_pct: number;
  best_pct: number;
  kind: "exact" | "at_least";
  min_depth_pct?: number;
  bucket_lo?: number;
  bucket_hi?: number;
  n_years?: number;
  confidence?: "high" | "medium" | "low";
}

export interface RiskFlag {
  code: string;
  label: string;
  kind: "risk" | "strength";
  severity: "high" | "medium" | "low";
  why: string;
  what_vets_do: string;
}

export interface WatchoutRow {
  row: StockRow;
  risk_score: number;
  flags: RiskFlag[];
}

export interface WatchoutsResponse {
  as_of: string;
  budget: number | null;
  rows: WatchoutRow[];
}

export interface Reading {
  aspect: string;
  headline: string;
  detail: string;
  tone: "constructive" | "caution" | "neutral";
  caveat: string;
}
export interface RadarRow {
  row: StockRow;
  depth_pct: number;
  depth_rank: number;
  falling_knife: boolean;
  entry_score: number;
  entry_factors: Record<string, number>;
  echo: EchoStats | null;
  flags: RiskFlag[];
}
export interface RadarResponse {
  as_of: string;
  budget: number | null;
  lookback: "1m" | "2m" | "3m";
  horizon_days: number;
  weights: Record<string, number>;
  rows: RadarRow[];
}

// --- Compare ---
export interface CompareSeries {
  ticker: string;
  name: string;
  points: PricePoint[];
}
export interface CompareStat {
  ticker: string;
  name: string;
  total_return_pct: number | null;
  annualized_return_pct: number | null;
  vol_90d: number | null;
  max_drawdown_pct: number;
  ret_1y: number | null;
}
export interface Histogram {
  counts: number[];
  edges: number[];
}
export interface CorrelationMatrix {
  labels: string[];
  matrix: number[][];
}
export interface CompareResponse {
  start_date: string;
  end_date: string;
  series: CompareSeries[];
  stats: CompareStat[];
  correlation: CorrelationMatrix;
  histograms: Record<string, Histogram>;
}

// --- Stock detail ---
export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
export interface SeriesPoint {
  date: string;
  value: number | null;
}
export interface StockDetail {
  ticker: string;
  name: string;
  sector: string | null;
  sub_industry: string | null;
  row: StockRow;
  candles: Candle[];
  ma50: SeriesPoint[];
  ma200: SeriesPoint[];
  rsi: SeriesPoint[];
  histogram: Histogram;
  benchmark_histogram: Histogram;
  entry: RadarRow | null;
  readings: Reading[];
  flags: RiskFlag[];
  risk_score: number;
}
export interface Fundamentals {
  ticker: string;
  available: boolean;
  market_cap: number | null;
  trailing_pe: number | null;
  forward_pe: number | null;
  beta: number | null;
  dividend_yield: number | null;
  profit_margin: number | null;
  short_percent_of_float: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  fetched_at: string | null;
}

// --- Calendar ---
export interface EarningsEvent {
  ticker: string;
  name: string;
  date: string;
}
export interface MacroEvent {
  date: string;
  label: string;
  kind: string;
}
export interface CalendarResponse {
  earnings: EarningsEvent[];
  macro: MacroEvent[];
}
