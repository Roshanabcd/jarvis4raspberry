import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "../../frontend/src/pages/DashboardPage";

describe("DashboardPage (Module 41 — Universal Notification Center)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders status metrics and notifications from API", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/status")) {
        return new Response(
          JSON.stringify({
            adapter: "local_notification_hub_engine",
            simulated: false,
            total_count: 1,
            unread_count: 1,
            suppressed_count: 0,
            dnd_enabled: false,
            uptime_seconds: 12.5,
          })
        );
      }
      if (url.endsWith("/preferences")) {
        return new Response(
          JSON.stringify({
            dnd_enabled: false,
            allow_critical_during_dnd: true,
            enabled_channels: ["hud", "desktop"],
          })
        );
      }
      return new Response(
        JSON.stringify({
          notifications: [
            {
              notification_id: "ntf_test001",
              source_module: "module-33-cybersecurity",
              title: "Firewall Rule Triggered",
              message: "Blocked unauthorized port scan.",
              priority: "critical",
              status: "unread",
              channels: ["hud"],
              delivered_channels: ["hud"],
            },
          ],
          count: 1,
        })
      );
    });

    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Universal Notification Center/i)).toBeTruthy();
      expect(screen.getByText(/Firewall Rule Triggered/i)).toBeTruthy();
    });
  });
});
