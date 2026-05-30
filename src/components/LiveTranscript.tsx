"use client";

import { motion, AnimatePresence } from "framer-motion";

interface LiveTranscriptProps {
  text: string;
  visible: boolean;
}

export function LiveTranscript({ text, visible }: LiveTranscriptProps) {
  return (
    <AnimatePresence>
      {visible && text && (
        <motion.p
          data-testid="live-transcript"
          className="font-mono text-[13px] leading-[1.7] tracking-[0.2px] text-muted text-center px-4 max-w-md"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.15 }}
        >
          {text}
          <motion.span
            className="inline-block w-[2px] h-[14px] bg-muted ml-[2px] align-middle"
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        </motion.p>
      )}
    </AnimatePresence>
  );
}
