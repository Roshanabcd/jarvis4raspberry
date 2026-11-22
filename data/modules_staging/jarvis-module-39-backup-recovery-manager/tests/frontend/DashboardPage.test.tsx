import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("Module 39 Backup & Recovery Manager DashboardPage", () => {
  it("renders heading and snapshot trigger", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Backup & Recovery Manager/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Create Workspace Snapshot/i })).toBeTruthy();
  });
});
