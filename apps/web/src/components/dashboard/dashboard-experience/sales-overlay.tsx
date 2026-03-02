"use client";

import { motion } from "motion/react";
import { CircleDollarSign, TrendingUp, X } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";
import type { FeedbackDashboardData, SalesDashboardData } from "@/lib/types";
import type { PrioritySignal } from "./types";
import { mapPalette } from "./types";
import {
  compactCurrencyFormatter,
  compactNumberFormatter,
  percentageFormatter,
} from "./types";
import {
  formatDelta,
  percentageValue,
  sentimentScoreLabel,
  shortDate,
  moneyTick,
} from "./utils";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Button } from "@/components/ui/button";
import {
  CenteredOverlayPanel,
  InsightTile,
  MetricTile,
  MiniStat,
  PrioritySignalRow,
  RankRow,
  SectionBlock,
  SignalRow,
} from "./ui-components";
import { cn } from "@/lib/utils";

export function SalesOverlay({
  data,
  feedbackData,
  loading,
  prioritySignals,
  onClose,
}: {
  data: SalesDashboardData | null;
  feedbackData: FeedbackDashboardData | null;
  loading: boolean;
  prioritySignals: PrioritySignal[];
  onClose: () => void;
}) {
  const leadMarket = data?.countryPerformance[0] ?? null;
  const fastestGrowthMarket =
    [...(data?.countryPerformance ?? [])].sort((left, right) => right.growth - left.growth)[0] ??
    null;
  const leadRegion = data?.regionPerformance[0] ?? null;
  const topProduct = data?.productMix[0] ?? null;
  const leadCampaign =
    [...(feedbackData?.campaignImpact ?? [])].sort(
      (left, right) => right.linkedRevenue - left.linkedRevenue,
    )[0] ?? null;
  const leadSentimentMarket =
    leadMarket
      ? feedbackData?.sentimentByCountry.find((row) => row.country === leadMarket.country) ?? null
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
        title="Sales Dashboard"
        subtitle="One commercial control panel layered over the live map."
        icon={<CircleDollarSign className="size-4" />}
        actions={
          <Button
            variant="outline"
            size="icon"
            className="rounded-2xl border-white/80 bg-white/88"
            onClick={onClose}
            aria-label="Close sales dashboard"
          >
            <X className="size-4" />
          </Button>
        }
      >
        <div className="grid gap-4">
          <SectionBlock
            title="Revenue stack"
            subtitle="Core sales KPIs across the selected window"
          >
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {(data?.heroMetrics ?? []).map((metric) => (
                <MetricTile key={metric.label} metric={metric} />
              ))}
            </div>
          </SectionBlock>

          <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <div className="grid gap-4">
              <SectionBlock
                title="Operator reads"
                subtitle="Commercial momentum and cross-layer reinforcement"
              >
                <div className="grid gap-3 md:grid-cols-3">
                  <InsightTile
                    label="Lead market"
                    value={leadMarket?.country ?? "No market"}
                    detail={
                      leadMarket
                        ? `${compactCurrencyFormatter.format(leadMarket.revenue)} revenue · ${formatDelta(leadMarket.growth)}`
                        : "Awaiting data"
                    }
                    tone="sales"
                  />
                  <InsightTile
                    label="Campaign lift"
                    value={leadCampaign?.campaignId ?? "No campaign"}
                    detail={
                      leadCampaign
                        ? `${leadCampaign.product} · ${compactCurrencyFormatter.format(leadCampaign.linkedRevenue)} linked sales`
                        : "Awaiting data"
                    }
                    tone="sales"
                  />
                  <InsightTile
                    label="Sentiment support"
                    value={leadSentimentMarket?.country ?? fastestGrowthMarket?.country ?? "No signal"}
                    detail={
                      leadSentimentMarket
                        ? `${sentimentScoreLabel(leadSentimentMarket.avgSentiment)} sentiment reinforcing the lead market`
                        : topProduct
                          ? `${percentageValue(topProduct.share)} of revenue · ${compactNumberFormatter.format(topProduct.units)} units`
                          : "Awaiting data"
                    }
                    tone="sales"
                  />
                </div>
              </SectionBlock>

              <SectionBlock
                title="Revenue trend"
                subtitle="Weekly revenue movement across the filtered perimeter"
              >
                <div className="grid gap-3 md:grid-cols-3">
                  <MiniStat
                    label="Top region"
                    value={leadRegion?.region ?? "n/a"}
                    detail={leadRegion ? percentageValue(leadRegion.share) : "No data"}
                  />
                  <MiniStat
                    label="Top product"
                    value={topProduct?.product ?? "n/a"}
                    detail={
                      topProduct
                        ? compactCurrencyFormatter.format(topProduct.revenue)
                        : "No data"
                    }
                  />
                  <MiniStat
                    label="Map coverage"
                    value={String(data?.mapConnections.length ?? 0)}
                    detail="active market links"
                  />
                </div>

                <ChartContainer
                  className={cn("mt-4 h-[240px] w-full", loading && "opacity-70")}
                  config={{
                    revenue: { label: "Revenue", color: "#f97316" },
                  }}
                >
                  <AreaChart data={data?.revenueTrend ?? []}>
                    <defs>
                      <linearGradient id="salesArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-revenue)" stopOpacity={0.28} />
                        <stop offset="95%" stopColor="var(--color-revenue)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} strokeDasharray="3 6" />
                    <XAxis
                      dataKey="date"
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={shortDate}
                    />
                    <YAxis tickLine={false} axisLine={false} tickFormatter={moneyTick} />
                    <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="var(--color-revenue)"
                      strokeWidth={2}
                      fill="url(#salesArea)"
                    />
                  </AreaChart>
                </ChartContainer>
              </SectionBlock>

              <SectionBlock
                title="Priority signals"
                subtitle="What to protect, what to push, and what to act on next"
              >
                <div className="grid gap-3">
                  {prioritySignals.map((signal) => (
                    <PrioritySignalRow key={signal.label} signal={signal} />
                  ))}
                  {(data?.spotlights ?? []).map((spotlight) => (
                    <SignalRow
                      key={spotlight}
                      icon={<TrendingUp className="size-4" />}
                      text={spotlight}
                      tone="sales"
                    />
                  ))}
                </div>
              </SectionBlock>
            </div>

            <div className="grid gap-4">
              <SectionBlock
                title="Market leaderboard"
                subtitle="Revenue, growth, and order density by country"
              >
                <div className="grid gap-3">
                  {(data?.countryPerformance ?? []).map((row) => (
                    <RankRow
                      key={row.country}
                      title={row.country}
                      subtitle={`${row.region} · ${compactNumberFormatter.format(row.orders)} orders`}
                      value={compactCurrencyFormatter.format(row.revenue)}
                      meta={formatDelta(row.growth)}
                    />
                  ))}
                </div>
              </SectionBlock>

              <SectionBlock
                title="Product mix"
                subtitle="How the revenue base is distributed by product family"
              >
                <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
                  <ChartContainer
                    className="h-[220px] w-full"
                    config={{ share: { label: "Share", color: "#0f172a" } }}
                  >
                    <PieChart>
                      <Pie
                        data={data?.productMix ?? []}
                        dataKey="revenue"
                        innerRadius={52}
                        outerRadius={84}
                        paddingAngle={4}
                      >
                        {(data?.productMix ?? []).map((row, index) => (
                          <Cell
                            key={row.product}
                            fill={mapPalette[index % mapPalette.length]}
                          />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent hideLabel />} />
                    </PieChart>
                  </ChartContainer>

                  <div className="grid gap-3">
                    {(data?.productMix ?? []).map((row, index) => (
                      <div key={row.product} className="panel-nested p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span
                              className="block h-3 w-3 rounded-full"
                              style={{ backgroundColor: mapPalette[index % mapPalette.length] }}
                            />
                            <div>
                              <div className="text-sm font-medium text-slate-900">
                                {row.product}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {compactNumberFormatter.format(row.units)} units
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-slate-900">
                              {compactCurrencyFormatter.format(row.revenue)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {percentageFormatter.format(row.share)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </SectionBlock>
            </div>
          </div>
        </div>
      </CenteredOverlayPanel>
    </motion.div>
  );
}
