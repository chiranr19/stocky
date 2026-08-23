"use client";

import { useEffect, useState } from "react";

/** True when the viewer asked the OS to reduce motion. JS-driven animation
 *  (rAF, Recharts draw-in) must gate on this — CSS `motion-safe:` can't reach it. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setReduced(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}
