import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "right";
  render: (row: T) => ReactNode;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
}

export function DataTable<T>({ columns, rows, rowKey }: Props<T>) {
  return (
    <div className="-mx-1 overflow-x-auto">
      <table className="w-full min-w-[480px] border-collapse text-[13.5px]">
        <thead>
          <tr className="border-b border-border">
            {columns.map((c) => (
              <th
                key={c.key}
                className={`px-3 py-2 font-medium text-muted ${
                  c.align === "right" ? "text-right" : "text-left"
                }`}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="border-b border-border last:border-0 hover:bg-surface-alt/60">
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={`px-3 py-2.5 ${
                    c.align === "right" ? "text-right tnum text-ink" : "text-body"
                  }`}
                >
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({
  offset,
  limit,
  total,
  onPage,
}: {
  offset: number;
  limit: number;
  total: number;
  onPage: (nextOffset: number) => void;
}) {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <div className="mt-3 flex items-center justify-between text-[12.5px] text-muted">
      <span className="tnum">
        {from}–{to} of {total.toLocaleString("en-GB")}
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onPage(Math.max(0, offset - limit))}
          disabled={offset === 0}
          className="rounded-md border border-border px-2.5 py-1 transition hover:border-iris hover:text-iris disabled:opacity-40"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => onPage(offset + limit)}
          disabled={to >= total}
          className="rounded-md border border-border px-2.5 py-1 transition hover:border-iris hover:text-iris disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>
  );
}
