import { format } from "date-fns";
import type { DashboardView } from "@/lib/types";
import {
  compactCurrencyFormatter,
  compactNumberFormatter,
  currencyFormatter,
  percentageFormatter,
} from "./types";

export function shortDate(value: string) {
  return format(new Date(value), "MMM d");
}

export function longDateTime(value: string) {
  return format(new Date(value), "MMM d, HH:mm");
}

export function formatMetricValue(
  value: number,
  formatType: "currency" | "number" | "percent",
) {
  if (formatType === "currency") {
    if (Math.abs(value) >= 1000) {
      return compactCurrencyFormatter.format(value);
    }
    return currencyFormatter.format(value);
  }

  if (formatType === "percent") {
    return percentageFormatter.format(value <= 1 ? value : value / 100);
  }

  return compactNumberFormatter.format(value);
}

export function formatDelta(delta: number) {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(1)}%`;
}

export function moneyTick(value: number) {
  return compactCurrencyFormatter.format(value);
}

export function retrievalTone(mode?: string) {
  if (!mode) return "border-slate-200 bg-white/80 text-slate-600";
  if (mode === "openai" || mode.includes("openai")) {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (mode.includes("ollama")) {
    return "border-violet-200 bg-violet-50 text-violet-700";
  }
  if (mode === "lexical" || mode.includes("lexical")) {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  if (mode === "fallback" || mode.includes("fallback")) {
    return "border-slate-200 bg-slate-100 text-slate-600";
  }
  return "border-slate-200 bg-white/80 text-slate-600";
}

export function sentimentTone(label: string) {
  if (label === "positive") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (label === "negative") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-amber-200 bg-amber-50 text-amber-700";
}

export function stageLineColor(view: DashboardView) {
  if (view === "map") return "#0f172a";
  if (view === "sales") return "#f97316";
  if (view === "feedback") return "#0ea5e9";
  return "#22c55e";
}

export function percentageValue(value: number) {
  return percentageFormatter.format(value <= 1 ? value : value / 100);
}

export function sentimentScoreLabel(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

export function truncateMiddle(value: string, maxLength = 42) {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength - 1)}…`;
}

export {
  compactCurrencyFormatter,
  compactNumberFormatter,
  currencyFormatter,
  percentageFormatter,
};
