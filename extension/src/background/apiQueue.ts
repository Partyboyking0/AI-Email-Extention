import { classifyEmailClient } from "../shared/classifier";
import { getClassification, getReply, getSummary, getTasks } from "../shared/mockApi";
import { getLocalUsage, incrementLocalUsage, resetLocalUsage } from "../shared/localUsage";
import type { EmailContext, Feature, Tone } from "../shared/types";
import {
  classifyViaBackend,
  recordUsage,
  replyViaBackend,
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
    return getLocalUsage();
  }
  if (type === "RESET_USAGE") {
    return resetLocalUsage();
  }

  const email = payload.email;
  if (!email) throw new Error("No email payload supplied.");

  try {
    if (type === "CLASSIFY") return await withUsage("classify", email.threadId, classifyEmailClient(email.emailText));
    if (type === "SUMMARIZE") return await withUsage("summarize", email.threadId, summarizeViaBackend(email));
    if (type === "REPLY") return await withUsage("reply", email.threadId, replyViaBackend(email, payload.tone ?? "formal"));
    if (type === "TASKS") return await withUsage("tasks", email.threadId, tasksViaBackend(email));
  } catch (error) {
    console.warn("[AI Email Assistant] Primary action failed, using fallback response.", error);
  }

  if (type === "CLASSIFY") {
    try {
      return await withLocalUsage("classify", email.threadId, classifyViaBackend(email));
    } catch {
      return withLocalUsage("classify", email.threadId, getClassification(email.emailText));
    }
  }
  if (type === "SUMMARIZE") return withLocalUsage("summarize", email.threadId, getSummary(email.emailText));
  if (type === "REPLY") return withLocalUsage("reply", email.threadId, getReply(email.emailText, payload.tone ?? "formal"));
  if (type === "TASKS") return withLocalUsage("tasks", email.threadId, getTasks(email.emailText));
  throw new Error(`Unsupported request type: ${type}`);
}

async function withUsage<T>(feature: Feature, emailId: string, job: Promise<T>): Promise<T> {
  const result = await job;
  await incrementLocalUsage(feature, emailId);
  try {
    await recordUsage(feature);
  } catch (error) {
    console.warn("[AI Email Assistant] Backend usage sync failed; local usage was recorded.", error);
  }
  return result;
}

async function withLocalUsage<T>(feature: Feature, emailId: string, job: Promise<T>): Promise<T> {
  const result = await job;
  await incrementLocalUsage(feature, emailId);
  return result;
}
