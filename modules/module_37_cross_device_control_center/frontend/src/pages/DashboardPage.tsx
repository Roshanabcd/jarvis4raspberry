import { useState } from "react";

interface MeshDevice {
  device_id: string;
  name: string;
  device_type: string;
  online: boolean;
}

export default function DashboardPage() {
  const [devices, setDevices] = useState<MeshDevice[]>([]);
  const [message, setMessage] = useState("Simulated cross-device mesh bridge ready.");

  async function registerSample() {
    const res = await fetch("/api/v1/devices/nodes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Roshan-Pi5-Node",
        device_type: "raspberry_pi",
        platform: "linux",
        capabilities: ["clipboard", "media", "notifications"],
        battery_pct: 100,
        online: true
      })
    });
    const dev = await res.json();
    setDevices((prev) => [dev, ...prev]);
    setMessage(`Registered ${dev.name} (${dev.device_id}).`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Cross-Device Control Center</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={registerSample}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Register Sample Device
        </button>
        <p className="text-sm text-jarvisGreen">{message}</p>
        <ul className="text-sm space-y-1">
          {devices.map((d) => (
            <li key={d.device_id}>
              {d.name} ({d.device_type}) — {d.online ? "ONLINE" : "OFFLINE"}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
