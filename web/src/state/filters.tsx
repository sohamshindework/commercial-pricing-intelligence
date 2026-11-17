// Global commercial filters (date range, market, family) shared across pages.

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import type { FilterValues } from "../api/types";

interface FilterContextValue {
  filters: FilterValues;
  set: (patch: Partial<FilterValues>) => void;
  reset: () => void;
  active: boolean;
}

const FilterContext = createContext<FilterContextValue | null>(null);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<FilterValues>({});

  const value = useMemo<FilterContextValue>(
    () => ({
      filters,
      set: (patch) =>
        setFilters((prev) => {
          const next = { ...prev, ...patch };
          // Empty strings clear a filter.
          (Object.keys(next) as (keyof FilterValues)[]).forEach((k) => {
            if (!next[k]) delete next[k];
          });
          return next;
        }),
      reset: () => setFilters({}),
      active: Object.keys(filters).length > 0,
    }),
    [filters],
  );

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useFilters(): FilterContextValue {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useFilters must be used within FilterProvider");
  return ctx;
}
