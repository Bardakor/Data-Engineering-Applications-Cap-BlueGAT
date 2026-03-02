"use client";

import { CalendarRange } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { defaultFilters } from "@/lib/defaults";
import type { DashboardFilters } from "@/lib/types";
import { Filter } from "lucide-react";

export function FiltersSheet({
  filters,
  filtersMeta,
  onChange,
}: {
  filters: DashboardFilters;
  filtersMeta: {
    products: string[];
    countries: string[];
    regions: string[];
    minDate: string;
    maxDate: string;
  };
  onChange: React.Dispatch<React.SetStateAction<DashboardFilters>>;
}) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="rounded-full border-white/80 bg-white/85">
          <Filter className="size-4 sm:mr-2" />
          <span className="hidden sm:inline">Filters</span>
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full border-l-white/80 bg-[rgba(255,250,242,0.95)] sm:max-w-[420px]">
        <SheetHeader className="px-6 pt-6">
          <SheetTitle>Viewport filters</SheetTitle>
          <SheetDescription>
            Keep the map as the main stage and adjust sales, feedback, and chat from here.
          </SheetDescription>
        </SheetHeader>

        <div className="flex h-full flex-col px-6 pb-6">
          <div className="grid gap-4 py-6">
            <FilterSelect
              label="Product"
              value={filters.product}
              options={filtersMeta.products}
              onValueChange={(value) =>
                onChange((current) => ({ ...current, product: value }))
              }
            />
            <FilterSelect
              label="Country"
              value={filters.country}
              options={filtersMeta.countries}
              onValueChange={(value) =>
                onChange((current) => ({ ...current, country: value }))
              }
            />
            <FilterSelect
              label="Region"
              value={filters.region}
              options={filtersMeta.regions}
              onValueChange={(value) =>
                onChange((current) => ({ ...current, region: value }))
              }
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <DateFilter
                label="From"
                value={filters.dateFrom}
                min={filtersMeta.minDate}
                max={filters.dateTo}
                onChange={(value) =>
                  onChange((current) => ({ ...current, dateFrom: value }))
                }
              />
              <DateFilter
                label="To"
                value={filters.dateTo}
                min={filters.dateFrom}
                max={filtersMeta.maxDate}
                onChange={(value) =>
                  onChange((current) => ({ ...current, dateTo: value }))
                }
              />
            </div>
          </div>

          <div className="mt-auto flex items-center justify-between gap-3 border-t border-white/70 pt-4">
            <div className="text-xs text-muted-foreground">
              Filters apply to the map, overlays, and CheepChat citations.
            </div>
            <Button
              variant="outline"
              className="rounded-full"
              onClick={() => onChange(defaultFilters)}
            >
              Reset
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onValueChange,
}: {
  label: string;
  value: string;
  options: string[];
  onValueChange: (value: string) => void;
}) {
  return (
    <div className="min-w-[150px]">
      <div className="mono-label mb-1">{label}</div>
      <Select value={value} onValueChange={onValueChange}>
        <SelectTrigger className="h-10 w-full rounded-2xl border-white/75 bg-white/85">
          <SelectValue placeholder={label} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

function DateFilter({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: string;
  min: string;
  max: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="min-w-[150px]">
      <div className="mono-label mb-1">{label}</div>
      <label className="flex h-10 items-center gap-2 rounded-2xl border border-white/75 bg-white/85 px-3">
        <CalendarRange className="size-4 text-slate-500" />
        <input
          type="date"
          min={min}
          max={max}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full bg-transparent text-sm text-slate-700 outline-none"
        />
      </label>
    </div>
  );
}
