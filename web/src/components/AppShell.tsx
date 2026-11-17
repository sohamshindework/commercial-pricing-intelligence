import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { IS_STATIC_DEMO } from "../api/client";

const NAV = [
  { to: "/", label: "Commercial Performance", end: true },
  { to: "/revenue", label: "Revenue & Products" },
  { to: "/customers", label: "Customer Analytics" },
  { to: "/pricing", label: "Pricing & Experiments" },
  { to: "/executive", label: "Executive Decisions" },
];

function Identity() {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-iris font-heading text-[15px] font-bold text-white">
        C
      </span>
      <span className="min-w-0 font-heading text-[12.5px] font-semibold uppercase tracking-[0.06em] text-ink">
        Revenue &amp; Pricing
        <span className="block text-[10.5px] font-medium tracking-[0.11em] text-muted">
          Analytics
        </span>
      </span>
    </div>
  );
}

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-0.5" aria-label="Primary">
      {NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `relative rounded-lg px-3 py-2 text-[13.5px] transition ${
              isActive
                ? "bg-iris/10 font-semibold text-iris"
                : "text-body hover:bg-surface-alt hover:text-ink"
            }`
          }
        >
          {({ isActive }) => (
            <>
              {isActive && (
                <span className="absolute left-0 top-1.5 h-[calc(100%-12px)] w-[3px] rounded-full bg-iris" />
              )}
              {item.label}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);

  return (
    <div className="min-h-screen overflow-x-hidden bg-canvas text-body">
      <a
        href="#main-content"
        className="fixed left-3 top-3 z-50 -translate-y-20 rounded-md bg-ink px-3 py-2 text-sm text-white transition focus:translate-y-0"
      >
        Skip to content
      </a>
      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex min-w-0 items-center gap-3 border-b border-border bg-surface px-4 py-3 md:hidden">
        <button
          type="button"
          aria-label="Toggle navigation"
          aria-expanded={open}
          aria-controls="mobile-navigation"
          onClick={() => setOpen((v) => !v)}
          className="shrink-0 rounded-md border border-border p-2"
        >
          <span className="block h-0.5 w-5 bg-ink" />
          <span className="mt-1 block h-0.5 w-5 bg-ink" />
        </button>
        <Identity />
      </header>

      {open && (
        <>
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="fixed inset-0 top-[57px] z-30 bg-ink/20 md:hidden"
          />
          <div
            id="mobile-navigation"
            className="fixed inset-x-0 top-[57px] z-40 max-h-[calc(100vh-57px)] overflow-y-auto border-b border-border bg-surface px-4 py-4 shadow-lg md:hidden"
          >
            <Nav onNavigate={() => setOpen(false)} />
          </div>
        </>
      )}

      <div className="mx-auto flex max-w-[1500px]">
        {/* Desktop sidebar */}
        <aside className="sticky top-0 hidden h-screen w-[216px] shrink-0 flex-col border-r border-border bg-surface px-4 py-6 md:flex">
          <Identity />
          <div className="my-5 h-px bg-border" />
          <Nav />
          <div className="mt-auto rounded-lg bg-surface-alt px-3 py-3 text-[11px] leading-relaxed text-muted">
            <p>
              Independent portfolio analysis · UCI Online Retail II · 2009–2011. Figures
              illustrate method, not current market facts.
            </p>
            <p className="mt-2">
              Dataset: Chen (2019),{" "}
              <a
                className="font-medium text-iris hover:underline"
                href="https://doi.org/10.24432/C5CG6D"
                target="_blank"
                rel="noreferrer"
              >
                UCI Online Retail II
              </a>{" "}
              ·{" "}
              <a
                className="font-medium text-iris hover:underline"
                href="https://creativecommons.org/licenses/by/4.0/"
                target="_blank"
                rel="noreferrer"
              >
                CC BY 4.0
              </a>
            </p>
          </div>
        </aside>

        <main id="main-content" className="min-w-0 flex-1 px-4 py-7 sm:px-5 md:px-10 md:py-9">
          <div className="mx-auto max-w-[1180px]">
            {IS_STATIC_DEMO && (
              <div
                role="note"
                className="mb-5 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-iris/20 bg-iris/5 px-4 py-3 text-[12px] leading-relaxed text-body"
              >
                <span>
                  <strong className="font-semibold text-ink">Verified historical snapshot.</strong>{" "}
                  This independent portfolio demo uses precomputed aggregate data and makes no
                  live backend or warehouse connection.
                </span>
                <span className="rounded-full bg-surface px-2.5 py-1 font-medium text-iris">
                  Static demo
                </span>
              </div>
            )}
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
