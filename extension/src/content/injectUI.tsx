import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { CheckSquare, Loader2, MessageSquareReply, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";
import { renderSummaryBullet } from "../shared/summaryBullet";
import type { EmailContext, ReplyResponse, SummaryResponse, TaskResponse, Tone } from "../shared/types";

type PanelState =
  | { status: "idle" }
  | { status: "loading"; feature: string }
  | { status: "summary"; data: SummaryResponse }
  | { status: "reply"; data: ReplyResponse }
  | { status: "tasks"; data: TaskResponse }
  | { status: "error"; message: string };

const styles = `
  :host { all: initial; font-family: Inter, Arial, sans-serif; color: #202124; }
  .bar { display: flex; align-items: center; gap: 8px; margin: 12px 0; padding: 8px; border: 1px solid #dadce0; border-radius: 8px; background: #fff; width: fit-content; max-width: 100%; }
  button { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #dadce0; border-radius: 6px; background: #fff; color: #202124; padding: 7px 10px; font-size: 13px; cursor: pointer; }
  button:hover { background: #f8fafd; border-color: #c7d2fe; }
  .panel { margin: 8px 0 14px; padding: 12px; border: 1px solid #dadce0; border-radius: 8px; background: #f8fafd; max-width: 680px; font-size: 13px; line-height: 1.45; }
  ul { margin: 8px 0 0; padding-left: 20px; }
  textarea { width: 100%; min-height: 92px; resize: vertical; border: 1px solid #dadce0; border-radius: 6px; padding: 8px; font: inherit; box-sizing: border-box; }
  .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .muted { color: #5f6368; font-size: 12px; }
  .success { color: #188038; font-size: 12px; }
  .spin { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
`;

function Toolbar({ email }: { email: EmailContext }) {
  const [panel, setPanel] = useState<PanelState>({ status: "idle" });
  const [tone, setTone] = useState<Tone>("formal");
  const [feedbackStatus, setFeedbackStatus] = useState("");

  useEffect(() => {
    chrome.storage.local.get("ai-email.settings", (result) => {
      if (result["ai-email.settings"]?.tone) setTone(result["ai-email.settings"].tone);
    });
  }, []);

  async function requestFeature(feature: "SUMMARIZE" | "REPLY" | "TASKS") {
    setFeedbackStatus("");
    setPanel({ status: "loading", feature });
    try {
      const response = await chrome.runtime.sendMessage({ type: feature, payload: { email, tone } });
      if (!response?.ok) throw new Error(response?.error ?? "Request failed");
      if (feature === "SUMMARIZE") setPanel({ status: "summary", data: response.data });
      if (feature === "REPLY") setPanel({ status: "reply", data: response.data });
      if (feature === "TASKS") setPanel({ status: "tasks", data: response.data });
    } catch (error) {
      setPanel({ status: "error", message: error instanceof Error ? error.message : "Unknown error" });
    }
  }

  async function submitFeedback(rating: "up" | "down", generatedReply: string) {
    setFeedbackStatus("Saving feedback...");
    const reason =
      rating === "down"
        ? window.prompt("What should improve? Too formal, too long, off-topic, or other?") ?? undefined
        : undefined;

    const response = await chrome.runtime.sendMessage({
      type: "FEEDBACK",
      payload: { email, generatedReply, rating, reason }
    });
    setFeedbackStatus(response?.ok ? "Feedback saved" : "Feedback could not be saved");
  }

  return (
    <>
      <style>{styles}</style>
      <div className="bar" aria-label="AI Email Assistant toolbar">
        <button title="Summarize email" onClick={() => requestFeature("SUMMARIZE")}>
          <Sparkles size={15} /> Summarize
        </button>
        <button title="Generate reply" onClick={() => requestFeature("REPLY")}>
          <MessageSquareReply size={15} /> Smart Reply
        </button>
        <button title="Extract tasks" onClick={() => requestFeature("TASKS")}>
          <CheckSquare size={15} /> Tasks
        </button>
      </div>
      {panel.status !== "idle" && (
        <div className="panel">
          {panel.status === "loading" && (
            <div className="row">
              <Loader2 className="spin" size={16} /> Working on {panel.feature.toLowerCase()}...
            </div>
          )}
          {panel.status === "summary" && (
            <>
              <strong>Summary</strong>
              <ul>{panel.data.bullets.map((bullet) => <li key={bullet}>{renderSummaryBullet(bullet)}</li>)}</ul>
              <p className="muted">{panel.data.modelVersion}</p>
            </>
          )}
          {panel.status === "reply" && (
            <>
              <strong>Suggested Reply</strong>
              <textarea readOnly value={panel.data.reply} />
              <div className="row">
                <button title="Good reply" onClick={() => submitFeedback("up", panel.data.reply)}>
                  <ThumbsUp size={15} />
                </button>
                <button title="Needs improvement" onClick={() => submitFeedback("down", panel.data.reply)}>
                  <ThumbsDown size={15} />
                </button>
                <span className="muted">{panel.data.tone} tone - {panel.data.modelVersion}</span>
              </div>
              {feedbackStatus && <p className="success">{feedbackStatus}</p>}
            </>
          )}
          {panel.status === "tasks" && (
            <>
              <strong>Tasks</strong>
              <ul>
                {panel.data.tasks.map((task) => (
                  <li key={task.id}>{task.text}{task.deadline ? ` - ${task.deadline}` : ""}</li>
                ))}
              </ul>
              <p className="muted">{panel.data.modelVersion}</p>
            </>
          )}
          {panel.status === "error" && <span>{panel.message}</span>}
        </div>
      )}
    </>
  );
}

export function injectToolbar(email: EmailContext) {
  const existing = document.getElementById("ai-email-assistant-root");
  existing?.remove();

  const mount = document.createElement("div");
  mount.id = "ai-email-assistant-root";

  const target =
    document.querySelector<HTMLElement>("h2[data-thread-perm-id], h2.hP")?.parentElement ??
    document.querySelector<HTMLElement>("[role='main']");

  if (!target) return;
  target.insertAdjacentElement("afterend", mount);

  const shadow = mount.attachShadow({ mode: "open" });
  const app = document.createElement("div");
  shadow.appendChild(app);
  createRoot(app).render(<Toolbar email={email} />);
}
