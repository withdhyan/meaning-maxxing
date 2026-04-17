/**
 * Feed filter engine.
 *
 * Uses MutationObserver to watch for new feed items, scores them against
 * the user's attention policies, and applies CSS classes for visual
 * filtering (dim/neutral/resonant).
 */

const MeaningFilter = window.MeaningFilter || {};
window.MeaningFilter = MeaningFilter;

MeaningFilter.Filter = (() => {
  const ATTR = "data-mf-scored";
  let _enabled = true;
  let _mode = "dim"; // "dim" | "hide" | "highlight"
  let _observer = null;
  let _stats = { total: 0, resonant: 0, dimmed: 0 };

  async function start() {
    const settings = await new Promise((resolve) => {
      chrome.storage.local.get(["enabled", "mode"], resolve);
    });
    _enabled = settings.enabled !== false;
    _mode = settings.mode || "dim";

    if (!_enabled) return;

    await MeaningFilter.Scorer.init();

    const platform = MeaningFilter.Platform.get();
    if (!platform) return;

    // Score existing items
    _scoreAll(platform);

    // Watch for new items
    _observer = new MutationObserver((mutations) => {
      let hasNew = false;
      for (const m of mutations) {
        if (m.addedNodes.length > 0) {
          hasNew = true;
          break;
        }
      }
      if (hasNew) _scoreAll(platform);
    });

    _observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Listen for settings changes
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.enabled) {
        _enabled = changes.enabled.newValue !== false;
        if (!_enabled) _removeAll();
        else _scoreAll(platform);
      }
      if (changes.mode) {
        _mode = changes.mode.newValue || "dim";
        _reapplyAll();
      }
      if (changes.values) {
        MeaningFilter.Scorer.init().then(() => {
          _clearScores();
          _scoreAll(platform);
        });
      }
    });
  }

  function _scoreAll(platform) {
    if (!_enabled) return;
    const items = document.querySelectorAll(platform.selector);
    for (const item of items) {
      if (item.hasAttribute(ATTR)) continue;

      const text = platform.getText(item);
      if (!text || text.length < 10) continue;

      const result = MeaningFilter.Scorer.score(text);
      const bucket = MeaningFilter.Scorer.classify(result.score);

      item.setAttribute(ATTR, bucket);
      _applyClass(item, bucket);
      _stats.total++;
      if (bucket === "resonant") _stats.resonant++;
      if (bucket === "dim") _stats.dimmed++;
    }
    _reportStats();
  }

  function _applyClass(el, bucket) {
    el.classList.remove("mf-resonant", "mf-neutral", "mf-dim", "mf-hidden");
    if (_mode === "hide" && bucket === "dim") {
      el.classList.add("mf-hidden");
    } else if (_mode === "highlight" && bucket === "resonant") {
      el.classList.add("mf-resonant");
    } else {
      el.classList.add(`mf-${bucket}`);
    }
  }

  function _reapplyAll() {
    const scored = document.querySelectorAll(`[${ATTR}]`);
    for (const el of scored) {
      const bucket = el.getAttribute(ATTR);
      _applyClass(el, bucket);
    }
  }

  function _removeAll() {
    const scored = document.querySelectorAll(`[${ATTR}]`);
    for (const el of scored) {
      el.classList.remove("mf-resonant", "mf-neutral", "mf-dim", "mf-hidden");
    }
  }

  function _clearScores() {
    const scored = document.querySelectorAll(`[${ATTR}]`);
    for (const el of scored) {
      el.removeAttribute(ATTR);
      el.classList.remove("mf-resonant", "mf-neutral", "mf-dim", "mf-hidden");
    }
    _stats = { total: 0, resonant: 0, dimmed: 0 };
  }

  function _reportStats() {
    chrome.runtime.sendMessage({ type: "stats", stats: _stats });
  }

  function getStats() {
    return _stats;
  }

  return { start, getStats };
})();

// Start when platform adapter is ready
if (MeaningFilter.Platform.get()) {
  MeaningFilter.Filter.start();
} else {
  document.addEventListener("mf:platform-ready", () => {
    MeaningFilter.Filter.start();
  });
}
