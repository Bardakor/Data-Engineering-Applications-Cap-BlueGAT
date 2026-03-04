import type { RagCitation } from "@/lib/types";

export const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export const compactCurrencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 1,
});

export const compactNumberFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export const percentageFormatter = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 0,
});

export const mapPalette = ["#f97316", "#0ea5e9", "#22c55e", "#f59e0b", "#6366f1"];

export const suggestedPrompts = [
  "What are the main complaints in recent feedback?",
  "Which campaign has the healthiest sentiment right now?",
  "Summarize feedback for Hot Wings by country.",
];

export type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  retrievalMode?: string;
  /** "ollama" | "openai" | "fallback" – proves answer came from LLM */
  generationMode?: string;
  citations?: RagCitation[];
};

export type SignalTone = "positive" | "neutral" | "negative";

export type PrioritySignal = {
  tone: SignalTone;
  label: string;
  detail: string;
  value: string;
};

export type ChainNode = {
  label: string;
  value: string;
  tone: SignalTone;
};

export type ControlRoomNarrative = {
  summary: string;
  risk: string;
  opportunity: string;
  action: string;
};
