import { extractEmailContext } from "./domReader";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "READ_ACTIVE_EMAIL") return false;

  const email = extractEmailContext();
  if (!email) {
    sendResponse({ ok: false, error: "Open a Gmail email first, then try again." });
    return false;
  }

  sendResponse({ ok: true, data: email });
  return false;
});
