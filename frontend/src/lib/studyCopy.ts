// Teaching copy for the v1.0 study wall — metaphor ledes, the "where this lies
// to you" line under each chart, and the methodology explainers. Kept out of the
// components so the copy law can scan it as plain text (no advice phrasing, no
// forbidden statistics jargon, no URLs). Computed values are interpolated in the
// components; only the static scaffolding lives here.

export interface StudyCopy {
  eyebrow: string;
  title: string;
  lede: string;
  lie: string;
  method: string;
}

export const STUDY: Record<"race" | "rain" | "constellation" | "cone", StudyCopy> = {
  race: {
    eyebrow: "The year they ran",
    title: "A $1,000 footrace",
    lede:
      "Picture a footrace. Every name starts the year with the same stake and we watch who pulls ahead — with the boring index running mid-pack as the pace car. Beating that pace car is the whole game.",
    lie:
      "A great year behind a name says almost nothing about the next one — last year's leader and this year's are rarely the same runner.",
    method:
      "Each line rebases a name's dividend-adjusted price to the same starting stake, so the shapes compare cleanly. A name that joined the list mid-year can't run a full lap and is named separately rather than started from a false line.",
  },
  rain: {
    eyebrow: "Their daily weather",
    title: "Sixty days of weather",
    lede:
      "Each dot is one trading day's move. A tight cluster of drizzle around zero is a calm name; wide scatter out to the edges is a stormy one. The index sits on top as the reference sky, and today's dot glows.",
    lie:
      "A calm past is not a calm promise — the quietest strip can still take one violent day the record has never seen.",
    method:
      "Every dot is a day's percent change on the dividend-adjusted close, over the last sixty trading days the names share. Moves past ±8% are pinned at the edge so a single crash day doesn't flatten the rest — hover a dot to read its true number and date.",
  },
  constellation: {
    eyebrow: "How they cluster",
    title: "A night sky of your names",
    lede:
      "Two stars sit close when the names tend to move together, and drift apart when they go their own way. The lines link each star to its nearest relative — the umbrellas pull into one little cluster, the loners hang off alone.",
    lie:
      "Correlations drift, and they snap toward one exactly when you'd least want them to — in a real crash almost everything falls together, and the map you studied in calm weather stops holding.",
    method:
      "Each pair's correlation becomes a distance — move-together names near, opposite names far — and the whole set is flattened onto this plane by classical multidimensional scaling. The links are the minimum spanning tree: the shortest set of connections that still reaches everyone. Flattening many dimensions onto two always fibs a little about the exact gaps.",
  },
  cone: {
    eyebrow: "The honest forecast",
    title: "A cone of what could happen",
    lede:
      "A weather forecaster's cone. We replay a name's own past daily moves thousands of times and shade where those futures land — the cone flares wider the further out you look, because the further ahead you look, the less anyone can honestly say.",
    lie:
      "This is a range of what the past could do again, not a call on what happens. Read the WIDTH of the cone, not its center — a single future can wander clear outside it and back.",
    method:
      "We take the last two years of daily moves and resample them in short runs — keeping the fact that calm and stormy days arrive in streaks — then let 2,000 simulated futures play out. Each shaded band is a percentile at that day, so it maps scatter, not a hard fence. Two years can pin down how wide the swings are but not which way the drift leans, so the center is the least trustworthy part of the picture.",
  },
};

// The theatrical replay.
export const RUN_FUTURES = "Run the futures";
export const RUNNING_FUTURES = "Running…";
