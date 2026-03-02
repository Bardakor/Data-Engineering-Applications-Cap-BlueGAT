"use client";

import { cn } from "@/lib/utils";
import type { ChainNode, ControlRoomNarrative, PrioritySignal } from "./types";

export function ControlRoomBanner({
  narrative,
  prioritySignals,
  growthChain,
}: {
  narrative: ControlRoomNarrative;
  prioritySignals: PrioritySignal[];
  growthChain: ChainNode[];
}) {
  return (
    <div className="panel w-[min(44rem,calc(100vw-58rem))] min-w-[30rem] px-4 py-3">
      <div className="mono-label">Executive summary</div>
      <p className="mt-2 text-sm leading-6 text-slate-800">{narrative.summary}</p>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {prioritySignals.map((signal) => (
          <div
            key={signal.label}
            className={cn(
              "rounded-[1rem] border px-3 py-2",
              signal.tone === "positive"
                ? "border-emerald-200/70 bg-emerald-50/55"
                : signal.tone === "negative"
                  ? "border-rose-200/70 bg-rose-50/55"
                  : "border-amber-200/70 bg-amber-50/55",
            )}
          >
            <div className="mono-label">{signal.label}</div>
            <div className="mt-1 text-xs font-semibold text-slate-900">{signal.value}</div>
          </div>
        ))}
      </div>
      <div className="mt-3">
        <div className="mono-label">
          Campaign {"->"} sentiment {"->"} topic {"->"} market {"->"} revenue
        </div>
        <div className="mt-2 flex items-center gap-2 overflow-x-auto pb-1">
          {growthChain.map((node, index) => (
            <div key={node.label} className="flex items-center gap-2">
              <div
                className={cn(
                  "min-w-[110px] rounded-[1rem] border px-3 py-2",
                  node.tone === "positive"
                    ? "border-emerald-200/70 bg-emerald-50/55"
                    : node.tone === "negative"
                      ? "border-rose-200/70 bg-rose-50/55"
                      : "border-slate-200/70 bg-white/80",
                )}
              >
                <div className="mono-label">{node.label}</div>
                <div className="mt-1 text-xs font-semibold text-slate-900">{node.value}</div>
              </div>
              {index < growthChain.length - 1 ? (
                <div className="text-slate-400">→</div>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
