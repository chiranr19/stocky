import type { Metadata } from "next";
import "./globals.css";
import { BudgetProvider } from "@/lib/budget";
import { Nav } from "@/components/Nav";
import { CommandPalette } from "@/components/CommandPalette";
import { Disclaimer } from "@/components/ui/Disclaimer";

export const metadata: Metadata = {
  title: "Stocky — Learn the market by using it",
  description:
    "A stock-market learning instrument. Pro analysis views with beginner captions. Scenario ranges, not predictions. Always benchmarked against just buying VOO.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="app-glow min-h-screen antialiased">
        <BudgetProvider>
          <Nav />
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:py-8">{children}</div>
          <footer className="mx-auto max-w-7xl space-y-3 px-4 pb-10 sm:px-6">
            <Disclaimer />
            <p className="text-center text-[11px] text-faint">
              Data via yfinance · cached in DuckDB · Stocky is a personal learning
              project, not investment advice.
            </p>
          </footer>
          <CommandPalette />
        </BudgetProvider>
      </body>
    </html>
  );
}
