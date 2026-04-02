/**
 * Metadata Cleaner — Upload UI
 * Handles: drag-and-drop, file validation, metadata preview, cleaning, toasts.
 */

(() => {
  "use strict";

  const MAX_FILES = window.APP_CONFIG?.maxFiles ?? 20;
  const MAX_MB    = window.APP_CONFIG?.maxFileSizeMb ?? 100;

  // High-sensitivity field names for color-coding in the preview
  const SENSITIVE_FIELDS = new Set([
    "GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSPosition",
    "Author", "Creator", "Artist", "OwnerName", "SerialNumber",
    "CameraSerialNumber", "LensSerialNumber", "InternalSerialNumber",
    "Comment", "UserComment", "XPComment", "Software",
  ]);

  // ── State ────────────────────────────────────────────────

  /** @type {File[]} */
  let files = [];

  /** @type {Map<string, object>} filename -> metadata result */
  const metadataCache = new Map();

  let activePreviewFile = null;

  // ── DOM refs ─────────────────────────────────────────────

  const dropzone         = q("#dropzone");
  const fileInput        = q("#file-input");
  const browseBtn        = q("#browse-btn");
  const fileListSection  = q("#file-list-section");
  const fileListEl       = q("#file-list");
  const fileCountEl      = q("#file-count");
  const clearAllBtn      = q("#clear-all-btn");
  const optionsSection   = q("#options-section");
  const presetCards      = qAll(".preset-card");
  const cleanBtn         = q("#clean-btn");
  const previewBtn       = q("#preview-btn");
  const previewPanel     = q("#preview-panel");
  const previewTabs      = q("#preview-file-tabs");
  const previewData      = q("#preview-data");
  const previewLoading   = q("#preview-loading");
  const closePreviewBtn  = q("#close-preview-btn");
  const resultsPanel     = q("#results-panel");
  const sizeSummary      = q("#size-summary");
  const metadataDiff     = q("#metadata-diff");
  const progressWrap     = q("#progress-wrap");
  const progressBar      = q("#progress-bar");
  const progressLabel    = q("#progress-label");

  // ── Helpers ──────────────────────────────────────────────

  function q(sel)    { return document.querySelector(sel); }
  function qAll(sel) { return document.querySelectorAll(sel); }

  function formatSize(bytes) {
    if (bytes < 1024)           return bytes + " B";
    if (bytes < 1024 * 1024)    return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function ext(filename) {
    const parts = filename.split(".");
    return parts.length > 1 ? parts.pop().toUpperCase() : "FILE";
  }

  function fileKey(file) {
    return `${file.name}__${file.size}`;
  }

  function selectedPreset() {
    const checked = q('input[name="preset"]:checked');
    return checked ? checked.value : "full";
  }

  // ── Toast ─────────────────────────────────────────────────

  let toastStack = document.createElement("div");
  toastStack.className = "toast-stack";
  document.body.appendChild(toastStack);

  function toast(message, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    const icons = { error: "✕", success: "✓", info: "i" };
    el.innerHTML = `<span class="toast-icon">${icons[type] ?? "i"}</span><span class="toast-msg">${message}</span>`;
    toastStack.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  // ── File management ───────────────────────────────────────

  function addFiles(incoming) {
    const errors = [];

    for (const file of incoming) {
      if (files.length >= MAX_FILES) {
        errors.push(`Maximum ${MAX_FILES} files allowed.`);
        break;
      }

      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > MAX_MB) {
        errors.push(`"${file.name}" exceeds the ${MAX_MB} MB limit.`);
        continue;
      }

      const alreadyAdded = files.some(f => fileKey(f) === fileKey(file));
      if (alreadyAdded) continue;

      files.push(file);
    }

    if (errors.length) toast(errors[0], "error");
    renderFileList();
    updateVisibility();
  }

  function removeFile(key) {
    files = files.filter(f => fileKey(f) !== key);
    metadataCache.delete(key);
    renderFileList();
    updateVisibility();

    if (files.length === 0) {
      previewPanel.hidden = true;
      activePreviewFile = null;
    }
  }

  function clearAll() {
    files = [];
    metadataCache.clear();
    activePreviewFile = null;
    fileListEl.innerHTML = "";
    previewPanel.hidden = true;
    updateVisibility();
  }

  function updateVisibility() {
    const hasFiles = files.length > 0;
    fileListSection.hidden = !hasFiles;
    optionsSection.hidden  = !hasFiles;
    fileCountEl.textContent = files.length;
  }

  // ── Render file list ──────────────────────────────────────

  function renderFileList() {
    fileListEl.innerHTML = "";
    files.forEach(file => {
      const key = fileKey(file);
      const li = document.createElement("li");
      li.className = "file-item";
      li.dataset.key = key;

      li.innerHTML = `
        <div class="file-icon">${ext(file.name).slice(0, 4)}</div>
        <div class="file-info">
          <div class="file-name" title="${file.name}">${file.name}</div>
          <div class="file-meta">${formatSize(file.size)}</div>
        </div>
        <span class="file-status status-ready" data-status="${key}">Ready</span>
        <button class="file-remove-btn" aria-label="Remove ${file.name}" data-key="${key}">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>`;

      li.querySelector(".file-remove-btn").addEventListener("click", () => removeFile(key));
      fileListEl.appendChild(li);
    });

    fileCountEl.textContent = files.length;
  }

  function setFileStatus(key, status, label) {
    const el = q(`[data-status="${key}"]`);
    if (!el) return;
    el.className = `file-status status-${status}`;
    el.textContent = label;
  }

  // ── Preset selection ──────────────────────────────────────

  presetCards.forEach(card => {
    card.addEventListener("click", () => {
      presetCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      const radio = card.querySelector("input[type='radio']");
      if (radio) radio.checked = true;
    });
  });

  // Default selected visual
  const defaultCard = q(`.preset-card[data-preset="full"]`);
  if (defaultCard) defaultCard.classList.add("selected");

  // ── Metadata preview ──────────────────────────────────────

  previewBtn.addEventListener("click", async () => {
    if (files.length === 0) return;
    previewPanel.hidden = false;
    previewPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    await loadPreviewForFile(files[0]);
  });

  closePreviewBtn.addEventListener("click", () => {
    previewPanel.hidden = true;
  });

  async function loadPreviewForFile(file) {
    const key = fileKey(file);
    activePreviewFile = key;
    renderPreviewTabs();

    if (metadataCache.has(key)) {
      renderPreviewData(metadataCache.get(key));
      return;
    }

    previewLoading.hidden = false;
    previewData.innerHTML = "";

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/get_metadata", { method: "POST", body: formData });
      const json = await resp.json();

      if (!resp.ok) {
        throw new Error(json.error || "Failed to read metadata.");
      }

      metadataCache.set(key, json);
      renderPreviewData(json);
    } catch (err) {
      previewData.innerHTML = `<p class="no-metadata">Error: ${err.message}</p>`;
    } finally {
      previewLoading.hidden = true;
    }
  }

  function renderPreviewTabs() {
    previewTabs.innerHTML = "";
    files.forEach(file => {
      const key = fileKey(file);
      const btn = document.createElement("button");
      btn.className = `preview-tab ${key === activePreviewFile ? "active" : ""}`;
      btn.textContent = file.name.length > 24 ? file.name.slice(0, 22) + "…" : file.name;
      btn.addEventListener("click", () => loadPreviewForFile(file));
      previewTabs.appendChild(btn);
    });
  }

  function renderPreviewData(data) {
    const { categories, risk, field_count } = data;

    if (!categories || field_count === 0) {
      previewData.innerHTML = `<p class="no-metadata">No metadata found in this file.</p>`;
      return;
    }

    let html = "";

    // Risk banner
    const riskIcons = { high: "!", medium: "~", low: "." };
    const riskLabels = {
      high:   "High privacy risk — sensitive metadata detected.",
      medium: "Medium privacy risk — some personal fields present.",
      low:    "Low privacy risk — minimal sensitive metadata.",
    };

    html += `
      <div class="risk-banner ${risk.level}">
        <span class="risk-icon">${riskIcons[risk.level] ?? "?"}</span>
        <div class="risk-details">
          <p class="risk-title">${riskLabels[risk.level] ?? ""}</p>
          ${risk.reasons?.length
            ? `<p class="risk-reasons">${risk.reasons.join(" · ")}</p>`
            : ""}
        </div>
      </div>`;

    // Categories
    for (const [cat, fields] of Object.entries(categories)) {
      if (!fields || Object.keys(fields).length === 0) continue;

      html += `<div class="meta-category">
        <p class="category-title"><span class="category-dot"></span>${cat}</p>
        <table class="meta-table">`;

      for (const [field, value] of Object.entries(fields)) {
        const sensitive = SENSITIVE_FIELDS.has(field) ? "meta-sensitive" : "";
        const displayVal = typeof value === "object" ? JSON.stringify(value) : String(value);
        html += `
          <tr>
            <td class="meta-field">${field}</td>
            <td class="meta-value ${sensitive}">${escapeHtml(displayVal)}</td>
          </tr>`;
      }

      html += `</table></div>`;
    }

    previewData.innerHTML = html;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderCleanSummary(batch) {
    if (!batch || !batch.results || !batch.results.length) {
      resultsPanel.hidden = true;
      return;
    }

    resultsPanel.hidden = false;

    const cards = batch.results.map(file => {
      const beforeKB = (file.original_size / 1024).toFixed(1);
      const afterKB = (file.cleaned_size / 1024).toFixed(1);
      const reducedKB = file.size_reduction_kb.toFixed(1);
      const pct = file.size_reduction_pct.toFixed(1);
      return `
        <div class="size-card">
          <h3>${escapeHtml(file.filename)}</h3>
          <p>Original: <strong>${beforeKB} KB</strong></p>
          <p>Cleaned: <strong>${afterKB} KB</strong></p>
          <p>Reduction: <strong>${reducedKB} KB (${pct}%)</strong></p>
        </div>`;
    }).join("");

    sizeSummary.innerHTML = cards;

    let diffHtml = "";
    batch.results.forEach(file => {
      const before = file.metadata_comparison?.removed || [];
      const remaining = file.metadata_comparison?.remaining || [];

      const removedRows = before.map(field => `<tr class="diff-removed"><td>${escapeHtml(field)}</td><td>Removed</td></tr>`).join("");
      const remainingRows = remaining.map(field => `<tr class="diff-remaining"><td>${escapeHtml(field)}</td><td>Remaining</td></tr>`).join("");

      diffHtml += `
        <section class="file-diff">
          <h3>${escapeHtml(file.filename)}</h3>
          <table>
            <thead><tr><th>Field</th><th>Status</th></tr></thead>
            <tbody>${removedRows}${remainingRows}</tbody>
          </table>
        </section>`;
    });

    metadataDiff.innerHTML = diffHtml;
  }

  // ── Clean & download ──────────────────────────────────────

  cleanBtn.addEventListener("click", async () => {
    if (files.length === 0) return;

    const preset = selectedPreset();

    cleanBtn.disabled  = true;
    previewBtn.disabled = true;
    progressWrap.hidden = false;
    setProgress(5, "Uploading files...");

    const formData = new FormData();
    files.forEach(f => formData.append("files", f));
    formData.append("preset", preset);

    try {
      setProgress(30, "Processing metadata and cleaning files...");

      const resp = await fetch("/process_files?json=1", {
        method: "POST",
        body: formData,
        headers: {
          "Accept": "application/json",
        },
      });

      if (!resp.ok) {
        let errMsg = "Processing failed.";
        try {
          const errJson = await resp.json();
          errMsg = errJson.error || errMsg;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const data = await resp.json();
      setProgress(60, "Applying summary...");
      renderCleanSummary(data.batch);
      files.forEach(f => setFileStatus(fileKey(f), "done", "Cleaned"));

      setProgress(80, "Downloading cleaned archive...");
      const dlResponse = await fetch(data.download_url);
      if (!dlResponse.ok) throw new Error("Download failed.");

      const blob = await dlResponse.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "cleaned_files.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);

      setProgress(100, "Done!");
      toast("Files cleaned and downloaded.", "success");

    } catch (err) {
      files.forEach(f => setFileStatus(fileKey(f), "error", "Error"));
      toast(err.message || "Something went wrong.", "error");
      setProgress(0, "");
      progressWrap.hidden = true;
    } finally {
      cleanBtn.disabled   = false;
      previewBtn.disabled = false;
      setTimeout(() => {
        progressWrap.hidden = true;
        setProgress(0, "");
      }, 1800);
    }
  });

  function setProgress(pct, label) {
    progressBar.style.width  = `${pct}%`;
    progressLabel.textContent = label;
  }

  // ── Drag and drop ─────────────────────────────────────────

  dropzone.addEventListener("click", (e) => {
    if (e.target !== browseBtn) fileInput.click();
  });

  browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) addFiles(Array.from(fileInput.files));
    fileInput.value = "";
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("drag-over");
  });

  dropzone.addEventListener("dragleave", (e) => {
    if (!dropzone.contains(e.relatedTarget)) {
      dropzone.classList.remove("drag-over");
    }
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("drag-over");
    const dropped = Array.from(e.dataTransfer.files);
    if (dropped.length) addFiles(dropped);
  });

  clearAllBtn.addEventListener("click", clearAll);

  // Theme toggle (dark/light mode)
  const themeToggle = q("#theme-toggle");
  const userMode = localStorage.getItem("themeMode");
  const defaultMode = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

  function applyTheme(mode) {
    const body = document.body;
    if (!body) return;

    if (mode === "dark") {
      body.classList.add("dark-mode");
      body.classList.remove("light-mode");
      if (themeToggle) themeToggle.textContent = "🌙";
    } else {
      body.classList.add("light-mode");
      body.classList.remove("dark-mode");
      if (themeToggle) themeToggle.textContent = "☀️";
    }

    localStorage.setItem("themeMode", mode);
  }

  applyTheme(userMode || defaultMode);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const newMode = document.body.classList.contains("dark-mode") ? "light" : "dark";
      applyTheme(newMode);
    });
  }

  // Prevent browser default drop behavior outside the zone
  document.addEventListener("dragover", (e) => e.preventDefault());
  document.addEventListener("drop",     (e) => e.preventDefault());

})();
