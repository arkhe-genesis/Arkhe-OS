
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'motion/react';
import React, { useEffect, useState, useRef } from 'react';

interface PiDayTerminalProps {
  text: string;
  onClose: () => void;
}

export default function PiDayTerminal({ text, onClose }: PiDayTerminalProps) {
  const [displayedText, setDisplayedText] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setDisplayedText(text.substring(0, i));
      i += 3; // Typewriter speed

      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }

      if (i > text.length) {
        clearInterval(interval);
      }
    }, 10);

    return () => clearInterval(interval);
  }, [text]);

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 md:p-8 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-5xl h-[85vh] bg-[#050505] border border-yellow-500/40 rounded-lg shadow-[0_0_40px_rgba(234,179,8,0.15)] flex flex-col overflow-hidden"
      >
        <div className="flex justify-between items-center p-4 border-b border-yellow-500/30 bg-yellow-500/10">
          <div className="flex items-center gap-3">
            <span className="text-yellow-500 animate-pulse">🜏</span>
            <h2 className="text-yellow-500 font-mono font-bold tracking-widest text-sm md:text-base">ARKHE PROTOCOL :: PI DAY INJECTION</h2>
          </div>
          <button
            onClick={onClose}
            className="text-yellow-500/70 hover:text-yellow-400 font-mono text-sm tracking-wider transition-colors"
          >
            [ TERMINATE ]
          </button>
        </div>

        <div
          ref={scrollRef}
          className="p-6 overflow-y-auto flex-1 font-mono text-xs md:text-sm text-yellow-500/90 whitespace-pre-wrap leading-relaxed"
          style={{ textShadow: '0 0 5px rgba(234,179,8,0.3)' }}
        >
          {displayedText}
          <span className="animate-pulse inline-block w-2 h-4 bg-yellow-500 ml-1 align-middle"></span>
        </div>
      </motion.div>
    </div>
  );
}
