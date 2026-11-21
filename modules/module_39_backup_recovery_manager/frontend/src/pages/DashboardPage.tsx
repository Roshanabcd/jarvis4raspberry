import { useState } from "react";

interface SnapshotItem {
  snapshot_id: string;
  name: string;
  file_count: number;
  byte_size: number;
}

export default function DashboardPage() {
  const [snapshots, setSnapshots] = useState<SnapshotItem[]>([]);
  const [status, setStatus] = useState("Local ZIP snapshot engine ready.");

  async function createSnapshot() {
    const res = await fetch("/api/v1/backups/snapshots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Workspace Snapshot", source_rel_path: "." })
    });
    const snap = await res.json();
    setSnapshots((prev) => [snap, ...prev]);
    setStatus(`Created snapshot ${snap.snapshot_id} (${snap.file_count} files).`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Backup &amp; Recovery Manager</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={createSnapshot}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Create Workspace Snapshot
        </button>
        <p className="text-sm text-jarvisGreen">{status}</p>
        <ul className="text-sm space-y-1">
          {snapshots.map((s) => (
            <li key={s.snapshot_id}>
              {s.name} ({s.snapshot_id}) — {s.file_count} files, {s.byte_size} bytes
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
