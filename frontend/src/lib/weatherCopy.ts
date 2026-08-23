// Weather-station copy for the market-conditions strip. Kept in one file so the
// copy-law test can scan it as text: no advice verbs, no forbidden statistics
// jargon, no links. Bands mirror the backend insights.py thresholds so the icon
// and the full reading behind it never disagree.

export type WeatherIcon = "sun" | "cloud-sun" | "cloud-rain" | "cloud-lightning" | "users" | "wind";
export type WeatherTone = "constructive" | "caution" | "neutral";

export interface WeatherRead {
  icon: WeatherIcon;
  label: string;
  line: string;
  tone: WeatherTone;
}

export function vixWeather(level: number): WeatherRead {
  if (level < 15)
    return { icon: "sun", label: "Clear skies", tone: "constructive",
      line: "Protection is cheap — nobody's carrying an umbrella." };
  if (level <= 25)
    return { icon: "cloud-sun", label: "Ordinary weather", tone: "neutral",
      line: "Might rain, might not; the forecast says nothing about direction." };
  if (level <= 35)
    return { icon: "cloud-rain", label: "Storm watch", tone: "caution",
      line: "Traders are paying up for umbrellas." };
  return { icon: "cloud-lightning", label: "Storm", tone: "caution",
    line: "Big swings are priced in — fear is loud today." };
}

export function breadthWeather(pctAboveMa50: number): WeatherRead {
  if (pctAboveMa50 >= 55)
    return { icon: "users", label: "Most of the parade is marching", tone: "constructive",
      line: `${Math.round(pctAboveMa50)}% of the market is above its own 50-day line.` };
  if (pctAboveMa50 >= 45)
    return { icon: "users", label: "Half the parade is marching", tone: "neutral",
      line: `${Math.round(pctAboveMa50)}% of the market is above its own 50-day line.` };
  return { icon: "users", label: "The parade has thinned", tone: "caution",
    line: `Only ${Math.round(pctAboveMa50)}% of the market is above its own 50-day line.` };
}

export function yieldWeather(level: number, changePct: number): WeatherRead {
  if (changePct > 0)
    return { icon: "wind", label: "Headwind for stocks", tone: "caution",
      line: `Safe bonds compete harder at ${level.toFixed(2)}%.` };
  if (changePct < 0)
    return { icon: "wind", label: "Tailwind for stocks", tone: "constructive",
      line: `The safe alternative pays less — ${level.toFixed(2)}% and easing.` };
  return { icon: "wind", label: "Crosswind", tone: "neutral",
    line: `The safe-money rate is holding at ${level.toFixed(2)}%.` };
}
