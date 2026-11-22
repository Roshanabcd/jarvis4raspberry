import { useState } from "react";

interface AlertItem {
  notification_id: string;
  title: string;
  priority: string;
  status: string;
}

export default function DashboardPage() {
  const [items, setItems] = useState<AlertItem[]>([]);
  const [status, setStatus] = useState("Universal notification hub ready.");

  async function sendSample() {
    const res = await fetch("/api/v1/notifications/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_module: "module-32-health",
        title: "System Check Complete",
        message: "All JARVIS modules nominal.",
        priority: "normal",
        channels: ["hud"]
      })
    });
    const item = await res.json();
    setItems((prev) => [item, ...prev]);
    setStatus(`Dispatched ${item.notification_id} (${item.status}).`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Universal Notification Center</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={sendSample}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Send Sample Alert
        </button>
        <p className="text-sm text-jarvisGreen">{status}</p>
        <ul className="text-sm space-y-1">
          {items.map((n) => (
            <li key={n.notification_id}>
              {n.title} ({n.priority}) — {n.status.toUpperCase()}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
