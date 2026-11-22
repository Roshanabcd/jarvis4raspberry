import React, { useState } from 'react';
import { Mic, Send, Square } from 'lucide-react';
import { HolographicAvatar } from '../components/HolographicAvatar';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
}

export const DashboardPage: React.FC = () => {
  const [persona, setPersona] = useState<'aria' | 'atlas'>('aria');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [subtitle, setSubtitle] = useState('Ready. Speak or type to start a conversation.');
  const [facialState, setFacialState] = useState('idle');
  const [mouthOpenness, setMouthOpenness] = useState(0.15);

  const send = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;
    const text = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setFacialState('thinking');

    const res = await fetch('/api/v1/conversational-ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, content: text, persona }),
    });
    const data = await res.json();
    if (data.session_id) setSessionId(data.session_id);
    const reply = data.assistant_message?.content || '';
    setMessages((prev) => [...prev, { role: 'assistant', content: reply, provider: data.assistant_message?.provider }]);
    setSubtitle(reply);
    setFacialState(data.facial_state || 'speaking');
    setMouthOpenness(0.7);
    setTimeout(() => {
      setMouthOpenness(0.15);
      setFacialState('idle');
    }, 1200);
  };

  const interrupt = async () => {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (sessionId) await fetch(`/api/v1/conversational-ai/sessions/${sessionId}/interrupt`, { method: 'POST' });
    setFacialState('interrupted');
    setMouthOpenness(0.1);
  };

  return (
    <main className="max-w-[1400px] mx-auto p-5 space-y-5">
      <header className="jarvis-glass rounded-2xl p-5 flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-lg font-bold tracking-wider">JARVIS OS · MODULE 20 — REAL-TIME CONVERSATIONAL AI</h1>
          <p className="text-xs text-slate-400">Holographic ARIA &amp; ATLAS · Approximate Viseme Lip-Sync · Voice Barge-In</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold border border-amber-400/50 bg-amber-400/15 text-amber-300">
          LIP-SYNC: APPROXIMATE VISEME (BROWSER FALLBACK)
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <section className="jarvis-glass rounded-2xl p-5 flex flex-col items-center gap-3">
          <div className="flex gap-2">
            <button type="button" onClick={() => setPersona('aria')} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${persona === 'aria' ? 'bg-[#00D9FF] text-[#050B16]' : 'bg-[#101E30]'}`}>
              ARIA (Female)
            </button>
            <button type="button" onClick={() => setPersona('atlas')} className={`px-3 py-1.5 rounded-lg text-xs font-bold ${persona === 'atlas' ? 'bg-[#218BFF] text-white' : 'bg-[#101E30]'}`}>
              ATLAS (Male)
            </button>
          </div>
          <HolographicAvatar persona={persona} facialState={facialState} mouthOpenness={mouthOpenness} />
          <div className="w-full p-3 rounded-xl bg-[#050B16]/85 border border-[#00D9FF]/25 text-xs text-center min-h-[54px]">
            {subtitle}
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={interrupt} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
              <Square className="w-3.5 h-3.5" /> Interrupt
            </button>
          </div>
        </section>

        <section className="lg:col-span-2 jarvis-glass rounded-2xl p-5 flex flex-col h-[560px]">
          <div className="flex-1 overflow-y-auto space-y-2.5 mb-3">
            {messages.map((m, i) => (
              <div key={i} className={`p-3 rounded-xl text-xs max-w-[85%] ${m.role === 'user' ? 'ml-auto bg-[#218BFF]/25' : 'bg-[#050B16]/80 border border-[#00D9FF]/25'}`}>
                <div className="text-[10px] text-slate-400 mb-1">{m.role.toUpperCase()} {m.provider ? `· ${m.provider}` : ''}</div>
                {m.content}
              </div>
            ))}
          </div>
          <form onSubmit={send} className="flex gap-2">
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type or speak to JARVIS..." className="flex-1 rounded-lg bg-[#050B16] border border-[#00D9FF]/30 px-3 py-2 text-xs" />
            <button type="submit" className="inline-flex items-center gap-1 px-4 py-2 rounded-lg text-xs font-bold bg-[#00D9FF] text-[#050B16]">
              <Send className="w-3.5 h-3.5" /> Send
            </button>
          </form>
        </section>
      </div>
    </main>
  );
};
