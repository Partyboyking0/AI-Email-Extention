import { DEFAULT_SETTINGS, STORAGE_KEYS } from "./constants";
import type { Tone, UserSettings } from "./types";

async function currentSettings(): Promise<UserSettings> {
  const result = await chrome.storage.local.get(STORAGE_KEYS.settings);
  return { ...DEFAULT_SETTINGS, ...(result[STORAGE_KEYS.settings] ?? {}) };
}

export async function syncPreferencesToBackend(tone: Tone, modelVersion: string): Promise<boolean> {
  try {
    const settings = await currentSettings();
    const tokenResult = await chrome.storage.local.get("ai-email.jwt");
    const token = tokenResult["ai-email.jwt"]?.token;
    const response = await fetch(`${settings.apiBaseUrl}/api/users/me/preferences`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ tone, model_version: modelVersion })
    });
    return response.ok;
  } catch (error) {
    console.warn("[AI Email Assistant] Preference sync failed.", error);
    return false;
  }
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const settings = await currentSettings();
    const response = await fetch(`${settings.apiBaseUrl}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
