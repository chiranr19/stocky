// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
// Metaphor ledes for the pages that aren't the six-act /learn tour. Kept in one
// file so the copy-law test can scan them: no advice verbs, no forbidden
// statistics jargon, no links.

export interface PageLessonCopy {
  metaphor: string;
  lie?: string;
}

export const PAGE_LESSONS: Record<string, PageLessonCopy> = {
  radar: {
    metaphor:
      "A good shop's sale rack, browsed while the shop is still busy — the radar looks for markdowns in stores that aren't closing down.",
    lie: "A small sample of past dips is fragile evidence, and a broken trend turns a markdown into a going-out-of-business sign.",
  },
  watchouts: {
    metaphor:
      "A museum of accidents: every exhibit is a named pattern that has actually hurt people. You walk it to learn the shapes, not to jeer.",
    lie: "Risk flags describe the past. A stock wearing three of them can still rally — the flags price the ride, never the destination.",
  },
  explore: {
    metaphor:
      "The whole market on one weather map — every dot a stock, every quadrant a different climate.",
    lie: "One year is a single season. A dot's neighborhood today says little about where it lives next year.",
  },
  compare: {
    metaphor:
      "A footrace where the boring runner — owning all 500 companies at once — sets the pace everyone else has to justify beating.",
    lie: "One historical window flatters somebody. Move the start date and the podium reorders.",
  },
  calendar: {
    metaphor:
      "The market's appointment book: earnings are report cards, macro prints are the whole school's fire drills — scheduled, but not therefore calm.",
    lie: "A date tells you when the news lands, never which way it breaks.",
  },
  timeMachine: {
    metaphor:
      "Driving with the rear-view mirror polished to perfection — every past trip replayed to the dollar.",
    lie: "Hindsight buys at the exact low and never panics. You would have had to hold through every red day on that chart.",
  },
};
