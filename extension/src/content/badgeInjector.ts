import { LABEL_COLORS } from "../shared/constants";
import { classifyEmail } from "./onnxClassifier";

const BADGE_CLASS = "ai-email-classifier-badge";
const ROW_SELECTORS = ["tr.zA", "[role='main'] tr[role='link']", "[role='main'] tr"];

function createBadge(label: string, score: number) {
  const badge = document.createElement("span");
  badge.className = BADGE_CLASS;
  badge.textContent = `${label} ${Math.round(score * 100)}%`;
  badge.title = "AI email classification";
  badge.style.cssText = [
    "display:inline-flex",
    "align-items:center",
    "margin-left:8px",
    "padding:2px 6px",
    "border-radius:999px",
    "font:500 11px Arial,sans-serif",
    "line-height:1.4",
    "color:#fff",
    `background:${LABEL_COLORS[label] ?? "#5f6368"}`,
    "vertical-align:middle",
    "white-space:nowrap"
  ].join(";");
  return badge;
}

function getRows() {
  for (const selector of ROW_SELECTORS) {
    const rows = Array.from(document.querySelectorAll<HTMLElement>(selector))
      .filter((row) => row.innerText && row.innerText.length > 20)
      .slice(0, 20);
    if (rows.length > 0) return rows;
  }
  return [];
}

function getBadgeTarget(row: HTMLElement) {
  return row.querySelector<HTMLElement>(".y6, .bog, [email], td:nth-child(6)") ?? row;
}

export async function classifyVisibleRows() {
  const rows = getRows().filter((row) => !row.querySelector(`.${BADGE_CLASS}`));
  for (const row of rows) {
    const result = await classifyEmail(row.innerText);
    const target = getBadgeTarget(row);
    target.appendChild(createBadge(result.label, result.score));
  }
}
