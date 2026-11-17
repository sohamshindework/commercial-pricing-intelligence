import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { KpiCard } from "../components/KpiCard";

describe("KpiCard", () => {
  it("renders label, value and hint", () => {
    render(<KpiCard label="Net revenue" value="£18.93m" hint="GBP" />);
    expect(screen.getByText("Net revenue")).toBeInTheDocument();
    expect(screen.getByText("£18.93m")).toBeInTheDocument();
    expect(screen.getByText("GBP")).toBeInTheDocument();
  });
});
