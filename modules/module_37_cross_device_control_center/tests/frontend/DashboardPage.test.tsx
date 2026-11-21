import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 37 Cross-Device Control Center DashboardPage", () => {
  it("renders heading and register device control", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Cross-Device Control Center/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Register Sample Device/i })).toBeTruthy();
  });
});
