import { useState } from "react";

interface MarketplacePkg {
  package_id: string;
  slug: string;
  name: string;
  version: string;
  installed: boolean;
  enabled: boolean;
}

export default function DashboardPage() {
  const [packages, setPackages] = useState<MarketplacePkg[]>([]);
  const [status, setStatus] = useState("Local plugin & skills registry ready.");

  async function publishSample() {
    const res = await fetch("/api/v1/marketplace/packages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        slug: "jarvis-briefing-skill",
        name: "JARVIS Briefing Skill",
        version: "1.0.0",
        kind: "skill",
        permissions: ["notifications"]
      })
    });
    const pkg = await res.json();
    setPackages((prev) => [pkg, ...prev]);
    setStatus(`Published ${pkg.slug}@${pkg.version}.`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Plugin &amp; Skills Marketplace</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={publishSample}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Publish Sample Skill
        </button>
        <p className="text-sm text-jarvisGreen">{status}</p>
        <ul className="text-sm space-y-1">
          {packages.map((p) => (
            <li key={p.package_id}>
              {p.name} ({p.slug}@{p.version}) — {p.installed ? (p.enabled ? "ENABLED" : "DISABLED") : "AVAILABLE"}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
