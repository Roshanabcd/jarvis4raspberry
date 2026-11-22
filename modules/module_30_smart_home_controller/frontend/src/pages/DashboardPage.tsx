import React, { useEffect, useState } from "react";

interface Device {
  device_id: string;
  name: string;
  room: string;
  device_type: "light" | "thermostat" | "smart_plug" | "lock" | "sensor";
  rated_watts: number;
  state: Record<string, unknown>;
}

interface StatusPayload {
  adapter: string;
  simulated: boolean;
  devices_count: number;
  active_devices: number;
  scenes_count: number;
  rules_count: number;
  total_active_watts: number;
}

const API_BASE = "/api/v1/smart-home";

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [name, setName] = useState("");
  const [room, setRoom] = useState("Living Room");
  const [deviceType, setDeviceType] = useState<Device["device_type"]>("light");
  const [ratedWatts, setRatedWatts] = useState("15");
  const [notice, setNotice] = useState<string | null>(null);

  const loadData = async () => {
    const [stRes, devRes] = await Promise.all([
      fetch(`${API_BASE}/status`),
      fetch(`${API_BASE}/devices`)
    ]);
    if (stRes.ok) setStatus(await stRes.json());
    if (devRes.ok) {
      const payload = await devRes.json();
      setDevices(payload.devices || []);
    }
  };

  useEffect(() => {
    loadData().catch(() => setNotice("Unable to connect to Smart Home API."));
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim().length < 2) return;
    const res = await fetch(`${API_BASE}/devices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.trim(),
        room: room.trim(),
        device_type: deviceType,
        rated_watts: Number(ratedWatts) || 12
      })
    });
    if (res.ok) {
      setName("");
      setNotice("Device registered.");
      await loadData();
    }
  };

  const sendCommand = async (
    deviceId: string,
    command: string,
    confirmUnlock = false
  ) => {
    const res = await fetch(`${API_BASE}/devices/${deviceId}/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, confirm_unlock: confirmUnlock })
    });
    if (!res.ok) {
      const err = await res.json();
      setNotice(err?.error?.message || "Command rejected.");
      return;
    }
    setNotice(`Command '${command}' completed.`);
    await loadData();
  };

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS Smart Home Controller
          </h1>
          <p className="text-sm text-slate-400">
            Module 30 • Unified IoT Device, Scene, Rule &amp; Energy Control Plane
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-3 py-1 rounded-full border border-[#9868FF]/50 text-[#9868FF]">
            {status?.simulated ? "SIMULATED BRIDGE" : "LIVE BRIDGE"}
          </span>
          <span className="px-3 py-1 rounded-full border border-[#25E6A2]/50 text-[#25E6A2]">
            {status ? `${status.total_active_watts} W Active` : "Loading..."}
          </span>
        </div>
      </header>

      {notice && (
        <div className="mb-4 rounded-lg border border-cyan-400/30 bg-[#101E30] px-4 py-2 text-sm text-[#00D9FF]">
          {notice}
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Devices</div>
          <div className="text-2xl font-bold">{status?.devices_count ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Active</div>
          <div className="text-2xl font-bold text-[#25E6A2]">{status?.active_devices ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Scenes</div>
          <div className="text-2xl font-bold">{status?.scenes_count ?? 0}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Rules</div>
          <div className="text-2xl font-bold">{status?.rules_count ?? 0}</div>
        </div>
      </section>

      <form
        onSubmit={handleRegister}
        className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4 mb-6 grid grid-cols-1 md:grid-cols-5 gap-3"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Device name"
          className="rounded-lg bg-[#050B16] border border-cyan-400/20 px-3 py-2 text-sm"
        />
        <input
          value={room}
          onChange={(e) => setRoom(e.target.value)}
          placeholder="Room"
          className="rounded-lg bg-[#050B16] border border-cyan-400/20 px-3 py-2 text-sm"
        />
        <select
          value={deviceType}
          onChange={(e) => setDeviceType(e.target.value as Device["device_type"])}
          className="rounded-lg bg-[#050B16] border border-cyan-400/20 px-3 py-2 text-sm"
        >
          <option value="light">Light</option>
          <option value="thermostat">Thermostat</option>
          <option value="smart_plug">Smart Plug</option>
          <option value="lock">Smart Lock</option>
          <option value="sensor">Sensor</option>
        </select>
        <input
          type="number"
          value={ratedWatts}
          onChange={(e) => setRatedWatts(e.target.value)}
          className="rounded-lg bg-[#050B16] border border-cyan-400/20 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          className="rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold px-4 py-2 text-sm"
        >
          Register Device
        </button>
      </form>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {devices.map((dev) => (
          <div
            key={dev.device_id}
            className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4 flex flex-col gap-2"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold">{dev.name}</span>
              <span className="text-xs px-2 py-0.5 rounded bg-[#050B16] text-[#00D9FF]">
                {dev.device_type}
              </span>
            </div>
            <div className="text-xs text-slate-400">
              {dev.room} • {dev.rated_watts}W
            </div>
            <pre className="text-xs bg-[#050B16] text-[#25E6A2] p-2 rounded overflow-x-auto">
              {JSON.stringify(dev.state)}
            </pre>
            <div className="flex gap-2 mt-1">
              {dev.device_type === "lock" ? (
                <>
                  <button
                    onClick={() => sendCommand(dev.device_id, "lock")}
                    className="px-3 py-1 rounded bg-[#218BFF]/20 text-[#00D9FF] text-xs"
                  >
                    Lock
                  </button>
                  <button
                    onClick={() => sendCommand(dev.device_id, "unlock", true)}
                    className="px-3 py-1 rounded bg-rose-500/20 text-rose-300 text-xs"
                  >
                    Confirm Unlock
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => sendCommand(dev.device_id, "turn_on")}
                    className="px-3 py-1 rounded bg-[#00D9FF] text-[#050B16] font-semibold text-xs"
                  >
                    ON
                  </button>
                  <button
                    onClick={() => sendCommand(dev.device_id, "turn_off")}
                    className="px-3 py-1 rounded bg-slate-700 text-slate-200 text-xs"
                  >
                    OFF
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
