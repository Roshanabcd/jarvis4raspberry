import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 33)", () => {
  it("renders JARVIS Defensive Cybersecurity Agent heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          adapter: "local_defensive_scanner",
          simulated: false,
          posture_score: 100,
          open_incidents: 0,
          baselines_count: 1,
          scans_count: 1
        })
      })
    );
    render(<DashboardPage />);
    expect(screen.getByText(/JARVIS Defensive Cybersecurity Agent/i)).toBeTruthy();
  });
});
