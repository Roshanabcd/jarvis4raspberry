import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 35 Visual Workflow Builder DashboardPage", () => {
  it("renders JARVIS Visual Workflow Builder heading and action controls", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Visual Workflow Builder/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Create Sample Pipeline/i })).toBeTruthy();
  });
});
