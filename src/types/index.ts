export type OrbState = "idle" | "listening" | "speaking";

export interface CRData {
  titre: string;
  date: string;
  participants: string[];
  points_discutes: string[];
  decisions: string[];
  actions: string[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  crData?: CRData;
}

export interface WSMessage {
  type: string;
  content?: string;
  audio?: string;
  transcript?: string;
  voice_origin?: boolean;
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
  { id: "compte-rendu", label: "Compte-rendu", command: "Jarvis, rédige un compte-rendu de réunion", emoji: "📋" },
  { id: "outlook-classify", label: "Outlook avocat", command: "Analyse mes emails Outlook", emoji: "📬" },
  { id: "classify", label: "Classify Gmail", command: "Classify my last 10 emails", emoji: "📨" },
  { id: "tasks", label: "My tasks", command: "Show my tasks", emoji: "✅" },
  { id: "memory", label: "What do you know?", command: "What do you know about me?", emoji: "🧠" },
];
