import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BarChart3, Settings as SettingsIcon, Wand2 } from "lucide-react";
import { Actions } from "./Actions";
import { Dashboard } from "./Dashboard";
import { Settings } from "./Settings";
import { usePopupStore } from "./store";
import "./popup.css";

function App() {
  const [tab, setTab] = useState<"actions" | "dashboard" | "settings">("actions");
  const hydrate = usePopupStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <main>
      <header>
        <h1>AI Email Assistant</h1>
        <p>Gmail intelligence controls</p>
      </header>
      <nav>
        <button className={tab === "actions" ? "active" : ""} onClick={() => setTab("actions")}>
          <Wand2 size={15} /> Actions
        </button>
        <button className={tab === "dashboard" ? "active" : ""} onClick={() => setTab("dashboard")}>
          <BarChart3 size={15} /> Dashboard
        </button>
        <button className={tab === "settings" ? "active" : ""} onClick={() => setTab("settings")}>
          <SettingsIcon size={15} /> Settings
        </button>
      </nav>
      {tab === "actions" && <Actions />}
      {tab === "dashboard" && <Dashboard />}
      {tab === "settings" && <Settings />}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
