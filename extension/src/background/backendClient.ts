import { DEFAULT_SETTINGS, STORAGE_KEYS } from "../shared/constants";
import type {
  ClassificationResponse,
  EmailContext,
  Feature,
  ReplyResponse,
  SummaryResponse,
  TaskResponse,
  Tone,
  UsageStats,
  UserSettings
} from "../shared/types";
import { getOrCreateDemoJwt } from "./authManager";

interface BackendSummaryResponse {
  bullets: string[];
  model_version: string;
  latency_ms: number;
}

interface BackendReplyResponse {
  reply: string;
  tone: Tone;
  model_version: string;
}

interface BackendTaskResponse {
  tasks: Array<{
    id: string;
    text: string;
    deadline?: string | null;
    assignee?: string | null;
  }>;
  model_version: string;
}

interface BackendClassificationResponse {
  label: string;
  score: number;
  model_version: string;
}

export interface FeedbackPayload {
  email: EmailContext;
  generatedReply: string;
  rating: "up" | "down";
  reason?: string;
}

interface BackendUsageResponse {
  processed_today: number;
  time_saved_minutes: number;
  most_used_feature: string;
  by_feature: Record<string, number>;
}

async function getSettings(): Promise<UserSettings> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.settings);
  return { ...DEFAULT_SETTINGS, ...(result[STORAGE_KEYS.settings] ?? {}) };
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const settings = await getSettings();
  const jwt = await getOrCreateDemoJwt(settings.apiBaseUrl);
  const response = await fetch(`${settings.apiBaseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${jwt.token}` },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`Backend ${path} failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  const settings = await getSettings();
  const jwt = await getOrCreateDemoJwt(settings.apiBaseUrl);
  const response = await fetch(`${settings.apiBaseUrl}${path}`, {
    headers: { Authorization: `Bearer ${jwt.token}` }
  });

  if (!response.ok) {
    throw new Error(`Backend ${path} failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function mapUsage(data: BackendUsageResponse): UsageStats {
  return {
    processedToday: data.processed_today,
    timeSavedMinutes: data.time_saved_minutes,
    mostUsedFeature: data.most_used_feature,
    byFeature: data.by_feature
  };
}

export async function summarizeViaBackend(email: EmailContext): Promise<SummaryResponse> {
  const data = await postJson<BackendSummaryResponse>("/api/summarize", {
    email_text: email.emailText,
    thread_id: email.threadId
  });

  return {
    bullets: data.bullets,
    modelVersion: data.model_version,
    latencyMs: data.latency_ms
  };
}

export async function replyViaBackend(email: EmailContext, tone: Tone): Promise<ReplyResponse> {
  const data = await postJson<BackendReplyResponse>("/api/reply", {
    email_text: email.emailText,
    thread_id: email.threadId,
    tone
  });

  return {
    reply: data.reply,
    tone: data.tone,
    modelVersion: data.model_version
  };
}

export async function tasksViaBackend(email: EmailContext): Promise<TaskResponse> {
  const data = await postJson<BackendTaskResponse>("/api/tasks", {
    email_text: email.emailText,
    thread_id: email.threadId
  });

  return {
    tasks: data.tasks.map((task) => ({
      id: task.id,
      text: task.text,
      deadline: task.deadline ?? undefined,
      assignee: task.assignee ?? undefined
    })),
    modelVersion: data.model_version
  };
}

export async function classifyViaBackend(email: EmailContext): Promise<ClassificationResponse> {
  const data = await postJson<BackendClassificationResponse>("/api/classify", {
    email_text: email.emailText,
    thread_id: email.threadId
  });

  return {
    label: data.label,
    score: data.score,
    modelVersion: data.model_version,
    source: "backend"
  };
}

export async function sendFeedback(payload: FeedbackPayload): Promise<{ status: string }> {
  return postJson<{ status: string }>("/api/feedback", {
    email_text: payload.email.emailText,
    generated_reply: payload.generatedReply,
    rating: payload.rating,
    reason: payload.reason
  });
}

export async function recordUsage(feature: Feature): Promise<UsageStats> {
  const data = await postJson<BackendUsageResponse>("/api/users/me/usage", { feature });
  return mapUsage(data);
}

export async function getUsageStats(): Promise<UsageStats> {
  const data = await getJson<BackendUsageResponse>("/api/users/me/usage");
  return mapUsage(data);
}
