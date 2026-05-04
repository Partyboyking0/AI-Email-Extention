import type { ReactNode } from "react";

const BOLD_PREFIX_PATTERN = /^\*\*([^*:]+)\*\*:?\s*(.*)$/;

export function renderSummaryBullet(bullet: string): ReactNode {
  const match = bullet.match(BOLD_PREFIX_PATTERN);
  if (!match) return bullet;

  const [, label, rest] = match;
  return (
    <>
      <strong>{label}:</strong> {rest}
    </>
  );
}
