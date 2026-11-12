// State Variables
let currentAnalysis = null;
let currentVisualMode = 'ela';

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupDropzone();
  loadDemoSamples();
});

// Navigation Handling
function setupNavigation() {
  const navButtons = document.querySelectorAll(".nav-item");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  const targetBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const targetPane = document.getElementById(`tab-${tabId}`);
  const pageTitle = document.getElementById("page-title");

  if (targetBtn) targetBtn.classList.add("active");
  if (targetPane) targetPane.classList.add("active");

  if (pageTitle) {
    if (tabId === "investigation") pageTitle.innerText = "Evidence analysis";
    else if (tabId === "methodology") pageTitle.innerText = "Methodology & Standards";
    else if (tabId === "stego-studio") pageTitle.innerText = "Stego Studio";
  }
}

// Dropzone & File Input Handling
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadAndAnalyze(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files.length > 0) {
      uploadAndAnalyze(fileInput.files[0]);
    }
  });
}

// Fetch Pre-built Demo Samples
async function loadDemoSamples() {
  const gridEl = document.getElementById("demo-cases-grid");
  if (!gridEl) return;

  try {
    const res = await fetch("/api/samples");
    const data = await res.json();
    
    if (!data.samples || data.samples.length === 0) {
      gridEl.innerHTML = `<div style="color: var(--text-muted); font-size: 11px;">No demo samples loaded.</div>`;
      return;
    }

    gridEl.innerHTML = data.samples.map(s => `
      <div class="demo-pill-btn" onclick="runSampleAnalysis('${s.filename}')" title="${s.description}">
        <div class="demo-pill-left">
          <span class="demo-pill-name">${s.filename}</span>
          <span class="demo-pill-badge">${s.description.split('(')[0].trim()}</span>
        </div>
        <span class="demo-run-glyph">Run →</span>
      </div>
    `).join("");

  } catch (err) {
    gridEl.innerHTML = `<div style="color: var(--accent-red); font-size: 11px;">Failed to load demo cases: ${err.message}</div>`;
  }
}

// Upload & Analyze Evidence File
async function uploadAndAnalyze(file) {
  showLoading(`Analyzing evidence: ${file.name}`);
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await res.json();
    currentAnalysis = data;
    renderAnalysisResults(data);
  } catch (err) {
    alert("Analysis Error: " + err.message);
  } finally {
    hideLoading();
  }
}

// Run Analysis on Selected Sample
async function runSampleAnalysis(sampleName) {
  showLoading(`Screening demo sample: ${sampleName}`);
  const formData = new FormData();
  formData.append("sample_name", sampleName);

  try {
    const res = await fetch("/api/analyze-sample", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await res.json();
    currentAnalysis = data;
    renderAnalysisResults(data);
  } catch (err) {
    alert("Sample Screening Error: " + err.message);
  } finally {
    hideLoading();
  }
}

// Stego Studio: Demo Generator
function handleDemoTypeChange() {
  const type = document.getElementById("demo-type").value;
  const coverGroup = document.getElementById("group-cover-text");
  const secretGroup = document.getElementById("group-secret-text");

  if (type === "zero_width") {
    coverGroup.style.display = "block";
    secretGroup.style.display = "block";
  } else if (type === "clean") {
    coverGroup.style.display = "none";
    secretGroup.style.display = "none";
  } else {
    coverGroup.style.display = "none";
    secretGroup.style.display = "block";
  }
}

async function handleGenerateDemo(event) {
  event.preventDefault();
  const demoType = document.getElementById("demo-type").value;
  const secretText = document.getElementById("demo-secret-text").value;
  const coverText = document.getElementById("demo-cover-text").value;

  const btn = document.getElementById("btn-generate-demo");
  btn.disabled = true;
  btn.innerHTML = `<span>⏳</span> Generating & Analyzing...`;

  const formData = new FormData();
  formData.append("demo_type", demoType);
  formData.append("secret_text", secretText);
  formData.append("cover_text", coverText);

  try {
    const res = await fetch("/api/generate-demo", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Generation failed");
    }

    const data = await res.json();
    currentAnalysis = data.analysis;
    switchTab("investigation");
    renderAnalysisResults(data.analysis);
  } catch (err) {
    alert("Demo Generation Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Generate Stego File & Analyze Instantly`;
  }
}

// Render Results Dashboard
function renderAnalysisResults(data) {
  const { triage, analysis, correlation, report, analysis_id, file_category } = data;

  // 1. Reference ID
  document.getElementById("res-analysis-ref").innerText = `REF: CASE-${analysis_id.substring(0,8).toUpperCase()}`;

  // 2. Verdict Master Banner & Gauge
  const scoreBadge = document.getElementById("score-badge");
  const verdictTag = document.getElementById("verdict-tag");
  const verdictTitle = document.getElementById("verdict-title");
  const verdictSummary = document.getElementById("verdict-summary");
  const verdictCard = document.getElementById("verdict-card");

  scoreBadge.innerText = correlation.risk_score;
  scoreBadge.style.borderColor = correlation.verdict_color;
  scoreBadge.style.color = correlation.verdict_color;
  scoreBadge.style.boxShadow = `0 0 20px ${correlation.verdict_color}33`;

  verdictTag.innerHTML = `<span>●</span> ${correlation.verdict}`;
  verdictTag.style.color = correlation.verdict_color;

  verdictTitle.innerText = correlation.verdict_label;
  verdictSummary.innerText = correlation.summary;
  verdictCard.style.borderLeftColor = correlation.verdict_color;

  // 3. Level 1 Triage Card
  document.getElementById("res-filename").innerText = triage.filename;
  document.getElementById("res-filesize").innerText = triage.filesize_formatted;
  document.getElementById("res-magic").innerText = triage.detected_format;
  document.getElementById("res-mime").innerText = triage.detected_mime;
  document.getElementById("res-entropy").innerText = `${triage.global_entropy} / 8.00 bits/byte`;
  document.getElementById("res-sha256").innerText = triage.hashes.sha256;
  document.getElementById("res-md5").innerText = triage.hashes.md5;

  const extBadge = document.getElementById("extension-badge");
  if (triage.extension_mismatch) {
    extBadge.className = "status-pill-alert";
    extBadge.innerText = "MISMATCH DETECTED!";
  } else {
    extBadge.className = "status-pill-clean";
    extBadge.innerText = "Signature Match";
  }

  // 4. Level 2 Steganography Card
  renderCategorySpecificAnalysis(file_category, analysis, correlation);

  // 5. Visual Artifact Forensics (For Images)
  const visualCard = document.getElementById("visual-card");
  if (file_category === "image" && analysis.visual_artifacts) {
    visualCard.style.display = "block";
    switchVisualTab('ela');
  } else {
    visualCard.style.display = "none";
  }

  // 6. Level 3 Correlation & Rules Card
  const rulesListEl = document.getElementById("rules-list");
  const rulesBadge = document.getElementById("rules-count-badge");
  rulesBadge.innerText = `${correlation.triggered_rules_count} Rule(s) Triggered`;

  if (correlation.triggered_rules_count > 0) {
    rulesBadge.className = "status-pill-alert";
    rulesListEl.innerHTML = correlation.triggered_rules.map(r => `
      <div class="rule-block">
        <div class="rule-header-row">
          <span class="rule-title">${r.name}</span>
          <span class="${r.severity === 'CRITICAL' ? 'status-pill-alert' : 'status-pill-warning'}">${r.severity}</span>
        </div>
        <span class="rule-id-tag">${r.rule_id}</span>
        <div class="rule-desc">${r.description}</div>
      </div>
    `).join("");
  } else {
    rulesBadge.className = "status-pill-clean";
    rulesListEl.innerHTML = `<div style="color: var(--accent-green); font-size: 12.5px; padding: 12px 0;">✓ Zero correlation anomalies detected. Evidence conforms to standard specifications.</div>`;
  }

  // Recommendations
  const recsListEl = document.getElementById("recommendations-list");
  recsListEl.innerHTML = correlation.forensic_recommendations.map(r => `<li>${r}</li>`).join("");

  // Reveal Results Viewport and smooth scroll
  const resultsViewport = document.getElementById("results-viewport");
  resultsViewport.style.display = "flex";
  resultsViewport.scrollIntoView({ behavior: 'smooth' });
}

function renderCategorySpecificAnalysis(category, analysis, correlation) {
  const contentEl = document.getElementById("stego-details-content");
  const badgeEl = document.getElementById("stego-status-badge");
  const titleEl = document.getElementById("stego-card-title");

  if (category === "image") {
    titleEl.innerText = "Image Steganalysis (Chi-Square & RS Test)";
    const chi2 = analysis.chi_square || {};
    const rs = analysis.rs_analysis || {};
    const overlay = analysis.container_overlay || {};
    const blind = analysis.blind_lsb || {};

    const isSuspicious = chi2.is_suspicious || rs.suspicious || overlay.overlay_found || blind.candidate_count > 0;
    badgeEl.className = isSuspicious ? "status-pill-alert" : "status-pill-clean";
    badgeEl.innerText = isSuspicious ? "Stego Indicators Found" : "Passes Statistical Tests";

    let html = `
      <div style="margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 6px;">
          1. Chi-Square (χ²) Pair-of-Values LSB Test
        </div>
        <table class="forensic-table" style="font-size: 11.5px;">
          <thead>
            <tr style="color: var(--text-muted); text-align: left; border-bottom: 1px solid var(--border-subtle);">
              <th style="padding: 4px;">Channel</th>
              <th style="padding: 4px;">χ² Stat</th>
              <th style="padding: 4px;">deg of freedom</th>
              <th style="padding: 4px;">p-Value</th>
              <th style="padding: 4px;">Status</th>
            </tr>
          </thead>
          <tbody>
    `;

    for (const [ch, res] of Object.entries(chi2.channels || {})) {
      const isSus = res.suspicious;
      html += `
        <tr>
          <td style="color: #ffffff; font-weight: 600; padding: 6px 4px;">${ch}</td>
          <td style="padding: 6px 4px;">${res.chi2_statistic}</td>
          <td style="padding: 6px 4px;">${res.degrees_of_freedom}</td>
          <td style="font-family: var(--font-mono); color: ${isSus ? '#ef4444' : '#10b981'}; padding: 6px 4px;">${res.p_value}</td>
          <td style="padding: 6px 4px;"><span class="${isSus ? 'status-pill-alert' : 'status-pill-clean'}">${isSus ? 'FLAGGED (p < 0.05)' : 'Normal'}</span></td>
        </tr>
      `;
    }

    html += `
          </tbody>
        </table>
      </div>

      <div style="margin-bottom: 14px; border-top: 1px solid var(--border-subtle); padding-top: 10px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 6px;">
          2. RS Steganalysis (Dual-Masking Group Shift)
        </div>
        <table class="forensic-table">
          <tr>
            <td class="td-label">Estimated Payload Fraction</td>
            <td class="td-value" style="color: ${rs.suspicious ? '#ef4444' : '#10b981'}; font-weight: 700;">
              ${rs.estimated_payload_percent || '0%'}
            </td>
          </tr>
          <tr>
            <td class="td-label">Regular Groups (R_M / R_-M)</td>
            <td class="td-value">${rs.regular_groups_pos} / ${rs.regular_groups_neg}</td>
          </tr>
          <tr>
            <td class="td-label">Singular Groups (S_M / S_-M)</td>
            <td class="td-value">${rs.singular_groups_pos} / ${rs.singular_groups_neg}</td>
          </tr>
        </table>
      </div>
    `;

    if (overlay.overlay_found) {
      html += `
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px; padding: 12px; margin-bottom: 12px;">
          <div style="color: #ef4444; font-size: 12px; font-weight: 700; margin-bottom: 4px;">⚠️ Trailing Container Overlay Discovered!</div>
          <p style="font-size: 11.5px; color: var(--text-secondary);">
            Found ${overlay.overlay_size_bytes} trailing bytes appended past ${overlay.marker_name}.
          </p>
          <div class="terminal-content" style="margin-top: 6px;">
            ${overlay.overlay_preview}
          </div>
        </div>
      `;
    }

    if (blind.candidate_count > 0) {
      html += `
        <div class="payload-terminal">
          <div class="terminal-title"><span>🔍</span> Extracted LSB Candidate Strings</div>
          ${blind.candidates.map(c => `
            <div style="margin-bottom: 6px;">
              <span style="font-size: 11px; color: var(--accent-cyan); font-weight: 600;">${c.type}:</span>
              <div class="terminal-content">${c.preview}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    contentEl.innerHTML = html;

  } else if (category === "text") {
    titleEl.innerText = "Text Steganography Screening (Zero-Width Analysis)";
    badgeEl.className = analysis.is_suspicious ? "status-pill-alert" : "status-pill-clean";
    badgeEl.innerText = analysis.is_suspicious ? "Invisible Characters Found" : "Clean Text";

    let html = `
      <table class="forensic-table">
        <tr>
          <td class="td-label">Total Visible Characters</td>
          <td class="td-value">${analysis.total_characters}</td>
        </tr>
        <tr>
          <td class="td-label">Zero-Width Hidden Characters</td>
          <td class="td-value" style="color: ${analysis.zero_width_characters_found > 0 ? '#ef4444' : '#10b981'}; font-weight: 700;">
            ${analysis.zero_width_characters_found} (${analysis.zero_width_ratio_percent}%)
          </td>
        </tr>
      </table>
    `;

    if (analysis.has_decoded_payload) {
      html += `
        <div class="payload-terminal">
          <div class="terminal-title"><span>🔓</span> Reconstructed Invisible Secret Message</div>
          <div class="terminal-content">${analysis.decoded_hidden_payload}</div>
        </div>
      `;
    }

    if (analysis.sample_positions && analysis.sample_positions.length > 0) {
      html += `
        <div style="margin-top: 10px;">
          <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">Detected Unicode Code Points:</div>
          <ul style="padding-left: 18px; font-size: 11px; color: var(--accent-cyan);">
            ${analysis.sample_positions.map(p => `<li>${p.name} (${p.char}) at character index ${p.index}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    contentEl.innerHTML = html;

  } else if (category === "pdf") {
    titleEl.innerText = "PDF Document Steganography Screening";
    badgeEl.className = analysis.is_suspicious ? "status-pill-alert" : "status-pill-clean";
    badgeEl.innerText = analysis.is_suspicious ? "Marker / Overlay Found" : "Normal PDF";

    contentEl.innerHTML = `
      <table class="forensic-table">
        <tr>
          <td class="td-label">Page Count</td>
          <td class="td-value">${analysis.num_pages}</td>
        </tr>
        <tr>
          <td class="td-label">/StegoData Marker</td>
          <td class="td-value" style="color: ${analysis.stegodata_marker_found ? '#ef4444' : '#10b981'}; font-weight: 700;">
            ${analysis.stegodata_marker_found ? 'DETECTED in Object Stream' : 'None'}
          </td>
        </tr>
        <tr>
          <td class="td-label">Trailing Data Past %%EOF</td>
          <td class="td-value" style="color: ${analysis.trailing_data_after_eof ? '#ef4444' : '#10b981'};">
            ${analysis.trailing_data_after_eof ? `${analysis.trailing_bytes} bytes appended` : 'None'}
          </td>
        </tr>
      </table>
      ${analysis.trailing_preview ? `
        <div class="payload-terminal">
          <div class="terminal-title">Appended Overlay Stream</div>
          <div class="terminal-content">${analysis.trailing_preview}</div>
        </div>
      ` : ''}
    `;

  } else {
    // Binary or Audio or Generic
    titleEl.innerText = `${triage.detected_format} Structural Screening`;
    contentEl.innerHTML = `
      <table class="forensic-table">
        <tr>
          <td class="td-label">Format Classification</td>
          <td class="td-value">${category.toUpperCase()}</td>
        </tr>
        <tr>
          <td class="td-label">Structural Validation</td>
          <td class="td-value">${analysis.is_suspicious ? 'Structural anomaly flagged' : 'Compliant with specification'}</td>
        </tr>
      </table>
    `;
  }
}

// Visual Tab Handling (ELA vs LSB Bit-Plane)
function switchVisualTab(mode) {
  currentVisualMode = mode;
  const btnEla = document.getElementById("btn-show-ela");
  const btnLsb = document.getElementById("btn-show-lsb");
  const imgEl = document.getElementById("visual-img");
  const captionEl = document.getElementById("visual-caption");

  if (!currentAnalysis || !currentAnalysis.analysis.visual_artifacts) return;

  const artifacts = currentAnalysis.analysis.visual_artifacts;

  if (mode === 'ela') {
    btnEla.classList.add("active");
    btnLsb.classList.remove("active");
    imgEl.src = artifacts.ela_data_url;
    captionEl.innerText = "Error Level Analysis (ELA): Amplifies compression discrepancies to highlight spliced, manipulated, or resaved pixel clusters.";
  } else {
    btnLsb.classList.add("active");
    btnEla.classList.remove("active");
    imgEl.src = artifacts.lsb_plane_data_url;
    captionEl.innerText = "LSB Bit-Plane Visualizer (Bit 0): Unveils hidden static noise. Natural images have smooth bit planes, while stego embedding produces random high-frequency static.";
  }
}

// Copy to Clipboard with Toast
function copyText(elementId, label) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText.trim();
  navigator.clipboard.writeText(text).then(() => {
    showToast(`Copied ${label} to clipboard!`);
  }).catch(() => {
    showToast(`Failed to copy`);
  });
}

function showToast(msg) {
  const toast = document.getElementById("toast-notice");
  if (!toast) return;
  toast.innerText = msg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 2200);
}

// Modal Report Generation
function openReportModal() {
  if (!currentAnalysis) return;
  const report = currentAnalysis.report;
  const contentEl = document.getElementById("report-content");

  contentEl.innerHTML = `
    <div style="border: 2px solid var(--border-medium); padding: 24px; background: rgba(10, 15, 26, 0.95); border-radius: 8px;">
      <div style="text-align: center; border-bottom: 2px solid var(--border-subtle); padding-bottom: 14px; margin-bottom: 16px;">
        <h2 style="font-size: 17px; color: #ffffff; letter-spacing: 0.5px;">${report.report_header.title}</h2>
        <div style="color: var(--accent-copper); font-size: 11px; margin-top: 4px; font-weight: 600;">
          ${report.report_header.tool_name} — v${report.report_header.tool_version}
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 12px;">
        <div><strong>Case ID:</strong> <span style="font-family: var(--font-mono);">${report.report_header.case_id}</span></div>
        <div><strong>Evidence ID:</strong> <span style="font-family: var(--font-mono);">${report.report_header.evidence_id}</span></div>
        <div><strong>Timestamp:</strong> ${report.report_header.generated_at}</div>
        <div><strong>Risk Verdict:</strong> <span style="color: ${currentAnalysis.correlation.verdict_color}; font-weight: bold;">${report.verdict_summary.verdict_label} (${report.verdict_summary.risk_score}/100)</span></div>
      </div>

      <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px; margin-bottom: 8px;">
        1. CHAIN OF CUSTODY &amp; EVIDENCE INTEGRITY
      </div>
      <table class="forensic-table" style="font-size: 11.5px; margin-bottom: 16px;">
        <tr><td class="td-label">Source Filename:</td><td class="td-value">${report.evidence_integrity.filename}</td></tr>
        <tr><td class="td-label">File Size:</td><td class="td-value">${report.evidence_integrity.filesize}</td></tr>
        <tr><td class="td-label">Magic Header:</td><td class="td-value">${report.evidence_integrity.magic_signature}</td></tr>
        <tr><td class="td-label">SHA-256 Digest:</td><td class="td-value"><span style="font-family: var(--font-mono); color: #38bdf8;">${report.evidence_integrity.sha256}</span></td></tr>
        <tr><td class="td-label">MD5 Digest:</td><td class="td-value"><span style="font-family: var(--font-mono); color: #38bdf8;">${report.evidence_integrity.md5}</span></td></tr>
      </table>

      <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px; margin-bottom: 8px;">
        2. CORRELATED FINDINGS &amp; TRIGGERED RULES
      </div>
      <div style="margin-bottom: 16px;">
        ${report.triggered_rules.length > 0 ? report.triggered_rules.map(r => `
          <div style="background: rgba(0,0,0,0.4); padding: 8px 12px; border-left: 3px solid #ef4444; margin-bottom: 6px; font-size: 11.5px;">
            <strong>[${r.rule_id}] ${r.name} (${r.severity})</strong><br>
            <span style="color: var(--text-secondary);">${r.description}</span>
          </div>
        `).join("") : '<div style="color: #10b981; font-size: 12px;">No anomalous rules triggered. Evidence conforms to expected format standards.</div>'}
      </div>

      <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; border-bottom: 1px solid var(--border-subtle); padding-bottom: 4px; margin-bottom: 8px;">
        3. RECOMMENDED FORENSIC ACTIONS
      </div>
      <ul style="padding-left: 18px; font-size: 11.5px; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.6;">
        ${report.recommendations.map(rc => `<li>${rc}</li>`).join("")}
      </ul>

      <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 4px; padding: 12px; font-size: 11px; color: var(--accent-copper); line-height: 1.5;">
        ${report.forensic_disclaimer}
      </div>
    </div>
  `;

  document.getElementById("report-modal").style.display = "flex";
}

function closeReportModal() {
  document.getElementById("report-modal").style.display = "none";
}

function downloadAuditJson() {
  if (!currentAnalysis) return;
  const jsonStr = JSON.stringify(currentAnalysis, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Forensic_Audit_${currentAnalysis.analysis_id.substring(0,8)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// Helpers
function showLoading(msg) {
  document.getElementById("loading-status").innerText = msg;
  document.getElementById("loading-overlay").style.display = "block";
  document.getElementById("results-viewport").style.display = "none";
}

function hideLoading() {
  document.getElementById("loading-overlay").style.display = "none";
}
