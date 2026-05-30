export type OrbState = "idle" | "listening" | "speaking";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export type MemoryScope = "projects" | "preferences" | "tasks" | "context";

export interface QuickAction {
  id: string;
  label: string;
  command: string;
  emoji: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: "briefing", label: "Start my day", command: "Start my day", emoji: "☀️" },
  { id: "tasks", label: "My tasks", command: "What are my current tasks?", emoji: "📋" },
  { id: "emails", label: "Check emails", command: "Check my priority emails", emoji: "📧" },
  { id: "memory", label: "What do you know?", command: "What do you know about me?", emoji: "🧠" },
  { id: "note", label: "New note", command: "Create a note:", emoji: "📝" },
];
