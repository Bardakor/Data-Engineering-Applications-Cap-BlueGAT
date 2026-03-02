"use client";

import { useRef, useState } from "react";

import { Menu, X } from "lucide-react";
import {
  AnimatePresence,
  type MotionValue,
  motion,
  useMotionValue,
  useSpring,
  useTransform,
} from "motion/react";

import { cn } from "@/lib/utils";

export interface DockItem {
  id: string;
  title: string;
  icon: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}

export function FloatingDock({
  items,
  className,
}: {
  items: DockItem[];
  className?: string;
}) {
  return (
    <>
      <FloatingDockDesktop items={items} className={className} />
      <FloatingDockMobile items={items} className={className} />
    </>
  );
}

function FloatingDockMobile({
  items,
  className,
}: {
  items: DockItem[];
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className={cn("fixed right-4 bottom-4 z-50 md:hidden", className)}>
      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            className="panel mb-3 flex min-w-[180px] flex-col gap-2 p-3"
          >
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  item.onClick?.();
                  setOpen(false);
                }}
                className={cn(
                  "flex items-center gap-3 rounded-2xl border border-white/70 px-3 py-2.5 text-left transition",
                  item.active
                    ? "bg-slate-900 text-white shadow-[0_14px_40px_-22px_rgba(15,23,42,0.9)]"
                    : "bg-white/85 text-slate-700 hover:bg-slate-100",
                )}
                aria-label={item.title}
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-black/5">
                  {item.icon}
                </span>
                <span>
                  <span className="block text-sm font-medium">{item.title}</span>
                  <span className="block text-[11px] text-current/65">Open layer</span>
                </span>
              </button>
            ))}
          </motion.div>
        ) : null}
      </AnimatePresence>

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="panel flex h-12 w-12 items-center justify-center rounded-2xl"
        aria-label="Toggle navigation dock"
      >
        {open ? <X className="size-5" /> : <Menu className="size-5" />}
      </button>
    </div>
  );
}

function FloatingDockDesktop({
  items,
  className,
}: {
  items: DockItem[];
  className?: string;
}) {
  const mouseX = useMotionValue(Infinity);

  return (
    <motion.div
      onMouseMove={(event) => mouseX.set(event.clientX)}
      onMouseLeave={() => mouseX.set(Infinity)}
      className={cn(
        "panel fixed inset-x-0 bottom-7 z-50 mx-auto hidden h-24 w-fit items-end gap-3 rounded-[2rem] px-4 pb-3 pt-2 md:flex",
        className,
      )}
    >
      {items.map((item) => (
        <DockIcon key={item.id} item={item} mouseX={mouseX} />
      ))}
    </motion.div>
  );
}

function DockIcon({
  item,
  mouseX,
}: {
  item: DockItem;
  mouseX: MotionValue<number>;
}) {
  const ref = useRef<HTMLButtonElement>(null);

  const distance = useTransform(mouseX, (value) => {
    const bounds = ref.current?.getBoundingClientRect() ?? {
      x: 0,
      width: 0,
    };

    return value - bounds.x - bounds.width / 2;
  });

  const containerSize = useSpring(
    useTransform(distance, [-180, 0, 180], [50, 82, 50]),
    { mass: 0.1, stiffness: 170, damping: 14 },
  );
  const iconSize = useSpring(
    useTransform(distance, [-180, 0, 180], [22, 34, 22]),
    { mass: 0.1, stiffness: 170, damping: 14 },
  );

  return (
    <button
      ref={ref}
      type="button"
      onClick={item.onClick}
      className="relative flex flex-col items-center justify-end gap-2"
      aria-label={item.title}
    >
      <motion.div
        style={{
          width: containerSize,
          height: containerSize,
        }}
        className={cn(
          "flex aspect-square items-center justify-center rounded-[1.6rem] border shadow-[0_20px_40px_-24px_rgba(15,23,42,0.4)] transition-colors",
          item.active
            ? "border-slate-900 bg-slate-900 text-white"
            : "border-white/70 bg-white/90 text-slate-700",
        )}
      >
        <motion.div
          style={{
            width: iconSize,
            height: iconSize,
          }}
          className="flex items-center justify-center"
        >
          {item.icon}
        </motion.div>
      </motion.div>
      <span
        className={cn(
          "text-[11px] font-medium transition-colors",
          item.active ? "text-slate-900" : "text-slate-500",
        )}
      >
        {item.title}
      </span>
    </button>
  );
}
