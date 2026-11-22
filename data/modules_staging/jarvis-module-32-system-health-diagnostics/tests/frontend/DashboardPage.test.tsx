import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 32)", () => {
  it("renders JARVIS System Health & Diagnostics heading", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          adapter: "local_linux_host_probe",
          simulated: false,
          hostname: "jarvis-pi5",
          load_1m: 0.42,
          memory_used_pct: 38.5,
          disk_used_pct: 41.2,
          cpu_temp_c: 48.0,
          open_alerts_count: 0,
          services_count: 1
        })
      })
    );
    render(<DashboardPage />);
    expect(screen.getByText(/JARVIS System Health/i)).toBeTruthy();
  });
});
