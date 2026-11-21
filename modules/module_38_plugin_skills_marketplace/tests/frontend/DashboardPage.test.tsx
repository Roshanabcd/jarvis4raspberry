import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 38 Plugin & Skills Marketplace DashboardPage", () => {
  it("renders marketplace heading and publish control", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Plugin & Skills Marketplace/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Publish Sample Skill/i })).toBeTruthy();
  });
});
