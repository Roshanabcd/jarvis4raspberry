import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  LayoutDashboard, MessageSquare, Mic, MicOff, Cpu, CheckSquare, Workflow,
  Code2, Terminal as TerminalIcon, Calendar as CalendarIcon, Brain, BookOpen,
  Activity, Bot, Plug, Settings as SettingsIcon, Search, Bell, User,
  Volume2, VolumeX, Play, Pause, Square, RotateCcw, Plus, Trash2, Copy, Check,
  ChevronLeft, ChevronRight, Sparkles, ShieldAlert, Radio, Wifi, Battery,
  Thermometer, HardDrive, Layers, GitBranch, FileCode, Folder, AlertTriangle,
  X, Send, Command, Sliders, Eye, EyeOff, ArrowUp, ArrowDown, ArrowLeft,
  ArrowRight, Zap, Clock, CheckCircle2, XCircle, Loader2, Menu, Power,
  RefreshCw, ExternalLink, Info, Edit3, Filter
} from 'lucide-react';

// ============================================================================
// DESIGN TOKENS & THEMES
// ============================================================================
const THEMES = {
  dark: {
    id: 'dark',
    name: 'Futuristic Dark',
    bg: '#050B16',
    secondaryBg: '#0B1525',
    cardBg: 'rgba(16, 30, 48, 0.72)',
    cardSolid: '#101E30',
    border: 'rgba(0, 217, 255, 0.16)',
    textPrimary: '#F0F8FF',
    textSecondary: '#97AEC7',
    gradient: 'radial-gradient(circle at 50% 0%, rgba(0,217,255,0.12), transparent 55%), radial-gradient(circle at 85% 80%, rgba(152,104,255,0.10), transparent 50%)'
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight Blue',
    bg: '#03081A',
    secondaryBg: '#071330',
    cardBg: 'rgba(12, 26, 58, 0.76)',
    cardSolid: '#0C1A3A',
    border: 'rgba(33, 139, 255, 0.22)',
    textPrimary: '#EEF6FF',
    textSecondary: '#8EAAD0',
    gradient: 'radial-gradient(circle at 50% 0%, rgba(33,139,255,0.16), transparent 55%), radial-gradient(circle at 15% 85%, rgba(0,217,255,0.10), transparent 50%)'
  },
  purple: {
    id: 'purple',
    name: 'Purple Neon',
    bg: '#090517',
    secondaryBg: '#130B29',
    cardBg: 'rgba(26, 16, 52, 0.74)',
    cardSolid: '#1A1034',
    border: 'rgba(152, 104, 255, 0.24)',
    textPrimary: '#F6F0FF',
    textSecondary: '#B29ED4',
    gradient: 'radial-gradient(circle at 50% 0%, rgba(152,104,255,0.18), transparent 55%), radial-gradient(circle at 80% 75%, rgba(0,217,255,0.10), transparent 50%)'
  }
};

const ACCENTS = [
  { id: 'cyan', name: 'Electric Cyan', hex: '#00D9FF' },
  { id: 'blue', name: 'Neon Blue', hex: '#218BFF' },
  { id: 'purple', name: 'Holo Purple', hex: '#9868FF' },
  { id: 'emerald', name: 'Cyber Emerald', hex: '#25E6A2' }
];

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, group: 'Core' },
  { id: 'chat', label: 'AI Chat', icon: MessageSquare, group: 'Core' },
  { id: 'voice', label: 'Voice Assistant', icon: Mic, group: 'Core' },
  { id: 'agents', label: 'AI Agents', icon: Cpu, group: 'Orchestration' },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare, group: 'Orchestration' },
  { id: 'automation', label: 'Automation', icon: Workflow, group: 'Orchestration' },
  { id: 'workspace', label: 'Developer Workspace', icon: Code2, group: 'Engineering' },
  { id: 'terminal', label: 'Terminal', icon: TerminalIcon, group: 'Engineering' },
  { id: 'calendar', label: 'Calendar', icon: CalendarIcon, group: 'Productivity' },
  { id: 'memory', label: 'Memory', icon: Brain, group: 'Knowledge' },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen, group: 'Knowledge' },
  { id: 'devices', label: 'Devices & Telemetry', icon: Activity, group: 'Hardware' },
  { id: 'robot', label: 'Robot Control', icon: Bot, group: 'Hardware' },
  { id: 'integrations', label: 'Integrations', icon: Plug, group: 'System' },
  { id: 'settings', label: 'Settings', icon: SettingsIcon, group: 'System' }
];

// ============================================================================
// INITIAL SIMULATED / DEMO DATA
// ============================================================================
const INITIAL_AGENTS = [
  { id: 'ag-1', name: 'JARVIS Main Orchestrator', model: 'Local Router / Hybrid (Demo)', status: 'Running', progress: 84, activity: 'Coordinating multi-agent task graph & context routing', logs: ['[11:30:02] Bootstrapped simulated orchestrator graph', '[11:32:15] Delegated code audit to Codex Agent', '[11:35:40] Synced memory embeddings (simulated)'] },
  { id: 'ag-2', name: 'OpenAI Codex Agent', model: 'Codex-5-Demo', status: 'Running', progress: 62, activity: 'Refactoring TypeScript API schema & unit tests', logs: ['[11:31:10] Scanned 14 frontend components', '[11:34:05] Generated 6 simulated test cases'] },
  { id: 'ag-3', name: 'Google Gemini Agent', model: 'Gemini-3.1-Pro (Demo)', status: 'Idle', progress: 100, activity: 'Completed multimodal architecture summary', logs: ['[11:20:00] Analyzed UI design tokens', '[11:28:44] Delivered responsive layout report'] },
  { id: 'ag-4', name: 'Antigravity Agent', model: 'Antigravity-Core (Demo)', status: 'Running', progress: 45, activity: 'Running simulated visual regression & layout checks', logs: ['[11:33:12] Checking 1366x768 & mobile viewports'] },
  { id: 'ag-5', name: 'GitHub Copilot Agent', model: 'Copilot-Workspace (Demo)', status: 'Paused', progress: 30, activity: 'Awaiting simulated PR review approval', logs: ['[11:15:22] Drafted PR #142 description', '[11:18:00] Paused by user policy'] },
  { id: 'ag-6', name: 'Research Agent', model: 'DeepSearch-Sim', status: 'Idle', progress: 100, activity: 'Indexed 24 local documentation files', logs: ['[11:10:05] Completed semantic indexing'] },
  { id: 'ag-7', name: 'Automation Agent', model: 'FlowEngine-v2 (Demo)', status: 'Running', progress: 78, activity: 'Monitoring nightly build & alert triggers', logs: ['[11:00:00] Triggered simulated health check'] },
  { id: 'ag-8', name: 'Local AI Agent', model: 'Ollama / Llama-3-8B (Demo)', status: 'Idle', progress: 100, activity: 'Standing by for offline privacy-first queries', logs: ['[10:55:00] Local weights loaded in simulation'] }
];

const INITIAL_TASKS = [
  { id: 't-1', title: 'Analyze codebase architecture', agent: 'JARVIS Main Orchestrator', status: 'Running', progress: 72, priority: 'High' },
  { id: 't-2', title: 'Fix simulated API timeout errors', agent: 'OpenAI Codex Agent', status: 'Queued', progress: 0, priority: 'High' },
  { id: 't-3', title: 'Generate component documentation', agent: 'Google Gemini Agent', status: 'Complete', progress: 100, priority: 'Medium' },
  { id: 't-4', title: 'Perform automated responsive tests', agent: 'Antigravity Agent', status: 'Running', progress: 48, priority: 'High' },
  { id: 't-5', title: 'Summarize weekly sprint progress', agent: 'Research Agent', status: 'Paused', progress: 35, priority: 'Low' },
  { id: 't-6', title: 'Organize project assets & logs', agent: 'Automation Agent', status: 'Failed', progress: 60, priority: 'Medium' }
];

const INITIAL_AUTOMATIONS = [
  { id: 'auto-1', name: 'Morning Briefing & Telemetry Digest', trigger: 'Daily at 08:00 Local', action: 'Speak summary via JARVIS Voice', enabled: true, runs: 42 },
  { id: 'auto-2', name: 'Auto-Triage Failed CI Builds', trigger: 'On Build Failure (Simulated)', action: 'Assign OpenAI Codex Agent + Notify', enabled: true, runs: 19 },
  { id: 'auto-3', name: 'Privacy Mode Local Fallback', trigger: 'When Offline Detected', action: 'Switch to Local AI Agent', enabled: true, runs: 7 },
  { id: 'auto-4', name: 'Robot Battery Low Return-to-Dock', trigger: 'Robot Battery < 20% (Sim)', action: 'Trigger Safe Stop & Alert', enabled: false, runs: 3 }
];

const DEMO_FILES = {
  'src/jarvis/orchestrator.ts': `// Simulated JARVIS Multi-Agent Orchestrator\nexport interface AgentTask {\n  id: string;\n  role: 'orchestrator' | 'coder' | 'researcher';\n  priority: 'high' | 'normal';\n}\n\nexport async function dispatchSimulatedTask(task: AgentTask) {\n  console.log(\`[JARVIS-SIM] Dispatching \${task.id} to \${task.role}\`);\n  return { status: 'queued', simulated: true, timestamp: Date.now() };\n}`,
  'src/avatar/lipSyncEngine.ts': `// Approximate Web Speech API Viseme / Cadence Mapper\nexport type MouthShape = 'closed' | 'smile' | 'small' | 'mid' | 'wide';\n\nexport function mapCharToViseme(char: string): MouthShape {\n  const c = char.toLowerCase();\n  if ('aeo'.includes(c)) return 'wide';\n  if ('iuwy'.includes(c)) return 'mid';\n  if ('bmpfv'.includes(c)) return 'closed';\n  return 'small';\n}`,
  'src/robot/safetyController.py': `# Simulated Raspberry Pi 5 + ESP32-S3 Safety Gate\nclass RobotSafetyController:\n    def __init__(self):\n        self.estop_active = False\n        self.mode = "SIMULATION"\n\n    def trigger_emergency_stop(self):\n        self.estop_active = True\n        return {"motors": "HALTED", "mode": self.mode}`
};

const INITIAL_MESSAGES = [
  {
    id: 'm-1',
    sender: 'jarvis',
    text: 'Welcome to JARVIS OS (Interactive Frontend Prototype). All telemetry, agent runs, and device links are clearly labeled simulated demo data. Ask me to run a status check, switch avatars, or test my voice synthesis.',
    time: '11:30 AM',
    source: 'Simulated AI Engine'
  }
];

const DEMO_PROMPTS = [
  'Give me a full system status briefing',
  'Inspect active agents and summarize progress',
  'Run a simulated robot hardware check',
  'Explain how your avatar lip-sync works'
];

const INITIAL_MEMORIES = [
  { id: 'mem-1', category: 'Conversation Memory', title: 'Preferred UI Aesthetic', content: 'User prefers Futuristic Dark Glass (#050B16) with electric cyan accents and human-like AI avatars over abstract orbs.', updated: '2 mins ago (Demo)' },
  { id: 'mem-2', category: 'Project Context', title: 'JARVIS Robotics Hardware Target', content: 'Future physical integration targets Raspberry Pi 5 + ESP32-S3 with strict E-STOP safety gates.', updated: '18 mins ago (Demo)' },
  { id: 'mem-3', category: 'Saved Documents', title: 'Multi-Agent Architecture Spec v2', content: 'Defines isolated worktrees and human approval gates for privileged actions.', updated: '1 hour ago (Demo)' },
  { id: 'mem-4', category: 'Conversation Memory', title: 'Voice Assistant Preferences', content: 'Browser SpeechSynthesis enabled with adjustable cadence and live subtitle bar.', updated: '3 hours ago (Demo)' }
];

const INITIAL_KB = [
  { id: 'kb-1', category: 'Architecture', title: 'JARVIS OS Modular Frontend Guide', summary: 'How to connect this React prototype to real WebSocket telemetry, FastAPI/Node backends, and STT/TTS pipelines.', tags: ['React', 'WebSockets', 'Architecture'] },
  { id: 'kb-2', category: 'Safety', title: 'Human-in-the-Loop Approval Gates', summary: 'Policy specification requiring explicit confirmation before destructive shell commands or physical robot actuation.', tags: ['Security', 'Robotics'] },
  { id: 'kb-3', category: 'Avatar', title: 'Holographic Avatar State Machine', summary: 'Documentation of Idle, Listening, Thinking, Speaking, Happy, and Offline states with Web Speech API sync.', tags: ['SVG', 'SpeechSynthesis'] },
  { id: 'kb-4', category: 'Agents', title: 'Conflict-Free Multi-Agent Execution', summary: 'Preventing concurrent coding agents from overwriting shared files using branch isolation.', tags: ['Agents', 'Git'] }
];

const INITIAL_EVENTS = [
  { id: 'ev-1', title: 'JARVIS UI Design Review (Demo)', day: 'Today', time: '02:00 PM', type: 'Meeting' },
  { id: 'ev-2', title: 'Simulated Nightly Build & E2E Check', day: 'Today', time: '06:30 PM', type: 'Automation' },
  { id: 'ev-3', title: 'Raspberry Pi 5 Sensor Calibration', day: 'Tomorrow', time: '10:00 AM', type: 'Hardware' },
  { id: 'ev-4', title: 'Weekly Agent Performance Digest', day: 'Fri', time: '04:00 PM', type: 'Reminder' }
];

const INITIAL_INTEGRATIONS = [
  { id: 'int-1', name: 'GitHub', category: 'Developer Tools', desc: 'PR reviews, issue triage, and repository sync.', status: 'Demo / Not Connected' },
  { id: 'int-2', name: 'Google Services', category: 'Productivity', desc: 'Calendar events, Drive docs, and Gmail briefings.', status: 'Demo / Not Connected' },
  { id: 'int-3', name: 'OpenAI API', category: 'AI Model Provider', desc: 'Codex & GPT reasoning endpoints.', status: 'Demo / Not Connected' },
  { id: 'int-4', name: 'Google Gemini API', category: 'AI Model Provider', desc: 'Multimodal reasoning & long-context analysis.', status: 'Demo / Not Connected' },
  { id: 'int-5', name: 'Local Ollama', category: 'Local Services', desc: 'Offline local LLM inference on localhost:11434.', status: 'Demo / Not Connected' },
  { id: 'int-6', name: 'Docker Engine', category: 'Developer Tools', desc: 'Sandboxed agent execution containers.', status: 'Demo / Not Connected' },
  { id: 'int-7', name: 'Slack Workspace', category: 'Cloud Services', desc: 'Alert routing and approval notifications.', status: 'Demo / Not Connected' }
];

// ============================================================================
// HUMAN-LIKE ANIMATED AI AVATAR COMPONENT (ARIA & ATLAS)
// ============================================================================
function HumanAIAvatar({ avatarType, state, mouthShape, accentColor, reducedMotion, size = 'lg' }) {
  const [isBlinking, setIsBlinking] = useState(false);
  const [gaze, setGaze] = useState({ x: 0, y: 0 });

  // Natural periodic blinking
  useEffect(() => {
    if (state === 'offline') return;
    let timeoutId;
    const scheduleBlink = () => {
      const nextBlink = 2400 + Math.random() * 3200;
      timeoutId = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          scheduleBlink();
        }, 140);
      }, nextBlink);
    };
    scheduleBlink();
    return () => clearTimeout(timeoutId);
  }, [state]);

  // Subtle natural eye gaze & head micro-movement
  useEffect(() => {
    if (state === 'offline' || reducedMotion) {
      setGaze({ x: 0, y: 0 });
      return;
    }
    const interval = setInterval(() => {
      if (state === 'listening') {
        setGaze({ x: (Math.random() - 0.5) * 1.2, y: -0.6 });
      } else if (state === 'thinking') {
        setGaze({ x: 2.5, y: -2.0 });
      } else {
        setGaze({ x: (Math.random() - 0.5) * 2.4, y: (Math.random() - 0.5) * 1.4 });
      }
    }, 2200);
    return () => clearInterval(interval);
  }, [state, reducedMotion]);

  const isFemale = avatarType === 'female';
  const isOffline = state === 'offline';
  const primaryGlow = isOffline ? '#475569' : accentColor;
  const secondaryGlow = isOffline ? '#334155' : (isFemale ? '#9868FF' : '#218BFF');

  // Mouth path based on state & live speech shape
  const getMouthPath = () => {
    if (isOffline) return 'M 140 164 Q 150 163 160 164';
    if (state === 'happy') return 'M 136 161 Q 150 173 164 161';
    if (state === 'thinking') return 'M 142 164 Q 150 162 158 165';
    if (state === 'listening') return 'M 139 162 Q 150 166 161 162';
    if (state === 'speaking') {
      switch (mouthShape) {
        case 'wide': return 'M 137 161 Q 150 157 163 161 Q 150 178 137 161 Z';
        case 'mid': return 'M 139 161 Q 150 159 161 161 Q 150 172 139 161 Z';
        case 'small': return 'M 142 162 Q 150 160 158 162 Q 150 168 142 162 Z';
        default: return 'M 139 163 Q 150 165 161 163';
      }
    }
    return 'M 138 162 Q 150 167 162 162';
  };

  const isOpenMouth = state === 'speaking' && ['wide', 'mid', 'small'].includes(mouthShape);
  const dim = size === 'sm' ? 'w-44 h-44' : size === 'md' ? 'w-60 h-60' : 'w-64 h-64 sm:w-72 sm:h-72';

  return (
    <div className={`relative flex items-center justify-center select-none ${dim}`}>
      {/* Holographic HUD Rings Behind Character */}
      <svg viewBox="0 0 300 300" className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <radialGradient id={`halo-${avatarType}`} cx="50%" cy="48%" r="50%">
            <stop offset="0%" stopColor={primaryGlow} stopOpacity={isOffline ? '0.05' : '0.24'} />
            <stop offset="65%" stopColor={secondaryGlow} stopOpacity={isOffline ? '0.02' : '0.08'} />
            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="150" cy="150" r="142" fill={`url(#halo-${avatarType})`} />
        <circle
          cx="150" cy="150" r="134" fill="none" stroke={primaryGlow} strokeOpacity="0.22"
          strokeWidth="1.2" strokeDasharray="12 8 4 8"
          className={!reducedMotion && !isOffline ? 'jarvis-spin-slow' : ''}
        />
        <circle
          cx="150" cy="150" r="120" fill="none" stroke={secondaryGlow} strokeOpacity="0.28"
          strokeWidth="1.5" strokeDasharray="45 25 10 25"
          className={!reducedMotion && !isOffline ? 'jarvis-spin-reverse' : ''}
        />
        {state === 'thinking' && !reducedMotion && (
          <circle
            cx="150" cy="150" r="106" fill="none" stroke={primaryGlow} strokeOpacity="0.55"
            strokeWidth="2" strokeDasharray="18 14" className="jarvis-spin-fast"
          />
        )}
        {state === 'listening' && !reducedMotion && (
          <circle
            cx="150" cy="150" r="128" fill="none" stroke="#25E6A2" strokeOpacity="0.5"
            strokeWidth="2" className="animate-ping" style={{ transformOrigin: '150px 150px', animationDuration: '2.2s' }}
          />
        )}
      </svg>

      {/* Human-Like Digital Character SVG */}
      <svg
        viewBox="0 0 300 300"
        className={`relative z-10 w-full h-full drop-shadow-2xl transition-all duration-500 ${isOffline ? 'grayscale opacity-55' : ''} ${!reducedMotion && !isOffline ? 'jarvis-breathe' : ''}`}
      >
        <defs>
          <linearGradient id="skinToneF" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F5D3C4" />
            <stop offset="65%" stopColor="#E6B8A2" />
            <stop offset="100%" stopColor="#CFA08A" />
          </linearGradient>
          <linearGradient id="skinToneM" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ECC5B0" />
            <stop offset="65%" stopColor="#D8A98E" />
            <stop offset="100%" stopColor="#BC8C72" />
          </linearGradient>
          <linearGradient id="suitGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#162844" />
            <stop offset="50%" stopColor="#0D192D" />
            <stop offset="100%" stopColor="#1A1738" />
          </linearGradient>
          <linearGradient id="hairF" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1E2B48" />
            <stop offset="50%" stopColor="#121A30" />
            <stop offset="100%" stopColor="#2B1F4D" />
          </linearGradient>
          <linearGradient id="hairM" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1C273D" />
            <stop offset="100%" stopColor="#0E1525" />
          </linearGradient>
          <clipPath id="avatarClip">
            <circle cx="150" cy="150" r="118" />
          </clipPath>
        </defs>

        <g clipPath="url(#avatarClip)">
          {/* Back Hair for ARIA */}
          {isFemale && (
            <path
              d="M 88 128 C 80 185 84 245 96 275 L 204 275 C 216 245 220 185 212 128 C 204 65 96 65 88 128 Z"
              fill="url(#hairF)"
            />
          )}

          {/* Futuristic Upper Torso & Suit */}
          <path
            d={isFemale
              ? 'M 66 285 C 74 232 104 214 150 214 C 196 214 226 232 234 285 Z'
              : 'M 54 285 C 64 226 98 208 150 208 C 202 208 236 226 246 285 Z'}
            fill="url(#suitGrad)"
            stroke={primaryGlow}
            strokeOpacity="0.45"
            strokeWidth="1.5"
          />

          {/* Suit Holographic Collar & Glowing Trim */}
          <path
            d="M 116 218 L 150 248 L 184 218"
            fill="none" stroke={primaryGlow} strokeWidth="2.2" strokeLinecap="round"
          />
          <path
            d="M 96 234 L 138 268 M 204 234 L 162 268"
            fill="none" stroke={secondaryGlow} strokeOpacity="0.7" strokeWidth="1.5"
          />
          <circle cx="150" cy="256" r="4" fill={primaryGlow} />

          {/* Neck */}
          <path
            d={isFemale
              ? 'M 134 182 L 134 219 Q 150 230 166 219 L 166 182 Z'
              : 'M 129 180 L 129 218 Q 150 230 171 218 L 171 180 Z'}
            fill={isFemale ? 'url(#skinToneF)' : 'url(#skinToneM)'}
          />
          {/* Neck Shadow */}
          <path d="M 134 185 Q 150 202 166 185 L 166 198 Q 150 210 134 198 Z" fill="#0B1525" fillOpacity="0.2" />

          {/* Head Group with subtle motion */}
          <g style={{ transform: `translate(${gaze.x * 0.5}px, ${gaze.y * 0.4}px)`, transition: 'transform 0.6s ease-out' }}>
            {/* Ears */}
            <ellipse cx={isFemale ? 105 : 102} cy="136" rx="7" ry="13" fill={isFemale ? '#E6B8A2' : '#D8A98E'} />
            <ellipse cx={isFemale ? 195 : 198} cy="136" rx="7" ry="13" fill={isFemale ? '#E6B8A2' : '#D8A98E'} />
            {/* Futuristic Earpiece Glow */}
            <circle cx={isFemale ? 195 : 198} cy="139" r="3" fill={primaryGlow} />

            {/* Face Shape */}
            <path
              d={isFemale
                ? 'M 106 118 C 106 80 194 80 194 118 C 194 156 176 190 150 192 C 124 190 106 156 106 118 Z'
                : 'M 103 114 C 103 76 197 76 197 114 C 197 154 183 182 166 191 L 150 195 L 134 191 C 117 182 103 154 103 114 Z'}
              fill={isFemale ? 'url(#skinToneF)' : 'url(#skinToneM)'}
            />

            {/* Subtle Cheekbone & Holographic Rim Light */}
            <path
              d="M 108 135 Q 112 168 135 184"
              fill="none" stroke={primaryGlow} strokeOpacity="0.28" strokeWidth="2"
            />
            <path
              d="M 192 135 Q 188 168 165 184"
              fill="none" stroke={secondaryGlow} strokeOpacity="0.28" strokeWidth="2"
            />

            {/* Eyebrows */}
            <path
              d={state === 'thinking'
                ? 'M 118 115 Q 129 111 140 116'
                : 'M 118 116 Q 129 112 140 115'}
              fill="none" stroke="#1E293B" strokeWidth={isFemale ? '2.4' : '3.4'} strokeLinecap="round"
            />
            <path
              d={state === 'thinking'
                ? 'M 160 113 Q 171 108 182 114'
                : 'M 160 115 Q 171 112 182 116'}
              fill="none" stroke="#1E293B" strokeWidth={isFemale ? '2.4' : '3.4'} strokeLinecap="round"
            />

            {/* Eyes */}
            {isBlinking || isOffline ? (
              <>
                <path d="M 119 128 Q 129 132 139 128" fill="none" stroke="#1E293B" strokeWidth="2.2" strokeLinecap="round" />
                <path d="M 161 128 Q 171 132 181 128" fill="none" stroke="#1E293B" strokeWidth="2.2" strokeLinecap="round" />
              </>
            ) : (
              <>
                {/* Left Eye */}
                <ellipse cx="129" cy="128" rx="10" ry={isFemale ? 6.2 : 5.4} fill="#F8FAFC" />
                <circle cx={129 + gaze.x} cy={128 + gaze.y} r={isFemale ? 4.6 : 4.2} fill={isFemale ? '#0E7490' : '#1D4ED8'} />
                <circle cx={129 + gaze.x} cy={128 + gaze.y} r="2.2" fill="#050B16" />
                <circle cx={130.5 + gaze.x} cy={126.5 + gaze.y} r="1.2" fill="#FFFFFF" />
                <path d="M 118 126 Q 129 120 140 126" fill="none" stroke="#0F172A" strokeWidth={isFemale ? '2.2' : '1.8'} strokeLinecap="round" />

                {/* Right Eye */}
                <ellipse cx="171" cy="128" rx="10" ry={isFemale ? 6.2 : 5.4} fill="#F8FAFC" />
                <circle cx={171 + gaze.x} cy={128 + gaze.y} r={isFemale ? 4.6 : 4.2} fill={isFemale ? '#0E7490' : '#1D4ED8'} />
                <circle cx={171 + gaze.x} cy={128 + gaze.y} r="2.2" fill="#050B16" />
                <circle cx={172.5 + gaze.x} cy={126.5 + gaze.y} r="1.2" fill="#FFFFFF" />
                <path d="M 160 126 Q 171 120 182 126" fill="none" stroke="#0F172A" strokeWidth={isFemale ? '2.2' : '1.8'} strokeLinecap="round" />
              </>
            )}

            {/* Nose */}
            <path d="M 150 132 L 147 148 Q 150 151 154 148" fill="none" stroke="#B5836B" strokeWidth="1.8" strokeLinecap="round" />

            {/* Mouth */}
            <path
              d={getMouthPath()}
              fill={isOpenMouth ? '#5B1F2E' : 'none'}
              stroke={isFemale ? '#B85D6E' : '#9E6254'}
              strokeWidth={isOpenMouth ? '1.8' : '2.4'}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {isOpenMouth && mouthShape === 'wide' && (
              <path d="M 142 162 L 158 162" stroke="#F8FAFC" strokeWidth="2.2" strokeLinecap="round" />
            )}

            {/* Front Hair */}
            {isFemale ? (
              <path
                d="M 101 124 C 98 86 122 68 152 68 C 182 68 202 88 199 124 C 192 104 178 92 154 90 C 130 92 114 104 101 124 Z"
                fill="url(#hairF)"
              />
            ) : (
              <path
                d="M 100 116 C 98 82 120 66 150 66 C 180 66 202 82 200 116 C 194 98 182 88 164 87 C 142 84 114 96 100 116 Z"
                fill="url(#hairM)"
              />
            )}
            {/* Subtle Cyan Hair Highlight */}
            <path
              d="M 124 76 Q 150 70 176 78"
              fill="none" stroke={primaryGlow} strokeOpacity="0.4" strokeWidth="1.5" strokeLinecap="round"
            />
          </g>
        </g>
      </svg>

      {/* State Badge Overlay */}
      <div
        className="absolute bottom-1 z-20 px-3 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase border backdrop-blur-md flex items-center gap-1.5"
        style={{
          backgroundColor: 'rgba(5, 11, 22, 0.85)',
          borderColor: state === 'speaking' ? accentColor : state === 'listening' ? '#25E6A2' : 'rgba(148,163,184,0.3)',
          color: state === 'offline' ? '#94A3B8' : '#F0F8FF'
        }}
      >
        <span
          className={`w-2 h-2 rounded-full ${state !== 'offline' && !reducedMotion ? 'animate-pulse' : ''}`}
          style={{
            backgroundColor:
              state === 'speaking' ? accentColor :
              state === 'listening' ? '#25E6A2' :
              state === 'thinking' ? '#9868FF' :
              state === 'happy' ? '#FBBF24' :
              state === 'offline' ? '#64748B' : '#38BDF8'
          }}
        />
        {isFemale ? 'ARIA' : 'ATLAS'} • {state}
      </div>
    </div>
  );
}

// ============================================================================
// DYNAMIC AUDIO WAVEFORM
// ============================================================================
function AudioWaveform({ active, mode, accentColor, reducedMotion }) {
  const bars = 24;
  return (
    <div className="flex items-center justify-center gap-1 h-10 px-4">
      {Array.from({ length: bars }).map((_, i) => {
        const centerDist = Math.abs(i - bars / 2) / (bars / 2);
        const baseH = active ? Math.max(20, (1 - centerDist * 0.7) * 95) : 14;
        const delay = (i * 0.06).toFixed(2);
        return (
          <div
            key={i}
            className="w-1 rounded-full transition-all duration-150"
            style={{
              height: `${active && !reducedMotion ? baseH : active ? 48 : 14}%`,
              backgroundColor: mode === 'listening' ? '#25E6A2' : accentColor,
              opacity: active ? 0.9 : 0.25,
              animation: active && !reducedMotion ? `jarvisWave 0.65s ease-in-out ${delay}s infinite alternate` : 'none'
            }}
          />
        );
      })}
    </div>
  );
}

// ============================================================================
// MINI SVG SPARKLINE CHART
// ============================================================================
function Sparkline({ data, color }) {
  const max = Math.max(...data, 100);
  const min = Math.min(...data, 0);
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * 120;
    const y = 32 - ((v - min) / (max - min || 1)) * 28;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 120 34" className="w-full h-9 overflow-visible">
      <polyline fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  );
}

// ============================================================================
// MAIN APPLICATION
// ============================================================================
export default function App() {
  // Persisted Settings
  const loadSetting = (key, fallback) => {
    try {
      const saved = localStorage.getItem(`jarvis_os_${key}`);
      return saved !== null ? JSON.parse(saved) : fallback;
    } catch {
      return fallback;
    }
  };

  const [avatarType, setAvatarType] = useState(() => loadSetting('avatar', 'female'));
  const [themeId, setThemeId] = useState(() => loadSetting('theme', 'dark'));
  const [accentColor, setAccentColor] = useState(() => loadSetting('accent', '#00D9FF'));
  const [voiceSpeed, setVoiceSpeed] = useState(() => loadSetting('voiceSpeed', 1.05));
  const [soundEnabled, setSoundEnabled] = useState(() => loadSetting('soundEnabled', true));
  const [reducedMotion, setReducedMotion] = useState(() => loadSetting('reducedMotion', false));
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => loadSetting('sidebarCollapsed', false));
  const [animationIntensity, setAnimationIntensity] = useState(() => loadSetting('animationIntensity', 'high'));
  const [selectedVoiceURI, setSelectedVoiceURI] = useState(() => loadSetting('voiceURI', ''));

  useEffect(() => {
    try {
      localStorage.setItem('jarvis_os_avatar', JSON.stringify(avatarType));
      localStorage.setItem('jarvis_os_theme', JSON.stringify(themeId));
      localStorage.setItem('jarvis_os_accent', JSON.stringify(accentColor));
      localStorage.setItem('jarvis_os_voiceSpeed', JSON.stringify(voiceSpeed));
      localStorage.setItem('jarvis_os_soundEnabled', JSON.stringify(soundEnabled));
      localStorage.setItem('jarvis_os_reducedMotion', JSON.stringify(reducedMotion));
      localStorage.setItem('jarvis_os_sidebarCollapsed', JSON.stringify(sidebarCollapsed));
      localStorage.setItem('jarvis_os_animationIntensity', JSON.stringify(animationIntensity));
      localStorage.setItem('jarvis_os_voiceURI', JSON.stringify(selectedVoiceURI));
    } catch { /* ignore storage quota errors */ }
  }, [avatarType, themeId, accentColor, voiceSpeed, soundEnabled, reducedMotion, sidebarCollapsed, animationIntensity, selectedVoiceURI]);

  const theme = THEMES[themeId] || THEMES.dark;

  // Boot Sequence State
  const [booted, setBooted] = useState(false);
  const [bootProgress, setBootProgress] = useState(0);

  useEffect(() => {
    if (booted) return;
    const timer = setInterval(() => {
      setBootProgress((p) => (p >= 100 ? 100 : p + 8));
    }, 110);
    return () => clearInterval(timer);
  }, [booted]);

  // Navigation & Modals
  const [activePage, setActivePage] = useState('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [cmdQuery, setCmdQuery] = useState('');
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 'n-1', title: 'Antigravity Agent (Demo)', desc: 'Responsive viewport checks at 48% completion.', time: 'Just now', type: 'info' },
    { id: 'n-2', title: 'Automation Triggered (Demo)', desc: 'Morning Briefing digest completed.', time: '14m ago', type: 'success' },
    { id: 'n-3', title: 'Task Warning (Demo)', desc: 'Organize project assets encountered a simulated error.', time: '28m ago', type: 'warning' }
  ]);

  // Clock
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // Global Ctrl+K / Cmd+K
  useEffect(() => {
    const onKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCmdOpen((v) => !v);
      } else if (e.key === 'Escape') {
        setCmdOpen(false);
        setNotifOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // ============================================================================
  // AVATAR & SPEECH SYNTHESIS ENGINE
  // ============================================================================
  const [avatarState, setAvatarState] = useState('idle');
  const [mouthShape, setMouthShape] = useState('closed');
  const [subtitle, setSubtitle] = useState('Ready. Click "Speak Demo" or send a message to test voice synthesis.');
  const [voices, setVoices] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const mouthIntervalRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const loadVoices = () => {
      const list = window.speechSynthesis.getVoices();
      setVoices(list);
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const stopSpeech = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (mouthIntervalRef.current) {
      clearInterval(mouthIntervalRef.current);
      mouthIntervalRef.current = null;
    }
    setMouthShape('closed');
    setAvatarState('idle');
  }, []);

  const speakText = useCallback((text) => {
    stopSpeech();
    setSubtitle(text);
    setAvatarState('speaking');

    const shapes = ['small', 'mid', 'wide', 'mid', 'small', 'closed'];
    let idx = 0;

    const startCadence = () => {
      if (mouthIntervalRef.current) clearInterval(mouthIntervalRef.current);
      mouthIntervalRef.current = setInterval(() => {
        idx = (idx + 1) % shapes.length;
        setMouthShape(shapes[idx]);
      }, 115);
    };

    if (soundEnabled && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = voiceSpeed;
      utter.pitch = avatarType === 'female' ? 1.08 : 0.92;

      if (selectedVoiceURI) {
        const chosen = voices.find((v) => v.voiceURI === selectedVoiceURI);
        if (chosen) utter.voice = chosen;
      } else if (voices.length > 0) {
        const engVoices = voices.filter((v) => v.lang.startsWith('en'));
        const preferred = engVoices.find((v) =>
          avatarType === 'female'
            ? /female|samantha|zira|google us english|victoria|aria/i.test(v.name)
            : /male|daniel|david|alex|google uk english male|guy/i.test(v.name)
        ) || engVoices[0];
        if (preferred) utter.voice = preferred;
      }

      utter.onstart = () => startCadence();
      utter.onboundary = () => {
        setMouthShape(shapes[Math.floor(Math.random() * 4)]);
      };
      utter.onend = () => {
        if (mouthIntervalRef.current) clearInterval(mouthIntervalRef.current);
        setMouthShape('closed');
        setAvatarState('idle');
      };
      utter.onerror = () => {
        if (mouthIntervalRef.current) clearInterval(mouthIntervalRef.current);
        setMouthShape('closed');
        setAvatarState('idle');
      };
      window.speechSynthesis.speak(utter);
    } else {
      // Timed visual speaking fallback when sound is muted or SpeechSynthesis unavailable
      startCadence();
      const duration = Math.min(8000, Math.max(2200, text.length * 52));
      setTimeout(() => {
        if (mouthIntervalRef.current) clearInterval(mouthIntervalRef.current);
        setMouthShape('closed');
        setAvatarState('idle');
      }, duration);
    }
  }, [soundEnabled, voiceSpeed, avatarType, selectedVoiceURI, voices, stopSpeech]);

  // ============================================================================
  // CHAT & VOICE INPUT
  // ============================================================================
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const generateSimulatedReply = (prompt) => {
    const p = prompt.toLowerCase();
    if (p.includes('status') || p.includes('briefing')) {
      return 'Simulated Status Briefing: 4 of 8 demo agents are actively running, simulated CPU load is nominal at 34%, and all UI modules are operational. No live backend is connected.';
    }
    if (p.includes('agent')) {
      return 'Simulated Agent Report: JARVIS Main Orchestrator is at 84%, OpenAI Codex Agent is refactoring TypeScript tests at 62%, and Antigravity Agent is validating responsive layouts.';
    }
    if (p.includes('robot') || p.includes('hardware')) {
      return 'Robot Simulation Mode: Virtual Raspberry Pi 5 and ESP32-S3 telemetry are nominal. Battery is at 86% simulated charge. Emergency Stop is armed and ready.';
    }
    if (p.includes('lip') || p.includes('avatar') || p.includes('voice')) {
      return 'My avatar uses a layered SVG digital human pipeline synchronized to the browser SpeechSynthesis API via boundary events and syllable cadence timing.';
    }
    return `Simulated JARVIS Response: I received "${prompt}". In this standalone frontend prototype, replies and actions are simulated locally so you can evaluate the UI, voice synthesis, and multi-agent workflows.`;
  };

  const handleSendMessage = useCallback((overrideText) => {
    const text = (overrideText ?? chatInput).trim();
    if (!text) return;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, sender: 'user', text, time: timeStr }]);
    if (!overrideText) setChatInput('');
    setIsTyping(true);
    setAvatarState('thinking');

    setTimeout(() => {
      const reply = generateSimulatedReply(text);
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { id: `j-${Date.now()}`, sender: 'jarvis', text: reply, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), source: 'Simulated AI Engine' }
      ]);
      speakText(reply);
    }, 850);
  }, [chatInput, speakText]);

  const toggleMicrophone = () => {
    if (isListening) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsListening(false);
      setAvatarState('idle');
      return;
    }
    const SpeechRec = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);
    if (SpeechRec) {
      try {
        const rec = new SpeechRec();
        rec.lang = 'en-US';
        rec.interimResults = false;
        rec.onstart = () => {
          setIsListening(true);
          setAvatarState('listening');
          setSubtitle('Listening via browser microphone...');
        };
        rec.onresult = (e) => {
          const transcript = e.results[0][0].transcript;
          setIsListening(false);
          handleSendMessage(transcript);
        };
        rec.onerror = () => {
          setIsListening(false);
          setAvatarState('idle');
          setSubtitle('Microphone unavailable or permission denied. Running simulated voice command instead.');
        };
        rec.onend = () => setIsListening(false);
        recognitionRef.current = rec;
        rec.start();
        return;
      } catch { /* fallback below */ }
    }
    // Graceful simulated voice input fallback
    setIsListening(true);
    setAvatarState('listening');
    setSubtitle('Listening (Simulated Voice Input)...');
    setTimeout(() => {
      setIsListening(false);
      handleSendMessage('Give me a full system status briefing');
    }, 1800);
  };

  // ============================================================================
  // AGENTS, TASKS, AUTOMATIONS STATE
  // ============================================================================
  const [agents, setAgents] = useState(INITIAL_AGENTS);
  const [selectedAgentLogs, setSelectedAgentLogs] = useState(null);
  const [assignModalAgent, setAssignModalAgent] = useState(null);
  const [assignTaskText, setAssignTaskText] = useState('');

  // Smooth simulated agent progress ticker
  useEffect(() => {
    const iv = setInterval(() => {
      setAgents((prev) =>
        prev.map((a) => {
          if (a.status !== 'Running') return a;
          const next = a.progress >= 100 ? 100 : Math.min(100, a.progress + 2);
          return { ...a, progress: next, status: next === 100 ? 'Idle' : 'Running' };
        })
      );
    }, 2400);
    return () => clearInterval(iv);
  }, []);

  const updateAgentStatus = (id, status) => {
    setAgents((prev) =>
      prev.map((a) =>
        a.id === id
          ? {
              ...a,
              status,
              progress: status === 'Running' && a.progress === 100 ? 10 : a.progress,
              logs: [...a.logs, `[${new Date().toLocaleTimeString()}] Status changed to ${status} (Simulated)`]
            }
          : a
      )
    );
  };

  const handleAssignAgentTask = (e) => {
    e.preventDefault();
    if (!assignModalAgent || !assignTaskText.trim()) return;
    setAgents((prev) =>
      prev.map((a) =>
        a.id === assignModalAgent.id
          ? {
              ...a,
              status: 'Running',
              progress: 5,
              activity: assignTaskText.trim(),
              logs: [...a.logs, `[${new Date().toLocaleTimeString()}] Assigned demo task: ${assignTaskText.trim()}`]
            }
          : a
      )
    );
    setAssignTaskText('');
    setAssignModalAgent(null);
  };

  // Tasks
  const [tasks, setTasks] = useState(INITIAL_TASKS);
  const [taskFilter, setTaskFilter] = useState('All');
  const [newTaskTitle, setNewTaskTitle] = useState('');

  const addTask = (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;
    setTasks((prev) => [
      { id: `t-${Date.now()}`, title: newTaskTitle.trim(), agent: 'JARVIS Main Orchestrator', status: 'Queued', progress: 0, priority: 'Medium' },
      ...prev
    ]);
    setNewTaskTitle('');
  };

  // Automations
  const [automations, setAutomations] = useState(INITIAL_AUTOMATIONS);
  const [newAutoName, setNewAutoName] = useState('');
  const [newAutoTrigger, setNewAutoTrigger] = useState('On Schedule (Simulated)');
  const [newAutoAction, setNewAutoAction] = useState('Notify & Speak Summary');

  const addAutomation = (e) => {
    e.preventDefault();
    if (!newAutoName.trim()) return;
    setAutomations((prev) => [
      { id: `auto-${Date.now()}`, name: newAutoName.trim(), trigger: newAutoTrigger, action: newAutoAction, enabled: true, runs: 0 },
      ...prev
    ]);
    setNewAutoName('');
  };

  // Developer Workspace & Terminal
  const [selectedFile, setSelectedFile] = useState('src/jarvis/orchestrator.ts');
  const [terminalLines, setTerminalLines] = useState([
    'JARVIS OS Simulated Terminal v2.4 — Local Demo Environment (No host shell access)',
    'Type "help" to see available simulated commands.'
  ]);
  const [termInput, setTermInput] = useState('');

  const runTerminalCommand = (e) => {
    e.preventDefault();
    const cmd = termInput.trim();
    if (!cmd) return;
    const lower = cmd.toLowerCase();
    let out = [];
    if (lower === 'clear') {
      setTerminalLines(['Terminal cleared (Simulated).']);
      setTermInput('');
      return;
    } else if (lower === 'help') {
      out = ['Available simulated commands: help, status, agents, test, ls, neofetch, clear'];
    } else if (lower === 'status') {
      out = ['[SIMULATED] JARVIS Core: ONLINE | Voice Engine: READY | Backend: DEMO MODE'];
    } else if (lower === 'agents') {
      out = agents.map((a) => `  • ${a.name.padEnd(26)} [${a.status}] ${a.progress}%`);
    } else if (lower === 'test') {
      out = ['Running simulated test suite...', '  ✓ Avatar state machine (6/6 passed)', '  ✓ Responsive layout checks (4/4 passed)', '  ✓ Robot E-STOP safety gate (2/2 passed)', 'All 12 simulated tests passed.'];
    } else if (lower === 'ls') {
      out = Object.keys(DEMO_FILES);
    } else if (lower === 'neofetch') {
      out = [
        '   _  _   ___  _   _ ___ ___    OS: JARVIS OS (Frontend Prototype)',
        '  | || | / _ \\| | | |_ _/ __|   Theme: ' + theme.name,
        '  | || || (_) | |_| || |\\__ \\   Avatar: ' + (avatarType === 'female' ? 'ARIA' : 'ATLAS'),
        '   \\__/  \\___/ \\___/|___|___/   Mode: Simulated Demo'
      ];
    } else {
      out = [`Simulated shell: command "${cmd}" not found. Type "help".`];
    }
    setTerminalLines((prev) => [...prev, `jarvis@sim:~$ ${cmd}`, ...out]);
    setTermInput('');
  };

  // Telemetry (Smoothly updating simulated metrics)
  const [telemetry, setTelemetry] = useState({
    cpu: [28, 32, 30, 35, 34, 36, 33],
    ram: [54, 55, 56, 55, 57, 56, 56],
    gpu: [18, 22, 25, 21, 24, 26, 23],
    disk: 62,
    net: [12, 18, 15, 22, 19, 16, 20],
    temp: 52,
    battery: 88
  });

  useEffect(() => {
    const iv = setInterval(() => {
      setTelemetry((prev) => {
        const nextVal = (arr, min, max, step) => {
          const last = arr[arr.length - 1];
          const delta = (Math.random() - 0.5) * step;
          return [...arr.slice(1), Math.round(Math.max(min, Math.min(max, last + delta)))];
        };
        return {
          ...prev,
          cpu: nextVal(prev.cpu, 15, 78, 8),
          ram: nextVal(prev.ram, 45, 72, 3),
          gpu: nextVal(prev.gpu, 10, 68, 9),
          net: nextVal(prev.net, 5, 60, 10),
          temp: Math.round(Math.max(44, Math.min(68, prev.temp + (Math.random() - 0.5) * 2)))
        };
      });
    }, 2800);
    return () => clearInterval(iv);
  }, []);

  // Robot Control (Explicitly Simulation Mode)
  const [robotEStop, setRobotEStop] = useState(false);
  const [robotMotion, setRobotMotion] = useState('STOPPED');
  const [robotLogs, setRobotLogs] = useState([
    '[SIM] Raspberry Pi 5 virtual node initialized',
    '[SIM] ESP32-S3 motor controller in SIMULATION MODE'
  ]);

  const sendRobotCmd = (cmd) => {
    if (robotEStop) {
      setRobotLogs((prev) => [`[BLOCKED] Clear EMERGENCY STOP before issuing "${cmd}"`, ...prev.slice(0, 7)]);
      return;
    }
    setRobotMotion(cmd);
    setRobotLogs((prev) => [`[SIM] Issued movement command: ${cmd}`, ...prev.slice(0, 7)]);
  };

  const triggerEStop = () => {
    setRobotEStop(true);
    setRobotMotion('EMERGENCY STOPPED');
    setRobotLogs((prev) => ['[E-STOP] EMERGENCY STOP ACTIVATED — All simulated motors halted.', ...prev.slice(0, 7)]);
  };

  // Calendar, Memory, Knowledge, Integrations
  const [events, setEvents] = useState(INITIAL_EVENTS);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventTime, setNewEventTime] = useState('03:00 PM');
  const [memorySearch, setMemorySearch] = useState('');
  const [kbSearch, setKbSearch] = useState('');
  const [selectedIntegration, setSelectedIntegration] = useState(null);

  // Command Palette Filtered Results
  const cmdResults = useMemo(() => {
    const q = cmdQuery.toLowerCase();
    const pages = NAV_ITEMS.filter((n) => n.label.toLowerCase().includes(q)).map((n) => ({
      type: 'Page', label: `Open ${n.label}`, action: () => { setActivePage(n.id); setCmdOpen(false); }
    }));
    const actions = [
      { type: 'Action', label: 'Switch Avatar (ARIA / ATLAS)', action: () => { setAvatarType((v) => v === 'female' ? 'male' : 'female'); setCmdOpen(false); } },
      { type: 'Action', label: 'Speak Demo Greeting', action: () => { speakText("Hello. I'm JARVIS, your personal AI assistant. All demonstration systems are ready."); setCmdOpen(false); } },
      { type: 'Action', label: 'Trigger Robot Emergency Stop (Sim)', action: () => { triggerEStop(); setActivePage('robot'); setCmdOpen(false); } }
    ].filter((a) => a.label.toLowerCase().includes(q));
    return [...actions, ...pages].slice(0, 8);
  }, [cmdQuery, speakText]);

  // ============================================================================
  // CINEMATIC BOOT SCREEN
  // ============================================================================
  if (!booted) {
    const checks = [
      { label: 'Neural UI Shell & Glassmorphism Engine', done: bootProgress >= 25 },
      { label: 'Holographic Human-Like Avatar Pipeline', done: bootProgress >= 55 },
      { label: 'Web Speech Synthesis & Audio Waveform', done: bootProgress >= 80 },
      { label: 'Simulated Telemetry & Multi-Agent Bus', done: bootProgress >= 100 }
    ];
    return (
      <div
        className="min-h-screen w-full flex items-center justify-center p-6 text-slate-100 relative overflow-hidden"
        style={{ backgroundColor: theme.bg, backgroundImage: theme.gradient }}
      >
        <div className="max-w-lg w-full rounded-2xl p-8 border backdrop-blur-xl shadow-2xl relative z-10" style={{ backgroundColor: theme.cardBg, borderColor: theme.border }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center border" style={{ borderColor: accentColor, backgroundColor: 'rgba(0,217,255,0.12)' }}>
              <Sparkles className="w-6 h-6" style={{ color: accentColor }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-wider" style={{ color: theme.textPrimary }}>JARVIS OS</h1>
              <p className="text-xs uppercase tracking-widest" style={{ color: accentColor }}>Initializing Futuristic AI Interface</p>
            </div>
          </div>

          <div className="space-y-3 mb-6">
            {checks.map((c, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span style={{ color: c.done ? theme.textPrimary : theme.textSecondary }}>{c.label}</span>
                {c.done ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />}
              </div>
            ))}
          </div>

          <div className="w-full h-2 rounded-full bg-slate-800/80 overflow-hidden mb-6">
            <div className="h-full transition-all duration-150 rounded-full" style={{ width: `${bootProgress}%`, backgroundColor: accentColor }} />
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => {
                setBooted(true);
                setTimeout(() => speakText("Hello. I'm JARVIS, your personal AI assistant. All demonstration systems are ready. How may I assist you today?"), 250);
              }}
              className="flex-1 py-2.5 px-4 rounded-xl font-semibold text-sm text-slate-950 flex items-center justify-center gap-2 transition hover:brightness-110"
              style={{ backgroundColor: accentColor }}
            >
              <Volume2 className="w-4 h-4" />
              Launch with Voice Greeting
            </button>
            <button
              onClick={() => setBooted(true)}
              className="py-2.5 px-4 rounded-xl font-medium text-sm border transition hover:bg-white/5"
              style={{ borderColor: theme.border, color: theme.textSecondary }}
            >
              Skip Boot
            </button>
          </div>
          <p className="text-[11px] text-center mt-4 opacity-70" style={{ color: theme.textSecondary }}>
            Standalone Interactive Frontend Prototype • All telemetry & agent runs are simulated
          </p>
        </div>
      </div>
    );
  }

  // ============================================================================
  // SHARED CARD WRAPPER
  // ============================================================================
  const cardStyle = {
    backgroundColor: theme.cardBg,
    borderColor: theme.border
  };

  // ============================================================================
  // PAGE RENDERER
  // ============================================================================
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return (
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
            {/* CENTER HERO: AVATAR & VOICE */}
            <div className="xl:col-span-7 flex flex-col gap-5">
              <div className="rounded-2xl border p-5 sm:p-6 backdrop-blur-xl relative overflow-hidden" style={cardStyle}>
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight flex items-center gap-2" style={{ color: theme.textPrimary }}>
                      JARVIS
                      <span className="text-xs font-medium px-2.5 py-0.5 rounded-full border" style={{ borderColor: accentColor, color: accentColor }}>
                        AI Assistant / Agent / OS
                      </span>
                    </h1>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {[
                        { label: 'Voice Active', color: '#25E6A2' },
                        { label: `${agents.filter((a) => a.status === 'Running').length} Agents Online (Sim)`, color: accentColor },
                        { label: 'Local Models (Demo)', color: '#9868FF' },
                        { label: 'Cloud Sync (Demo)', color: '#218BFF' }
                      ].map((pill, i) => (
                        <span key={i} className="text-[11px] px-2.5 py-0.5 rounded-full bg-slate-900/70 border border-slate-700/60 flex items-center gap-1.5" style={{ color: theme.textSecondary }}>
                          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: pill.color }} />
                          {pill.label}
                        </span>
                      ))}
                    </div>
                  </div>
                  {/* Avatar Switcher */}
                  <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900/80 border border-slate-700/60">
                    <button
                      onClick={() => setAvatarType('female')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${avatarType === 'female' ? 'text-slate-950' : 'text-slate-400 hover:text-white'}`}
                      style={avatarType === 'female' ? { backgroundColor: accentColor } : {}}
                    >
                      ARIA (Female)
                    </button>
                    <button
                      onClick={() => setAvatarType('male')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${avatarType === 'male' ? 'text-slate-950' : 'text-slate-400 hover:text-white'}`}
                      style={avatarType === 'male' ? { backgroundColor: accentColor } : {}}
                    >
                      ATLAS (Male)
                    </button>
                  </div>
                </div>

                {/* Human-Like Avatar Centerpiece */}
                <div className="flex flex-col items-center justify-center my-2">
                  <HumanAIAvatar
                    avatarType={avatarType}
                    state={avatarState}
                    mouthShape={mouthShape}
                    accentColor={accentColor}
                    reducedMotion={reducedMotion}
                  />
                  <div className="w-full max-w-md mt-2">
                    <AudioWaveform
                      active={avatarState === 'speaking' || avatarState === 'listening'}
                      mode={avatarState}
                      accentColor={accentColor}
                      reducedMotion={reducedMotion}
                    />
                  </div>
                  {/* Live Subtitle */}
                  <div className="w-full max-w-xl mt-2 px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center text-sm" style={{ color: theme.textPrimary }}>
                    "{subtitle}"
                  </div>
                </div>

                {/* Voice & State Controls */}
                <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                  <button
                    onClick={toggleMicrophone}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition ${isListening ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800/90 hover:bg-slate-700 text-white border border-slate-700'}`}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    {isListening ? 'Stop Listening' : 'Voice Command'}
                  </button>
                  <button
                    onClick={() => speakText(`Hello. I am ${avatarType === 'female' ? 'ARIA' : 'ATLAS'}, your JARVIS OS interface. All demonstration modules are online and ready for testing.`)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-950 flex items-center gap-2 transition hover:brightness-110"
                    style={{ backgroundColor: accentColor }}
                  >
                    <Volume2 className="w-4 h-4" />
                    Speak Demo
                  </button>
                  {avatarState === 'speaking' && (
                    <button
                      onClick={stopSpeech}
                      className="px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5"
                    >
                      <Square className="w-3.5 h-3.5" /> Stop
                    </button>
                  )}
                </div>

                {/* Interactive State Tester */}
                <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-center gap-1.5">
                  <span className="text-[11px] uppercase tracking-wider mr-2" style={{ color: theme.textSecondary }}>Test Avatar State:</span>
                  {['idle', 'listening', 'thinking', 'speaking', 'happy', 'offline'].map((st) => (
                    <button
                      key={st}
                      onClick={() => {
                        if (st === 'speaking') {
                          speakText('Testing synchronized speaking animation and audio waveform.');
                        } else {
                          stopSpeech();
                          setAvatarState(st);
                        }
                      }}
                      className={`px-2.5 py-1 rounded-lg text-[11px] capitalize border transition ${avatarState === st ? 'font-semibold text-slate-950' : 'text-slate-300 hover:bg-white/5 border-slate-700/70'}`}
                      style={avatarState === st ? { backgroundColor: accentColor, borderColor: accentColor } : {}}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Telemetry Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'CPU (Sim)', val: `${telemetry.cpu[telemetry.cpu.length - 1]}%`, data: telemetry.cpu, color: accentColor },
                  { label: 'RAM (Sim)', val: `${telemetry.ram[telemetry.ram.length - 1]}%`, data: telemetry.ram, color: '#218BFF' },
                  { label: 'GPU (Sim)', val: `${telemetry.gpu[telemetry.gpu.length - 1]}%`, data: telemetry.gpu, color: '#9868FF' },
                  { label: 'Temp (Sim)', val: `${telemetry.temp}°C`, data: telemetry.net, color: '#25E6A2' }
                ].map((m, i) => (
                  <div key={i} onClick={() => setActivePage('devices')} className="rounded-xl border p-3.5 cursor-pointer transition hover:border-cyan-400/50" style={cardStyle}>
                    <div className="flex items-center justify-between text-xs mb-1" style={{ color: theme.textSecondary }}>
                      <span>{m.label}</span>
                      <span className="font-bold text-sm" style={{ color: theme.textPrimary }}>{m.val}</span>
                    </div>
                    <Sparkline data={m.data} color={m.color} />
                  </div>
                ))}
              </div>
            </div>

            {/* RIGHT COLUMN: LIVE CHAT & ACTIVE AGENTS */}
            <div className="xl:col-span-5 flex flex-col gap-5">
              {/* Compact Live Chat */}
              <div className="rounded-2xl border p-4 backdrop-blur-xl flex flex-col h-[380px]" style={cardStyle}>
                <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" style={{ color: accentColor }} />
                    <h2 className="font-semibold text-sm">Live Conversation</h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Simulated AI</span>
                  </div>
                  <button onClick={() => setActivePage('chat')} className="text-xs hover:underline" style={{ color: accentColor }}>Expand</button>
                </div>

                <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1">
                  {messages.slice(-5).map((m) => (
                    <div key={m.id} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                      <div
                        className={`max-w-[88%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${m.sender === 'user' ? 'text-slate-950 font-medium' : 'bg-slate-900/80 border border-slate-700/70'}`}
                        style={m.sender === 'user' ? { backgroundColor: accentColor } : { color: theme.textPrimary }}
                      >
                        {m.text}
                      </div>
                      <span className="text-[10px] mt-1 opacity-60">{m.time}</span>
                    </div>
                  ))}
                  {isTyping && <div className="text-xs text-cyan-300 animate-pulse">JARVIS is thinking (simulated)...</div>}
                </div>

                <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="pt-2 border-t border-slate-800/80 flex gap-2">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask JARVIS (simulated)..."
                    className="flex-1 bg-slate-950/70 border border-slate-700/70 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-cyan-400"
                  />
                  <button type="submit" className="p-2 rounded-xl text-slate-950" style={{ backgroundColor: accentColor }}>
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>

              {/* Active Agents Summary */}
              <div className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" style={{ color: accentColor }} />
                    <h2 className="font-semibold text-sm">Active Agents (Simulated)</h2>
                  </div>
                  <button onClick={() => setActivePage('agents')} className="text-xs hover:underline" style={{ color: accentColor }}>Manage All</button>
                </div>
                <div className="space-y-2.5">
                  {agents.slice(0, 4).map((ag) => (
                    <div key={ag.id} className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium">{ag.name}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${ag.status === 'Running' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700/60 text-slate-300'}`}>
                          {ag.status} • {ag.progress}%
                        </span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${ag.progress}%`, backgroundColor: accentColor }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'chat':
        return (
          <div className="rounded-2xl border p-5 backdrop-blur-xl flex flex-col h-[calc(100vh-155px)] min-h-[520px]" style={cardStyle}>
            <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-800/80">
              <div>
                <h2 className="text-lg font-bold flex items-center gap-2">
                  AI Conversation Studio
                  <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Simulated AI Responses</span>
                </h2>
                <p className="text-xs" style={{ color: theme.textSecondary }}>Send a message or click a preset prompt to test streaming-style responses and voice playback.</p>
              </div>
              <button
                onClick={() => setMessages(INITIAL_MESSAGES)}
                className="px-3 py-1.5 rounded-lg text-xs border border-slate-700 hover:bg-white/5 flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear Chat
              </button>
            </div>

            {/* Preset Prompts */}
            <div className="flex flex-wrap gap-2 py-3">
              {DEMO_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(p)}
                  className="text-xs px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-700/70 hover:border-cyan-400/60 transition"
                >
                  {p}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 py-2 pr-2">
              {messages.map((m) => (
                <div key={m.id} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${m.sender === 'user' ? 'text-slate-950 font-medium' : 'bg-slate-900/90 border border-slate-700/70'}`}
                    style={m.sender === 'user' ? { backgroundColor: accentColor } : {}}
                  >
                    <p>{m.text}</p>
                    {m.sender === 'jarvis' && (
                      <div className="flex items-center gap-3 mt-2.5 pt-2 border-t border-slate-800 text-[11px] text-slate-400">
                        <span>{m.source}</span>
                        <button onClick={() => speakText(m.text)} className="hover:text-cyan-300 flex items-center gap-1">
                          <Volume2 className="w-3.5 h-3.5" /> Speak
                        </button>
                        <button
                          onClick={() => { navigator.clipboard?.writeText(m.text); setCopiedId(m.id); setTimeout(() => setCopiedId(null), 1500); }}
                          className="hover:text-cyan-300 flex items-center gap-1"
                        >
                          {copiedId === m.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedId === m.id ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                    )}
                  </div>
                  <span className="text-[10px] mt-1 opacity-60">{m.time}</span>
                </div>
              ))}
              {isTyping && <div className="text-xs text-cyan-400 animate-pulse">JARVIS is composing a simulated response...</div>}
            </div>

            <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="pt-3 border-t border-slate-800/80 flex gap-2">
              <button type="button" onClick={toggleMicrophone} className={`p-3 rounded-xl border ${isListening ? 'bg-emerald-500 text-slate-950 border-emerald-400' : 'bg-slate-900 border-slate-700 text-slate-300'}`}>
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Type a message to JARVIS (Demo)..."
                className="flex-1 bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-400"
              />
              <button type="submit" className="px-5 py-2.5 rounded-xl font-semibold text-sm text-slate-950 flex items-center gap-2" style={{ backgroundColor: accentColor }}>
                <Send className="w-4 h-4" /> Send
              </button>
            </form>
          </div>
        );

      case 'voice':
        return (
          <div className="rounded-2xl border p-6 backdrop-blur-xl flex flex-col items-center text-center" style={cardStyle}>
            <span className="text-xs uppercase tracking-widest mb-1" style={{ color: accentColor }}>Voice-First Studio</span>
            <h2 className="text-2xl font-bold mb-4">Real-Time Speech & Avatar Sync</h2>
            <HumanAIAvatar avatarType={avatarType} state={avatarState} mouthShape={mouthShape} accentColor={accentColor} reducedMotion={reducedMotion} size="lg" />
            <div className="w-full max-w-lg my-3">
              <AudioWaveform active={avatarState === 'speaking' || avatarState === 'listening'} mode={avatarState} accentColor={accentColor} reducedMotion={reducedMotion} />
            </div>
            <p className="max-w-xl text-sm px-4 py-3 rounded-xl bg-slate-950/70 border border-slate-800 mb-5">"{subtitle}"</p>

            <div className="flex flex-wrap justify-center gap-3 mb-6">
              <button
                onClick={toggleMicrophone}
                className={`px-6 py-3 rounded-2xl font-semibold text-sm flex items-center gap-2 shadow-lg transition ${isListening ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-white border border-slate-700 hover:border-cyan-400'}`}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                {isListening ? 'Listening... Click to Stop' : 'Start Voice Input'}
              </button>
              <button
                onClick={() => speakText('Voice synthesis calibration complete. Adjusting speech cadence and holographic audio waveform.')}
                className="px-6 py-3 rounded-2xl font-semibold text-sm text-slate-950 flex items-center gap-2"
                style={{ backgroundColor: accentColor }}
              >
                <Volume2 className="w-5 h-5" /> Test Voice Output
              </button>
              <button onClick={stopSpeech} className="px-4 py-3 rounded-2xl text-sm border border-slate-700 hover:bg-white/5">
                Interrupt
              </button>
            </div>

            <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
              {['Give me a morning briefing', 'Check simulated robot battery', 'Summarize active agents', 'Switch to standby mode'].map((cmd, i) => (
                <button key={i} onClick={() => handleSendMessage(cmd)} className="text-xs px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-cyan-400/60">
                  "{cmd}"
                </button>
              ))}
            </div>
          </div>
        );

      case 'agents':
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">AI Agents Control Center</h2>
                <p className="text-xs" style={{ color: theme.textSecondary }}>Simulated multi-agent orchestration — start, pause, assign demo tasks, or inspect execution logs.</p>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Simulated Orchestration</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {agents.map((ag) => (
                <div key={ag.id} className="rounded-2xl border p-4 backdrop-blur-xl flex flex-col justify-between" style={cardStyle}>
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-700 flex items-center justify-center">
                        <Cpu className="w-4 h-4" style={{ color: accentColor }} />
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        ag.status === 'Running' ? 'bg-emerald-500/20 text-emerald-300' :
                        ag.status === 'Paused' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-700/70 text-slate-300'
                      }`}>
                        {ag.status}
                      </span>
                    </div>
                    <h3 className="font-semibold text-sm">{ag.name}</h3>
                    <p className="text-[11px] mb-2" style={{ color: theme.textSecondary }}>{ag.model}</p>
                    <p className="text-xs text-slate-300 mb-3 min-h-[32px]">{ag.activity}</p>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden mb-1">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${ag.progress}%`, backgroundColor: accentColor }} />
                    </div>
                    <div className="text-[10px] text-right mb-3" style={{ color: theme.textSecondary }}>{ag.progress}%</div>
                  </div>

                  <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800/80">
                    {ag.status !== 'Running' ? (
                      <button onClick={() => updateAgentStatus(ag.id, 'Running')} className="flex-1 py-1.5 rounded-lg text-[11px] font-semibold text-slate-950 flex items-center justify-center gap-1" style={{ backgroundColor: accentColor }}>
                        <Play className="w-3 h-3" /> Start
                      </button>
                    ) : (
                      <button onClick={() => updateAgentStatus(ag.id, 'Paused')} className="flex-1 py-1.5 rounded-lg text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center justify-center gap-1">
                        <Pause className="w-3 h-3" /> Pause
                      </button>
                    )}
                    <button onClick={() => setAssignModalAgent(ag)} className="px-2.5 py-1.5 rounded-lg text-[11px] bg-slate-800 hover:bg-slate-700">Assign</button>
                    <button onClick={() => setSelectedAgentLogs(ag)} className="px-2.5 py-1.5 rounded-lg text-[11px] bg-slate-800 hover:bg-slate-700">Logs</button>
                  </div>
                </div>
              ))}
            </div>

            {/* Agent Activity Timeline */}
            <div className="rounded-2xl border p-5 backdrop-blur-xl" style={cardStyle}>
              <h3 className="font-semibold text-sm mb-3">Visual Agent Activity Timeline (Simulated)</h3>
              <div className="space-y-3 border-l-2 border-cyan-500/30 pl-4">
                {agents.slice(0, 4).map((ag) => (
                  <div key={ag.id} className="relative">
                    <span className="w-2.5 h-2.5 rounded-full absolute -left-[21px] top-1" style={{ backgroundColor: accentColor }} />
                    <div className="text-xs font-semibold">{ag.name} — <span className="font-normal text-slate-400">{ag.status}</span></div>
                    <div className="text-xs text-slate-300">{ag.logs[ag.logs.length - 1]}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'tasks':
        const filteredTasks = taskFilter === 'All' ? tasks : tasks.filter((t) => t.status === taskFilter);
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold">Tasks & Execution Queue (Simulated)</h2>
              <div className="flex flex-wrap gap-1.5">
                {['All', 'Queued', 'Running', 'Complete', 'Paused', 'Failed'].map((f) => (
                  <button
                    key={f}
                    onClick={() => setTaskFilter(f)}
                    className={`px-3 py-1 rounded-lg text-xs border transition ${taskFilter === f ? 'text-slate-950 font-semibold' : 'border-slate-700 text-slate-300 hover:bg-white/5'}`}
                    style={taskFilter === f ? { backgroundColor: accentColor, borderColor: accentColor } : {}}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={addTask} className="flex gap-2">
              <input
                value={newTaskTitle}
                onChange={(e) => setNewTaskTitle(e.target.value)}
                placeholder="Add a new simulated task..."
                className="flex-1 bg-slate-950/70 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-400"
              />
              <button type="submit" className="px-4 py-2.5 rounded-xl font-semibold text-sm text-slate-950 flex items-center gap-1.5" style={{ backgroundColor: accentColor }}>
                <Plus className="w-4 h-4" /> Add Task
              </button>
            </form>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTasks.map((t) => (
                <div key={t.id} className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="font-semibold text-sm">{t.title}</h3>
                      <p className="text-xs" style={{ color: theme.textSecondary }}>Assigned: {t.agent} • Priority: {t.priority}</p>
                    </div>
                    <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full ${
                      t.status === 'Complete' ? 'bg-emerald-500/20 text-emerald-300' :
                      t.status === 'Running' ? 'bg-cyan-500/20 text-cyan-300' :
                      t.status === 'Failed' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-700/70 text-slate-300'
                    }`}>
                      {t.status}
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden mb-3">
                    <div className="h-full rounded-full" style={{ width: `${t.progress}%`, backgroundColor: t.status === 'Failed' ? '#FB7185' : accentColor }} />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setTasks((prev) => prev.map((x) => x.id === t.id ? { ...x, status: x.status === 'Running' ? 'Paused' : 'Running', progress: x.progress === 0 ? 25 : x.progress } : x))}
                      className="px-3 py-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700"
                    >
                      {t.status === 'Running' ? 'Pause' : 'Start Demo'}
                    </button>
                    <button
                      onClick={() => setTasks((prev) => prev.map((x) => x.id === t.id ? { ...x, status: 'Complete', progress: 100 } : x))}
                      className="px-3 py-1.5 rounded-lg text-xs bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30"
                    >
                      Mark Complete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'automation':
        return (
          <div className="space-y-5">
            <h2 className="text-xl font-bold">Workflow Automations (Simulated)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {automations.map((a) => (
                <div key={a.id} className="rounded-2xl border p-4 backdrop-blur-xl flex items-center justify-between gap-4" style={cardStyle}>
                  <div>
                    <h3 className="font-semibold text-sm">{a.name}</h3>
                    <p className="text-xs mt-1" style={{ color: theme.textSecondary }}>Trigger: <span className="text-slate-200">{a.trigger}</span></p>
                    <p className="text-xs" style={{ color: theme.textSecondary }}>Action: <span className="text-slate-200">{a.action}</span></p>
                    <span className="text-[10px] text-cyan-400 mt-1 inline-block">Simulated runs: {a.runs}</span>
                  </div>
                  <button
                    onClick={() => setAutomations((prev) => prev.map((x) => x.id === a.id ? { ...x, enabled: !x.enabled } : x))}
                    className={`w-12 h-6 rounded-full p-1 transition ${a.enabled ? '' : 'bg-slate-700'}`}
                    style={a.enabled ? { backgroundColor: accentColor } : {}}
                  >
                    <div className={`w-4 h-4 rounded-full bg-white transition-transform ${a.enabled ? 'translate-x-6' : 'translate-x-0'}`} />
                  </button>
                </div>
              ))}
            </div>

            <form onSubmit={addAutomation} className="rounded-2xl border p-5 backdrop-blur-xl space-y-3" style={cardStyle}>
              <h3 className="font-semibold text-sm">Simple Workflow Builder (Demo)</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input value={newAutoName} onChange={(e) => setNewAutoName(e.target.value)} placeholder="Workflow Name" className="bg-slate-950/70 border border-slate-700 rounded-xl px-3 py-2 text-xs" />
                <input value={newAutoTrigger} onChange={(e) => setNewAutoTrigger(e.target.value)} placeholder="Trigger" className="bg-slate-950/70 border border-slate-700 rounded-xl px-3 py-2 text-xs" />
                <input value={newAutoAction} onChange={(e) => setNewAutoAction(e.target.value)} placeholder="Action" className="bg-slate-950/70 border border-slate-700 rounded-xl px-3 py-2 text-xs" />
              </div>
              <button type="submit" className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-950" style={{ backgroundColor: accentColor }}>
                Create Simulated Workflow
              </button>
            </form>
          </div>
        );

      case 'workspace':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-3 rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
              <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: theme.textSecondary }}>Project Explorer (Demo)</h3>
              <div className="space-y-1.5">
                {Object.keys(DEMO_FILES).map((file) => (
                  <button
                    key={file}
                    onClick={() => setSelectedFile(file)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center gap-2 transition ${selectedFile === file ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'hover:bg-white/5 text-slate-300'}`}
                  >
                    <FileCode className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{file}</span>
                  </button>
                ))}
              </div>
              <div className="mt-5 pt-4 border-t border-slate-800 space-y-2 text-xs">
                <div className="flex items-center gap-2 text-emerald-400"><GitBranch className="w-3.5 h-3.5" /> Branch: feat/jarvis-ui-v2</div>
                <div className="text-slate-400">Build: Passing (Simulated)</div>
                <div className="text-slate-400">Tests: 12/12 Passed (Sim)</div>
              </div>
            </div>

            <div className="lg:col-span-9 flex flex-col gap-4">
              <div className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono text-cyan-300">{selectedFile}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">Read-Only Demo Viewer</span>
                </div>
                <pre className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-xs font-mono text-sky-200 overflow-x-auto leading-relaxed">
                  {DEMO_FILES[selectedFile]}
                </pre>
              </div>

              <div className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold flex items-center gap-2"><TerminalIcon className="w-3.5 h-3.5 text-cyan-400" /> Integrated Terminal (Simulated)</span>
                  <button onClick={() => setActivePage('terminal')} className="text-xs text-cyan-400 hover:underline">Full Screen</button>
                </div>
                <div className="bg-slate-950/90 rounded-xl p-3 font-mono text-xs h-36 overflow-y-auto space-y-1 text-emerald-300">
                  {terminalLines.slice(-6).map((l, i) => <div key={i}>{l}</div>)}
                </div>
              </div>
            </div>
          </div>
        );

      case 'terminal':
        return (
          <div className="rounded-2xl border p-5 backdrop-blur-xl flex flex-col h-[calc(100vh-160px)] min-h-[460px]" style={cardStyle}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <TerminalIcon className="w-4 h-4" style={{ color: accentColor }} />
                <h2 className="font-semibold text-sm">JARVIS Simulated Terminal</h2>
              </div>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Simulated — No Host Shell Access</span>
            </div>
            <div className="flex-1 overflow-y-auto py-4 font-mono text-xs space-y-1.5 text-emerald-300">
              {terminalLines.map((line, i) => <div key={i} className="whitespace-pre-wrap">{line}</div>)}
            </div>
            <form onSubmit={runTerminalCommand} className="flex gap-2 pt-3 border-t border-slate-800">
              <span className="font-mono text-xs text-cyan-400 self-center">jarvis@sim:~$</span>
              <input
                value={termInput}
                onChange={(e) => setTermInput(e.target.value)}
                placeholder='Try "help", "status", "agents", "test", "neofetch"...'
                className="flex-1 bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 font-mono text-xs focus:outline-none focus:border-cyan-400"
              />
              <button type="submit" className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-950" style={{ backgroundColor: accentColor }}>Run</button>
            </form>
          </div>
        );

      case 'calendar':
        return (
          <div className="space-y-5">
            <h2 className="text-xl font-bold">Calendar & Reminders (Demo)</h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              <div className="lg:col-span-2 rounded-2xl border p-5 backdrop-blur-xl space-y-3" style={cardStyle}>
                <h3 className="font-semibold text-sm mb-2">Upcoming Schedule</h3>
                {events.map((ev) => (
                  <div key={ev.id} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-sm">{ev.title}</div>
                      <div className="text-xs" style={{ color: theme.textSecondary }}>{ev.day} at {ev.time}</div>
                    </div>
                    <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300">{ev.type}</span>
                  </div>
                ))}
              </div>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!newEventTitle.trim()) return;
                  setEvents((prev) => [{ id: `ev-${Date.now()}`, title: newEventTitle.trim(), day: 'Today', time: newEventTime, type: 'Reminder' }, ...prev]);
                  setNewEventTitle('');
                }}
                className="rounded-2xl border p-5 backdrop-blur-xl space-y-3 h-fit"
                style={cardStyle}
              >
                <h3 className="font-semibold text-sm">Create Demo Event</h3>
                <input value={newEventTitle} onChange={(e) => setNewEventTitle(e.target.value)} placeholder="Event title..." className="w-full bg-slate-950/70 border border-slate-700 rounded-xl px-3 py-2 text-xs" />
                <input value={newEventTime} onChange={(e) => setNewEventTime(e.target.value)} placeholder="Time (e.g. 03:00 PM)" className="w-full bg-slate-950/70 border border-slate-700 rounded-xl px-3 py-2 text-xs" />
                <button type="submit" className="w-full py-2 rounded-xl text-xs font-semibold text-slate-950" style={{ backgroundColor: accentColor }}>Add to Calendar</button>
              </form>
            </div>
          </div>
        );

      case 'memory':
        const filteredMem = INITIAL_MEMORIES.filter((m) => (m.title + m.content + m.category).toLowerCase().includes(memorySearch.toLowerCase()));
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold">Memory Vault (Demo)</h2>
              <input value={memorySearch} onChange={(e) => setMemorySearch(e.target.value)} placeholder="Search simulated memories..." className="bg-slate-950/70 border border-slate-700 rounded-xl px-3.5 py-2 text-xs w-64" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredMem.map((m) => (
                <div key={m.id} className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                  <div className="flex items-center justify-between text-[11px] mb-1.5">
                    <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">{m.category}</span>
                    <span style={{ color: theme.textSecondary }}>{m.updated}</span>
                  </div>
                  <h3 className="font-semibold text-sm mb-1">{m.title}</h3>
                  <p className="text-xs leading-relaxed" style={{ color: theme.textSecondary }}>{m.content}</p>
                </div>
              ))}
            </div>
          </div>
        );

      case 'knowledge':
        const filteredKb = INITIAL_KB.filter((k) => (k.title + k.summary + k.category).toLowerCase().includes(kbSearch.toLowerCase()));
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold">Indexed Knowledge Base (Demo)</h2>
              <input value={kbSearch} onChange={(e) => setKbSearch(e.target.value)} placeholder="Search articles..." className="bg-slate-950/70 border border-slate-700 rounded-xl px-3.5 py-2 text-xs w-64" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredKb.map((k) => (
                <div key={k.id} className="rounded-2xl border p-5 backdrop-blur-xl" style={cardStyle}>
                  <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300">{k.category}</span>
                  <h3 className="font-semibold text-base mt-2 mb-1">{k.title}</h3>
                  <p className="text-xs leading-relaxed mb-3" style={{ color: theme.textSecondary }}>{k.summary}</p>
                  <div className="flex gap-1.5">
                    {k.tags.map((tag) => <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">#{tag}</span>)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'devices':
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-xl font-bold">System Monitoring & Telemetry</h2>
              <span className="text-xs px-3 py-1 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">Simulated Live Metrics</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'CPU Utilization', val: `${telemetry.cpu[telemetry.cpu.length - 1]}%`, data: telemetry.cpu, color: accentColor, icon: Cpu },
                { label: 'Memory (RAM)', val: `${telemetry.ram[telemetry.ram.length - 1]}%`, data: telemetry.ram, color: '#218BFF', icon: Layers },
                { label: 'GPU Compute', val: `${telemetry.gpu[telemetry.gpu.length - 1]}%`, data: telemetry.gpu, color: '#9868FF', icon: Activity },
                { label: 'Network I/O', val: `${telemetry.net[telemetry.net.length - 1]} MB/s`, data: telemetry.net, color: '#25E6A2', icon: Wifi }
              ].map((card, i) => (
                <div key={i} className="rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs" style={{ color: theme.textSecondary }}>{card.label}</span>
                    <card.icon className="w-4 h-4" style={{ color: card.color }} />
                  </div>
                  <div className="text-2xl font-bold mb-2">{card.val}</div>
                  <Sparkline data={card.data} color={card.color} />
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-2xl border p-4" style={cardStyle}>
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-1"><HardDrive className="w-4 h-4 text-cyan-400" /> Disk Usage (Sim)</div>
                <div className="text-xl font-bold">{telemetry.disk}% of 1 TB NVMe</div>
              </div>
              <div className="rounded-2xl border p-4" style={cardStyle}>
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-1"><Thermometer className="w-4 h-4 text-amber-400" /> CPU Temp (Sim)</div>
                <div className="text-xl font-bold">{telemetry.temp}°C — Optimal</div>
              </div>
              <div className="rounded-2xl border p-4" style={cardStyle}>
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-1"><Battery className="w-4 h-4 text-emerald-400" /> Battery (Sim)</div>
                <div className="text-xl font-bold">{telemetry.battery}% • AC Connected</div>
              </div>
            </div>
          </div>
        );

      case 'robot':
        return (
          <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2">
                  JARVIS Robot Control Panel
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">SIMULATION MODE</span>
                </h2>
                <p className="text-xs" style={{ color: theme.textSecondary }}>Virtual Raspberry Pi 5 + ESP32-S3 telemetry & safety-gated movement controls.</p>
              </div>
              <button
                onClick={robotEStop ? () => { setRobotEStop(false); setRobotMotion('STANDBY'); } : triggerEStop}
                className={`px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 shadow-lg transition ${robotEStop ? 'bg-amber-500 text-slate-950' : 'bg-rose-600 hover:bg-rose-500 text-white'}`}
              >
                <ShieldAlert className="w-5 h-5" />
                {robotEStop ? 'RESET E-STOP' : 'EMERGENCY STOP'}
              </button>
            </div>

            {robotEStop && (
              <div className="p-4 rounded-xl bg-rose-500/20 border border-rose-500/50 text-rose-200 text-sm font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                EMERGENCY STOP ACTIVE — All simulated motor outputs are locked. Click "RESET E-STOP" to resume simulation.
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* Simulated Camera HUD */}
              <div className="lg:col-span-7 rounded-2xl border p-4 backdrop-blur-xl" style={cardStyle}>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-semibold">Optical Camera Feed (Simulated Placeholder)</span>
                  <span className="text-emerald-400">60 FPS • SIM HUD</span>
                </div>
                <div className="aspect-video rounded-xl bg-slate-950 border border-cyan-500/30 relative flex items-center justify-center overflow-hidden">
                  <div className="absolute inset-4 border border-cyan-400/20 rounded-lg pointer-events-none" />
                  <div className="text-center">
                    <Bot className="w-12 h-12 mx-auto mb-2 opacity-60" style={{ color: accentColor }} />
                    <div className="text-xs font-mono text-cyan-300">STATE: {robotMotion}</div>
                    <div className="text-[11px] text-slate-400 mt-1">Raspberry Pi 5 • ESP32-S3 • LiDAR Sim Active</div>
                  </div>
                </div>
              </div>

              {/* Controls & Logs */}
              <div className="lg:col-span-5 flex flex-col gap-4">
                <div className="rounded-2xl border p-5 backdrop-blur-xl flex flex-col items-center" style={cardStyle}>
                  <h3 className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: theme.textSecondary }}>Simulated Movement Pad</h3>
                  <div className="grid grid-cols-3 gap-2">
                    <div />
                    <button onClick={() => sendRobotCmd('FORWARD')} className="p-3.5 rounded-xl bg-slate-800 hover:bg-slate-700"><ArrowUp className="w-5 h-5" /></button>
                    <div />
                    <button onClick={() => sendRobotCmd('TURN LEFT')} className="p-3.5 rounded-xl bg-slate-800 hover:bg-slate-700"><ArrowLeft className="w-5 h-5" /></button>
                    <button onClick={() => sendRobotCmd('STOPPED')} className="p-3.5 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold text-xs">STOP</button>
                    <button onClick={() => sendRobotCmd('TURN RIGHT')} className="p-3.5 rounded-xl bg-slate-800 hover:bg-slate-700"><ArrowRight className="w-5 h-5" /></button>
                    <div />
                    <button onClick={() => sendRobotCmd('REVERSE')} className="p-3.5 rounded-xl bg-slate-800 hover:bg-slate-700"><ArrowDown className="w-5 h-5" /></button>
                    <div />
                  </div>
                </div>

                <div className="rounded-2xl border p-4 backdrop-blur-xl flex-1" style={cardStyle}>
                  <h3 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: theme.textSecondary }}>Hardware Activity Log</h3>
                  <div className="space-y-1.5 font-mono text-[11px] text-slate-300">
                    {robotLogs.map((l, i) => <div key={i}>{l}</div>)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'integrations':
        return (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-bold">App & Service Integrations</h2>
              <p className="text-xs" style={{ color: theme.textSecondary }}>All connectors are shown in Demo / Not Connected state until wired to your real JARVIS backend.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {INITIAL_INTEGRATIONS.map((item) => (
                <div key={item.id} className="rounded-2xl border p-5 backdrop-blur-xl flex flex-col justify-between" style={cardStyle}>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-sm">{item.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-amber-300 border border-amber-500/30">{item.status}</span>
                    </div>
                    <p className="text-[11px] text-cyan-400 mb-1">{item.category}</p>
                    <p className="text-xs mb-4" style={{ color: theme.textSecondary }}>{item.desc}</p>
                  </div>
                  <button
                    onClick={() => setSelectedIntegration(item)}
                    className="w-full py-2 rounded-xl text-xs font-semibold border border-slate-700 hover:border-cyan-400/60 hover:bg-white/5 transition"
                  >
                    Preview Configuration
                  </button>
                </div>
              ))}
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="max-w-3xl space-y-5">
            <h2 className="text-xl font-bold">JARVIS OS Settings & Customization</h2>
            <div className="rounded-2xl border p-5 backdrop-blur-xl space-y-5" style={cardStyle}>
              {/* Avatar */}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-semibold text-sm">AI Avatar Character</div>
                  <div className="text-xs" style={{ color: theme.textSecondary }}>Switch between ARIA (Female) and ATLAS (Male).</div>
                </div>
                <div className="flex gap-2">
                  {[{ id: 'female', label: 'ARIA (Female)' }, { id: 'male', label: 'ATLAS (Male)' }].map((av) => (
                    <button
                      key={av.id}
                      onClick={() => setAvatarType(av.id)}
                      className={`px-3.5 py-2 rounded-xl text-xs font-semibold border ${avatarType === av.id ? 'text-slate-950' : 'border-slate-700 text-slate-300'}`}
                      style={avatarType === av.id ? { backgroundColor: accentColor, borderColor: accentColor } : {}}
                    >
                      {av.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Theme */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
                <div>
                  <div className="font-semibold text-sm">Interface Theme</div>
                  <div className="text-xs" style={{ color: theme.textSecondary }}>Persisted automatically in localStorage.</div>
                </div>
                <div className="flex gap-2">
                  {Object.values(THEMES).map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setThemeId(t.id)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold border ${themeId === t.id ? 'text-slate-950' : 'border-slate-700 text-slate-300'}`}
                      style={themeId === t.id ? { backgroundColor: accentColor, borderColor: accentColor } : {}}
                    >
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Accent Color */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
                <div>
                  <div className="font-semibold text-sm">Accent Color</div>
                  <div className="text-xs" style={{ color: theme.textSecondary }}>Primary holographic highlight color.</div>
                </div>
                <div className="flex gap-2">
                  {ACCENTS.map((ac) => (
                    <button
                      key={ac.id}
                      onClick={() => setAccentColor(ac.hex)}
                      className={`w-7 h-7 rounded-full border-2 transition ${accentColor === ac.hex ? 'scale-110 border-white' : 'border-transparent'}`}
                      style={{ backgroundColor: ac.hex }}
                      title={ac.name}
                    />
                  ))}
                </div>
              </div>

              {/* Voice & Speed */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                <div>
                  <label className="text-xs font-semibold block mb-1.5">Browser Speech Voice</label>
                  <select
                    value={selectedVoiceURI}
                    onChange={(e) => setSelectedVoiceURI(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs"
                  >
                    <option value="">Auto-Match Avatar ({avatarType})</option>
                    {voices.map((v) => <option key={v.voiceURI} value={v.voiceURI}>{v.name} ({v.lang})</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold block mb-1.5">Speech Speed: {voiceSpeed.toFixed(2)}x</label>
                  <input
                    type="range" min="0.7" max="1.5" step="0.05"
                    value={voiceSpeed}
                    onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                </div>
              </div>

              {/* Toggles */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-slate-800">
                {[
                  { label: 'Voice Sound', val: soundEnabled, set: setSoundEnabled },
                  { label: 'Reduced Motion', val: reducedMotion, set: setReducedMotion },
                  { label: 'Collapse Sidebar', val: sidebarCollapsed, set: setSidebarCollapsed }
                ].map((tg, i) => (
                  <button
                    key={i}
                    onClick={() => tg.set(!tg.val)}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs font-medium"
                  >
                    <span>{tg.label}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${tg.val ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                      {tg.val ? 'ON' : 'OFF'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // ============================================================================
  // MAIN SHELL LAYOUT
  // ============================================================================
  return (
    <div
      className="min-h-screen w-full flex flex-col transition-colors duration-300"
      style={{ backgroundColor: theme.bg, backgroundImage: theme.gradient, color: theme.textPrimary }}
    >
      <style>{`
        @keyframes jarvisSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes jarvisBreathe { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-3px); } }
        @keyframes jarvisWave { 0% { transform: scaleY(0.35); } 100% { transform: scaleY(1); } }
        .jarvis-spin-slow { transform-origin: 150px 150px; animation: jarvisSpin 24s linear infinite; }
        .jarvis-spin-reverse { transform-origin: 150px 150px; animation: jarvisSpin 18s linear infinite reverse; }
        .jarvis-spin-fast { transform-origin: 150px 150px; animation: jarvisSpin 4s linear infinite; }
        .jarvis-breathe { animation: jarvisBreathe 4.2s ease-in-out infinite; }
      `}</style>

      {/* TOP HEADER */}
      <header className="h-14 border-b px-4 flex items-center justify-between gap-3 sticky top-0 z-30 backdrop-blur-xl" style={{ backgroundColor: 'rgba(5, 11, 22, 0.82)', borderColor: theme.border }}>
        <div className="flex items-center gap-3">
          <button onClick={() => setMobileMenuOpen((v) => !v)} className="lg:hidden p-1.5 rounded-lg hover:bg-white/10">
            <Menu className="w-5 h-5" />
          </button>
          <div onClick={() => setActivePage('dashboard')} className="flex items-center gap-2 cursor-pointer">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center border" style={{ borderColor: accentColor, backgroundColor: 'rgba(0,217,255,0.12)' }}>
              <Sparkles className="w-4 h-4" style={{ color: accentColor }} />
            </div>
            <span className="font-bold tracking-wider text-sm sm:text-base">JARVIS OS</span>
          </div>

          {/* Quick Nav Tabs */}
          <nav className="hidden md:flex items-center gap-1 ml-4">
            {[
              { id: 'dashboard', label: 'Control Center' },
              { id: 'workspace', label: 'Workspace' },
              { id: 'agents', label: 'Agents' },
              { id: 'memory', label: 'Memory' },
              { id: 'integrations', label: 'Integrations' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActivePage(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${activePage === tab.id ? 'text-slate-950 font-semibold' : 'text-slate-300 hover:bg-white/5'}`}
                style={activePage === tab.id ? { backgroundColor: accentColor } : {}}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={() => setCmdOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-700/80 text-xs text-slate-300 hover:border-cyan-400/60"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Search</span>
            <kbd className="hidden md:inline text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">Ctrl+K</kbd>
          </button>

          <span className="hidden xl:inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
            <Radio className="w-3 h-3" /> SIMULATED DEMO
          </span>

          <div className="hidden lg:block text-right text-[11px] leading-tight" style={{ color: theme.textSecondary }}>
            <div className="font-semibold text-slate-200">{now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            <div>{now.toLocaleDateString([], { month: 'short', day: 'numeric' })}</div>
          </div>

          <div className="relative">
            <button onClick={() => setNotifOpen((v) => !v)} className="p-2 rounded-xl hover:bg-white/10 relative">
              <Bell className="w-4 h-4" />
              <span className="w-2 h-2 rounded-full bg-cyan-400 absolute top-1.5 right-1.5" />
            </button>
            {notifOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl border p-3 shadow-2xl z-50 backdrop-blur-xl" style={{ backgroundColor: theme.cardSolid, borderColor: theme.border }}>
                <div className="text-xs font-semibold mb-2">Notifications (Demo)</div>
                <div className="space-y-2">
                  {notifications.map((n) => (
                    <div key={n.id} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                      <div className="font-semibold">{n.title}</div>
                      <div className="text-[11px] text-slate-400">{n.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button onClick={() => setActivePage('settings')} className="p-2 rounded-xl hover:bg-white/10">
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* BODY: SIDEBAR + MAIN CONTENT */}
      <div className="flex flex-1 min-h-0">
        {/* DESKTOP SIDEBAR */}
        <aside
          className={`hidden lg:flex flex-col border-r transition-all duration-200 shrink-0 ${sidebarCollapsed ? 'w-16' : 'w-56'}`}
          style={{ backgroundColor: theme.secondaryBg, borderColor: theme.border }}
        >
          <div className="flex-1 overflow-y-auto p-2.5 space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActivePage(item.id)}
                  title={item.label}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                    isActive ? 'text-slate-950 font-semibold shadow-md' : 'text-slate-300 hover:bg-white/5'
                  }`}
                  style={isActive ? { backgroundColor: accentColor } : {}}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setSidebarCollapsed((v) => !v)}
            className="p-3 border-t flex items-center justify-center text-slate-400 hover:text-white"
            style={{ borderColor: theme.border }}
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </aside>

        {/* MOBILE DRAWER */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 lg:hidden flex">
            <div className="w-64 h-full p-4 overflow-y-auto border-r" style={{ backgroundColor: theme.secondaryBg, borderColor: theme.border }}>
              <div className="flex items-center justify-between mb-4">
                <span className="font-bold">JARVIS Navigation</span>
                <button onClick={() => setMobileMenuOpen(false)}><X className="w-5 h-5" /></button>
              </div>
              <div className="space-y-1">
                {NAV_ITEMS.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => { setActivePage(item.id); setMobileMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium ${activePage === item.id ? 'text-slate-950 font-semibold' : 'text-slate-300'}`}
                    style={activePage === item.id ? { backgroundColor: accentColor } : {}}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1 bg-black/60" onClick={() => setMobileMenuOpen(false)} />
          </div>
        )}

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 pb-24 lg:pb-6">
          {renderPage()}
        </main>
      </div>

      {/* MOBILE BOTTOM NAVIGATION */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 h-16 border-t flex items-center justify-around px-2 z-30 backdrop-blur-xl" style={{ backgroundColor: 'rgba(5, 11, 22, 0.92)', borderColor: theme.border }}>
        {[
          { id: 'dashboard', label: 'Home', icon: LayoutDashboard },
          { id: 'voice', label: 'Voice', icon: Mic },
          { id: 'chat', label: 'Chat', icon: MessageSquare },
          { id: 'agents', label: 'Agents', icon: Cpu },
          { id: 'settings', label: 'Settings', icon: SettingsIcon }
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className="flex flex-col items-center gap-1 text-[10px]"
            style={{ color: activePage === item.id ? accentColor : theme.textSecondary }}
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* GLOBAL COMMAND PALETTE (Ctrl+K) */}
      {cmdOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-20 p-4" onClick={() => setCmdOpen(false)}>
          <div className="w-full max-w-lg rounded-2xl border p-4 shadow-2xl" style={{ backgroundColor: theme.cardSolid, borderColor: theme.border }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
              <Search className="w-4 h-4 text-cyan-400" />
              <input
                autoFocus
                value={cmdQuery}
                onChange={(e) => setCmdQuery(e.target.value)}
                placeholder="Type a command or search pages..."
                className="flex-1 bg-transparent text-sm focus:outline-none"
              />
              <button onClick={() => setCmdOpen(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <div className="mt-2 space-y-1 max-h-72 overflow-y-auto">
              {cmdResults.map((r, i) => (
                <button key={i} onClick={r.action} className="w-full text-left px-3 py-2.5 rounded-xl hover:bg-white/5 flex items-center justify-between text-xs">
                  <span>{r.label}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">{r.type}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* AGENT LOGS DRAWER */}
      {selectedAgentLogs && (
        <div className="fixed inset-0 z-50 bg-black/60 flex justify-end" onClick={() => setSelectedAgentLogs(null)}>
          <div className="w-full max-w-md h-full p-5 border-l overflow-y-auto" style={{ backgroundColor: theme.cardSolid, borderColor: theme.border }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="font-bold text-sm">{selectedAgentLogs.name} — Logs (Sim)</h3>
              <button onClick={() => setSelectedAgentLogs(null)}><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-2 font-mono text-xs text-emerald-300">
              {selectedAgentLogs.logs.map((l, i) => <div key={i} className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">{l}</div>)}
            </div>
          </div>
        </div>
      )}

      {/* ASSIGN TASK MODAL */}
      {assignModalAgent && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={() => setAssignModalAgent(null)}>
          <form onSubmit={handleAssignAgentTask} className="w-full max-w-md rounded-2xl border p-5 space-y-4" style={{ backgroundColor: theme.cardSolid, borderColor: theme.border }} onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold text-sm">Assign Demo Task to {assignModalAgent.name}</h3>
            <input
              autoFocus
              value={assignTaskText}
              onChange={(e) => setAssignTaskText(e.target.value)}
              placeholder="e.g., Audit accessibility & keyboard focus states"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-xs"
            />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setAssignModalAgent(null)} className="px-4 py-2 rounded-xl text-xs border border-slate-700">Cancel</button>
              <button type="submit" className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-950" style={{ backgroundColor: accentColor }}>Start Simulated Run</button>
            </div>
          </form>
        </div>
      )}

      {/* INTEGRATION CONFIG PREVIEW MODAL */}
      {selectedIntegration && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={() => setSelectedIntegration(null)}>
          <div className="w-full max-w-md rounded-2xl border p-5 space-y-3" style={{ backgroundColor: theme.cardSolid, borderColor: theme.border }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm">{selectedIntegration.name} Configuration</h3>
              <button onClick={() => setSelectedIntegration(null)}><X className="w-4 h-4" /></button>
            </div>
            <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 p-3 rounded-xl">
              Status: Demo / Not Connected. Connect this adapter in your JARVIS backend to enable live credentials and webhooks.
            </p>
            <div className="text-xs text-slate-400">Category: {selectedIntegration.category}</div>
            <button onClick={() => setSelectedIntegration(null)} className="w-full py-2 rounded-xl text-xs font-semibold text-slate-950" style={{ backgroundColor: accentColor }}>Close Preview</button>
          </div>
        </div>
      )}
    </div>
  );
}