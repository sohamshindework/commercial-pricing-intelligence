import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FilterBar } from "../components/FilterBar";
import { FilterProvider, useFilters } from "../state/filters";

vi.mock("../api/hooks", () => ({
  useMetadata: () => ({
    data: {
      date_min: "2009-12-01",
      date_max: "2011-12-09",
      markets: ["United Kingdom", "France"],
      families: [{ family_code: "HOME", name: "Home & Living" }],
    },
  }),
}));

function FilterProbe() {
  const { filters } = useFilters();
  return <output>{JSON.stringify(filters)}</output>;
}

describe("FilterBar", () => {
  it("applies market and family filters and resets them", () => {
    render(
      <FilterProvider>
        <FilterBar />
        <FilterProbe />
      </FilterProvider>,
    );

    fireEvent.change(screen.getByLabelText("Market"), { target: { value: "France" } });
    fireEvent.change(screen.getByLabelText("Product family"), { target: { value: "HOME" } });
    expect(screen.getByText(/"market":"France"/)).toBeInTheDocument();
    expect(screen.getByText(/"family":"HOME"/)).toBeInTheDocument();
    expect(screen.getByText("2 active")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(screen.getByText("{}")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset" })).toBeDisabled();
  });

  it("constrains each date control using metadata and the selected peer date", () => {
    render(
      <FilterProvider>
        <FilterBar />
      </FilterProvider>,
    );
    const from = screen.getByLabelText("Start date");
    const to = screen.getByLabelText("End date");
    expect(from).toHaveAttribute("min", "2009-12-01");
    expect(to).toHaveAttribute("max", "2011-12-09");

    fireEvent.change(from, { target: { value: "2011-01-01" } });
    fireEvent.change(to, { target: { value: "2011-06-30" } });
    expect(from).toHaveAttribute("max", "2011-06-30");
    expect(to).toHaveAttribute("min", "2011-01-01");
  });
});
