// Prioritised recommendations + limitations, assembled server-side from the
// pipeline numbers and presented in the dedicated executive decision layer.

import { Link } from "react-router-dom";
import type { ApiError } from "../api/client";
import { useExecutive } from "../api/hooks";
import type { Recommendation } from "../api/types";
import { Card } from "./Card";
import { BarsSkeleton } from "./Skeleton";
import { ErrorState } from "./states";

function confidenceTone(level: string): { chip: string; label: string } {
  const head = level.split("—")[0].trim();
  const l = head.toLowerCase();
  if (l.startsWith("high") || l.includes("medium-high")) {
    return { chip: "bg-positive/10 text-positive", label: head };
  }
  if (l.startsWith("low")) return { chip: "bg-coral/15 text-coral", label: head };
  return { chip: "bg-warning/15 text-warning", label: head };
}

function toCsv(recs: Recommendation[]): string {
  const header = ["priority", "action", "evidence", "scenario_impact", "success_metric", "confidence"];
  const esc = (s: string) => `"${s.replace(/"/g, '""')}"`;
  const rows = recs.map((r) =>
    [r.priority, r.action, r.evidence, r.scenario_impact, r.success_metric, r.confidence]
      .map((v) => esc(String(v)))
      .join(","),
  );
  return [header.join(","), ...rows].join("\n");
}

function downloadCsv(csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "commercial_recommendations.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export function RecommendedActions() {
  const q = useExecutive();
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-heading text-[20px] text-ink">Recommended actions</h2>
        {q.data && (
          <button
            type="button"
            onClick={() => downloadCsv(toCsv(q.data!.recommendations))}
            className="rounded-md border border-border px-3 py-1.5 text-[13px] font-medium text-body transition hover:border-iris hover:text-iris"
          >
            Export summary (CSV)
          </button>
        )}
      </div>

      {q.isLoading && <BarsSkeleton rows={3} />}
      {q.isError && <ErrorState message={(q.error as ApiError).message} />}
      {q.data && (
        <div className="space-y-3">
          {q.data.recommendations.map((r) => {
            const meta = recommendationMeta(r.priority);
            return (
            <Card key={r.priority} className="p-5">
              <div className="flex items-start gap-4">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-iris/10 font-heading text-[14px] font-semibold text-iris">
                  {r.priority}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="font-heading text-[15.5px] text-ink">{r.action}</h3>
                    <div className="flex flex-wrap gap-2">
                      <span className="rounded-full bg-iris/10 px-2.5 py-0.5 text-[11.5px] font-semibold text-iris">
                        {meta.importance} importance
                      </span>
                      <span
                        className={`shrink-0 rounded-full px-2.5 py-0.5 text-[11.5px] font-semibold ${confidenceTone(r.confidence).chip}`}
                        title={r.confidence}
                      >
                        {confidenceTone(r.confidence).label} confidence
                      </span>
                    </div>
                  </div>
                  <dl className="mt-2 grid grid-cols-1 gap-x-8 gap-y-2 text-[13px] sm:grid-cols-2">
                    <Field term="Suggested lead" value={meta.lead} />
                    <Field term="Evidence" value={r.evidence} />
                    <Field term="Hypothetical impact" value={r.scenario_impact} />
                    <Field term="Success looks like" value={r.success_metric} />
                    <Field
                      term="Why this confidence"
                      value={r.confidence.split("—").slice(1).join("—").trim()}
                    />
                  </dl>
                  <Link className="mt-3 inline-flex text-[12.5px] font-semibold text-iris hover:underline" to={meta.link}>
                    Review supporting analysis →
                  </Link>
                </div>
              </div>
            </Card>
          );
          })}

          <Card className="border-l-[3px] border-l-warning p-5">
            <h3 className="mb-3 font-heading text-[16px] text-ink">What we do not know</h3>
            <ul className="space-y-2 text-[13.5px] text-body">
              {q.data.limitations.map((l) => (
                <li key={l} className="flex gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" />
                  {l}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </section>
  );
}

function recommendationMeta(priority: number) {
  if (priority === 1) {
    return { importance: "Highest", lead: "Pricing manager + category lead (suggested)", link: "/pricing" };
  }
  if (priority === 2) {
    return { importance: "High", lead: "CRM / lifecycle lead (suggested)", link: "/customers" };
  }
  return { importance: "Supporting", lead: "Commercial analytics lead (suggested)", link: "/revenue" };
}

function Field({ term, value }: { term: string; value: string }) {
  return (
    <div>
      <dt className="text-[11.5px] font-medium uppercase tracking-wide text-muted">{term}</dt>
      <dd className="mt-0.5 text-body">{value}</dd>
    </div>
  );
}
