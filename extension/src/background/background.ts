import { enqueue } from "./apiQueue";

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    "ai-email.usage": {
      processedToday: 0,
      timeSavedMinutes: 0,
      mostUsedFeature: "None",
      lastUsedFeature: "None",
      byFeature: {},
      processedEmailIds: []
    }
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message?.type || !message?.payload) {
    sendResponse({ ok: false, error: "Invalid message" });
    return false;
  }

  enqueue(message.type, message.payload)
    .then((data) => sendResponse({ ok: true, data }))
    .catch((error) => sendResponse({ ok: false, error: error instanceof Error ? error.message : "Unknown error" }));
  return true;
});
