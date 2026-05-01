import type { EmailContext } from "../shared/types";

const EMAIL_SELECTORS = [
  ".ii.gt .a3s",
  ".a3s.aiL",
  ".a3s",
  "[data-message-id] .a3s",
  ".adn .a3s",
  "[role='main'] [data-message-id]"
];

function cleanText(value: string) {
  return value
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function textFromNode(node: HTMLElement) {
  const clone = node.cloneNode(true) as HTMLElement;
  clone.querySelectorAll("script, style, noscript, svg, img, [aria-hidden='true']").forEach((child) => child.remove());
  clone.querySelectorAll("[role='button'], button").forEach((child) => child.remove());
  return cleanText(clone.textContent ?? clone.innerText ?? "");
}

function uniqueTexts(nodes: HTMLElement[]) {
  const seen = new Set<string>();
  const texts: string[] = [];
  for (const node of nodes) {
    const text = textFromNode(node);
    const key = text.slice(0, 300);
    if (text.length > 30 && !seen.has(key)) {
      seen.add(key);
      texts.push(text);
    }
  }
  return texts;
}

export function extractEmailContext(): EmailContext | null {
  for (const selector of EMAIL_SELECTORS) {
    const nodes = Array.from(document.querySelectorAll<HTMLElement>(selector));
    const text = uniqueTexts(nodes).join("\n\n---\n\n");
    if (text.length > 30) {
      const subject = cleanText(document.querySelector<HTMLElement>("h2[data-thread-perm-id], h2.hP")?.innerText ?? "");
      const threadId =
        document.querySelector<HTMLElement>("[data-thread-id]")?.dataset.threadId ??
        document.querySelector<HTMLElement>("[data-message-id]")?.dataset.messageId ??
        location.hash;

      console.info("[AI Email Assistant] Email extracted with selector:", selector);
      console.info("[AI Email Assistant] Extracted characters:", text.length);
      return { threadId, subject, emailText: text, selector };
    }
  }

  console.warn("[AI Email Assistant] No Gmail email body selector matched.");
  return null;
}
