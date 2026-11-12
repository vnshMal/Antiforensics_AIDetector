# Anti-Forensics & Steganography AI Detection Suite
**AI-Assisted Detection & Analysis of Concealed & Manipulated Digital Evidence**

---

## 📌 Project Overview
Digital evidence can be concealed or altered using steganography (hiding secret data inside images, documents, audio, or text) and anti-forensic techniques (tampering with metadata, appending trailing overlays past EOF, altering extensions, or zero-width character injection).

This project provides an automated, multi-level digital forensics screening dashboard designed for triage and preliminary investigation. It inspects evidence files across 4 formal levels, produces calibrated risk ratings, highlights visual artifacts, and generates structured forensic reports for chain of custody.

---

## 🚀 Quick Start (Running the Project)

### 1-Click Launch (Windows)
Double-click `run.bat` in the project root folder.
It checks your environment, launches the backend, and opens your browser automatically at `http://127.0.0.1:8000`.

### Manual Launch
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python app.py
```
Open your browser at: **`http://127.0.0.1:8000`**

---

## 🎯 How to Demonstrate to Your Professor / Sir

Here is the exact step-by-step walkthrough to present to your teacher:

### Step 1: Clean Baseline (False-Positive Safeguard)
1. In the **Demo Test Cases** panel on the right, click **`sample_clean_evidence.png`**.
2. **Observe**:
   - Risk Index is **0 / 100** (Clean / Green).
   - SHA-256 and MD5 cryptographic hashes are recorded.
   - Shows that natural images do not trigger false alerts.

### Step 2: Image LSB Steganography Detection
1. Click **`sample_stego_lsb.png`** (or create a custom one in the **Stego Studio** tab).
2. **Observe**:
   - Status changes to **SUSPICIOUS / HIGH RISK**.
   - **Chi-Square ($\chi^2$) PoV Test**: Detects equalization of adjacent luminance values ($2k, 2k+1$) caused by bit-plane modification.
   - **RS Steganalysis (Fridrich method)**: Computes Regular ($R_M, R_{-M}$) and Singular ($S_M, S_{-M}$) group shifts and displays the estimated payload percentage.
   - **Blind LSB Extractor**: Extracts the embedded string `TOP_SECRET_COVERT_EXFILTRATION_FLAG...` directly!
   - **Visual Forensics**: Toggle between **Error Level Analysis (ELA)** and **LSB Bit-Plane (Bit 0)** to visually reveal the hidden static noise pattern.

### Step 3: Invisible Text Steganography (Unicode Zero-Width)
1. Click **`sample_zero_width_stego.txt`**.
2. **Observe**:
   - The visible text looks like normal English: *"The quick brown fox jumps over the lazy dog..."*
   - The detector instantly discovers invisible characters (`\u200B`, `\u200C`).
   - The **Reconstructed Invisible Secret Message** box decodes the binary sequence and prints the secret string: `ATTACK_AT_DAWN_1001`!

### Step 4: Container Boundary & Overlay Anomaly
1. Click **`sample_overlay_stego.jpg`**.
2. **Observe**:
   - Level 2 structural inspection identifies bytes appended **beyond the standard JPEG End-of-Image marker (`FF D9`)**.
   - Displays the trailing payload size and a preview of the concealed archive text.

### Step 5: Extension Disguise Detection
1. Click **`sample_disguised_archive.jpg`**.
2. **Observe**:
   - File extension claims `.jpg`, but Level 1 magic header inspection flags that the true signature is `PK\x03\x04` (ZIP archive).
   - Triggers `CORR_01_EXT_MISMATCH` with high severity.

### Step 6: Live Stego Studio (Create & Attack on the Fly)
1. Switch to the **🧪 Stego Studio & Demo Lab** tab.
2. Select any attack (e.g. *Image LSB Steganography* or *Zero-Width Text*).
3. Type your Sir's name or custom secret message (e.g., `CONFIDENTIAL_EVALUATION_PASS_2026`).
4. Click **Generate Stego File & Analyze Instantly**.
5. The system creates the stego file on the fly, immediately screens it, and displays the decoded payload and statistical flags in real time!

### Step 7: Formal Forensic Report Export
1. Click **Generate Formal Forensic Report**.
2. Shows a formal investigation document complete with:
   - Case ID and Evidence ID
   - Timestamp and Custody Hashes (SHA-256, MD5)
   - Correlated Findings and Triggered Forensic Rules
   - Recommended Examiner Actions & Responsible Use Disclaimer
3. Click **🖨️ Print / Save as PDF** to generate an official PDF report.

---

## 🔬 Four-Level Forensic Architecture

```
| Level 1: Evidence Intake & Triage |
  -> Cryptographic Hashing (SHA-256, MD5, SHA-1)
  -> Magic Byte Signature Detection
  -> Extension Mismatch Identification
  -> Global Shannon Entropy

| Level 2: Format-Specific Steganography Screening |
  -> Images: Chi-Square Pair-of-Values test, RS Steganalysis, Blind LSB Carver, ELA & Bit-Planes
  -> Text: Unicode Zero-Width character counter & binary decoder
  -> Documents: PDF /StegoData marker & EOF overlay scanner, DOCX stegodata.xml checker
  -> Binary / Audio: PE section overlay analyzer, WAV PCM entropy & RIFF container boundary

| Level 3: Forensic Correlation Engine |
  -> Cross-source rule evaluation (CORR_01, STEG_IMG_01, STEG_TXT_01, etc.)
  -> Calibrated Risk Score calculation (0 - 100)
  -> Verdict Assignment: CLEAN, LOW RISK, SUSPICIOUS, HIGH SUSPICION

| Level 4: Triage Reporting & Human-Centric Review |
  -> Formal Case Documentation & Chain of Custody
  -> Technical Observations and Next-Step Action Items
  -> Evidentiary limitations & responsible use boundaries
```

---

## ⚖️ Responsible Use & Limitations
This system is designed as an investigative screening aid to assist forensic examiners, students, and analysts in prioritizing files for deeper examination. Statistical flags indicate anomalies and potential concealment; final forensic determinations must be corroborated by validated forensic tools and qualified human review.
