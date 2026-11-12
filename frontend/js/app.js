// State variables
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
  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

  const targetBtn = document.querySelector(`.nav-btn[data-tab="${tabId}"]`);
  const targetPane = document.getElementById(`tab-${tabId}`);

  if (targetBtn) targetBtn.classList.add("active");
  if (targetPane) targetPane.classList.add("active");
}

// Dropzone & File Input Handling
function setupDropzone() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");

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
  const listEl = document.getElementById("samples-list");
  try {
    const res = await fetch("/api/samples");
    const data = await res.json();
    
    if (!data.samples || data.samples.length === 0) {
      listEl.innerHTML = `<div style="color: var(--text-muted); padding: 10px; font-size: 0.8rem;">No demo samples loaded.</div>`;
      return;
    }

    listEl.innerHTML = data.samples.map(s => `
      <div class="sample-item" onclick="runSampleAnalysis('${s.filename}')">
        <div class="sample-info">
          <span class="sample-title">${s.filename}</span>
          <span class="sample-desc">${s.description}</span>
        </div>
        <button class="sample-run-btn">Run</button>
      </div>
    `).join("");

  } catch (err) {
    listEl.innerHTML = `<div style="color: var(--accent-red); font-size: 0.8rem; padding: 10px;">Failed to load samples: ${err.message}</div>`;
  }
}

// Upload & Analyze Evidence File
async function uploadAndAnalyze(file) {
  showLoading(`Screening uploaded file: ${file.name}`);
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

// Analyze Sample Directly
async function runSampleAnalysis(sampleName) {
  showLoading(`Analyzing test sample: ${sampleName}`);
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
    alert("Sample Analysis Error: " + err.message);
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

// UI Rendering
function renderAnalysisResults(data) {
  const { triage, analysis, correlation, report, analysis_id, file_category } = data;

  // 1. Verdict Banner & Score Meter
  const scoreCircle = document.getElementById("score-circle");
  const verdictBadge = document.getElementById("verdict-badge");
  const verdictTitle = document.getElementById("verdict-title");
  const verdictSummary = document.getElementById("verdict-summary");
  const verdictBanner = document.getElementById("verdict-banner");

  scoreCircle.innerText = correlation.risk_score;
  scoreCircle.style.borderColor = correlation.verdict_color;
  scoreCircle.style.color = correlation.verdict_color;

  verdictBadge.innerHTML = `<span>●</span> ${correlation.verdict}`;
  verdictBadge.style.color = correlation.verdict_color;

  verdictTitle.innerText = correlation.verdict_label;
  verdictSummary.innerText = correlation.summary;
  verdictBanner.style.borderLeftColor = correlation.verdict_color;

  // 2. Level 1 Triage Card
  document.getElementById("res-filename").innerText = triage.filename;
  document.getElementById("res-filesize").innerText = triage.filesize_formatted;
  document.getElementById("res-magic").innerText = triage.detected_format;
  document.getElementById("res-mime").innerText = triage.detected_mime;
  document.getElementById("res-entropy").innerText = `${triage.global_entropy} bits/byte`;
  document.getElementById("res-sha256").innerText = triage.hashes.sha256;
  document.getElementById("res-md5").innerText = triage.hashes.md5;
  document.getElementById("res-analysis-id").innerText = analysis_id;

  const extBadge = document.getElementById("extension-match-badge");
  if (triage.extension_mismatch) {
    extBadge.className = "badge-danger";
    extBadge.innerText = "MISMATCH DETECTED!";
  } else {
    extBadge.className = "badge-clean";
    extBadge.innerText = "Signature Match";
  }

  // 3. Level 2 Steganography Card
  renderCategorySpecificAnalysis(file_category, analysis, correlation);

  // 4. Visual Card (Only for Images)
  const visualCard = document.getElementById("visual-card");
  if (file_category === "image" && analysis.visual_artifacts) {
    visualCard.style.display = "block";
    switchVisualTab('ela');
  } else {
    visualCard.style.display = "none";
  }

  // 5. Level 3 Correlation & Rules Card
  const rulesListEl = document.getElementById("rules-list");
  const rulesBadge = document.getElementById("rules-count-badge");
  rulesBadge.innerText = `${correlation.triggered_rules_count} Rule(s) Triggered`;

  if (correlation.triggered_rules_count > 0) {
    rulesBadge.className = "badge-danger";
    rulesListEl.innerHTML = correlation.triggered_rules.map(r => `
      <div class="rule-item">
        <div class="rule-header">
          <span class="rule-name">${r.name}</span>
          <span class="${r.severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}">${r.severity}</span>
        </div>
        <span style="font-size: 0.72rem; color: var(--accent-cyan); font-family: var(--font-mono);">${r.rule_id}</span>
        <div class="rule-desc">${r.description}</div>
      </div>
    `).join("");
  } else {
    rulesBadge.className = "badge-clean";
    rulesListEl.innerHTML = `<div style="color: var(--accent-green); font-size: 0.85rem; padding: 12px 0;">✓ Zero correlation rules violated. File passes automated checks.</div>`;
  }

  // Recommendations
  const recsListEl = document.getElementById("recommendations-list");
  recsListEl.innerHTML = correlation.forensic_recommendations.map(r => `<li>${r}</li>`).join("");

  // Show container
  document.getElementById("results-container").style.display = "flex";
  document.getElementById("results-container").scrollIntoView({ behavior: 'smooth' });
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
    badgeEl.className = isSuspicious ? "badge-danger" : "badge-clean";
    badgeEl.innerText = isSuspicious ? "Stego Indicators Found" : "Passes Statistical Tests";

    let html = `
      <div style="margin-bottom: 15px;">
        <h4 style="font-size: 0.8rem; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 6px;">
          1. Chi-Square (χ²) Pair-of-Values LSB Test
        </h4>
        <table class="kv-table" style="font-size: 0.8rem;">
          <thead>
            <tr style="color: var(--text-muted); text-align: left;">
              <th>Channel</th>
              <th>χ² Stat</th>
              <th>deg of freedom</th>
              <th>p-Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
    `;

    for (const [ch, res] of Object.entries(chi2.channels || {})) {
      const isSus = res.suspicious;
      html += `
        <tr>
          <td style="color: #fff; font-weight: 600;">${ch}</td>
          <td>${res.chi2_statistic}</td>
          <td>${res.degrees_of_freedom}</td>
          <td style="font-family: var(--font-mono); color: ${isSus ? '#ef4444' : '#10b981'};">${res.p_value}</td>
          <td><span class="${isSus ? 'badge-danger' : 'badge-clean'}">${isSus ? 'FLAGGED (p < 0.05)' : 'Normal'}</span></td>
        </tr>
      `;
    }

    html += `
          </tbody>
        </table>
      </div>

      <div style="margin-bottom: 15px; border-top: 1px solid var(--border-color); padding-top: 12px;">
        <h4 style="font-size: 0.8rem; color: var(--accent-cyan); text-transform: uppercase; margin-bottom: 6px;">
          2. RS Steganalysis (Fridrich Dual-Masking)
        </h4>
        <table class="kv-table">
          <tr>
            <td class="kv-key">Estimated Payload Fraction</td>
            <td class="kv-val" style="color: ${rs.suspicious ? '#ef4444' : '#10b981'}; font-weight: 700;">
              ${rs.estimated_payload_percent || '0%'}
            </td>
          </tr>
          <tr>
            <td class="kv-key">Regular Groups (R_M / R_-M)</td>
            <td class="kv-val">${rs.regular_groups_pos} / ${rs.regular_groups_neg}</td>
          </tr>
          <tr>
            <td class="kv-key">Singular Groups (S_M / S_-M)</td>
            <td class="kv-val">${rs.singular_groups_pos} / ${rs.singular_groups_neg}</td>
          </tr>
        </table>
      </div>
    `;

    if (overlay.overlay_found) {
      html += `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
          <h5 style="color: #ef4444; font-size: 0.8rem; margin-bottom: 4px;">⚠️ Trailing Container Overlay Detected!</h5>
          <p style="font-size: 0.75rem; color: var(--text-muted);">
            Detected ${overlay.overlay_size_bytes} trailing bytes appended past ${overlay.marker_name}.
          </p>
          <div style="font-family: var(--font-mono); font-size: 0.75rem; background: #000; padding: 6px; border-radius: 4px; margin-top: 4px; word-break: break-all;">
            ${overlay.overlay_preview}
          </div>
        </div>
      `;
    }

    if (blind.candidate_count > 0) {
      html += `
        <div class="payload-box">
          <h4><span>🔍</span> Extracted LSB Candidate Strings</h4>
          ${blind.candidates.map(c => `
            <div style="margin-bottom: 6px;">
              <span style="font-size: 0.75rem; color: var(--accent-cyan); font-weight: 600;">${c.type}:</span>
              <div class="payload-content">${c.preview}</div>
            </div>
          `).join("")}
        </div>
      `;
    }

    contentEl.innerHTML = html;

  } else if (category === "text") {
    titleEl.innerText = "Text Steganography Screening (Zero-Width Analysis)";
    badgeEl.className = analysis.is_suspicious ? "badge-danger" : "badge-clean";
    badgeEl.innerText = analysis.is_suspicious ? "Invisible Characters Found" : "Clean Text";

    let html = `
      <table class="kv-table">
        <tr>
          <td class="kv-key">Total Visible Characters</td>
          <td class="kv-val">${analysis.total_characters}</td>
        </tr>
        <tr>
          <td class="kv-key">Zero-Width Hidden Characters</td>
          <td class="kv-val" style="color: ${analysis.zero_width_characters_found > 0 ? '#ef4444' : '#10b981'}; font-weight: 700;">
            ${analysis.zero_width_characters_found} (${analysis.zero_width_ratio_percent}%)
          </td>
        </tr>
      </table>
    `;

    if (analysis.has_decoded_payload) {
      html += `
        <div class="payload-box">
          <h4><span>🔓</span> Reconstructed Invisible Secret Message</h4>
          <div class="payload-content">${analysis.decoded_hidden_payload}</div>
        </div>
      `;
    }

    if (analysis.sample_positions && analysis.sample_positions.length > 0) {
      html += `
        <div style="margin-top: 12px;">
          <h5 style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px;">Detected Unicode Code Points:</h5>
          <ul style="padding-left: 20px; font-size: 0.75rem; color: var(--accent-cyan);">
            ${analysis.sample_positions.map(p => `<li>${p.name} (${p.char}) at character index ${p.index}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    contentEl.innerHTML = html;

  } else if (category === "pdf") {
    titleEl.innerText = "PDF Document Steganography Screening";
    badgeEl.className = analysis.is_suspicious ? "badge-danger" : "badge-clean";
    badgeEl.innerText = analysis.is_suspicious ? "Marker / Overlay Found" : "Normal PDF";

    contentEl.innerHTML = `
      <table class="kv-table">
        <tr>
          <td class="kv-key">Page Count</td>
          <td class="kv-val">${analysis.num_pages}</td>
        </tr>
        <tr>
          <td class="kv-key">/StegoData Marker</td>
          <td class="kv-val" style="color: ${analysis.stegodata_marker_found ? '#ef4444' : '#10b981'}; font-weight: 700;">
            ${analysis.stegodata_marker_found ? 'DETECTED in Object Stream' : 'None'}
          </td>
        </tr>
        <tr>
          <td class="kv-key">Trailing Bytes Past %%EOF</td>
          <td class="kv-val" style="color: ${analysis.trailing_data_after_eof ? '#ef4444' : '#10b981'};">
            ${analysis.trailing_data_after_eof ? `${analysis.trailing_bytes} bytes appended` : 'None'}
          </td>
        </tr>
      </table>
      ${analysis.trailing_preview ? `
        <div class="payload-box">
          <h4>Appended Overlay Content</h4>
          <div class="payload-content">${analysis.trailing_preview}</div>
        </div>
      ` : ''}
    `;

  } else {
    // Binary or Audio or Generic
    titleEl.innerText = `${triage.detected_format} Anomaly Screening`;
    contentEl.innerHTML = `
      <table class="kv-table">
        <tr>
          <td class="kv-key">Format Category</td>
          <td class="kv-val">${category.toUpperCase()}</td>
        </tr>
        <tr>
          <td class="kv-key">Structural Status</td>
          <td class="kv-val">${analysis.is_suspicious ? 'Suspicious anomaly identified' : 'Verified compliant'}</td>
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
    captionEl.innerText = "Error Level Analysis (ELA): Amplifies compression rate discrepancies to highlight spliced, manipulated, or resaved image regions.";
  } else {
    btnLsb.classList.add("active");
    btnEla.classList.remove("active");
    imgEl.src = artifacts.lsb_plane_data_url;
    captionEl.innerText = "LSB Bit-Plane Visualizer (Bit 0): Unveils hidden noise patterns. Natural images have smooth bit planes, while stego embedding produces random static noise.";
  }
}

// Modal Report Generation
function openReportModal() {
  if (!currentAnalysis) return;
  const report = currentAnalysis.report;
  const contentEl = document.getElementById("report-content");

  contentEl.innerHTML = `
    <div style="border: 2px solid var(--accent-cyan); padding: 1.5rem; background: rgba(10, 14, 23, 0.9); border-radius: 8px;">
      <div style="text-align: center; border-bottom: 2px solid var(--border-color); padding-bottom: 12px; margin-bottom: 15px;">
        <h2 style="font-size: 1.2rem; color: #fff; letter-spacing: 1px;">${report.report_header.title}</h2>
        <div style="color: var(--accent-cyan); font-size: 0.8rem; margin-top: 4px;">
          ${report.report_header.tool_name} — v${report.report_header.tool_version}
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; font-size: 0.8rem;">
        <div><strong>Case ID:</strong> ${report.report_header.case_id}</div>
        <div><strong>Evidence ID:</strong> ${report.report_header.evidence_id}</div>
        <div><strong>Date / Time:</strong> ${report.report_header.generated_at}</div>
        <div><strong>Risk Assessment:</strong> <span style="color: ${currentAnalysis.correlation.verdict_color}; font-weight: bold;">${report.verdict_summary.verdict_label} (${report.verdict_summary.risk_score}/100)</span></div>
      </div>

      <h4 style="color: var(--accent-cyan); font-size: 0.85rem; border-bottom: 1px solid var(--border-color); padding-bottom: 4px; margin-bottom: 8px;">
        1. CHAIN OF CUSTODY & EVIDENCE INTEGRITY
      </h4>
      <table class="kv-table" style="font-size: 0.78rem; margin-bottom: 15px;">
        <tr><td class="kv-key">Source Filename:</td><td class="kv-val">${report.evidence_integrity.filename}</td></tr>
        <tr><td class="kv-key">File Size:</td><td class="kv-val">${report.evidence_integrity.filesize}</td></tr>
        <tr><td class="kv-key">Magic Header:</td><td class="kv-val">${report.evidence_integrity.magic_signature}</td></tr>
        <tr><td class="kv-key">SHA-256 Digest:</td><td class="kv-val"><span class="hash-val">${report.evidence_integrity.sha256}</span></td></tr>
        <tr><td class="kv-key">MD5 Digest:</td><td class="kv-val"><span class="hash-val">${report.evidence_integrity.md5}</span></td></tr>
      </table>

      <h4 style="color: var(--accent-cyan); font-size: 0.85rem; border-bottom: 1px solid var(--border-color); padding-bottom: 4px; margin-bottom: 8px;">
        2. CORRELATED FINDINGS & TRIGGERED RULES
      </h4>
      <div style="margin-bottom: 15px;">
        ${report.triggered_rules.length > 0 ? report.triggered_rules.map(r => `
          <div style="background: rgba(0,0,0,0.4); padding: 8px 12px; border-left: 3px solid #ef4444; margin-bottom: 6px; font-size: 0.78rem;">
            <strong>[${r.rule_id}] ${r.name} (${r.severity})</strong><br>
            <span style="color: var(--text-muted);">${r.description}</span>
          </div>
        `).join("") : '<div style="color: #10b981; font-size: 0.8rem;">No anomalous rules triggered. Evidence conforms to expected format standards.</div>'}
      </div>

      <h4 style="color: var(--accent-cyan); font-size: 0.85rem; border-bottom: 1px solid var(--border-color); padding-bottom: 4px; margin-bottom: 8px;">
        3. RECOMMENDED FORENSIC ACTIONS
      </h4>
      <ul style="padding-left: 20px; font-size: 0.78rem; color: var(--text-muted); margin-bottom: 15px;">
        ${report.recommendations.map(rc => `<li>${rc}</li>`).join("")}
      </ul>

      <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; padding: 10px; font-size: 0.72rem; color: #fcd34d;">
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
}

function hideLoading() {
  document.getElementById("loading-overlay").style.display = "none";
}
