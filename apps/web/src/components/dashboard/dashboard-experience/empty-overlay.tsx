"use client";

import { motion } from "motion/react";
import { Database, Globe2, MessageSquareText, Package2 } from "lucide-react";
import { InfoBlock } from "./ui-components";

export function EmptyOverlay() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      className="absolute inset-0 z-20 flex items-center justify-center p-6"
    >
      <div className="panel-strong max-w-2xl p-6 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-sky-600">
          <Database className="size-5" />
        </div>
        <h2 className="mt-4 text-2xl font-semibold text-slate-900">
          No data is loaded yet
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          The interface now reads only from the backend API and database. Ingest
          sales CSV data and push feedback events to `/api/v1/ingest/feedback`, then refresh.
        </p>
        <div className="mt-5 grid gap-3 text-left sm:grid-cols-3">
          <InfoBlock icon={<Globe2 className="size-4" />} text="Upload sales CSV" />
          <InfoBlock icon={<MessageSquareText className="size-4" />} text="Push feedback JSON list" />
          <InfoBlock icon={<Package2 className="size-4" />} text="Upload campaign mapping CSV" />
        </div>
      </div>
    </motion.div>
  );
}
