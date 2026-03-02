"use client";

import { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Bot, SendHorizontal, X } from "lucide-react";
import type { FeedbackDashboardData, SalesDashboardData } from "@/lib/types";
import type { ChatMessage, ControlRoomNarrative, PrioritySignal } from "./types";
import { compactCurrencyFormatter } from "./types";
import { suggestedPrompts } from "./types";
import { retrievalTone, shortDate, truncateMiddle } from "./utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  CenteredOverlayPanel,
  MiniStat,
  NarrativeChip,
  NarrativeLine,
  PrioritySignalRow,
  SectionBlock,
} from "./ui-components";

export function ChatOverlay({
  salesData,
  feedbackData,
  prompt,
  setPrompt,
  messages,
  isChatting,
  narrative,
  prioritySignals,
  onSubmit,
  onUsePrompt,
  onClose,
}: {
  salesData: SalesDashboardData | null;
  feedbackData: FeedbackDashboardData | null;
  prompt: string;
  setPrompt: (value: string) => void;
  messages: ChatMessage[];
  isChatting: boolean;
  narrative: ControlRoomNarrative;
  prioritySignals: PrioritySignal[];
  onSubmit: () => void;
  onUsePrompt: (prompt: string) => void;
  onClose: () => void;
}) {
  const messageViewportRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const latestAssistantMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && message.retrievalMode);
  const lastUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");
  const citationCount = latestAssistantMessage?.citations?.length ?? 0;
  const leadSalesMarket = salesData?.countryPerformance[0] ?? null;
  const pressureCountry =
    [...(feedbackData?.sentimentByCountry ?? [])].sort(
      (left, right) => left.avgSentiment - right.avgSentiment,
    )[0] ?? null;

  useEffect(() => {
    const viewport = messageViewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, isChatting]);

  useEffect(() => {
    composerRef.current?.focus();
  }, [messages.length]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      className="pointer-events-none absolute inset-0 z-30"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08),rgba(15,23,42,0.12))] backdrop-blur-[2px]" />

      <CenteredOverlayPanel
        title="CheepChat"
        subtitle="One centered chat workspace connected to the feedback and sales layers."
        icon={<Bot className="size-4" />}
        actions={
          <Button
            variant="outline"
            size="icon"
            className="rounded-2xl border-white/80 bg-white/88"
            onClick={onClose}
            aria-label="Close CheepChat"
          >
            <X className="size-4" />
          </Button>
        }
        bodyClassName="grid min-h-0 gap-4 xl:grid-cols-[320px_minmax(0,1fr)]"
      >
        <div className="grid gap-4">
          <SectionBlock
            title="Context signals"
            subtitle="What the assistant should keep in frame while answering"
          >
            <div className="space-y-3">
              <NarrativeLine label="Signal" text={narrative.summary} />
              <NarrativeLine label="Risk" text={narrative.risk} />
              <NarrativeLine label="Action" text={narrative.action} />
            </div>
          </SectionBlock>

          <SectionBlock
            title="Priority signals"
            subtitle="Business issues that should be escalated, not just retrieved"
          >
            <div className="space-y-3">
              {prioritySignals.map((signal) => (
                <PrioritySignalRow key={signal.label} signal={signal} />
              ))}
            </div>
          </SectionBlock>

          <SectionBlock
            title="Suggested prompts"
            subtitle="Start with a scoped question grounded in the current dataset"
          >
            <div className="space-y-2">
              {suggestedPrompts.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => onUsePrompt(suggestion)}
                  className="panel-nested w-full px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-white"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </SectionBlock>
        </div>

        <div className="grid min-h-0 gap-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <MiniStat
              label="Mode"
              value={latestAssistantMessage?.retrievalMode ?? "waiting"}
              detail="current engine"
            />
            <MiniStat
              label="Last ask"
              value={lastUserMessage ? "live" : "none"}
              detail={lastUserMessage ? truncateMiddle(lastUserMessage.content, 24) : "No prompt yet"}
            />
            <MiniStat
              label="Citations"
              value={String(citationCount)}
              detail="supporting comments"
            />
          </div>

          <SectionBlock
            title="Cross-layer read"
            subtitle="Explain why revenue is moving, not just what people said"
          >
            <div className="grid gap-3 md:grid-cols-3">
              <NarrativeChip label="Opportunity" text={narrative.opportunity} tone="positive" />
              <NarrativeChip label="Risk" text={narrative.risk} tone="negative" />
              <NarrativeChip label="Action" text={narrative.action} tone="neutral" />
            </div>
          </SectionBlock>

          <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
            <SectionBlock
              title="Conversation"
              subtitle="Live discussion grounded in stored feedback comments"
              className="min-h-0 flex h-full flex-col"
            >
              <div
                ref={messageViewportRef}
                className="min-h-0 flex-1 overflow-y-auto pr-2 [scrollbar-width:thin]"
              >
                <div className="space-y-3">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={
                        message.role === "assistant"
                          ? "panel-nested rounded-[1.4rem] p-4"
                          : "ml-6 rounded-[1.4rem] bg-slate-900 p-4 text-white shadow-[0_24px_60px_-28px_rgba(15,23,42,0.8)]"
                      }
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="mono-label">
                          {message.role === "assistant" ? "Assistant" : "You"}
                        </div>
                        {message.retrievalMode ? (
                          <Badge
                            variant="outline"
                            className={cn(
                              "rounded-full px-3 py-1 text-[10px]",
                              retrievalTone(message.retrievalMode),
                            )}
                          >
                            {message.retrievalMode}
                          </Badge>
                        ) : null}
                      </div>
                      <p
                        className={
                          message.role === "assistant"
                            ? "mt-2 text-sm leading-7 text-slate-700"
                            : "mt-2 text-sm leading-7 text-white"
                        }
                      >
                        {message.content}
                      </p>
                      {message.citations?.length ? (
                        <div className="mt-3 space-y-2">
                          {message.citations.map((citation) => (
                            <div
                              key={`${message.id}-${citation.feedbackId}`}
                              className="rounded-2xl border border-slate-200/70 bg-white/92 p-3"
                            >
                              <div className="text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                                {citation.campaignId} · {citation.product} · {citation.country} ·{" "}
                                {shortDate(citation.feedbackDate)}
                              </div>
                              <p className="mt-2 text-sm leading-6 text-slate-700">
                                {citation.comment}
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel-nested mt-4 shrink-0 p-4">
                <Textarea
                  ref={composerRef}
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      onSubmit();
                    }
                  }}
                  className="min-h-[104px] max-h-[160px] resize-none overflow-y-auto border-white/75 bg-white/75"
                  placeholder="Ask about complaints, campaign sentiment, product perception, or market-specific issues..."
                />
                <div className="mt-3 flex items-center justify-between gap-3">
                  <div className="text-xs text-muted-foreground">
                    `Enter` sends, `Shift + Enter` adds a new line.
                  </div>
                  <Button className="rounded-full px-5" onClick={onSubmit} disabled={isChatting}>
                    <SendHorizontal className="mr-2 size-4" />
                    {isChatting ? "Thinking..." : "Ask"}
                  </Button>
                </div>
              </div>
            </SectionBlock>

            <SectionBlock
              title="Live context"
              subtitle="Retrieval state, lead markets, and active feedback themes"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant="outline"
                  className={cn(
                    "rounded-full px-3 py-1.5 text-[11px]",
                    retrievalTone(latestAssistantMessage?.retrievalMode),
                  )}
                >
                  {latestAssistantMessage?.retrievalMode ?? "waiting"}
                </Badge>
                <Badge variant="outline" className="rounded-full px-3 py-1.5 text-[11px]">
                  {citationCount} citations
                </Badge>
                {leadSalesMarket ? (
                  <Badge variant="outline" className="rounded-full px-3 py-1.5 text-[11px]">
                    Lead market · {leadSalesMarket.country}
                  </Badge>
                ) : null}
                {pressureCountry ? (
                  <Badge variant="outline" className="rounded-full px-3 py-1.5 text-[11px]">
                    Watch · {pressureCountry.country}
                  </Badge>
                ) : null}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {(feedbackData?.topicSignals ?? []).map((topic) => (
                  <Badge
                    key={topic.topic}
                    variant="outline"
                    className="rounded-full px-3 py-1.5 text-[11px]"
                  >
                    {topic.topic}
                  </Badge>
                ))}
              </div>

              <div className="mt-4 grid gap-3">
                <div className="panel-nested p-3">
                  <div className="mono-label">Lead market</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">
                    {leadSalesMarket?.country ?? "No lead market"}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {leadSalesMarket
                      ? `${leadSalesMarket.region} · ${compactCurrencyFormatter.format(leadSalesMarket.revenue)}`
                      : "Sales data required"}
                  </div>
                </div>
                <div className="panel-nested p-3">
                  <div className="mono-label">Pressure market</div>
                  <div className="mt-2 text-sm font-semibold text-slate-900">
                    {pressureCountry?.country ?? "No pressure market"}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {pressureCountry
                      ? `${pressureCountry.region} · ${pressureCountry.feedbackCount} comments`
                      : "Feedback data required"}
                  </div>
                </div>
              </div>
            </SectionBlock>
          </div>
        </div>
      </CenteredOverlayPanel>
    </motion.div>
  );
}
