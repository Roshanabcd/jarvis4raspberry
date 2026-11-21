import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 31)", () => {
  it("renders JARVIS Robot Brain heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          adapter: "simulated_ros2_gpio_bridge",
          simulated: true,
          mode: "idle",
          estop_engaged: false,
          pose: { x: 0, y: 0, heading_deg: 0 },
          battery_pct: 92,
          front_obstacle_m: 2.5,
          cpu_temp_c: 44,
          waypoints_count: 0,
          missions_count: 0
        })
      })
    );
    render(<DashboardPage />);
    expect(screen.getByText(/JARVIS Robot Brain/i)).toBeTruthy();
  });
});
