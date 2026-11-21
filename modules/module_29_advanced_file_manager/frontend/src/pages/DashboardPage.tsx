import React, { useEffect, useState } from 'react';

interface FileEntry {
  name: string;
  rel_path: string;
  is_dir: boolean;
  size_bytes: number;
  category: string;
  tags: string[];
}

const API_BASE = '/api/v1/file-manager';

export const DashboardPage: React.FC = () => {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [relPath, setRelPath] = useState('');
  const [content, setContent] = useState('');

  const loadFiles = async () => {
    const res = await fetch(`${API_BASE}/files`);
    if (res.ok) {
      const data = await res.json();
      setEntries(data.entries || []);
    }
  };

  useEffect(() => {
    void loadFiles();
  }, []);

  const saveFile = async () => {
    if (!relPath.trim()) return;
    await fetch(`${API_BASE}/files`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rel_path: relPath.trim(), content }),
    });
    setRelPath('');
    setContent('');
    await loadFiles();
  };

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text p-6">
      <header className="flex items-center justify-between border-b border-jarvis-cyan/25 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-jarvis-cyan">JARVIS OS — Module 29: Advanced File Manager</h1>
          <p className="text-xs text-slate-400">Sandboxed CRUD, SHA-256 Duplicates, Auto-Organization &amp; Trash Restore</p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs border border-emerald-400/50 text-emerald-300 bg-emerald-500/10">
          Local Sandboxed FS
        </span>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-3">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Write File</h2>
          <input value={relPath} onChange={(e) => setRelPath(e.target.value)} placeholder="notes.md" className="w-full bg-jarvis-bg border border-slate-700 rounded-lg px-3 py-2 text-sm" />
          <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="File content..." className="w-full h-24 bg-jarvis-bg border border-slate-700 rounded-lg p-2 text-sm" />
          <button onClick={saveFile} className="w-full py-2 rounded-lg bg-jarvis-cyan text-slate-950 font-semibold text-sm">Save File</button>
        </section>

        <section className="lg:col-span-2 bg-jarvis-panel border border-jarvis-cyan/20 rounded-xl p-4 space-y-2">
          <h2 className="text-sm font-semibold text-jarvis-cyan">Managed Files ({entries.length})</h2>
          {entries.map((e) => (
            <div key={e.rel_path} className="p-3 rounded-lg bg-jarvis-bg border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{e.name}</div>
                <div className="text-xs text-slate-400">{e.category} · {e.size_bytes} bytes</div>
              </div>
              <span className="text-xs text-jarvis-cyan">{e.is_dir ? 'DIR' : 'FILE'}</span>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};
