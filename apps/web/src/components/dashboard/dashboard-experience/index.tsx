"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { format } from "date-fns";
import {
  Bot,
  ChartColumn,
  CircleDollarSign,
  MapPinned,
  RefreshCw,
  Waypoints,
} from "lucide-react";
import { AnimatePresence } from "motion/react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FloatingDock } from "@/components/ui/floating-dock";
import { WorldMap } from "@/components/ui/world-map";
import type { WorldMapMarker } from "@/components/ui/world-map";
import {
  askFeedbackRag,
  getDataPreview,
  getFeedbackDashboard,
  getSalesDashboard,
} from "@/lib/api";
import { defaultFilters } from "@/lib/defaults";
import type {
  DashboardFilters,
  DashboardView,
  DataPreview,
  FeedbackDashboardData,
  SalesDashboardData,
} from "@/lib/types";
import { compactCurrencyFormatter, compactNumberFormatter, suggestedPrompts } from "./types";
import type { ChatMessage } from "./types";
import {
  compactCurrencyFormatter as sharedCompactCurrencyFormatter,
  formatDelta,
  longDateTime,
  stageLineColor,
} from "./utils";
import { buildControlRoomState } from "./control-room";
import { ChatOverlay } from "./chat-overlay";
import { EmptyOverlay } from "./empty-overlay";
import { ErrorOverlay } from "./error-overlay";
import { FeedbackOverlay } from "./feedback-overlay";
import { SalesOverlay } from "./sales-overlay";
import { DataPreviewSheet } from "./data-preview-sheet";
import { FiltersSheet } from "./filters-sheet";
import { MiniStat, StatusPill } from "./ui-components";

type MapLocationSummary = {
  id: string;
  country: string;
  region: string;
  lat: number;
  lng: number;
  revenue: number;
  orders: number;
  growth: number | null;
  feedbackCount: number;
  avgSentiment: number | null;
  positiveShare: number | null;
  negativeShare: number | null;
  reviewDelta: number | null;
};

export function DashboardExperience() {
  const [view, setView] = useState<DashboardView>("map");
  const [filters, setFilters] = useState<DashboardFilters>(defaultFilters);
  const deferredFilters = useDeferredValue(filters);
  const [salesData, setSalesData] = useState<SalesDashboardData | null>(null);
  const [feedbackData, setFeedbackData] = useState<FeedbackDashboardData | null>(null);
  const [preview, setPreview] = useState<DataPreview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadTick, setReloadTick] = useState(0);
  const [prompt, setPrompt] = useState(suggestedPrompts[0]);
  const [isChatting, setIsChatting] = useState(false);
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "assistant-welcome",
      role: "assistant",
      content:
        "Ask directly about campaign sentiment, complaints, product perception, or market-specific issues. Responses are grounded on feedback stored in the API.",
    },
  ]);

  useEffect(() => {
    let active = true;

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const [sales, feedback] = await Promise.all([
          getSalesDashboard(deferredFilters),
          getFeedbackDashboard(deferredFilters),
        ]);

        if (!active) return;

        setSalesData(sales);
        setFeedbackData(feedback);
      } catch (loadError) {
        if (!active) return;

        setError(
          loadError instanceof Error
            ? loadError.message
            : "The dashboard could not reach the API.",
        );
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [deferredFilters, reloadTick]);

  useEffect(() => {
    let active = true;

    void getDataPreview()
      .then((data) => {
        if (active) {
          setPreview(data);
        }
      })
      .catch(() => {
        if (active) {
          setPreview(null);
        }
      });

    return () => {
      active = false;
    };
  }, [reloadTick]);

  const filtersMeta =
    salesData?.filters ??
    feedbackData?.filters ?? {
      products: [filters.product],
      countries: [filters.country],
      regions: [filters.region],
      minDate: filters.dateFrom,
      maxDate: filters.dateTo,
    };

  const combinedConnections = useMemo(() => {
    const uniqueConnections = new Map<
      string,
      NonNullable<SalesDashboardData["mapConnections"]>[number]
    >();

    for (const connection of [
      ...(salesData?.mapConnections ?? []),
      ...(feedbackData?.mapConnections ?? []),
    ]) {
      const key = connection.end.label ?? `${connection.end.lat}:${connection.end.lng}`;
      const existing = uniqueConnections.get(key);

      if (!existing || connection.share > existing.share) {
        uniqueConnections.set(key, connection);
      }
    }

    return Array.from(uniqueConnections.values());
  }, [feedbackData?.mapConnections, salesData?.mapConnections]);

  const mapConnections = useMemo(() => {
    if (view === "sales") {
      return salesData?.mapConnections ?? combinedConnections;
    }
    if (view === "feedback") {
      return feedbackData?.mapConnections ?? combinedConnections;
    }
    return combinedConnections;
  }, [combinedConnections, feedbackData?.mapConnections, salesData?.mapConnections, view]);

  const mapLocations = useMemo<MapLocationSummary[]>(() => {
    const salesByCountry = new Map(
      (salesData?.countryPerformance ?? []).map((row) => [row.country, row] as const),
    );
    const feedbackByCountry = new Map(
      (feedbackData?.sentimentByCountry ?? []).map((row) => [row.country, row] as const),
    );

    return Array.from(
      new Set([...salesByCountry.keys(), ...feedbackByCountry.keys()]),
    )
      .map((country) => {
        const sales = salesByCountry.get(country) ?? null;
        const feedback = feedbackByCountry.get(country) ?? null;
        const lat = sales?.lat ?? feedback?.lat ?? 0;
        const lng = sales?.lng ?? feedback?.lng ?? 0;

        return {
          id: country,
          country,
          region: sales?.region ?? feedback?.region ?? "Unknown",
          lat,
          lng,
          revenue: sales?.revenue ?? 0,
          orders: sales?.orders ?? 0,
          growth: sales?.growth ?? null,
          feedbackCount: feedback?.feedbackCount ?? 0,
          avgSentiment: feedback?.avgSentiment ?? null,
          positiveShare: feedback?.positiveShare ?? null,
          negativeShare: feedback?.negativeShare ?? null,
          reviewDelta:
            feedback && typeof feedback.positiveShare === "number"
              ? feedback.positiveShare - feedback.negativeShare
              : null,
        };
      })
      .filter(
        (location) =>
          Number.isFinite(location.lat) &&
          Number.isFinite(location.lng) &&
          (location.lat !== 0 || location.lng !== 0),
      )
      .sort((left, right) => {
        if (right.revenue !== left.revenue) {
          return right.revenue - left.revenue;
        }
        return right.feedbackCount - left.feedbackCount;
      });
  }, [feedbackData?.sentimentByCountry, salesData?.countryPerformance]);

  useEffect(() => {
    if (!mapLocations.length) {
      setSelectedLocationId(null);
      return;
    }

    setSelectedLocationId((current) => {
      if (current && mapLocations.some((location) => location.id === current)) {
        return current;
      }
      return mapLocations[0].id;
    });
  }, [mapLocations]);

  const selectedLocation =
    mapLocations.find((location) => location.id === selectedLocationId) ?? mapLocations[0] ?? null;

  const mapMarkers = useMemo<WorldMapMarker[]>(
    () =>
      mapLocations.map((location) => {
        const reviewDeltaLabel =
          location.reviewDelta === null
            ? "No reviews"
            : `${location.reviewDelta >= 0 ? "+" : ""}${Math.round(location.reviewDelta * 100)} pts`;

        return {
          id: location.id,
          lat: location.lat,
          lng: location.lng,
          label: location.country,
          statValue: reviewDeltaLabel,
          secondaryValue:
            location.revenue > 0
              ? sharedCompactCurrencyFormatter.format(location.revenue)
              : undefined,
          detail:
            location.feedbackCount > 0
              ? `${compactNumberFormatter.format(location.feedbackCount)} reviews`
              : location.region,
          tone:
            location.reviewDelta === null
              ? "neutral"
              : location.reviewDelta >= 0.08
                ? "positive"
                : location.reviewDelta <= -0.08
                  ? "negative"
                  : "neutral",
          active: location.id === selectedLocationId,
          onClick: () => setSelectedLocationId(location.id),
        };
      }),
    [mapLocations, selectedLocationId],
  );

  const currentGeneratedAt = salesData?.generatedAt ?? feedbackData?.generatedAt ?? null;
  const hasDatabaseContent = Boolean(
    (salesData?.countryPerformance.length ?? 0) > 0 ||
      (feedbackData?.recentFeedback.length ?? 0) > 0,
  );
  const activeFilterBadges = [
    filters.product !== defaultFilters.product ? `Product · ${filters.product}` : null,
    filters.country !== defaultFilters.country ? `Country · ${filters.country}` : null,
    filters.region !== defaultFilters.region ? `Region · ${filters.region}` : null,
  ].filter((value): value is string => Boolean(value));
  const dateWindowLabel = `${format(new Date(filters.dateFrom), "MMM d")} - ${format(
    new Date(filters.dateTo),
    "MMM d",
  )}`;
  const latestRetrievalMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && message.retrievalMode);
  const lastUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");
  const controlRoom = useMemo(
    () => buildControlRoomState(salesData, feedbackData, latestRetrievalMessage, lastUserMessage),
    [feedbackData, lastUserMessage, latestRetrievalMessage, salesData],
  );

  async function submitPrompt(nextPrompt?: string) {
    const userPrompt = (nextPrompt ?? prompt).trim();

    if (!userPrompt) return;

    setView("chat");
    setPrompt("");
    setIsChatting(true);
    setMessages((current) => [
      ...current,
      {
        id: `${Date.now()}-user`,
        role: "user",
        content: userPrompt,
      },
    ]);

    try {
      const result = await askFeedbackRag(userPrompt, filters);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          retrievalMode: result.retrievalMode,
          generationMode: result.generationMode,
        },
      ]);
    } catch (submitError) {
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant-error`,
          role: "assistant",
          content:
            submitError instanceof Error
              ? submitError.message
              : "The chat request failed.",
        },
      ]);
    } finally {
      setIsChatting(false);
    }
  }

  const dockItems = [
    {
      id: "map",
      title: "Map",
      active: view === "map",
      onClick: () => setView("map"),
      icon: <MapPinned className="size-full" />,
    },
    {
      id: "sales",
      title: "Sales",
      active: view === "sales",
      onClick: () => setView("sales"),
      icon: <CircleDollarSign className="size-full" />,
    },
    {
      id: "feedback",
      title: "Feedback",
      active: view === "feedback",
      onClick: () => setView("feedback"),
      icon: <ChartColumn className="size-full" />,
    },
    {
      id: "chat",
      title: "CheepChat",
      active: view === "chat",
      onClick: () => setView("chat"),
      icon: <Bot className="size-full" />,
    },
  ];

  return (
    <main className="h-[100dvh] overflow-hidden p-2.5 lg:p-3">
      <div className="grid h-full grid-rows-[auto_1fr] gap-3">
        <header className="panel flex items-center gap-3 px-4 py-3 lg:px-5">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
              <Waypoints className="size-4" />
            </div>
            <div className="min-w-0">
              <div className="mono-label">BlueGAT x AFC</div>
              <div className="flex items-center gap-2">
                <div className="truncate text-sm font-semibold text-slate-900 lg:text-base">
                  Nugget Data & AI Initiative
                </div>
                <Badge
                  variant="outline"
                  className="hidden rounded-full px-3 py-1 md:inline-flex"
                >
                  {view === "map"
                    ? "Live map"
                    : view === "sales"
                      ? "Sales dashboard"
                      : view === "feedback"
                        ? "Feedback dashboard"
                        : "CheepChat"}
                </Badge>
              </div>
              <div className="hidden text-xs text-muted-foreground xl:block">
                Map-first dashboard over stored sales and feedback data.
              </div>
            </div>
          </div>

          <div className="hidden min-w-0 flex-1 items-center gap-2 overflow-x-auto xl:flex">
            <Badge variant="outline" className="shrink-0 rounded-full px-3 py-1 text-[11px]">
              Window · {dateWindowLabel}
            </Badge>
            {activeFilterBadges.length ? (
              activeFilterBadges.map((badge) => (
                <Badge
                  key={badge}
                  variant="outline"
                  className="shrink-0 rounded-full px-3 py-1 text-[11px]"
                >
                  {badge}
                </Badge>
              ))
            ) : (
              <Badge variant="outline" className="shrink-0 rounded-full px-3 py-1 text-[11px]">
                Network scope
              </Badge>
            )}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <StatusPill
              label={
                error
                  ? "API error"
                  : hasDatabaseContent
                    ? "Database live"
                    : "Awaiting ingestion"
              }
              tone={
                error
                  ? "critical"
                  : hasDatabaseContent
                    ? "healthy"
                    : "neutral"
              }
            />
            {currentGeneratedAt ? (
              <Badge
                variant="outline"
                className="hidden rounded-full px-3 py-1 text-[11px] lg:inline-flex"
              >
                Updated {longDateTime(currentGeneratedAt)}
              </Badge>
            ) : null}
            <FiltersSheet
              filters={filters}
              filtersMeta={filtersMeta}
              onChange={setFilters}
            />
            <Button
              variant="outline"
              className="rounded-full border-white/80 bg-white/85"
              onClick={() => setReloadTick((current) => current + 1)}
            >
              <RefreshCw className="size-4 sm:mr-2" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <DataPreviewSheet preview={preview} />
          </div>
        </header>

        <section className="relative min-h-0 overflow-hidden rounded-[2.35rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.78),rgba(247,244,236,0.68))]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.14),transparent_28%),radial-gradient(circle_at_top_right,rgba(249,115,22,0.16),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.2),rgba(255,255,255,0))]" />
          <div className="absolute inset-0 px-2.5 pb-24 pt-2.5 lg:px-3 lg:pb-28 lg:pt-3">
            <WorldMap
              dots={mapConnections}
              markers={mapMarkers}
              className="h-full min-h-full aspect-auto rounded-[2rem]"
              lineColor={stageLineColor(view)}
              dotColor="#0f172a"
              mapColor="rgba(15, 23, 42, 0.18)"
              showLabels={false}
            />
          </div>

          <div className="absolute left-4 top-4 z-20 flex flex-wrap items-center gap-2">
            <Badge className="rounded-full bg-slate-900 px-3 py-1 text-white">
              {view === "map"
                ? "Map layer"
                : view === "sales"
                  ? "Sales panel open"
                  : view === "feedback"
                    ? "Feedback panel open"
                    : "CheepChat open"}
            </Badge>
            <Badge variant="outline" className="rounded-full px-3 py-1 text-[11px]">
              {compactNumberFormatter.format(mapLocations.length)} locations
            </Badge>
            <Badge variant="outline" className="rounded-full px-3 py-1 text-[11px]">
              {compactNumberFormatter.format(mapConnections.length)} map links
            </Badge>
            <Badge variant="outline" className="rounded-full px-3 py-1 text-[11px]">
              {view === "sales"
                ? "Revenue-weighted arcs"
                : view === "feedback"
                  ? "Feedback-weighted arcs"
                  : "Click a location dot for a quick summary"}
            </Badge>
          </div>

          {selectedLocation && !error && hasDatabaseContent ? (
            <div className="pointer-events-auto absolute bottom-24 left-4 z-20 w-[min(22rem,calc(100%-2rem))]">
              <div className="panel-strong p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="mono-label">Location quick summary</div>
                    <div className="mt-1 text-lg font-semibold text-slate-900">
                      {selectedLocation.country}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {selectedLocation.region}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      selectedLocation.reviewDelta === null
                        ? "rounded-full border-slate-200 bg-white/80 px-3 py-1 text-[11px] text-slate-600"
                        : selectedLocation.reviewDelta >= 0.08
                          ? "rounded-full border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] text-emerald-700"
                          : selectedLocation.reviewDelta <= -0.08
                            ? "rounded-full border-rose-200 bg-rose-50 px-3 py-1 text-[11px] text-rose-700"
                            : "rounded-full border-amber-200 bg-amber-50 px-3 py-1 text-[11px] text-amber-700"
                    }
                  >
                    {selectedLocation.reviewDelta === null
                      ? "No review delta"
                      : `${selectedLocation.reviewDelta >= 0 ? "+" : ""}${Math.round(
                          selectedLocation.reviewDelta * 100,
                        )} pts`}
                  </Badge>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <MiniStat
                    label="Revenue"
                    value={
                      selectedLocation.revenue > 0
                        ? compactCurrencyFormatter.format(selectedLocation.revenue)
                        : "n/a"
                    }
                    detail={
                      selectedLocation.orders > 0
                        ? `${compactNumberFormatter.format(selectedLocation.orders)} orders`
                        : "No sales"
                    }
                  />
                  <MiniStat
                    label="Reviews"
                    value={compactNumberFormatter.format(selectedLocation.feedbackCount)}
                    detail={
                      selectedLocation.positiveShare !== null &&
                      selectedLocation.negativeShare !== null
                        ? `${Math.round(selectedLocation.positiveShare * 100)}% positive · ${Math.round(selectedLocation.negativeShare * 100)}% negative`
                        : "No feedback split"
                    }
                  />
                  <MiniStat
                    label="Avg sentiment"
                    value={
                      selectedLocation.avgSentiment !== null
                        ? selectedLocation.avgSentiment.toFixed(2)
                        : "n/a"
                    }
                    detail="compound sentiment"
                  />
                  <MiniStat
                    label="Sales growth"
                    value={
                      selectedLocation.growth !== null
                        ? formatDelta(selectedLocation.growth)
                        : "n/a"
                    }
                    detail="vs previous window"
                  />
                </div>
              </div>
            </div>
          ) : null}

          <AnimatePresence mode="wait">
            {error ? (
              <ErrorOverlay
                key="error"
                message={error}
                onRetry={() => setReloadTick((current) => current + 1)}
              />
            ) : !hasDatabaseContent && !isLoading ? (
              <EmptyOverlay key="empty" />
            ) : view === "sales" ? (
              <SalesOverlay
                key="sales"
                data={salesData}
                feedbackData={feedbackData}
                loading={isLoading}
                prioritySignals={controlRoom.prioritySignals}
                onClose={() => setView("map")}
              />
            ) : view === "feedback" ? (
              <FeedbackOverlay
                key="feedback"
                data={feedbackData}
                salesData={salesData}
                loading={isLoading}
                prioritySignals={controlRoom.prioritySignals}
                onPrompt={(value) => void submitPrompt(value)}
                onClose={() => setView("map")}
              />
            ) : view === "chat" ? (
              <ChatOverlay
                key="chat"
                salesData={salesData}
                feedbackData={feedbackData}
                prompt={prompt}
                setPrompt={setPrompt}
                messages={messages}
                isChatting={isChatting}
                narrative={controlRoom.narrative}
                prioritySignals={controlRoom.prioritySignals}
                onSubmit={() => void submitPrompt()}
                onUsePrompt={(value) => void submitPrompt(value)}
                onClose={() => setView("map")}
              />
            ) : null}
          </AnimatePresence>
        </section>
      </div>

      <FloatingDock items={dockItems} />
    </main>
  );
}
