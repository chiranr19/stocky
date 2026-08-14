"use client";

import { useEffect, useRef, useState } from "react";
import {
  ColorType,
  createChart,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle, SeriesPoint } from "@/lib/types";

const UP = "#22C989";
const DOWN = "#F6465D";
const MA50 = "#7C6BFF";
const MA200 = "#F59E0B";

function toTime(dateStr: string): UTCTimestamp {
  return (new Date(dateStr + "T00:00:00Z").getTime() / 1000) as UTCTimestamp;
}

/** TradingView-style candlestick + volume + MA overlays. Imperative; cleaned up on unmount. */
export function CandleChart({
  candles,
  ma50,
  ma200,
}: {
  candles: Candle[];
  ma50: SeriesPoint[];
  ma200: SeriesPoint[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [showMA, setShowMA] = useState(true);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || candles.length === 0) return;

    const chart: IChartApi = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8B929C",
        fontFamily: "var(--font-mono)",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.08)" },
      timeScale: { borderColor: "rgba(255,255,255,0.08)", timeVisible: false },
      crosshair: { mode: 0 },
      autoSize: true,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: UP,
      downColor: DOWN,
      borderVisible: false,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    candleSeries.setData(
      candles.map((c) => ({
        time: toTime(c.date),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
      color: "rgba(124,107,255,0.3)",
    });
    chart.priceScale("vol").applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });
    volumeSeries.setData(
      candles.map((c) => ({
        time: toTime(c.date),
        value: c.volume,
        color: c.close >= c.open ? "rgba(34,201,137,0.35)" : "rgba(246,70,93,0.35)",
      })),
    );

    if (showMA) {
      const line = (data: SeriesPoint[], color: string) => {
        const s = chart.addLineSeries({ color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
        s.setData(
          data
            .filter((p) => p.value !== null)
            .map((p) => ({ time: toTime(p.date), value: p.value as number })),
        );
      };
      line(ma50, MA50);
      line(ma200, MA200);
    }

    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [candles, ma50, ma200, showMA]);

  return (
    <div className="card p-4">
      <div className="mb-2 flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ background: UP }} />/
          <span className="h-2 w-2 rounded-full" style={{ background: DOWN }} />
          Daily candles
        </span>
        <button
          onClick={() => setShowMA((s) => !s)}
          className={`flex items-center gap-2 rounded-md border px-2 py-1 transition-colors ${showMA ? "border-hair text-ink" : "border-hair text-faint"}`}
        >
          <span className="h-0.5 w-3" style={{ background: MA50 }} /> MA50
          <span className="ml-1 h-0.5 w-3" style={{ background: MA200 }} /> MA200
          <span className="text-faint">{showMA ? "on" : "off"}</span>
        </button>
      </div>
      <div ref={containerRef} className="h-[360px] w-full" />
    </div>
  );
}
