"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { OrbState } from "@/types";

interface VoiceOrbProps {
  state: OrbState;
  onClick?: () => void;
}

const orbVariants = {
  idle: {
    scale: [1, 1.05, 1],
    backgroundColor: "#111827",       // surface-card
    boxShadow: "0 0 0px transparent",
    borderColor: "#374151",            // hairline-soft
    transition: {
      scale: { duration: 3, repeat: Infinity, ease: "easeInOut" },
    },
  },
  listening: {
    scale: [1, 1.08, 1],
    backgroundColor: "#1E3A4A",        // voice-muted
    boxShadow: "0 0 24px #0EA5E9",     // voice-glow
    borderColor: "#00D4FF",            // voice-active
    transition: {
      scale: { duration: 1.5, repeat: Infinity, ease: "easeInOut" },
      backgroundColor: { duration: 0.3 },
      boxShadow: { duration: 0.3 },
    },
  },
  speaking: {
    scale: [1, 1.12, 0.98, 1.1, 1],
    backgroundColor: "#4F46E5",        // primary
    boxShadow: "0 0 32px #00D4FF",     // voice-active glow
    borderColor: "#00D4FF",
    transition: {
      scale: { duration: 0.8, repeat: Infinity, ease: "easeInOut" },
      backgroundColor: { duration: 0.3 },
      boxShadow: { duration: 0.3 },
    },
  },
};

const iconVariants = {
  idle: { opacity: 0.5, scale: 1 },
  listening: { opacity: 1, scale: 1.1 },
  speaking: { opacity: 1, scale: 1, rotate: [0, -5, 5, 0] },
};

export function VoiceOrb({ state, onClick }: VoiceOrbProps) {
  return (
    <motion.button
      data-testid="voice-orb"
      data-state={state}
      onClick={onClick}
      className="relative w-[120px] h-[120px] rounded-pill border-2 cursor-pointer focus-visible:outline-none"
      variants={orbVariants}
      animate={state}
      aria-label={
        state === "idle"
          ? "Cliquer pour parler à Jarvis"
          : state === "listening"
          ? "Jarvis écoute — cliquer pour arrêter"
          : "Jarvis parle"
      }
      style={{ borderRadius: "999px" }}
    >
      {/* Icône centrale */}
      <motion.span
        className="absolute inset-0 flex items-center justify-center text-3xl pointer-events-none"
        variants={iconVariants}
        animate={state}
      >
        {state === "idle" && "🤖"}
        {state === "listening" && "🎤"}
        {state === "speaking" && "🔊"}
      </motion.span>

      {/* Halo externe — listening/speaking uniquement */}
      <AnimatePresence>
        {(state === "listening" || state === "speaking") && (
          <motion.span
            key="halo"
            className="absolute inset-0 rounded-pill pointer-events-none"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: [0.3, 0.6, 0.3], scale: [1, 1.2, 1] }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            style={{
              border: `1px solid ${state === "speaking" ? "#00D4FF" : "#0EA5E9"}`,
              borderRadius: "999px",
            }}
          />
        )}
      </AnimatePresence>
    </motion.button>
  );
}
