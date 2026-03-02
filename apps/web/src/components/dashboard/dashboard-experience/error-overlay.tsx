"use client";

import { motion } from "motion/react";
import { RefreshCw, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ErrorOverlay({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      className="absolute inset-0 z-20 flex items-center justify-center p-6"
    >
      <div className="panel-strong max-w-xl p-6 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-50 text-rose-600">
          <XCircle className="size-5" />
        </div>
        <h2 className="mt-4 text-2xl font-semibold text-slate-900">
          The dashboard could not load
        </h2>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">{message}</p>
        <Button className="mt-5 rounded-full" onClick={onRetry}>
          <RefreshCw className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    </motion.div>
  );
}
