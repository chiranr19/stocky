"use client";

import { useEffect, useState } from "react";
import { getHealth } from "./api";
import type { DataHealth } from "./types";

/** Poll /health/data — fast while warming, slow once ready. */
export function useHealth(): DataHealth | null {
  const [health, setHealth] = useState<DataHealth | null>(null);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const h = await getHealth();
        if (!alive) return;
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
