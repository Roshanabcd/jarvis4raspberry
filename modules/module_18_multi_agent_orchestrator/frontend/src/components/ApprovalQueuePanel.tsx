import React from 'react';
import { ApprovalRecord } from '../services/api';

interface Props {
  approvals: ApprovalRecord[];
  onDecide: (approvalId: string, approved: boolean) => Promise<void>;
}

export const ApprovalQueuePanel: React.FC<Props> = ({ approvals, onDecide }) => (
  <div className="jarvis-glass rounded-xl p-4 overflow-x-auto">
    <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">HUMAN APPROVAL CHECKPOINTS</h2>
    {approvals.length === 0 ? (
      <p className="text-xs text-slate-400 py-6 text-center">No approval requests pending.</p>
    ) : (
      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-400 border-b border-white/10">
            <th className="py-2 text-left">Approval ID</th>
            <th className="py-2 text-left">Task</th>
            <th className="py-2 text-left">Prompt</th>
            <th className="py-2 text-left">Status</th>
            <th className="py-2 text-left">Action</th>
          </tr>
        </thead>
        <tbody>
          {approvals.map((ap) => (
            <tr key={ap.approval_id} className="border-b border-white/5">
              <td className="py-2.5">{ap.approval_id}</td>
              <td className="py-2.5">{ap.task_id}</td>
              <td className="py-2.5">{ap.prompt}</td>
              <td className="py-2.5">{ap.status}</td>
              <td className="py-2.5 flex gap-1.5">
                {ap.status === 'pending' ? (
                  <>
                    <button type="button" onClick={() => onDecide(ap.approval_id, true)} className="px-2.5 py-1 rounded bg-[#25E6A2]/20 text-[#25E6A2]">
                      Approve
                    </button>
                    <button type="button" onClick={() => onDecide(ap.approval_id, false)} className="px-2.5 py-1 rounded bg-rose-500/20 text-rose-300">
                      Reject
                    </button>
                  </>
                ) : (
                  <span className="text-slate-400">{ap.decided_by ?? 'decided'}</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    )}
  </div>
);
