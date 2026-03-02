"use client";

import { useId, useRef } from "react";

import DottedMap from "dotted-map";
import { motion } from "motion/react";
import Image from "next/image";

import { cn } from "@/lib/utils";

export interface WorldMapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  statValue?: string;
  secondaryValue?: string;
  detail?: string;
  tone?: "positive" | "neutral" | "negative";
  active?: boolean;
  onClick?: () => void;
}

interface WorldMapProps {
  dots?: Array<{
    start: { lat: number; lng: number; label?: string };
    end: { lat: number; lng: number; label?: string };
    share?: number;
    weight?: number;
    sentiment?: number;
  }>;
  markers?: WorldMapMarker[];
  className?: string;
  lineColor?: string;
  dotColor?: string;
  mapColor?: string;
  showLabels?: boolean;
}

function projectPoint(lat: number, lng: number) {
  return {
    x: (lng + 180) * (800 / 360),
    y: (90 - lat) * (400 / 180),
  };
}

function createCurvedPath(
  start: { x: number; y: number },
  end: { x: number; y: number },
) {
  const midX = (start.x + end.x) / 2;
  const arcHeight = Math.max(36, Math.abs(start.x - end.x) * 0.08);
  const midY = Math.min(start.y, end.y) - arcHeight;

  return `M ${start.x} ${start.y} Q ${midX} ${midY} ${end.x} ${end.y}`;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function WorldMap({
  dots = [],
  markers = [],
  className,
  lineColor = "#f97316",
  dotColor = "#0f172a",
  mapColor = "rgba(15, 23, 42, 0.17)",
  showLabels = true,
}: WorldMapProps) {
  const gradientId = useId().replace(/:/g, "");
  const svgRef = useRef<SVGSVGElement>(null);

  const map = new DottedMap({ height: 100, grid: "diagonal" });
  const svgMap = map.getSVG({
    radius: 0.2,
    color: mapColor,
    shape: "circle",
    backgroundColor: "transparent",
  });

  return (
    <div
      className={cn(
        "relative aspect-[2/1] w-full overflow-hidden rounded-[1.8rem]",
        className,
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(14,165,233,0.1),transparent_24%),radial-gradient(circle_at_80%_0%,rgba(249,115,22,0.12),transparent_26%),linear-gradient(180deg,rgba(255,255,255,0.94),rgba(252,248,241,0.84))]" />
      <Image
        src={`data:image/svg+xml;utf8,${encodeURIComponent(svgMap)}`}
        className="relative h-full w-full select-none object-cover opacity-85 [mask-image:linear-gradient(to_bottom,transparent,white_10%,white_92%,transparent)]"
        alt="world map"
        width={1056}
        height={495}
        draggable={false}
        unoptimized
      />
      <svg
        ref={svgRef}
        viewBox="0 0 800 400"
        className="absolute inset-0 h-full w-full select-none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient
            id={gradientId}
            x1="0%"
            y1="0%"
            x2="100%"
            y2="0%"
          >
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="12%" stopColor={lineColor} stopOpacity="0.95" />
            <stop offset="88%" stopColor={lineColor} stopOpacity="0.95" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>

        {dots.map((dot, index) => {
          const startPoint = projectPoint(dot.start.lat, dot.start.lng);
          const endPoint = projectPoint(dot.end.lat, dot.end.lng);
          const flowWeight = clamp(dot.weight ?? dot.share ?? 0.18, 0.08, 0.34);
          const strokeWidth = 0.9 + flowWeight * 6.4;
          const pulseRadius = 2.2 + flowWeight * 8;
          const endColor =
            typeof dot.sentiment === "number"
              ? dot.sentiment >= 0.25
                ? "#16a34a"
                : dot.sentiment <= -0.1
                  ? "#dc2626"
                  : "#d97706"
              : lineColor;

          return (
            <g key={`${dot.start.label}-${dot.end.label}-${index}`}>
              <motion.path
                d={createCurvedPath(startPoint, endPoint)}
                fill="none"
                stroke={`url(#${gradientId})`}
                strokeWidth={strokeWidth}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{
                  duration: 1.2,
                  delay: index * 0.08,
                  ease: "easeOut",
                }}
              />
              <g>
                <circle cx={startPoint.x} cy={startPoint.y} r="2.2" fill={dotColor} />
                <circle cx={startPoint.x} cy={startPoint.y} r="2.2" fill={lineColor} opacity="0.3" />
              </g>
              <g>
                <circle cx={endPoint.x} cy={endPoint.y} r="2.8" fill={endColor} />
                <circle cx={endPoint.x} cy={endPoint.y} r="2.8" fill={endColor}>
                  <animate
                    attributeName="r"
                    from="2.8"
                    to={String(pulseRadius)}
                    dur="2.1s"
                    begin={`${index * 0.15}s`}
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    from="0.4"
                    to="0"
                    dur="2.1s"
                    begin={`${index * 0.15}s`}
                    repeatCount="indefinite"
                  />
                </circle>
              </g>
            </g>
          );
        })}

        {showLabels &&
          markers.length === 0 &&
          dots.slice(0, 4).map((dot, index) => {
            const labelPoint = projectPoint(dot.end.lat, dot.end.lng);

            return (
              <text
                key={`label-${dot.end.label}-${index}`}
                x={labelPoint.x + 8}
                y={labelPoint.y - 8}
                fill="rgba(15, 23, 42, 0.78)"
                fontSize="10"
                fontFamily="var(--font-ibm-plex-mono)"
                letterSpacing="0.16em"
                textAnchor="start"
              >
                {(dot.end.label ?? "").toUpperCase()}
              </text>
            );
          })}
      </svg>

      <div className="pointer-events-none absolute inset-0">
        {markers.map((marker) => {
          const point = projectPoint(marker.lat, marker.lng);
          const left = `${(point.x / 800) * 100}%`;
          const top = `${(point.y / 400) * 100}%`;
          const alignRight = point.x > 620;
          const verticalClass = point.y < 70 ? "top-6" : point.y > 320 ? "bottom-6" : "top-1/2 -translate-y-1/2";
          const toneClass =
            marker.tone === "positive"
              ? "bg-emerald-500"
              : marker.tone === "negative"
                ? "bg-rose-500"
                : "bg-amber-500";
          const chipToneClass =
            marker.tone === "positive"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : marker.tone === "negative"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-amber-200 bg-amber-50 text-amber-700";

          return (
            <div
              key={marker.id}
              className="absolute z-10"
              style={{
                left,
                top,
                transform: "translate(-50%, -50%)",
              }}
            >
              <button
                type="button"
                onClick={marker.onClick}
                aria-label={`Open ${marker.label} quick summary`}
                className="pointer-events-auto relative block rounded-full"
              >
                <span
                  className={cn(
                    "absolute -inset-2 rounded-full border transition",
                    marker.active ? "border-slate-900/25 bg-slate-900/5" : "border-transparent",
                  )}
                />
                <span className="relative flex h-5 w-5 items-center justify-center rounded-full border-4 border-white bg-white shadow-[0_12px_30px_-14px_rgba(15,23,42,0.8)]">
                  <span className={cn("block h-2.5 w-2.5 rounded-full", toneClass)} />
                </span>
              </button>

              <div
                className={cn(
                  "absolute hidden min-w-[154px] max-w-[198px] rounded-[1.15rem] border border-white/85 bg-white/94 p-2.5 shadow-[0_24px_50px_-26px_rgba(15,23,42,0.45)] backdrop-blur lg:block",
                  verticalClass,
                  alignRight ? "right-8" : "left-8",
                )}
              >
                <div className="mono-label text-[10px] tracking-[0.14em] text-slate-500">
                  {marker.label}
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {marker.statValue ? (
                    <span className={cn("rounded-full border px-2 py-1 text-[11px] font-medium", chipToneClass)}>
                      {marker.statValue}
                    </span>
                  ) : null}
                  {marker.secondaryValue ? (
                    <span className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700">
                      {marker.secondaryValue}
                    </span>
                  ) : null}
                </div>
                {marker.detail ? (
                  <div className="mt-2 text-[11px] leading-5 text-slate-500">{marker.detail}</div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
