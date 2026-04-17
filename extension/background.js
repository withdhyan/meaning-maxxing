/**
 * Service worker: manages values storage, handles messages from
 * content scripts and popup.
 */

// Default state
const DEFAULTS = {
  enabled: true,
  mode: "dim", // "dim" | "hide" | "highlight"
  values: [],
  apiUrl: "",
  stats: { total: 0, resonant: 0, dimmed: 0 },
};

// Initialize on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(null, (existing) => {
    const merged = { ...DEFAULTS, ...existing };
    chrome.storage.local.set(merged);
  });
});

// Handle messages
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  switch (msg.type) {
    case "stats":
      chrome.storage.local.set({ stats: msg.stats });
      break;

    case "get-state":
      chrome.storage.local.get(null, (state) => {
        sendResponse(state);
      });
      return true; // async response

    case "import-values":
      _importFromApi(msg.apiUrl, msg.userId).then((result) => {
        sendResponse(result);
      });
      return true;

    case "set-values":
      chrome.storage.local.set({ values: msg.values });
      sendResponse({ ok: true });
      return true;

    case "toggle":
      chrome.storage.local.get(["enabled"], (s) => {
        chrome.storage.local.set({ enabled: !s.enabled });
        sendResponse({ enabled: !s.enabled });
      });
      return true;

    case "set-mode":
      chrome.storage.local.set({ mode: msg.mode });
      sendResponse({ ok: true });
      return true;
  }
});

/**
 * Import values from the matching API.
 */
async function _importFromApi(apiUrl, userId) {
  try {
    const resp = await fetch(`${apiUrl}/user/${userId}`);
    if (!resp.ok) {
      return { ok: false, error: `API returned ${resp.status}` };
    }
    const values = await resp.json();
    chrome.storage.local.set({ values, apiUrl });
    return { ok: true, count: values.length };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}
