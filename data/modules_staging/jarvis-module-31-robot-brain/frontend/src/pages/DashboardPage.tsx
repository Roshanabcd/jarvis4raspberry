import React, { useEffect, useState } from "react";

interface RobotStatus {
  adapter: string;
  simulated: boolean;
  mode: string;
  estop_engaged: boolean;
  pose: { x: number; y: number; heading_deg: number };
  battery_pct: number;
  front_obstacle_m: number;
  cpu_temp_c: number;
  waypoints_count: number;
  missions_count: number;
}

const API = "/api/v1/robot-brain";

export default function DashboardPage() {
  const [status, setStatus] = useState<RobotStatus | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadStatus = async () => {
    const res = await fetch(`${API}/status`);
    if (res.ok) setStatus(await res.json());
  };

  useEffect(() => {
    loadStatus().catch(() => setNotice("Unable to connect to Robot Brain API."));
  }, []);

  const triggerEstop = async () => {
    await fetch(`${API}/estop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Dashboard E-STOP" })
    });
    setNotice("E-STOP engaged.");
    await loadStatus();
  };

  const resetEstop = async () => {
    await fetch(`${API}/estop/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm_reset: true, operator_note: "Dashboard reset" })
    });
    setNotice("E-STOP cleared.");
    await loadStatus();
  };

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS Robot Brain
          </h1>
          <p className="text-sm text-slate-400">
            Module 31 • E-STOP Safety Interlock, Kinematics &amp; Autonomous Missions
          </p>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="px-3 py-1 rounded-full border border-[#9868FF]/50 text-[#9868FF]">
            {status?.simulated ? "SIMULATED ROS2/GPIO" : "LIVE HARDWARE"}
          </span>
          <span
            className={`px-3 py-1 rounded-full border ${
              status?.estop_engaged
                ? "border-rose-400 text-rose-300"
                : "border-[#25E6A2]/50 text-[#25E6A2]"
            }`}
          >
            {status?.estop_engaged ? "E-STOP ENGAGED" : "SAFETY CLEAR"}
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
          <div className="text-xs uppercase text-slate-400">Mode</div>
          <div className="text-xl font-bold">{status?.mode ?? "idle"}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Pose (X, Y)</div>
          <div className="text-xl font-bold">
            {status ? `${status.pose.x}, ${status.pose.y}` : "0, 0"}
          </div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Battery</div>
          <div className="text-xl font-bold text-[#25E6A2]">
            {status?.battery_pct ?? 0}%
          </div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Front Obstacle</div>
          <div className="text-xl font-bold">{status?.front_obstacle_m ?? 0} m</div>
        </div>
      </section>

      <div className="flex gap-3">
        <button
          onClick={triggerEstop}
          className="px-4 py-2 rounded-lg bg-rose-500/20 border border-rose-400 text-rose-200 font-semibold text-sm"
        >
          ENGAGE E-STOP
        </button>
        <button
          onClick={resetEstop}
          className="px-4 py-2 rounded-lg bg-[#00D9FF] text-[#050B16] font-semibold text-sm"
        >
          Confirm E-STOP Reset
        </button>
      </div>
    </div>
  );
}
