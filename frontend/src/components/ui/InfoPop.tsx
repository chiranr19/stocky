"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Tap-to-open explanation wrapper.
 *
 * `title=` hover text does not exist on touch devices, so any explanation that
 * only lived in a tooltip was invisible on a phone — which is where most of the
 * teaching in this app happens. This wraps arbitrary content in a tappable
 * popover while keeping the native `title` for desktop hover.
 *
 * Content is the same string a `title` would carry; blank lines become
 * paragraphs so the longer explanations stay readable.
 */
export function InfoPop({
  content,
  children,
  align = "right",
  className = "",
}: {
  content: string;
  children: React.ReactNode;
  /** Which edge the popover anchors to — keeps it on-screen near page edges. */
  align?: "left" | "right";
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const paragraphs = content.split("\n").filter((p) => p.trim().length > 0);

  return (
    <span ref={ref} className={`relative inline-block ${className}`}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setOpen((o) => !o);
        }}
        className="cursor-help text-left"
        title={content}
        aria-expanded={open}
        aria-label="Explain this"
      >
        {children}
      </button>

      {open && (
        <span
          role="dialog"
          onClick={(e) => e.stopPropagation()}
          className={`absolute top-full z-50 mt-2 block w-64 animate-fade-in cursor-default rounded-xl border border-hair bg-elevated p-3 text-left shadow-glow sm:w-72 ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {paragraphs.map((p, i) => (
            <span
              key={i}
              className={`block text-xs leading-relaxed text-muted ${i > 0 ? "mt-2" : ""}`}
            >
              {p}
            </span>
          ))}
        </span>
      )}
    </span>
  );
}
