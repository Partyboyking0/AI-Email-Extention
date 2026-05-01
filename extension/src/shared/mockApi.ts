import { classifyEmailClient } from "./classifier";
import type { ClassificationResponse, ReplyResponse, SummaryResponse, TaskResponse, Tone } from "./types";

const wait = (ms: number) => new Promise((resolve) => globalThis.setTimeout(resolve, ms));

export async function getSummary(emailText: string): Promise<SummaryResponse> {
  await wait(600);
  const hint = emailText.slice(0, 90).replace(/\s+/g, " ").trim();
  return {
    bullets: [
      "Confirm the requested next step and owner.",
      "Review the deadline or meeting time mentioned in the thread.",
      `Use the email context: ${hint || "No readable email text found."}`
    ],
    modelVersion: "mock-pegasus-phase-1",
    latencyMs: 600
  };
}

export async function getReply(emailText: string, tone: Tone): Promise<ReplyResponse> {
  await wait(600);
  const templates: Record<Tone, string> = {
    formal:
      "Thank you for the update. I will review the details and follow up with the next steps shortly.",
    casual: "Thanks for sending this over. I’ll take a look and get back to you soon.",
    concise: "Thanks. I’ll review and follow up shortly."
  };
  return {
    reply: templates[tone] + (emailText.length > 500 ? " I noted the broader context in the thread." : ""),
    tone,
    modelVersion: "mock-flan-t5-phase-1"
  };
}

export async function getTasks(emailText: string): Promise<TaskResponse> {
  await wait(600);
  const hasDeadline = /\b(today|tomorrow|eod|friday|monday|deadline|due)\b/i.test(emailText);
  return {
    tasks: [
      {
        id: crypto.randomUUID(),
        text: "Respond with confirmation and next action",
        deadline: hasDeadline ? "Mentioned in email" : undefined
      },
      {
        id: crypto.randomUUID(),
        text: "Capture any meeting or review request from the thread"
      }
    ],
    modelVersion: "mock-ner-phase-1"
  };
}

export async function getClassification(emailText: string): Promise<ClassificationResponse> {
  await wait(200);
  return classifyEmailClient(emailText);
}
