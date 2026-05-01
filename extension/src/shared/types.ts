export type Tone = "formal" | "casual" | "concise";

export type Feature = "summarize" | "reply" | "tasks" | "classify";

export interface EmailContext {
  threadId: string;
  subject: string;
  emailText: string;
  selector: string;
}

export interface SummaryResponse {
  bullets: string[];
  modelVersion: string;
  latencyMs: number;
}

export interface ReplyResponse {
  reply: string;
  tone: Tone;
  modelVersion: string;
}

export interface TaskItem {
  id: string;
  text: string;
  deadline?: string;
  assignee?: string;
}

export interface TaskResponse {
  tasks: TaskItem[];
  modelVersion: string;
}

export interface ClassificationResponse {
  label: string;
  score: number;
  modelVersion: string;
  source: "onnx" | "keyword" | "backend";
}

export interface UserSettings {
  tone: Tone;
  apiBaseUrl: string;
  modelVersion: string;
}

export interface UsageStats {
  processedToday: number;
  timeSavedMinutes: number;
  mostUsedFeature: string;
  lastUsedFeature?: string;
  byFeature: Record<string, number>;
  processedEmailIds?: string[];
}
