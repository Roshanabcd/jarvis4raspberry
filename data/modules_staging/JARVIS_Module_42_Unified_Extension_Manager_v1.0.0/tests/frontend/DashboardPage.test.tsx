import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 42 — Unified Extension Manager)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders status metrics and registered modules", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/status")) {
        return new Response(
          JSON.stringify({
            adapter: "local_unified_extension_manager",
            simulated: false,
            default_archives_dir: "/home/roshan/Downloads/module-jarvis",
            total_modules: 1,
            enabled_modules: 0,
            health_breakdown: { not_verified: 1 },
            pending_approvals: 0,
            cross_module_conflicts: 0,
            uptime_seconds: 3.1,
          })
        );
      }
      return new Response(
        JSON.stringify({
          modules: [
            {
              module_id: "jarvis-module-18",
              name: "Multi-Agent Task Orchestrator",
              version: "1.0.0",
              category: "core_orchestration",
              source_archive: "/home/roshan/Downloads/module-jarvis/m18.zip",
              installed_location: null,
              integration_status: "discovered",
              enabled: false,
              health_status: "not_verified",
              health_endpoint: null,
              dependencies: {},
              required_permissions: ["orchestrator.tasks.create"],
              config: {},
              compatibility: {},
              error_details: null,
            },
          ],
          count: 1,
        })
      );
    });

    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Unified Extension Manager/i)).toBeTruthy();
      expect(screen.getByText(/Multi-Agent Task Orchestrator/i)).toBeTruthy();
    });
  });
});
