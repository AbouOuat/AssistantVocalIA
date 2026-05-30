"use client";

import { motion } from "framer-motion";
import { QUICK_ACTIONS } from "@/types";

interface QuickActionsProps {
  onAction: (command: string) => void;
  disabled?: boolean;
}

export function QuickActions({ onAction, disabled }: QuickActionsProps) {
  return (
    <div
      data-testid="quick-actions"
      className="flex gap-2 overflow-x-auto pb-1 scrollbar-none"
      role="toolbar"
      aria-label="Actions rapides"
    >
      {QUICK_ACTIONS.map((action) => (
        <motion.button
          key={action.id}
          data-testid={`qa-${action.id}`}
          onClick={() => !disabled && onAction(action.command)}
          disabled={disabled}
          className="flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-pill
                     bg-surface-card text-muted text-[12px] font-medium
                     border border-hairline
                     hover:border-primary hover:text-body
                     disabled:opacity-40 disabled:cursor-not-allowed
                     transition-colors duration-150 cursor-pointer"
          whileTap={{ scale: 0.95 }}
          aria-label={action.label}
        >
          <span aria-hidden="true">{action.emoji}</span>
          <span>{action.label}</span>
        </motion.button>
      ))}
    </div>
  );
}
