"use client";

import {
  CloudLightning,
  CloudRain,
  CloudSun,
  Sun,
  Users,
  Wind,
} from "lucide-react";
import type { BreadthStats, IndexTile, Reading } from "@/lib/types";
import {
  breadthWeather,
  vixWeather,
  yieldWeather,
  type WeatherIcon,
  type WeatherRead,
} from "@/lib/weatherCopy";
import { InfoPop } from "@/components/ui/InfoPop";

const ICONS: Record<WeatherIcon, React.ComponentType<{ className?: string }>> = {
  sun: Sun,
  "cloud-sun": CloudSun,
  "cloud-rain": CloudRain,
  "cloud-lightning": CloudLightning,
  users: Users,
  wind: Wind,
};

const TONE = {
  constructive: "text-up",
  caution: "text-down",
  neutral: "text-muted",
} as const;

function Cell({ w, value, reading }: { w: WeatherRead; value: string; reading?: Reading }) {
  const Icon = ICONS[w.icon];
  const content = reading
    ? [
        reading.headline,
        reading.detail,
        reading.analogy ? `Think of it like: ${reading.analogy}` : "",
        reading.caveat ? `When it lies: ${reading.caveat}` : "",
      ]
        .filter(Boolean)
        .join("\n\n")
    : `${w.label}\n\n${w.line}`;

  return (
    <InfoPop content={content} align="left">
      <span className="flex flex-1 items-start gap-2.5 rounded-lg border border-hair bg-elevated/40 px-3 py-2.5 text-left">
        <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${TONE[w.tone]}`} />
        <span className="min-w-0">
          <span className="block text-sm font-medium text-ink">{w.label}</span>
          <span className="tnum block text-xs text-muted">{value}</span>
          <span className="mt-0.5 block text-[11px] leading-snug text-faint">{w.line}</span>
        </span>
      </span>
    </InfoPop>
  );
}

/** The market's weather in three glanceable tiles — fear, participation, rates. */
export function WeatherStation({
  tiles,
  breadth,
  readings,
}: {
  tiles: IndexTile[];
  breadth: BreadthStats;
  readings: Reading[];
}) {
  const vix = tiles.find((t) => t.ticker === "^VIX");
  const tnx = tiles.find((t) => t.ticker === "^TNX");
  const byAspect = (a: string) => readings.find((r) => r.aspect === a);

  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {vix && (
        <Cell w={vixWeather(vix.value)} value={`VIX ${vix.value.toFixed(1)}`} reading={byAspect("vix")} />
      )}
      <Cell
        w={breadthWeather(breadth.pct_above_ma50)}
        value={`${breadth.advancers} up · ${breadth.decliners} down`}
        reading={byAspect("breadth")}
      />
      {tnx && (
        <Cell
          w={yieldWeather(tnx.value, tnx.change_pct)}
          value={`10-year ${tnx.value.toFixed(2)}%`}
          reading={byAspect("tnx")}
        />
      )}
    </div>
  );
}
