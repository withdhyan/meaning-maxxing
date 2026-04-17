document.addEventListener("DOMContentLoaded", () => {
  const apiUrl = document.getElementById("api-url");
  const userId = document.getElementById("user-id");
  const importBtn = document.getElementById("import-btn");
  const importStatus = document.getElementById("import-status");
  const newTitle = document.getElementById("new-title");
  const newPolicies = document.getElementById("new-policies");
  const addBtn = document.getElementById("add-btn");
  const valuesContainer = document.getElementById("values-container");
  const exportBtn = document.getElementById("export-btn");
  const importJsonBtn = document.getElementById("import-json-btn");
  const importFile = document.getElementById("import-file");

  let _values = [];

  // Load
  chrome.storage.local.get(["values", "apiUrl"], (result) => {
    _values = result.values || [];
    if (result.apiUrl) apiUrl.value = result.apiUrl;
    _render();
  });

  // Import from API
  importBtn.addEventListener("click", () => {
    const url = apiUrl.value.trim();
    const uid = userId.value.trim();
    if (!url || !uid) {
      _showStatus("error", "Both API URL and User ID are required.");
      return;
    }
    importBtn.disabled = true;
    importBtn.textContent = "Importing...";

    chrome.runtime.sendMessage(
      { type: "import-values", apiUrl: url, userId: uid },
      (result) => {
        importBtn.disabled = false;
        importBtn.textContent = "Import";
        if (result && result.ok) {
          _showStatus("success", `Imported ${result.count} values.`);
          chrome.storage.local.get(["values"], (r) => {
            _values = r.values || [];
            _render();
          });
        } else {
          _showStatus("error", result ? result.error : "Import failed.");
        }
      }
    );
  });

  // Add manual value
  addBtn.addEventListener("click", () => {
    const title = newTitle.value.trim();
    const policiesText = newPolicies.value.trim();
    if (!title || !policiesText) return;

    const policies = policiesText
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (policies.length === 0) return;

    const value = { title, policies };
    _values.push(value);
    chrome.runtime.sendMessage({ type: "set-values", values: _values });
    newTitle.value = "";
    newPolicies.value = "";
    _render();
  });

  // Export
  exportBtn.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(_values, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "meaning-filter-values.json";
    a.click();
    URL.revokeObjectURL(url);
  });

  // Import JSON
  importJsonBtn.addEventListener("click", () => importFile.click());
  importFile.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const imported = JSON.parse(ev.target.result);
        if (!Array.isArray(imported)) throw new Error("Expected array");
        _values = imported;
        chrome.runtime.sendMessage({ type: "set-values", values: _values });
        _render();
      } catch (err) {
        alert("Invalid JSON file: " + err.message);
      }
    };
    reader.readAsText(file);
  });

  // Remove value
  valuesContainer.addEventListener("click", (e) => {
    if (e.target.classList.contains("remove")) {
      const idx = parseInt(e.target.dataset.idx, 10);
      _values.splice(idx, 1);
      chrome.runtime.sendMessage({ type: "set-values", values: _values });
      _render();
    }
  });

  function _render() {
    if (_values.length === 0) {
      valuesContainer.innerHTML = '<p style="color: #555;">No values yet.</p>';
      return;
    }
    valuesContainer.innerHTML = _values
      .map(
        (v, i) => `
      <div class="value-card">
        <span class="remove" data-idx="${i}">remove</span>
        <h4>${_esc(v.title)}</h4>
        ${(v.policies || []).map((p) => `<div class="policy">${_esc(p)}</div>`).join("")}
      </div>`
      )
      .join("");
  }

  function _showStatus(type, msg) {
    importStatus.className = "status " + type;
    importStatus.textContent = msg;
    setTimeout(() => {
      importStatus.className = "status";
    }, 5000);
  }

  function _esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
});
