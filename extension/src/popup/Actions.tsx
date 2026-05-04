import { CheckSquare, Copy, Loader2, MessageSquareReply, Sparkles, Tags } from "lucide-react";
import { useState } from "react";
import { LABEL_COLORS } from "../shared/constants";
import { renderSummaryBullet } from "../shared/summaryBullet";
import type { ClassificationResponse, EmailContext, ReplyResponse, SummaryResponse, TaskResponse } from "../shared/types";
import { usePopupStore } from "./store";

type ResultState =
  | { status: "idle" }
  | { status: "loading"; label: string }
  | { status: "summary"; data: SummaryResponse; context: string }
  | { status: "reply"; data: ReplyResponse; context: string }
  | { status: "tasks"; data: TaskResponse; context: string }
  | { status: "classification"; data: ClassificationResponse; context: string }
  | { status: "error"; message: string };

function contextLabel(email: EmailContext) {
  return `${email.emailText.length.toLocaleString()} chars read`;
}

async function readActiveEmail(): Promise<EmailContext> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("https://mail.google.com/")) {
    throw new Error("Open a Gmail email tab first.");
  }

  let response: { ok: boolean; data?: EmailContext; error?: string } | undefined;
  try {
    response = await chrome.tabs.sendMessage(tab.id, { type: "READ_ACTIVE_EMAIL" });
  } catch {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["assets/gmail.js"]
    });
    response = await chrome.tabs.sendMessage(tab.id, { type: "READ_ACTIVE_EMAIL" });
  }

  if (!response?.ok || !response.data) {
    throw new Error(response?.error ?? "Could not read the current Gmail email.");
  }

  return response.data;
}

export function Actions() {
  const tone = usePopupStore((state) => state.settings.tone);
  const [result, setResult] = useState<ResultState>({ status: "idle" });

  async function runAction(type: "SUMMARIZE" | "REPLY" | "TASKS" | "CLASSIFY", label: string) {
    setResult({ status: "loading", label });
    try {
      const email = await readActiveEmail();
      const response = await chrome.runtime.sendMessage({ type, payload: { email, tone } });
      if (!response?.ok) throw new Error(response?.error ?? `${label} failed`);

      console.info("[AI Email Assistant] Popup action email context:", contextLabel(email), email.selector);
      if (type === "SUMMARIZE") setResult({ status: "summary", data: response.data, context: contextLabel(email) });
      if (type === "REPLY") setResult({ status: "reply", data: response.data, context: contextLabel(email) });
      if (type === "TASKS") setResult({ status: "tasks", data: response.data, context: contextLabel(email) });
      if (type === "CLASSIFY") setResult({ status: "classification", data: response.data, context: contextLabel(email) });
    } catch (error) {
      setResult({ status: "error", message: error instanceof Error ? error.message : "Unknown error" });
    }
  }

  async function copyReply(reply: string) {
    await navigator.clipboard.writeText(reply);
  }

  return (
    <section className="view">
      <div className="action-grid">
        <button onClick={() => runAction("SUMMARIZE", "Summarize")}>
          <Sparkles size={16} /> Summarize
        </button>
        <button onClick={() => runAction("REPLY", "Smart Reply")}>
          <MessageSquareReply size={16} /> Smart Reply
        </button>
        <button onClick={() => runAction("TASKS", "Tasks")}>
          <CheckSquare size={16} /> Tasks
        </button>
        <button onClick={() => runAction("CLASSIFY", "Classify")}>
          <Tags size={16} /> Classify
        </button>
      </div>

      {result.status === "idle" && (
        <div className="result-panel muted-panel">Open a Gmail email, then choose an action.</div>
      )}
      {result.status === "loading" && (
        <div className="result-panel loading-row">
          <Loader2 className="spinner-icon" size={16} /> {result.label} is running...
        </div>
      )}
      {result.status === "summary" && (
        <div className="result-panel">
          <div className="result-title">
            <strong>Summary</strong>
            <span className="inline-muted">{result.context}</span>
          </div>
          <ul>{result.data.bullets.map((bullet) => <li key={bullet}>{renderSummaryBullet(bullet)}</li>)}</ul>
          <span className="inline-muted">{result.data.modelVersion}</span>
        </div>
      )}
      {result.status === "reply" && (
        <div className="result-panel">
          <div className="result-title">
            <strong>Suggested Reply</strong>
            <span className="inline-muted">{result.context}</span>
            <button className="icon-button" title="Copy reply" onClick={() => copyReply(result.data.reply)}>
              <Copy size={15} />
            </button>
          </div>
          <textarea readOnly value={result.data.reply} />
          <span className="inline-muted">{result.data.modelVersion}</span>
        </div>
      )}
      {result.status === "tasks" && (
        <div className="result-panel">
          <div className="result-title">
            <strong>Tasks</strong>
            <span className="inline-muted">{result.context}</span>
          </div>
          <ul>
            {result.data.tasks.map((task) => (
              <li key={task.id}>{task.text}{task.deadline ? ` - ${task.deadline}` : ""}</li>
            ))}
          </ul>
          <span className="inline-muted">{result.data.modelVersion}</span>
        </div>
      )}
      {result.status === "classification" && (
        <div className="result-panel">
          <div className="result-title">
            <strong>Classification</strong>
            <span className="inline-muted">{result.context}</span>
          </div>
          <div className="classification-row">
            <span
              className="classification-badge"
              style={{ backgroundColor: LABEL_COLORS[result.data.label] ?? "#5f6368" }}
            >
              {result.data.label}
            </span>
            <span>{Math.round(result.data.score * 100)}% confidence</span>
          </div>
          <span className="inline-muted">
            {result.data.modelVersion} · {result.data.source}
          </span>
        </div>
      )}
      {result.status === "error" && <div className="result-panel error-panel">{result.message}</div>}
    </section>
  );
}
