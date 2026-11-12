import sys
from pathlib import Path
from backend.config import SAMPLES_DIR, TEMP_DIR
import backend.stego_studio as studio
from backend.triage import perform_triage
from backend.image_stego import analyze_image
from backend.text_stego import analyze_text
from backend.doc_stego import analyze_pdf
from backend.correlation import correlate_findings
from backend.report_generator import generate_forensic_report

def run_tests():
    print("=== [1] Testing Clean Baseline Image ===")
    clean_path = SAMPLES_DIR / "test_clean.png"
    studio.create_clean_baseline_image(clean_path)
    triage_clean = perform_triage(clean_path, "test_clean.png")
    analysis_clean = analyze_image(clean_path, TEMP_DIR)
    corr_clean = correlate_findings(triage_clean, analysis_clean, "image")
    print(f"Clean Image Verdict: {corr_clean['verdict']} (Risk: {corr_clean['risk_score']})")
    assert corr_clean['risk_score'] <= 15, "Clean image should have low risk score!"

    print("\n=== [2] Testing Image LSB Steganography ===")
    lsb_path = SAMPLES_DIR / "test_lsb.png"
    studio.create_lsb_stego_image("SECRET_EXFILTRATION_FLAG_2026", lsb_path)
    triage_lsb = perform_triage(lsb_path, "test_lsb.png")
    analysis_lsb = analyze_image(lsb_path, TEMP_DIR)
    corr_lsb = correlate_findings(triage_lsb, analysis_lsb, "image")
    print(f"LSB Image Verdict: {corr_lsb['verdict']} (Risk: {corr_lsb['risk_score']})")
    print(f"Triggered Rules: {[r['rule_id'] for r in corr_lsb['triggered_rules']]}")
    assert corr_lsb['risk_score'] >= 40, "LSB stego should trigger high suspicion!"

    print("\n=== [3] Testing Text Zero-Width Steganography ===")
    zw_path = SAMPLES_DIR / "test_zw.txt"
    studio.create_zero_width_text("Digital forensics is essential.", "SECRET_PASSWORD_XYZ", zw_path)
    triage_zw = perform_triage(zw_path, "test_zw.txt")
    analysis_zw = analyze_text(zw_path)
    corr_zw = correlate_findings(triage_zw, analysis_zw, "text")
    print(f"Zero-Width Verdict: {corr_zw['verdict']} (Risk: {corr_zw['risk_score']})")
    print(f"Decoded secret: '{analysis_zw.get('decoded_hidden_payload')}'")
    assert analysis_zw.get('decoded_hidden_payload') == "SECRET_PASSWORD_XYZ", "Decoded secret mismatch!"

    print("\n=== [4] Testing Container Trailing Overlay ===")
    overlay_path = SAMPLES_DIR / "test_overlay.jpg"
    studio.create_trailing_overlay_image("HIDDEN_ARCHIVE_DATA", overlay_path)
    triage_ov = perform_triage(overlay_path, "test_overlay.jpg")
    analysis_ov = analyze_image(overlay_path, TEMP_DIR)
    corr_ov = correlate_findings(triage_ov, analysis_ov, "image")
    print(f"Overlay Verdict: {corr_ov['verdict']} (Risk: {corr_ov['risk_score']})")
    print(f"Overlay size: {analysis_ov['container_overlay']['overlay_size_bytes']} bytes")
    assert analysis_ov['container_overlay']['overlay_found'] is True, "Overlay should be detected!"

    print("\n=== [5] Testing Extension Mismatch (Disguised File) ===")
    disguised_path = SAMPLES_DIR / "test_disguised.jpg"
    studio.create_disguised_file(disguised_path)
    triage_dis = perform_triage(disguised_path, "test_disguised.jpg")
    corr_dis = correlate_findings(triage_dis, {}, "generic")
    print(f"Disguised Verdict: {corr_dis['verdict']} (Risk: {corr_dis['risk_score']})")
    assert triage_dis['extension_mismatch'] is True, "Extension mismatch should be detected!"

    print("\n=== [6] Testing Report Generation ===")
    report = generate_forensic_report("test-uuid-1234", triage_lsb, analysis_lsb, corr_lsb)
    print(f"Report Title: {report['report_header']['title']}")
    print(f"Case ID: {report['report_header']['case_id']}")
    print(f"SHA-256: {report['evidence_integrity']['sha256']}")
    assert "DIGITAL FORENSIC" in report['report_header']['title'].upper()

    print("\n>>> ALL 6 FORENSIC TESTS PASSED PERFECTLY! <<<")

if __name__ == "__main__":
    run_tests()
