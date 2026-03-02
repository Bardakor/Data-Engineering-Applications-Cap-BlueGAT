"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PrioritySignal, SignalTone } from "./types";
import { formatDelta, formatMetricValue } from "./utils";
import type { SalesDashboardData } from "@/lib/types";

export function OverlayCard({
  title,
  icon,
  children,
  padded = true,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  padded?: boolean;
}) {
  return (
    <div className="panel flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-white/70 px-4 py-3">
        <div>
          <div className="mono-label">{title}</div>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-slate-900 text-white">
          {icon}
        </div>
      </div>
      <div className={cn("min-h-0 flex-1", padded && "p-4")}>{children}</div>
    </div>
  );
}

export function CenteredOverlayPanel({
  title,
  subtitle,
  icon,
  actions,
  children,
  className,
  bodyClassName,
}: {
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <div className="pointer-events-auto absolute inset-x-3 bottom-20 top-16 z-30 md:inset-x-6 md:bottom-24 md:top-20 xl:inset-auto xl:left-1/2 xl:top-1/2 xl:h-[min(82vh,880px)] xl:w-[min(1180px,calc(100vw-4rem))] xl:-translate-x-1/2 xl:-translate-y-1/2">
      <div className={cn("panel-strong data-glow flex h-full flex-col overflow-hidden", className)}>
        <div className="flex items-center justify-between gap-3 border-b border-white/80 px-4 py-3 lg:px-5">
          <div className="min-w-0">
            <div className="mono-label">{title}</div>
            {subtitle ? (
              <p className="mt-1 text-sm leading-6 text-slate-600">{subtitle}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            {actions}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white">
              {icon}
            </div>
          </div>
        </div>
        <div className={cn("min-h-0 flex-1 overflow-y-auto p-4 lg:p-5", bodyClassName)}>
          {children}
        </div>
      </div>
    </div>
  );
}

export function SectionBlock({
  title,
  subtitle,
  children,
  className,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("panel-nested p-4", className)}>
      <div className="mb-3">
        <div className="mono-label">{title}</div>
        {subtitle ? <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div> : null}
      </div>
      {children}
    </div>
  );
}

export function InsightTile({
  label,
  value,
  detail,
  tone = "sales",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "sales" | "feedback" | "chat";
}) {
  return (
    <div
      className={cn(
        "rounded-[1.3rem] border p-3",
        tone === "sales"
          ? "border-orange-200/70 bg-orange-50/55"
          : tone === "feedback"
            ? "border-sky-200/70 bg-sky-50/55"
            : "border-emerald-200/70 bg-emerald-50/55",
      )}
    >
      <div className="mono-label">{label}</div>
      <div className="mt-2 text-base font-semibold text-slate-900">{value}</div>
      <div className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</div>
    </div>
  );
}

export function SignalRow({
  icon,
  text,
  tone = "sales",
}: {
  icon: React.ReactNode;
  text: string;
  tone?: "sales" | "feedback" | "chat";
}) {
  return (
    <div
      className={cn(
        "flex gap-3 rounded-[1.35rem] border p-3",
        tone === "sales"
          ? "border-orange-200/60 bg-orange-50/45"
          : tone === "feedback"
            ? "border-sky-200/60 bg-sky-50/45"
            : "border-emerald-200/60 bg-emerald-50/45",
      )}
    >
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white">
        {icon}
      </div>
      <p className="text-sm leading-6 text-slate-700">{text}</p>
    </div>
  );
}

export function MiniStat({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-[1.2rem] border border-white/70 bg-white/72 p-3">
      <div className="mono-label">{label}</div>
      <div className="mt-2 truncate text-sm font-semibold text-slate-900">{value}</div>
      <div className="mt-1 text-[11px] text-muted-foreground">{detail}</div>
    </div>
  );
}

export function PrioritySignalRow({ signal }: { signal: PrioritySignal }) {
  return (
    <div
      className={cn(
        "rounded-[1.35rem] border p-3",
        signal.tone === "positive"
          ? "border-emerald-200/70 bg-emerald-50/55"
          : signal.tone === "negative"
            ? "border-rose-200/70 bg-rose-50/55"
            : "border-amber-200/70 bg-amber-50/55",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="mono-label">{signal.label}</div>
          <div className="mt-2 text-sm font-semibold text-slate-900">{signal.value}</div>
        </div>
        <Badge
          variant="outline"
          className={cn(
            "rounded-full px-2.5 py-1 text-[10px]",
            signal.tone === "positive"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : signal.tone === "negative"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-amber-200 bg-amber-50 text-amber-700",
          )}
        >
          {signal.tone}
        </Badge>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-700">{signal.detail}</p>
    </div>
  );
}

export function NarrativeLine({ label, text }: { label: string; text: string }) {
  return (
    <div className="rounded-[1.3rem] border border-white/75 bg-white/82 p-3">
      <div className="mono-label">{label}</div>
      <p className="mt-2 text-sm leading-6 text-slate-700">{text}</p>
    </div>
  );
}

export function NarrativeChip({
  label,
  text,
  tone,
}: {
  label: string;
  text: string;
  tone: SignalTone;
}) {
  return (
    <div
      className={cn(
        "rounded-[1.25rem] border p-3",
        tone === "positive"
          ? "border-emerald-200/70 bg-emerald-50/55"
          : tone === "negative"
            ? "border-rose-200/70 bg-rose-50/55"
            : "border-slate-200/70 bg-slate-50/60",
      )}
    >
      <div className="mono-label">{label}</div>
      <p className="mt-2 text-sm leading-6 text-slate-700">{text}</p>
    </div>
  );
}

export function MetricTile({
  metric,
  compact = false,
}: {
  metric: SalesDashboardData["heroMetrics"][number];
  compact?: boolean;
}) {
  return (
    <div className="panel-nested p-3">
      <div className="mono-label">{metric.label}</div>
      <div className={cn("mt-2 font-semibold text-slate-900", compact ? "text-lg" : "text-2xl")}>
        {formatMetricValue(metric.value, metric.format)}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        {formatDelta(metric.delta)} · {metric.caption}
      </div>
    </div>
  );
}

export function InfoBlock({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="panel-nested flex gap-3 p-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white">
        {icon}
      </div>
      <p className="text-sm leading-6 text-slate-700">{text}</p>
    </div>
  );
}

export function RankRow({
  title,
  subtitle,
  value,
  meta,
}: {
  title: string;
  subtitle: string;
  value: string;
  meta: string;
}) {
  return (
    <div className="panel-nested p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-slate-900">{title}</div>
          <div className="text-xs text-muted-foreground">{subtitle}</div>
        </div>
        <div className="min-w-[92px] pr-1 text-right">
          <div className="text-sm font-semibold text-slate-900">{value}</div>
          <div className="text-xs text-emerald-600">{meta}</div>
        </div>
      </div>
    </div>
  );
}

export function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "healthy" | "neutral" | "critical";
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full px-3 py-1 text-[11px]",
        tone === "healthy"
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : tone === "critical"
            ? "border-rose-200 bg-rose-50 text-rose-700"
            : "border-slate-200 bg-white/80 text-slate-600",
      )}
    >
      {label}
    </Badge>
  );
}

export function MobileModeCard({
  title,
  icon,
  children,
  tall = false,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  tall?: boolean;
}) {
  return (
    <div
      className={cn(
        "panel overflow-hidden p-3",
        tall ? "h-full" : "max-h-[48vh]",
      )}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="mono-label">{title}</div>
        <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-slate-900 text-white">
          {icon}
        </div>
      </div>
      <div className={cn("min-h-0", tall && "flex h-[calc(100%-2.75rem)] flex-col")}>
        {children}
      </div>
    </div>
  );
}
