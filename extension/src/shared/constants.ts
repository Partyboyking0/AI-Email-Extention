import type { UserSettings } from "./types";

export const DEFAULT_SETTINGS: UserSettings = {
  tone: "formal",
  apiBaseUrl: "http://127.0.0.1:8001",
  modelVersion: "mock-phase-1"
};

export const STORAGE_KEYS = {
  settings: "ai-email.settings",
  usage: "ai-email.usage",
  requestCache: "ai-email.request-cache",
  classifierModel: "ai-email.classifier-model"
} as const;

export const LABEL_COLORS: Record<string, string> = {
  urgent: "#d93025",
  "follow-up": "#f9ab00",
  "action-required": "#b06000",
  "low-priority": "#5f6368",
  opportunity: "#0f766e",
  spam: "#9334e6",
  work: "#1a73e8",
  personal: "#188038",
  finance: "#0b8043",
  newsletter: "#1967d2"
};
