"use client";

import { motion } from "framer-motion";

interface WaveformProps {
  active: boolean;
  barCount?: number;
}

export function Waveform({ active, barCount = 16 }: WaveformProps) {
  return (
    <div
      data-testid="waveform"
      className="flex items-center justify-center gap-[3px] h-8"
      aria-hidden="true"
    >
      {Array.from({ length: barCount }).map((_, i) => (
        <motion.span
          key={i}
          className="w-[3px] rounded-pill"
          style={{ backgroundColor: "#00D4FF" }} // voice-active
          animate={
            active
              ? {
                  height: ["8px", `${12 + Math.random() * 36}px`, "8px"],
                  opacity: 1,
                }
              : { height: "8px", opacity: 0.3 }
          }
          transition={
            active
              ? {
                  duration: 0.4 + Math.random() * 0.3,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: i * 0.03,
                }
              : { duration: 0.3 }
          }
        />
      ))}
    </div>
  );
}
