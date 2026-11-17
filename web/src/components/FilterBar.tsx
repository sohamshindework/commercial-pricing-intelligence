// Commercial filters toolbar. Every control has a defined effect; Reset clears all.

import type { ReactNode } from "react";

import { IS_STATIC_DEMO } from "../api/client";
import { useMetadata } from "../api/hooks";
import { useFilters } from "../state/filters";

export function FilterBar() {
  const { data: meta } = useMetadata();
  const { filters, set, reset, active } = useFilters();
  const activeCount = Object.keys(filters).length;

  return (
    <div className="grid min-w-0 grid-cols-1 gap-3 rounded-card border border-border bg-surface px-4 py-3 shadow-card sm:grid-cols-2 lg:flex lg:flex-wrap lg:items-end lg:gap-x-4">
      <div className="mr-1 flex items-center gap-2 self-center sm:col-span-2 lg:col-span-1">
        <span className="font-heading text-[13px] font-semibold text-ink">Filters</span>
        {active && (
          <span className="rounded-full bg-iris/10 px-2 py-0.5 text-[11px] font-medium text-iris">
            {activeCount} active
          </span>
        )}
      </div>

      <Field label="From">
        <input
          type="date"
          disabled={IS_STATIC_DEMO}
          value={filters.start ?? ""}
          min={meta?.date_min}
          max={filters.end ?? meta?.date_max}
          onChange={(e) => set({ start: e.target.value })}
          className="input w-full min-w-0 lg:w-auto"
          aria-label="Start date"
          aria-describedby={IS_STATIC_DEMO ? "static-date-note" : undefined}
          title={IS_STATIC_DEMO ? "Date filters require the local analytical backend." : undefined}
        />
      </Field>
      <Field label="To">
        <input
          type="date"
          disabled={IS_STATIC_DEMO}
          value={filters.end ?? ""}
          min={filters.start ?? meta?.date_min}
          max={meta?.date_max}
          onChange={(e) => set({ end: e.target.value })}
          className="input w-full min-w-0 lg:w-auto"
          aria-label="End date"
          aria-describedby={IS_STATIC_DEMO ? "static-date-note" : undefined}
          title={IS_STATIC_DEMO ? "Date filters require the local analytical backend." : undefined}
        />
      </Field>
      <Field label="Market">
        <select
          value={filters.market ?? ""}
          onChange={(e) => set({ market: e.target.value })}
          className="input w-full min-w-0 lg:w-auto lg:min-w-[132px]"
          aria-label="Market"
        >
          <option value="">All markets</option>
          {meta?.markets.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Product family">
        <select
          value={filters.family ?? ""}
          onChange={(e) => set({ family: e.target.value })}
          className="input w-full min-w-0 lg:w-auto lg:min-w-[160px]"
          aria-label="Product family"
        >
          <option value="">All families</option>
          {meta?.families.map((f) => (
            <option key={f.family_code} value={f.family_code}>
              {f.name}
            </option>
          ))}
        </select>
      </Field>

      <button
        type="button"
        onClick={reset}
        disabled={!active}
        className="self-center rounded-md px-3 py-2 text-[13px] font-medium text-body transition hover:text-iris disabled:cursor-not-allowed disabled:opacity-40 sm:col-span-2 lg:col-span-1 lg:ml-auto"
      >
        Reset
      </button>
      {IS_STATIC_DEMO && (
        <p id="static-date-note" className="text-[11.5px] leading-relaxed text-muted sm:col-span-2 lg:basis-full">
          This public snapshot supports exact market and product-family filters. Date filters are
          available in the local full-data application and are disabled here to avoid publishing
          fine-grained transaction data.
        </p>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex min-w-0 flex-col gap-1 text-[11.5px] font-medium text-muted">
      {label}
      {children}
    </label>
  );
}
