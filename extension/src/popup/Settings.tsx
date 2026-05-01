import type { Tone } from "../shared/types";
import { usePopupStore } from "./store";

const tones: Tone[] = ["formal", "casual", "concise"];

export function Settings() {
  const { settings, setTone, setApiBaseUrl } = usePopupStore();

  return (
    <section className="view">
      <label>
        Tone preference
        <select value={settings.tone} onChange={(event) => setTone(event.target.value as Tone)}>
          {tones.map((tone) => <option key={tone} value={tone}>{tone}</option>)}
        </select>
      </label>
      <label>
        API base URL
        <input value={settings.apiBaseUrl} onChange={(event) => setApiBaseUrl(event.target.value)} />
      </label>
      <div className="model-row">
        <span>Model version</span>
        <strong>{settings.modelVersion}</strong>
      </div>
    </section>
  );
}
