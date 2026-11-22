import React, { useState } from 'react';
import { AgentMessageRecord, ExecutionLogRecord } from '../services/api';

interface Props {
  messages: AgentMessageRecord[];
  logs: ExecutionLogRecord[];
  onSendMessage: (content: string) => Promise<void>;
}

export const CommsAndLogsPanel: React.FC<Props> = ({ messages, logs, onSendMessage }) => {
  const [content, setContent] = useState('');

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    await onSendMessage(content.trim());
    setContent('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="jarvis-glass rounded-xl p-4">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">INTER-AGENT MESSAGE BUS</h2>
        <form onSubmit={handleSend} className="flex gap-2 mb-3">
          <input
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Broadcast coordination message..."
            className="flex-1 rounded-lg bg-[#050B16]/85 border border-[#00D9FF]/25 px-3 py-2 text-xs"
          />
          <button type="submit" className="px-3.5 py-2 rounded-lg text-xs font-bold bg-[#00D9FF] text-[#050B16]">
            Send
          </button>
        </form>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {messages.map((m) => (
            <div key={m.message_id} className="p-2.5 rounded-lg bg-[#050B16]/70 border border-white/5 text-xs">
              <div className="flex justify-between">
                <span className="font-semibold text-[#00D9FF]">
                  {m.sender_agent_id} &rarr; <span className="text-[#9868FF]">{m.recipient_agent_id}</span>
                </span>
                <span className="text-slate-400">{m.channel}</span>
              </div>
              <p className="mt-1 text-slate-200">{m.content}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="jarvis-glass rounded-xl p-4">
        <h2 className="text-sm font-bold tracking-wider text-[#00D9FF] mb-3">EXECUTION LOGS</h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {logs.map((l) => (
            <div key={l.log_id} className="p-2.5 rounded-lg bg-[#050B16]/70 border border-white/5 text-xs">
              <span className="px-2 py-0.5 rounded bg-[#218BFF]/20 text-[#00D9FF] mr-2">{l.event_type}</span>
              <span className="text-slate-200">{l.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
