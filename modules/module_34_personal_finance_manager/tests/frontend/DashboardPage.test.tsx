import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 34)", () => {
  it("renders JARVIS Personal Finance Manager heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          month: "2026-11",
          net_worth: 1500,
          total_income: 2000,
          total_expense: 500,
          net_cashflow: 1500,
          savings_rate_pct: 75
        })
      })
    );
    render(<DashboardPage />);
    expect(screen.getByText(/JARVIS Personal Finance Manager/i)).toBeTruthy();
  });
});
