import { create } from "zustand";
import { DEFAULT_SETTINGS, STORAGE_KEYS } from "../shared/constants";
import { syncPreferencesToBackend } from "../shared/settingsApi";
import type { Tone, UserSettings } from "../shared/types";

interface PopupState {
  settings: UserSettings;
  hydrate: () => Promise<void>;
  setTone: (tone: Tone) => Promise<void>;
  setApiBaseUrl: (apiBaseUrl: string) => Promise<void>;
}

export const usePopupStore = create<PopupState>((set, get) => ({
  settings: DEFAULT_SETTINGS,
  async hydrate() {
    const result = await chrome.storage.local.get(STORAGE_KEYS.settings);
    const stored = result[STORAGE_KEYS.settings] ?? {};
    const settings = { ...DEFAULT_SETTINGS, ...stored };
    if (settings.apiBaseUrl === "http://127.0.0.1:8000") {
      settings.apiBaseUrl = DEFAULT_SETTINGS.apiBaseUrl;
      await chrome.storage.local.set({ [STORAGE_KEYS.settings]: settings });
    }
    set({ settings });
  },
  async setTone(tone) {
    const settings = { ...get().settings, tone };
    await chrome.storage.local.set({ [STORAGE_KEYS.settings]: settings });
    void syncPreferencesToBackend(tone, settings.modelVersion);
    set({ settings });
  },
  async setApiBaseUrl(apiBaseUrl) {
    const settings = { ...get().settings, apiBaseUrl };
    await chrome.storage.local.set({ [STORAGE_KEYS.settings]: settings });
    set({ settings });
  }
}));
