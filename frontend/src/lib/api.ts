import type {
  CalendarResponse,
  CompareResponse,
  DataHealth,
  Fundamentals,
  OverviewResponse,
  PulseResponse,
  RadarResponse,
  RiskMapResponse,
  SectorsResponse,
  SignalsResponse,
  StockDetail,
  TimeMachineResult,
  UniverseItem,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getJSON<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiError(
      `Can't reach the API at ${BASE_URL}. Is the backend running (uvicorn app.main:app)?`,
      0,
    );
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

/** Serialize a budget cap for the query string. null = no cap → budget=0. */
function budgetParam(budget: number | null): string {
  return `budget=${budget === null ? 0 : budget}`;
}

export const getHealth = () => getJSON<DataHealth>("/health/data");
export const getUniverse = () => getJSON<UniverseItem[]>("/universe");
export const getOverview = () => getJSON<OverviewResponse>("/overview");
export const getPulse = () => getJSON<PulseResponse>("/pulse");
export const getCalendar = () => getJSON<CalendarResponse>("/calendar");

export const getSectors = (budget: number | null) =>
  getJSON<SectorsResponse>(`/sectors?${budgetParam(budget)}`);

export const getMovers = (type: string, budget: number | null, limit = 25) =>
  getJSON<import("./types").StockRow[]>(
    `/movers?type=${type}&${budgetParam(budget)}&limit=${limit}`,
  );

export const getRiskMap = (budget: number | null) =>
  getJSON<RiskMapResponse>(`/riskmap?${budgetParam(budget)}`);

export const getSignals = (budget: number | null) =>
  getJSON<SignalsResponse>(`/signals?${budgetParam(budget)}`);

export const getRadar = (
  budget: number | null,
  lookback: "1m" | "2m" | "3m" = "3m",
  limit = 30,
) =>
  getJSON<RadarResponse>(
    `/radar?${budgetParam(budget)}&lookback=${lookback}&limit=${limit}`,
  );

export const getCompare = (tickers: string[]) =>
  getJSON<CompareResponse>(`/compare?tickers=${tickers.join(",")}`);

export const getStock = (ticker: string) =>
  getJSON<StockDetail>(`/stock/${encodeURIComponent(ticker.toUpperCase())}`);

export const getFundamentals = (ticker: string) =>
  getJSON<Fundamentals>(`/stock/${encodeURIComponent(ticker.toUpperCase())}/fundamentals`);

export const getTimeMachine = (ticker: string, date: string, amount: number) => {
  const qs = new URLSearchParams({
    ticker: ticker.trim().toUpperCase(),
    date,
    amount: String(amount),
  });
  return getJSON<TimeMachineResult>(`/timemachine?${qs.toString()}`);
};
