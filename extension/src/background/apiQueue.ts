import { classifyEmailClient } from "../shared/classifier";
import { usageEmailId } from "../shared/emailIdentity";
import { getClassification, getReply, getSummary, getTasks } from "../shared/mockApi";
import { getLocalUsage, incrementLocalUsage, resetLocalUsage, saveLocalUsage } from "../shared/localUsage";
import type { EmailContext, Feature, Tone } from "../shared/types";
import {
  classifyViaBackend,
  getUsageStats,
  recordUsage,
  replyViaBackend,
  resetUsageStats,
  sendFeedback,
  summarizeViaBackend,
  tasksViaBackend,
  type FeedbackPayload
} from "./backendClient";

type Payload = {
  email?: EmailContext;
  tone?: Tone;
  generatedReply?: string;
  rating?: "up" | "down";
  reason?: string;
};

const inflight = new Map<string, Promise<unknown>>();

function fingerprint(type: string, payload: Payload) {
  if (type === "USAGE_STATS") return "USAGE_STATS";
  if (type === "FEEDBACK") return `FEEDBACK:${payload.email?.threadId ?? "unknown"}:${payload.rating ?? ""}`;
  if (!payload.email) return `${type}:no-email`;

  return `${type}:${payload.email.threadId}:${payload.email.emailText.length}:${payload.tone ?? ""}`;
}

export function enqueue(type: string, payload: Payload): Promise<unknown> {
  const key = fingerprint(type, payload);
  const existing = inflight.get(key);
  if (existing) return existing;

  const job = run(type, payload).finally(() => inflight.delete(key));
  inflight.set(key, job);
  return job;
}

async function run(type: string, payload: Payload) {
  if (type === "FEEDBACK") {
    return sendFeedback(payload as FeedbackPayload);
  }
  if (type === "USAGE_STATS") {
    try {
      const stats = await getUsageStats();
      return await saveLocalUsage(stats);
    } catch (error) {
      console.warn("[AI Email Assistant] Backend usage stats unavailable; using local stats.", error);
      return getLocalUsage();
    }
  }
  if (type === "RESET_USAGE") {
    try {
      const stats = await resetUsageStats();
      await resetLocalUsage();
      return await saveLocalUsage(stats);
    } catch (error) {
      console.warn("[AI Email Assistant] Backend usage reset unavailable; resetting local stats.", error);
      return resetLocalUsage();
    }
  }

  const email = payload.email;
  if (!email) throw new Error("No email payload supplied.");

  try {
    if (type === "CLASSIFY") return await withUsage("classify", email, classifyEmailClient(email.emailText));
    if (type === "SUMMARIZE") return await withUsage("summarize", email, summarizeViaBackend(email));
    if (type === "REPLY") return await withUsage("reply", email, replyViaBackend(email, payload.tone ?? "formal"));
    if (type === "TASKS") return await withUsage("tasks", email, tasksViaBackend(email));
  } catch (error) {
    console.warn("[AI Email Assistant] Primary action failed, using fallback response.", error);
  }

  if (type === "CLASSIFY") {
    try {
      return await withLocalUsage("classify", email, classifyViaBackend(email));
    } catch {
      return withLocalUsage("classify", email, getClassification(email.emailText));
    }
  }
  if (type === "SUMMARIZE") return withLocalUsage("summarize", email, getSummary(email.emailText));
  if (type === "REPLY") return withLocalUsage("reply", email, getReply(email.emailText, payload.tone ?? "formal"));
  if (type === "TASKS") return withLocalUsage("tasks", email, getTasks(email.emailText));
  throw new Error(`Unsupported request type: ${type}`);
}

async function withUsage<T>(feature: Feature, email: EmailContext, job: Promise<T>): Promise<T> {
  const result = await job;
  await incrementLocalUsage(feature, usageEmailId(email), email.emailText.length);
  try {
    const stats = await recordUsage(feature, email);
    await saveLocalUsage(stats);
  } catch (error) {
    console.warn("[AI Email Assistant] Backend usage sync failed; local usage was recorded.", error);
  }
  return result;
}

async function withLocalUsage<T>(feature: Feature, email: EmailContext, job: Promise<T>): Promise<T> {
  const result = await job;
  await incrementLocalUsage(feature, usageEmailId(email), email.emailText.length);
  return result;
}
