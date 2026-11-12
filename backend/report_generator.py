import json
import time
from typing import Dict, Any

def generate_forensic_report(
    analysis_id: str,
    triage_data: Dict[str, Any],
    specific_data: Dict[str, Any],
    correlation_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates a structured forensic triage report."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    return {
        "report_header": {
            "title": "DIGITAL FORENSIC TRIAGE & STEGANOGRAPHY SCREENING REPORT",
            "case_id": f"CASE-{analysis_id[:8].upper()}",
            "evidence_id": f"EVID-{analysis_id[-6:].upper()}",
            "generated_at": now_str,
            "tool_name": "Anti-Forensics & Steganography AI Detection Suite",
            "tool_version": "2.0-Production"
        },
        "evidence_integrity": {
            "filename": triage_data.get("filename"),
            "filesize": triage_data.get("filesize_formatted"),
            "sha256": triage_data.get("hashes", {}).get("sha256"),
            "md5": triage_data.get("hashes", {}).get("md5"),
            "sha1": triage_data.get("hashes", {}).get("sha1"),
            "magic_signature": triage_data.get("detected_format"),
            "mime_type": triage_data.get("detected_mime"),
            "extension_status": "VALID" if not triage_data.get("extension_mismatch") else "MISMATCH_SUSPECT"
        },
        "verdict_summary": {
            "risk_score": correlation_data.get("risk_score"),
            "verdict": correlation_data.get("verdict"),
            "verdict_label": correlation_data.get("verdict_label"),
            "summary": correlation_data.get("summary")
        },
        "triggered_rules": correlation_data.get("triggered_rules", []),
        "recommendations": correlation_data.get("forensic_recommendations", []),
        "technical_details": {
            "triage": triage_data,
            "analysis": specific_data
        },
        "forensic_disclaimer": (
            "IMPORTANT NOTICE: This screening report is an automated preliminary investigative aid. "
            "Statistical deviations and heuristics highlight items requiring further manual review. "
            "An anomaly is not proof of malicious intent, and a clean result does not guarantee absence "
            "of sophisticated concealment. Final forensic conclusions must be verified by a qualified examiner."
        )
    }

