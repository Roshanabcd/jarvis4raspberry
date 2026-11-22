import React, { useEffect, useState } from "react";

interface FinanceSummary {
  month: string;
  net_worth: number;
  total_income: number;
  total_expense: number;
  net_cashflow: number;
  savings_rate_pct: number;
}

const API = "/api/v1/finance";

export default function DashboardPage() {
  const [summary, setSummary] = useState<FinanceSummary | null>(null);

  useEffect(() => {
    fetch(`${API}/summary`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setSummary(d))
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[#050B16] text-[#F0F8FF] p-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyan-400/20 pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-[#00D9FF]">
            JARVIS Personal Finance Manager
          </h1>
          <p className="text-sm text-slate-400">
            Module 34 • Multi-Account Ledger, Monthly Budgets &amp; Savings Goals
          </p>
        </div>
        <span className="px-3 py-1 rounded-full border border-[#25E6A2]/50 text-[#25E6A2] text-xs">
          LOCAL SQLITE LEDGER
        </span>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Net Worth</div>
          <div className="text-2xl font-bold">{summary?.net_worth?.toFixed(2) ?? "0.00"}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Income</div>
          <div className="text-2xl font-bold text-[#25E6A2]">{summary?.total_income?.toFixed(2) ?? "0.00"}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Expenses</div>
          <div className="text-2xl font-bold">{summary?.total_expense?.toFixed(2) ?? "0.00"}</div>
        </div>
        <div className="rounded-xl bg-[#101E30] border border-cyan-400/20 p-4">
          <div className="text-xs uppercase text-slate-400">Savings Rate</div>
          <div className="text-2xl font-bold">{summary?.savings_rate_pct ?? 0}%</div>
        </div>
      </section>
    </div>
  );
}
