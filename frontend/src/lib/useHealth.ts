"use client";

import { useEffect, useRef, useState } from "react";
import { clearApiCache, getHealth } from "./api";
import type { DataHealth } from "./types";

/** Poll /health/data — fast while warming, slow once ready. */
export function useHealth(): DataHealth | null {
  const [health, setHealth] = useState<DataHealth | null>(null);
  const wasWarming = useRef(false);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const h = await getHealth();
        if (!alive) return;
        // Warm-up finished: every cached analytics payload was computed from a
        // partial universe, so drop them rather than serving stale rankings.
        if (wasWarming.current && h.status === "ready") clearApiCache();
        wasWarming.current = h.status === "warming";
        setHealth(h);
        const delay = h.status === "warming" ? 3000 : 60000;
        timer = setTimeout(tick, delay);
      } catch {
        if (!alive) return;
        timer = setTimeout(tick, 8000);
      }
    };
    tick();

    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);

  return health;
}
