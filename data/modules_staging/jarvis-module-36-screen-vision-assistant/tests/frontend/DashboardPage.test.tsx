import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 36 Screen Vision Assistant DashboardPage", () => {
  it("renders Screen Vision Assistant heading and capture trigger", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Screen Vision Assistant/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Create Sample Capture/i })).toBeTruthy();
  });
});
