import { STORAGE_KEYS } from "./constants";
import type { Feature, UsageStats } from "./types";

const EMPTY_USAGE: UsageStats = {
  processedToday: 0,
  timeSavedMinutes: 0,
  mostUsedFeature: "None",
  lastUsedFeature: "None",
  byFeature: {},
  processedEmailIds: []
};

function formatFeature(feature: string | undefined) {
  if (!feature) return "None";
  return feature[0].toUpperCase() + feature.slice(1);
}

function normalizeUsage(value: Partial<UsageStats> | undefined): UsageStats {
  const byFeature = value?.byFeature ?? {};
  const processedEmailIds = [...new Set(value?.processedEmailIds ?? [])];
  const processedToday = processedEmailIds.length || value?.processedToday || 0;
  const mostUsed = Object.entries(byFeature).sort((a, b) => b[1] - a[1])[0]?.[0];
  return {
    processedToday,
    timeSavedMinutes: processedToday * 2,
    mostUsedFeature: formatFeature(mostUsed),
    lastUsedFeature: value?.lastUsedFeature ?? "None",
    byFeature,
    processedEmailIds
  };
}

export async function getLocalUsage(): Promise<UsageStats> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.usage);
  return normalizeUsage(result[STORAGE_KEYS.usage] ?? EMPTY_USAGE);
}

export async function incrementLocalUsage(feature: Feature, emailId: string): Promise<UsageStats> {
  const current = await getLocalUsage();
  const next = normalizeUsage({
    byFeature: {
      ...current.byFeature,
      [feature]: (current.byFeature[feature] ?? 0) + 1
    },
    processedEmailIds: [...(current.processedEmailIds ?? []), emailId],
    lastUsedFeature: formatFeature(feature)
  });
  await chrome.storage.local.set({ [STORAGE_KEYS.usage]: next });
  return next;
}

export async function saveLocalUsage(stats: UsageStats): Promise<UsageStats> {
  const normalized = normalizeUsage(stats);
  await chrome.storage.local.set({ [STORAGE_KEYS.usage]: normalized });
  return normalized;
}

export async function resetLocalUsage(): Promise<UsageStats> {
  await chrome.storage.local.set({ [STORAGE_KEYS.usage]: EMPTY_USAGE });
  return EMPTY_USAGE;
}
