import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 40 Permissions & Approval Center DashboardPage", () => {
  it("renders heading and request submission button", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Permissions & Approval Center/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Submit High-Risk Request/i })).toBeTruthy();
  });
});
