from typing import Dict, Any, List

def correlate_findings(
    triage_info: Dict[str, Any],
    specific_analysis: Dict[str, Any],
    file_category: str
) -> Dict[str, Any]:
    """
    Level 3: Forensic Correlation Engine
    Correlates independent indicators across triage, structure, statistics, and markers.
    Produces calibrated risk score (0-100) and severity rating.
    """
    score = 0
    triggered_rules = []
    
    # 1. Extension mismatch rule
    if triage_info.get("extension_mismatch"):
        score += 35
        triggered_rules.append({
            "rule_id": "CORR_01_EXT_MISMATCH",
            "name": "Extension vs Magic Byte Discrepancy",
            "severity": "HIGH",
            "description": triage_info.get("mismatch_details", "Extension does not match file magic header.")
        })

    # 2. Global Entropy check
    global_entropy = triage_info.get("global_entropy", 0.0)
    claimed_ext = triage_info.get("claimed_extension", "")
    if global_entropy > 7.92 and claimed_ext in [".bmp", ".wav", ".txt"]:
        score += 25
        triggered_rules.append({
            "rule_id": "CORR_02_HIGH_ENTROPY",
            "name": "Abnormal Carrier Entropy",
            "severity": "MEDIUM",
            "description": f"Carrier format normally exhibits moderate entropy, but observed {global_entropy} bits/byte, suggesting encryption or compressed payload."
        })

    # 3. Category-specific rules
    if file_category == "image":
        # Chi-Square
        chi2 = specific_analysis.get("chi_square", {})
        if chi2.get("is_suspicious"):
            ch_list = ", ".join(chi2.get("suspicious_channels", []))
            score += 30
            triggered_rules.append({
                "rule_id": "STEG_IMG_01_CHI_SQUARE",
                "name": "Chi-Square Pair-of-Values LSB Equalization",
                "severity": "HIGH",
                "description": f"Statistical LSB test indicates significant equalization of adjacent pixel values in channels: {ch_list} (Stego Probability > 60%)."
            })

        # RS Steganalysis
        rs = specific_analysis.get("rs_analysis", {})
        if rs.get("suspicious"):
            payload_pct = rs.get("estimated_payload_percent", "N/A")
            score += 30
            triggered_rules.append({
                "rule_id": "STEG_IMG_02_RS_ANALYSIS",
                "name": "RS Steganalysis Regular/Singular Group Shift",
                "severity": "HIGH",
                "description": f"Regular vs Singular pixel group behavior indicates an estimated hidden payload fraction of {payload_pct}."
            })

        # Container overlay
        overlay = specific_analysis.get("container_overlay", {})
        if overlay.get("overlay_found"):
            score += 40
            triggered_rules.append({
                "rule_id": "ANTI_01_TRAILING_OVERLAY",
                "name": "Container Structural Boundary Violation",
                "severity": "CRITICAL",
                "description": f"Found {overlay.get('overlay_size_bytes')} trailing bytes appended past {overlay.get('marker_name')}."
            })

        # Blind extraction candidate
        blind = specific_analysis.get("blind_lsb", {})
        if blind.get("candidate_count", 0) > 0:
            score += 45
            triggered_rules.append({
                "rule_id": "STEG_IMG_03_BLIND_CANDIDATE",
                "name": "Compatible Hidden Payload Extracted",
                "severity": "CRITICAL",
                "description": f"Found {blind.get('candidate_count')} readable string or known signature candidate(s) directly in LSB bitstream."
            })

    elif file_category == "text":
        zw_found = specific_analysis.get("zero_width_characters_found", 0)
        has_decoded = specific_analysis.get("has_decoded_payload", False)
        if has_decoded:
            score += 50
            triggered_rules.append({
                "rule_id": "STEG_TXT_01_DECODED_ZW",
                "name": "Decoded Zero-Width Hidden Message",
                "severity": "CRITICAL",
                "description": f"Successfully decoded hidden secret message from zero-width Unicode characters: '{specific_analysis.get('decoded_hidden_payload')}'."
            })
        elif specific_analysis.get("is_suspicious"):
            score += 35
            triggered_rules.append({
                "rule_id": "STEG_TXT_02_ZERO_WIDTH_DENSITY",
                "name": "Abnormal Zero-Width Character Density",
                "severity": "HIGH",
                "description": f"Detected {zw_found} invisible zero-width Unicode characters in plain text."
            })

    elif file_category == "pdf":
        if specific_analysis.get("stegodata_marker_found"):
            score += 45
            triggered_rules.append({
                "rule_id": "STEG_DOC_01_PDF_STEGODATA",
                "name": "Known /StegoData Marker in PDF Dictionary",
                "severity": "CRITICAL",
                "description": "Found project-specific /StegoData dictionary key in PDF stream."
            })
        if specific_analysis.get("trailing_data_after_eof"):
            score += 35
            triggered_rules.append({
                "rule_id": "ANTI_02_PDF_EOF_OVERLAY",
                "name": "Appended Payload Beyond %%EOF",
                "severity": "HIGH",
                "description": f"Detected {specific_analysis.get('trailing_bytes')} bytes appended past the last %%EOF marker."
            })

    elif file_category == "office":
        if specific_analysis.get("stegodata_xml_found"):
            score += 50
            triggered_rules.append({
                "rule_id": "STEG_DOC_02_OFFICE_STEGODATA",
                "name": "Office stegodata.xml Part Detected",
                "severity": "CRITICAL",
                "description": "Package contains 'word/custom/stegodata.xml' steganography container."
            })
        elif specific_analysis.get("is_suspicious"):
            score += 25
            triggered_rules.append({
                "rule_id": "STEG_DOC_03_OFFICE_ANOMALY",
                "name": "Suspicious Custom Package Parts",
                "severity": "MEDIUM",
                "description": "Office container contains unrecognized custom parts or zero-width sequences."
            })

    elif file_category == "binary":
        if specific_analysis.get("has_trailing_overlay"):
            score += 40
            triggered_rules.append({
                "rule_id": "ANTI_03_PE_OVERLAY",
                "name": "PE Executable Section Overlay",
                "severity": "HIGH",
                "description": f"Found {specific_analysis.get('overlay_size_bytes')} bytes appended beyond defined PE sections."
            })

    elif file_category == "audio":
        if specific_analysis.get("has_trailing_data"):
            score += 35
            triggered_rules.append({
                "rule_id": "ANTI_04_WAV_CHUNK_OVERLAY",
                "name": "Trailing Data Past RIFF Container",
                "severity": "HIGH",
                "description": f"Detected {specific_analysis.get('trailing_size_bytes')} bytes appended beyond WAV header length."
            })
        if specific_analysis.get("lsb_entropy", 0) > 0.999:
            score += 20
            triggered_rules.append({
                "rule_id": "STEG_AUD_01_PCM_ENTROPY",
                "name": "Uniform PCM LSB Entropy",
                "severity": "MEDIUM",
                "description": "Audio PCM LSB stream exhibits near-perfect 1.0 entropy consistent with pseudo-random steganographic payload."
            })

    # Clamp score to 100
    risk_score = min(100, score)

    # Determine status & badge
    if risk_score <= 15:
        verdict = "CLEAN"
        verdict_label = "Clean / No Obvious Concealment"
        verdict_color = "#10b981" # green
        summary = "No anomalous statistical deviation, known stego markers, or structural overlay violations were detected. Evidence appears consistent with standard formats."
    elif risk_score <= 40:
        verdict = "LOW_RISK"
        verdict_label = "Low Risk / Informational"
        verdict_color = "#3b82f6" # blue
        summary = "Minor structural or statistical variations detected. Low likelihood of intentional concealment, but warrants logging for baseline comparison."
    elif risk_score <= 70:
        verdict = "SUSPICIOUS"
        verdict_label = "Suspicious Evidence"
        verdict_color = "#f59e0b" # amber
        summary = "Moderate steganographic or anti-forensic anomalies identified. Statistical tests or metadata indicate possible data concealment. Manual examiner inspection recommended."
    else:
        verdict = "HIGH_SUSPICION"
        verdict_label = "High Suspicion / Concealed Content"
        verdict_color = "#ef4444" # red
        summary = "Multiple corroborating indicators or critical steganography signatures discovered. Strong probability of intentional data concealment or container tampering."

    # Next steps recommendations
    recommendations = []
    if risk_score > 40:
        recommendations.append("Isolate evidence file and preserve cryptographic SHA-256 fingerprint in custody log.")
        if any(r["rule_id"].startswith("STEG_IMG") for r in triggered_rules):
            recommendations.append("Inspect visual bit planes and apply specialized dictionary/carver attacks to extract full payload.")
        if any(r["rule_id"].startswith("ANTI") for r in triggered_rules):
            recommendations.append("Carve trailing overlay bytes from EOF offset using hex editor to recover hidden archive/payload.")
        if any("EXT_MISMATCH" in r["rule_id"] for r in triggered_rules):
            recommendations.append("Correct file extension to true magic byte format before running dynamic analysis in an isolated sandbox.")
    else:
        recommendations.append("File passed baseline automated screening. Retain hash in audit index.")

    return {
        "risk_score": risk_score,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "verdict_color": verdict_color,
        "triggered_rules_count": len(triggered_rules),
        "triggered_rules": triggered_rules,
        "summary": summary,
        "forensic_recommendations": recommendations
    }
