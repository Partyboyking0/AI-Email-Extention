import type { EmailContext } from "./types";

function hashText(text: string): string {
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(36);
}

export function usageEmailId(email: EmailContext): string {
  const base = (email.threadId || email.subject || "email")
    .replace(/[^a-z0-9_-]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return `${base || "email"}:${hashText(email.emailText)}`.slice(0, 128);
}
