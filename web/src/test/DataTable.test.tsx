import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Pagination } from "../components/DataTable";

describe("Pagination", () => {
  it("shows the range and disables Previous on the first page", () => {
    render(<Pagination offset={0} limit={10} total={4739} onPage={() => {}} />);
    expect(screen.getByText("1–10 of 4,739")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
  });

  it("advances the offset when Next is clicked", () => {
    const onPage = vi.fn();
    render(<Pagination offset={0} limit={10} total={40} onPage={onPage} />);
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(onPage).toHaveBeenCalledWith(10);
  });

  it("disables Next on the final page and moves back by one page", () => {
    const onPage = vi.fn();
    render(<Pagination offset={30} limit={10} total={35} onPage={onPage} />);
    expect(screen.getByText("31–35 of 35")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(onPage).toHaveBeenCalledWith(20);
  });
});
