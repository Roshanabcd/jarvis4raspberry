import { useState } from "react";

interface ApprovalItem {
  request_id: string;
  summary: string;
  status: string;
  risk_level: string;
}

export default function DashboardPage() {
  const [requests, setRequests] = useState<ApprovalItem[]>([]);
  const [status, setStatus] = useState("Fail-closed approval gate ready.");

  async function submitSample() {
    const res = await fetch("/api/v1/approvals/requests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requester: "agent-deploy-bot",
        module_id: "module-27-github-cicd",
        action: "deploy_production",
        risk_level: "critical",
        summary: "Deploy release to Raspberry Pi 5"
      })
    });
    const item = await res.json();
    setRequests((prev) => [item, ...prev]);
    setStatus(`Submitted ${item.request_id} (${item.status}).`);
  }

  return (
    <div className="min-h-screen bg-jarvisBg text-[#F0F8FF] p-6">
      <h1 className="text-2xl font-bold text-jarvisCyan mb-4">Permissions &amp; Approval Center</h1>
      <div className="bg-jarvisPanel border border-jarvisCyan/30 rounded-xl p-4 space-y-4">
        <button
          type="button"
          onClick={submitSample}
          className="px-4 py-2 rounded-lg bg-jarvisCyan text-jarvisBg font-semibold"
        >
          Submit High-Risk Request
        </button>
        <p className="text-sm text-jarvisGreen">{status}</p>
        <ul className="text-sm space-y-1">
          {requests.map((r) => (
            <li key={r.request_id}>
              {r.summary} ({r.risk_level}) — {r.status.toUpperCase()}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
