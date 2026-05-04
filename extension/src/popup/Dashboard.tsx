import { RefreshCcw, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { STORAGE_KEYS } from "../shared/constants";
import { checkBackendHealth } from "../shared/settingsApi";
import type { UsageStats } from "../shared/types";
import { Badge } from "./components/Badge";

export function Dashboard() {
  const [backendReady, setBackendReady] = useState<boolean | null>(null);
  const [usage, setUsage] = useState<UsageStats>({
    processedToday: 0,
    timeSavedMinutes: 0,
    mostUsedFeature: "None",
    lastUsedFeature: "None",
    byFeature: {}
  });

  async function refreshDashboard() {
    checkBackendHealth().then(setBackendReady);
    const response = await chrome.runtime.sendMessage({ type: "USAGE_STATS", payload: {} });
    if (response?.ok) setUsage(response.data);
  }

  async function resetUsage() {
    const response = await chrome.runtime.sendMessage({ type: "RESET_USAGE", payload: {} });
    if (response?.ok) setUsage(response.data);
  }

  useEffect(() => {
    refreshDashboard();
  }, []);

  useEffect(() => {
    function syncUsage(changeSet: Record<string, chrome.storage.StorageChange>, areaName: string) {
      if (areaName !== "local") return;
      const usageChange = changeSet[STORAGE_KEYS.usage];
      if (usageChange?.newValue) setUsage(usageChange.newValue as UsageStats);
    }

    chrome.storage.onChanged.addListener(syncUsage);
    return () => chrome.storage.onChanged.removeListener(syncUsage);
  }, []);

  return (
    <section className="view">
      <div className="dashboard-actions">
        <button title="Refresh dashboard" onClick={refreshDashboard}>
          <RefreshCcw size={15} /> Refresh
        </button>
        <button title="Reset local usage" onClick={resetUsage}>
          <RotateCcw size={15} /> Reset
        </button>
      </div>
      <div className="metric">
        <span>Emails processed today</span>
        <strong>{usage.processedToday}</strong>
      </div>
      <div className="metric">
        <span>Estimated time saved</span>
        <strong>{usage.timeSavedMinutes} min</strong>
      </div>
      <div className="metric">
        <span>Last used feature</span>
        <Badge>{usage.lastUsedFeature ?? "None"}</Badge>
      </div>
      <div className="metric">
        <span>Backend status</span>
        <Badge>{backendReady === null ? "Checking" : backendReady ? "Connected" : "Offline fallback"}</Badge>
      </div>
    </section>
  );
}
