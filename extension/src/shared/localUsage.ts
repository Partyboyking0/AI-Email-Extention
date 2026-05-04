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

const LETTERS_READ_PER_SAVED_MINUTE = 900;

function formatFeature(feature: string | undefined) {
  if (!feature) return "None";
  return feature[0].toUpperCase() + feature.slice(1);
}

function normalizeUsage(value: Partial<UsageStats> | undefined): UsageStats {
  const byFeature = value?.byFeature ?? {};
  const processedEmailIds = [...new Set(value?.processedEmailIds ?? [])];
  const processedToday = Math.max(processedEmailIds.length, value?.processedToday ?? 0);
  const mostUsed = Object.entries(byFeature).sort((a, b) => b[1] - a[1])[0]?.[0];
  const lettersReadToday = value?.lettersReadToday ?? 0;
  const timeSavedMinutes = lettersReadToday
    ? Math.ceil(lettersReadToday / LETTERS_READ_PER_SAVED_MINUTE)
    : value?.timeSavedMinutes ?? 0;
  return {
    processedToday,
    timeSavedMinutes,
    mostUsedFeature: formatFeature(mostUsed),
    lastUsedFeature: value?.lastUsedFeature ?? "None",
    byFeature,
    processedEmailIds,
    lettersReadToday
  };
}

export async function getLocalUsage(): Promise<UsageStats> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.usage);
  return normalizeUsage(result[STORAGE_KEYS.usage] ?? EMPTY_USAGE);
}

export async function incrementLocalUsage(feature: Feature, emailId: string, lettersRead: number): Promise<UsageStats> {
  const current = await getLocalUsage();
  const processedEmailIds = [...new Set(current.processedEmailIds ?? [])];
  const isNewEmail = !processedEmailIds.includes(emailId);
  const next = normalizeUsage({
    byFeature: {
      ...current.byFeature,
      [feature]: (current.byFeature[feature] ?? 0) + 1
    },
    processedToday: current.processedToday + (isNewEmail ? 1 : 0),
    processedEmailIds: isNewEmail ? [...processedEmailIds, emailId] : processedEmailIds,
    lettersReadToday: (current.lettersReadToday ?? 0) + (isNewEmail ? lettersRead : 0),
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
