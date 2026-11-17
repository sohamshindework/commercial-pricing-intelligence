import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AppShell } from "../components/AppShell";

function renderShell() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<p>Overview content</p>} />
          <Route path="executive" element={<p>Executive content</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppShell navigation", () => {
  it("exposes all five destinations and opens then closes the mobile menu", () => {
    renderShell();
    expect(screen.getAllByRole("link", { name: "Executive Decisions" })).toHaveLength(1);

    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByRole("link", { name: "Executive Decisions" })).toHaveLength(2);

    fireEvent.keyDown(document, { key: "Escape" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("closes the menu after navigating to Executive Decisions", () => {
    renderShell();
    const toggle = screen.getByRole("button", { name: "Toggle navigation" });
    fireEvent.click(toggle);
    fireEvent.click(screen.getAllByRole("link", { name: "Executive Decisions" })[0]);
    expect(screen.getByText("Executive content")).toBeInTheDocument();
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });
});
