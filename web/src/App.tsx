import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { Loading } from "./components/states";
import { FilterProvider } from "./state/filters";

const Overview = lazy(() => import("./pages/Overview").then((m) => ({ default: m.Overview })));
const RevenueProduct = lazy(() =>
  import("./pages/RevenueProduct").then((m) => ({ default: m.RevenueProduct })),
);
const Customers = lazy(() =>
  import("./pages/Customers").then((m) => ({ default: m.Customers })),
);
const Pricing = lazy(() => import("./pages/Pricing").then((m) => ({ default: m.Pricing })));
const Executive = lazy(() =>
  import("./pages/Executive").then((m) => ({ default: m.Executive })),
);

export default function App() {
  return (
    <FilterProvider>
      <Suspense fallback={<div className="p-6"><Loading label="Loading workspace…" /></div>}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Overview />} />
            <Route path="revenue" element={<RevenueProduct />} />
            <Route path="customers" element={<Customers />} />
            <Route path="pricing" element={<Pricing />} />
            <Route path="executive" element={<Executive />} />
          </Route>
        </Routes>
      </Suspense>
    </FilterProvider>
  );
}
