document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("enabled");
  const modeButtons = document.querySelectorAll(".modes button");
  const statTotal = document.getElementById("stat-total");
  const statResonant = document.getElementById("stat-resonant");
  const statDimmed = document.getElementById("stat-dimmed");
  const valuesList = document.getElementById("values-list");
  const optionsLink = document.getElementById("options-link");

  // Load state
  chrome.runtime.sendMessage({ type: "get-state" }, (state) => {
    if (!state) return;
    toggle.checked = state.enabled !== false;
    _setActiveMode(state.mode || "dim");
    _renderStats(state.stats || {});
    _renderValues(state.values || []);
  });

  // Toggle
  toggle.addEventListener("change", () => {
    chrome.runtime.sendMessage({ type: "toggle" });
  });

  // Mode buttons
  for (const btn of modeButtons) {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      _setActiveMode(mode);
      chrome.runtime.sendMessage({ type: "set-mode", mode });
    });
  }

  // Options link
  optionsLink.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });

  function _setActiveMode(mode) {
    for (const b of modeButtons) {
      b.classList.toggle("active", b.dataset.mode === mode);
    }
  }

  function _renderStats(stats) {
    statTotal.textContent = stats.total || 0;
    statResonant.textContent = stats.resonant || 0;
    statDimmed.textContent = stats.dimmed || 0;
  }

  function _renderValues(values) {
    if (!values.length) {
      valuesList.innerHTML = '<span class="no-values">No values loaded. Add them in settings.</span>';
      return;
    }
    valuesList.innerHTML = values
      .map((v) => `<span class="value-tag">${_esc(v.title)}</span>`)
      .join("");
  }

  function _esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
});
