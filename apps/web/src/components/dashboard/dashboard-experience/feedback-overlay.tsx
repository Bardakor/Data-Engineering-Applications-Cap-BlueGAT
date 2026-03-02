"use client";

import { motion } from "motion/react";
import { Activity, BrainCircuit, Radar, X } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import type { FeedbackDashboardData, SalesDashboardData } from "@/lib/types";
import type { PrioritySignal } from "./types";
import {
  compactCurrencyFormatter,
  compactNumberFormatter,
} from "./types";
import {
  sentimentScoreLabel,
  sentimentTone,
  shortDate,
} from "./utils";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CenteredOverlayPanel,
  InsightTile,
  MetricTile,
  MiniStat,
  PrioritySignalRow,
  SectionBlock,
  SignalRow,
} from "./ui-components";
import { cn } from "@/lib/utils";

export function FeedbackOverlay({
  data,
  salesData,
  loading,
  prioritySignals,
  onPrompt,
  onClose,
}: {
  data: FeedbackDashboardData | null;
  salesData: SalesDashboardData | null;
  loading: boolean;
  prioritySignals: PrioritySignal[];
  onPrompt: (value: string) => void;
  onClose: () => void;
}) {
  const healthiestCampaign =
    [...(data?.campaignImpact ?? [])].sort((left, right) => {
      if (right.avgSentiment !== left.avgSentiment) {
        return right.avgSentiment - left.avgSentiment;
      }
      return right.feedbackCount - left.feedbackCount;
    })[0] ?? null;
  const mostFragileMarket =
    [...(data?.sentimentByCountry ?? [])].sort((left, right) => {
      if (left.avgSentiment !== right.avgSentiment) {
        return left.avgSentiment - right.avgSentiment;
      }
      return right.feedbackCount - left.feedbackCount;
    })[0] ?? null;
  const pressureTopic =
    [...(data?.topicSignals ?? [])]
      .sort((left, right) => {
        if (left.tone === right.tone) {
          return right.count - left.count;
        }
        return left.tone === "negative" ? -1 : 1;
      })[0] ?? null;
  const exposedRevenueMarket =
    mostFragileMarket
      ? salesData?.countryPerformance.find((row) => row.country === mostFragileMarket.country) ??
        null
      : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      className="pointer-events-none absolute inset-0 z-30"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08),rgba(15,23,42,0.12))] backdrop-blur-[2px]" />

      <CenteredOverlayPanel
        title="Feedback Dashboard"
        subtitle="One feedback panel layered over the live market map."
        icon={<Radar className="size-4" />}
        actions={
          <Button
            variant="outline"
            size="icon"
            className="rounded-2xl border-white/80 bg-white/88"
            onClick={onClose}
            aria-label="Close feedback dashboard"
          >
            <X className="size-4" />
          </Button>
        }
      >
        <div className="grid gap-4">
          <SectionBlock
            title="Sentiment stack"
            subtitle="Feedback KPIs for the current filtered slice"
          >
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {(data?.heroMetrics ?? []).map((metric) => (
                <MetricTile key={metric.label} metric={metric} />
              ))}
            </div>
          </SectionBlock>

          <div className="grid gap-4 xl:grid-cols-[1.04fr_0.96fr]">
            <div className="grid gap-4">
              <SectionBlock
                title="Operator reads"
                subtitle="Where feedback is helping or threatening the revenue layer"
              >
                <div className="grid gap-3 md:grid-cols-3">
                  <InsightTile
                    label="Healthiest campaign"
                    value={healthiestCampaign?.campaignId ?? "No campaign"}
                    detail={
                      healthiestCampaign
                        ? `${healthiestCampaign.product} · ${sentimentScoreLabel(healthiestCampaign.avgSentiment)} sentiment`
                        : "Awaiting data"
                    }
                    tone="feedback"
                  />
                  <InsightTile
                    label="Pressure market"
                    value={mostFragileMarket?.country ?? "No market"}
                    detail={
                      mostFragileMarket
                        ? `${sentimentScoreLabel(mostFragileMarket.avgSentiment)} sentiment · ${compactNumberFormatter.format(mostFragileMarket.feedbackCount)} comments`
                        : "Awaiting data"
                    }
                    tone="feedback"
                  />
                  <InsightTile
                    label="Revenue exposure"
                    value={exposedRevenueMarket?.country ?? pressureTopic?.topic ?? "No topic"}
                    detail={
                      exposedRevenueMarket
                        ? `${compactCurrencyFormatter.format(exposedRevenueMarket.revenue)} revenue still exposed while sentiment weakens`
                        : pressureTopic
                          ? `${pressureTopic.count} mentions · ${pressureTopic.tone} tone`
                          : "Awaiting data"
                    }
                    tone="feedback"
                  />
                </div>
              </SectionBlock>

              <SectionBlock
                title="Sentiment trend"
                subtitle="Positive versus negative comment drift over time"
              >
                <div className="grid gap-3 md:grid-cols-3">
                  <MiniStat
                    label="Best campaign"
                    value={healthiestCampaign?.campaignId ?? "n/a"}
                    detail={
                      healthiestCampaign
                        ? `${compactNumberFormatter.format(healthiestCampaign.feedbackCount)} comments`
                        : "No data"
                    }
                  />
                  <MiniStat
                    label="Risk market"
                    value={mostFragileMarket?.country ?? "n/a"}
                    detail={
                      mostFragileMarket
                        ? sentimentScoreLabel(mostFragileMarket.avgSentiment)
                        : "No data"
                    }
                  />
                  <MiniStat
                    label="Live topics"
                    value={String(data?.topicSignals.length ?? 0)}
                    detail="keywords tracked"
                  />
                </div>

                <ChartContainer
                  className={cn("mt-4 h-[240px] w-full", loading && "opacity-70")}
                  config={{
                    positive: { label: "Positive", color: "#22c55e" },
                    negative: { label: "Negative", color: "#ef4444" },
                  }}
                >
                  <AreaChart data={data?.sentimentTrend ?? []}>
                    <defs>
                      <linearGradient id="feedbackPositive" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-positive)" stopOpacity={0.22} />
                        <stop offset="95%" stopColor="var(--color-positive)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} strokeDasharray="3 6" />
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={shortDate}
                    />
                    <YAxis tickLine={false} axisLine={false} />
                    <ChartTooltip content={<ChartTooltipContent indicator="dot" />} />
                    <Area
                      type="monotone"
                      dataKey="positive"
                      stroke="var(--color-positive)"
                      strokeWidth={2}
                      fill="url(#feedbackPositive)"
                    />
                    <Area
                      type="monotone"
                      dataKey="negative"
                      stroke="var(--color-negative)"
                      strokeWidth={2}
                      fill="transparent"
                    />
                  </AreaChart>
                </ChartContainer>
              </SectionBlock>

              <SectionBlock
                title="Action lane"
                subtitle="Escalations and next prompts for the assistant"
              >
                <div className="grid gap-3">
                  {prioritySignals.map((signal) => (
                    <PrioritySignalRow key={signal.label} signal={signal} />
                  ))}
                  {(data?.briefs ?? []).map((brief) => (
                    <SignalRow
                      key={brief}
                      icon={<Activity className="size-4" />}
                      text={brief}
                      tone="feedback"
                    />
                  ))}
                </div>
                <Button
                  className="mt-4 w-full rounded-2xl"
                  onClick={() =>
                    onPrompt("What are the biggest operational issues in feedback right now?")
                  }
                >
                  <BrainCircuit className="mr-2 size-4" />
                  Send to CheepChat
                </Button>
              </SectionBlock>
            </div>

            <div className="grid gap-4">
              <SectionBlock
                title="Topic drift"
                subtitle="Keywords shaping the campaign conversation"
              >
                <div className="flex flex-wrap gap-2">
                  {(data?.topicSignals ?? []).map((topic) => (
                    <Badge
                      key={topic.topic}
                      variant="outline"
                      className={cn(
                        "rounded-full px-3 py-1.5 text-[11px]",
                        topic.tone === "positive"
                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                          : topic.tone === "negative"
                            ? "border-rose-200 bg-rose-50 text-rose-700"
                            : "border-amber-200 bg-amber-50 text-amber-700",
                      )}
                    >
                      {topic.topic} · {topic.count}
                    </Badge>
                  ))}
                </div>
              </SectionBlock>

              <SectionBlock
                title="Campaign detail"
                subtitle="Campaign impact and the most recent voices in one panel"
              >
                <Tabs defaultValue="campaigns" className="w-full">
                  <TabsList className="grid w-full grid-cols-2 rounded-full bg-white/80">
                    <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
                    <TabsTrigger value="voices">Voices</TabsTrigger>
                  </TabsList>

                  <TabsContent value="campaigns" className="mt-4 space-y-3">
                    {(data?.campaignImpact ?? []).map((campaign) => (
                      <div key={campaign.campaignId} className="panel-nested p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-semibold text-slate-900">
                              {campaign.campaignId}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {campaign.product}
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              "rounded-full px-3 py-1 text-[10px]",
                              campaign.avgSentiment >= 0.25
                                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                : campaign.avgSentiment < 0
                                  ? "border-rose-200 bg-rose-50 text-rose-700"
                                  : "border-amber-200 bg-amber-50 text-amber-700",
                            )}
                          >
                            {campaign.avgSentiment.toFixed(2)}
                          </Badge>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <Badge variant="outline" className="rounded-full px-2.5 py-1 text-[10px]">
                            {compactNumberFormatter.format(campaign.feedbackCount)} comments
                          </Badge>
                          <Badge variant="outline" className="rounded-full px-2.5 py-1 text-[10px]">
                            {compactCurrencyFormatter.format(campaign.linkedRevenue)} linked sales
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-700">
                          {campaign.headline}
                        </p>
                      </div>
                    ))}
                  </TabsContent>

                  <TabsContent value="voices" className="mt-4 space-y-3">
                    {(data?.recentFeedback ?? []).map((entry) => (
                      <div key={entry.id} className="panel-nested p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-slate-900">
                            {entry.product}
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              "rounded-full px-3 py-1 text-[10px]",
                              sentimentTone(entry.sentimentLabel),
                            )}
                          >
                            {entry.sentimentLabel}
                          </Badge>
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          {entry.country} · {entry.campaignId} · {shortDate(entry.feedbackDate)}
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-700">
                          {entry.comment}
                        </p>
                      </div>
                    ))}
                  </TabsContent>
                </Tabs>
              </SectionBlock>

              <SectionBlock
                title="Country watchlist"
                subtitle="Where volume is high and sentiment is starting to fracture"
              >
                <div className="grid gap-3">
                  {(data?.sentimentByCountry ?? []).map((country) => (
                    <div key={country.country} className="panel-nested p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">
                            {country.country}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {country.region}
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className={cn(
                            "rounded-full px-3 py-1 text-[10px]",
                            country.avgSentiment >= 0.25
                              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                              : country.avgSentiment < 0
                                ? "border-rose-200 bg-rose-50 text-rose-700"
                                : "border-amber-200 bg-amber-50 text-amber-700",
                          )}
                        >
                          {sentimentScoreLabel(country.avgSentiment)}
                        </Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Badge variant="outline" className="rounded-full px-2.5 py-1 text-[10px]">
                          {compactNumberFormatter.format(country.feedbackCount)} comments
                        </Badge>
                        <Badge variant="outline" className="rounded-full px-2.5 py-1 text-[10px]">
                          +{Math.round(country.positiveShare * 100)}% positive
                        </Badge>
                        <Badge variant="outline" className="rounded-full px-2.5 py-1 text-[10px]">
                          -{Math.round(country.negativeShare * 100)}% negative
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </SectionBlock>
            </div>
          </div>
        </div>
      </CenteredOverlayPanel>
    </motion.div>
  );
}
