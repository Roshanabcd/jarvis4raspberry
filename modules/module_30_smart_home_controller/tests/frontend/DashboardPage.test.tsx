import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 30)", () => {
  it("renders JARVIS Smart Home Controller heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          adapter: "simulated_iot_home_bridge",
          simulated: true,
          devices_count: 0,
          active_devices: 0,
          scenes_count: 0,
          rules_count: 0,
          total_active_watts: 0,
          devices: []
        })
      })
    );
    render(<DashboardPage />);
    expect(screen.getByText(/JARVIS Smart Home Controller/i)).toBeTruthy();
  });
});
