import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface Props {
  persona: 'aria' | 'atlas';
  facialState: string;
  mouthOpenness: number;
}

export const HolographicAvatar: React.FC<Props> = ({ persona, facialState, mouthOpenness }) => {
  const [blinking, setBlinking] = useState(false);

  useEffect(() => {
    const id = setInterval(() => {
      setBlinking(true);
      setTimeout(() => setBlinking(false), 140);
    }, 3500);
    return () => clearInterval(id);
  }, []);

  const primary = persona === 'aria' ? '#00D9FF' : '#218BFF';
  const secondary = persona === 'aria' ? '#9868FF' : '#25E6A2';
  const mouthRy = Math.max(2, Math.round(mouthOpenness * 14));

  return (
    <div className="flex flex-col items-center">
      <svg width="260" height="260" viewBox="0 0 280 280" role="img" aria-label={`${persona.toUpperCase()} holographic avatar`}>
        <motion.circle
          cx="140"
          cy="140"
          r="118"
          fill="none"
          stroke={primary}
          strokeWidth="1.5"
          strokeDasharray="14 8"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 16, ease: 'linear' }}
          style={{ transformOrigin: '140px 140px' }}
        />
        <motion.circle
          cx="140"
          cy="140"
          r="98"
          fill="none"
          stroke={secondary}
          strokeWidth="1.2"
          strokeDasharray="6 10"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 22, ease: 'linear' }}
          style={{ transformOrigin: '140px 140px' }}
        />
        <path
          d="M92,130 C92,82 188,82 188,130 C188,178 168,210 140,214 C112,210 92,178 92,130 Z"
          fill="rgba(16,30,48,0.7)"
          stroke={primary}
          strokeWidth="2.2"
        />
        <ellipse cx="118" cy="134" rx="10" ry={blinking ? 1 : 6} fill={primary} />
        <ellipse cx="162" cy="134" rx="10" ry={blinking ? 1 : 6} fill={primary} />
        <ellipse cx="140" cy="176" rx="18" ry={mouthRy} fill="#25E6A2" fillOpacity="0.85" stroke={primary} strokeWidth="1.4" />
      </svg>
      <div className="text-xs font-bold tracking-widest mt-1" style={{ color: primary }}>
        {persona.toUpperCase()} · {facialState.toUpperCase()}
      </div>
    </div>
  );
};
