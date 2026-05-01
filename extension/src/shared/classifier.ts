export interface ClassificationResponse {
  label: string;
  score: number;
  modelVersion: string;
  source: "onnx" | "keyword";
}

type Signal = {
  label: string;
  pattern: RegExp;
  weight: number;
};

const SIGNALS: Signal[] = [
  { label: "urgent", pattern: /\b(urgent|asap|immediately|eod|blocked|critical|important)\b/i, weight: 0.36 },
  { label: "follow-up", pattern: /\b(following up|follow up|checking in|reminder|gentle reminder|waiting)\b/i, weight: 0.3 },
  { label: "action-required", pattern: /\b(please|can you|could you|need you to|submit|confirm|send|review)\b/i, weight: 0.28 },
  { label: "opportunity", pattern: /\b(internship|placement|tnp|training and placement|career opportunity|hiring|apply|campus drive)\b/i, weight: 0.42 },
  { label: "work", pattern: /\b(project|meeting|deadline|review|proposal|invoice|client|report)\b/i, weight: 0.26 },
  { label: "finance", pattern: /\b(invoice|payment|receipt|billing|refund|paid|amount due)\b/i, weight: 0.25 },
  { label: "personal", pattern: /\b(family|dinner|birthday|weekend|trip|holiday)\b/i, weight: 0.22 },
  { label: "spam", pattern: /\b(winner|free money|claim now|limited offer|act now|prize)\b/i, weight: 0.34 },
  { label: "newsletter", pattern: /\b(newsletter|unsubscribe|weekly update|digest|read more)\b/i, weight: 0.24 }
];

const BASE_MODEL_VERSION = "keyword-classifier-phase-2";
const ONNX_MODEL_PATH = "models/classifier/model.onnx";

let onnxAvailability: Promise<boolean> | undefined;

export async function classifyEmailClient(emailText: string): Promise<ClassificationResponse> {
  if (await hasBundledOnnxModel()) {
    // The ONNX model slot is intentionally detected before fallback so a trained
    // classifier can be wired in without changing the popup/background flow.
    return classifyWithKeywordFallback(emailText, "onnx-ready-keyword-fallback");
  }

  return classifyWithKeywordFallback(emailText, BASE_MODEL_VERSION);
}

async function hasBundledOnnxModel(): Promise<boolean> {
  onnxAvailability ??= checkOnnxModel();
  return onnxAvailability;
}

async function checkOnnxModel(): Promise<boolean> {
  if (!globalThis.chrome?.runtime?.getURL) return false;

  try {
    const url = chrome.runtime.getURL(ONNX_MODEL_PATH);
    const response = await fetch(url, { method: "HEAD" });
    return response.ok;
  } catch {
    return false;
  }
}

function classifyWithKeywordFallback(emailText: string, modelVersion: string): ClassificationResponse {
  const normalized = emailText.replace(/\s+/g, " ").trim();
  const scores = new Map<string, number>();

  for (const signal of SIGNALS) {
    if (signal.pattern.test(normalized)) {
      scores.set(signal.label, (scores.get(signal.label) ?? 0.18) + signal.weight);
    }
  }

  if (hasInstitutionalSignal(normalized)) {
    scores.set("opportunity", (scores.get("opportunity") ?? 0.18) + 0.42);
    scores.set("work", (scores.get("work") ?? 0.18) + 0.18);
    if (scores.has("newsletter")) {
      scores.set("newsletter", (scores.get("newsletter") ?? 0) * 0.35);
    }
  }

  if (scores.size === 0) {
    return {
      label: normalized.length > 900 ? "newsletter" : "low-priority",
      score: normalized.length > 900 ? 0.68 : 0.62,
      modelVersion,
      source: "keyword"
    };
  }

  const [label, score] = [...scores.entries()].sort((a, b) => b[1] - a[1])[0];
  return {
    label,
    score: Math.min(0.95, Math.max(0.55, score)),
    modelVersion,
    source: "keyword"
  };
}

function hasInstitutionalSignal(text: string): boolean {
  return /\b(tnp|training and placement|placement cell|career development|iiit|iit|nit|university|college|\.edu\b|\.ac\.in\b|@[^@\s]+\.ac\.in\b)\b/i.test(text);
}
