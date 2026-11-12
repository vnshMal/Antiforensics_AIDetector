import os
import math
import io
import base64
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
from scipy import stats

def calculate_channel_chi_square(channel_data: np.ndarray) -> Dict[str, Any]:
    """
    Chi-Square LSB detector (Pair of Values PoVs test).
    Tests for equalization of adjacent luminance values caused by LSB substitution.
    """
    flat = channel_data.flatten()
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))
    
    chi2_sum = 0.0
    degrees_of_freedom = 0
    
    # Analyze adjacent pairs (2k, 2k+1)
    for k in range(128):
        n1 = hist[2 * k]
        n2 = hist[2 * k + 1]
        pair_sum = n1 + n2
        
        # Only evaluate non-empty pairs to avoid division by zero
        if pair_sum > 10:
            expected = pair_sum / 2.0
            chi2_sum += ((n1 - expected) ** 2) / expected + ((n2 - expected) ** 2) / expected
            degrees_of_freedom += 1
            
    if degrees_of_freedom > 5:
        # In Westfeld's PoV test, under LSB embedding adjacent values equalize (n1 ~ n2).
        # Hence, chi2_sum approaches 0, and sf(chi2, df) approaches 1.0 (indicating stego).
        # In clean images, natural gradients cause n1 != n2, so chi2_sum is large and sf -> 0.0.
        stego_probability = float(stats.chi2.sf(chi2_sum, degrees_of_freedom))
        is_suspicious = stego_probability > 0.60
    else:
        chi2_sum = 0.0
        stego_probability = 0.0
        is_suspicious = False
        
    return {
        "chi2_statistic": round(float(chi2_sum), 2),
        "degrees_of_freedom": degrees_of_freedom,
        "p_value": round(float(stego_probability), 6),
        "stego_probability": round(float(stego_probability) * 100, 2),
        "suspicious": is_suspicious
    }

def calculate_rs_steganalysis(image_gray: np.ndarray) -> Dict[str, Any]:
    """
    RS Steganalysis (Fridrich et al.).
    Measures the ratio of regular and singular groups under flipping operations.
    Returns estimated payload fraction.
    """
    h, w = image_gray.shape
    # Block size 4x1
    num_blocks = (w // 4) * h
    if num_blocks < 50:
        return {"estimated_payload_fraction": 0.0, "details": "Image too small for reliable RS analysis"}

    # Mask M = [0, 1, 1, 0]
    mask = np.array([0, 1, 1, 0], dtype=np.int32)
    
    def discrimination(group):
        return np.sum(np.abs(np.diff(group)))
        
    def flip_pos(group, m):
        res = group.copy()
        for i in range(len(m)):
            if m[i] == 1:
                # LSB invert
                res[i] = res[i] ^ 1
        return res

    def flip_neg(group, m):
        res = group.copy()
        for i in range(len(m)):
            if m[i] == 1:
                # Invert dual: 0->-1->0, 1->2, 2->1, 3->4, etc.
                if res[i] % 2 == 0:
                    res[i] = max(0, res[i] - 1)
                else:
                    res[i] = min(255, res[i] + 1)
        return res

    r_m = 0
    s_m = 0
    r_neg_m = 0
    s_neg_m = 0
    total_groups = 0

    # Sample rows for speed and stability
    step_y = max(1, h // 120)
    for y in range(0, h, step_y):
        for x in range(0, w - 4, 4):
            group = image_gray[y, x:x+4].astype(np.int32)
            d = discrimination(group)
            
            g_pos = flip_pos(group, mask)
            d_pos = discrimination(g_pos)
            if d_pos > d:
                r_m += 1
            elif d_pos < d:
                s_m += 1
                
            g_neg = flip_neg(group, mask)
            d_neg = discrimination(g_neg)
            if d_neg > d:
                r_neg_m += 1
            elif d_neg < d:
                s_neg_m += 1
                
            total_groups += 1

    if total_groups == 0:
        return {"estimated_payload_fraction": 0.0, "regular_groups": 0, "singular_groups": 0}

    r_m_norm = r_m / total_groups
    s_m_norm = s_m / total_groups
    r_neg_m_norm = r_neg_m / total_groups
    s_neg_m_norm = s_neg_m / total_groups

    # In clean images: R_M - S_M >> 0, and R_M ~ R_-M, S_M ~ S_-M
    # In full stego images: R_M ~ S_M
    diff_clean = r_m_norm - s_m_norm
    diff_neg = r_neg_m_norm - s_neg_m_norm
    
    # Simplified payload fraction estimation
    # As embedding increases, (R_M - S_M) decreases linearly
    if (diff_clean + diff_neg) != 0:
        d0 = diff_clean
        d1 = diff_neg
        # If d0 is close to 0 or negative, payload is high
        if d0 <= 0.01:
            estimated_payload = 1.0
        else:
            estimated_payload = max(0.0, min(1.0, (d1 - d0) / (d1 + d0 + 1e-6)))
    else:
        estimated_payload = 0.0

    return {
        "regular_groups_pos": r_m,
        "singular_groups_pos": s_m,
        "regular_groups_neg": r_neg_m,
        "singular_groups_neg": s_neg_m,
        "total_groups_sampled": total_groups,
        "estimated_payload_fraction": round(float(estimated_payload), 4),
        "estimated_payload_percent": f"{round(float(estimated_payload) * 100, 1)}%",
        "suspicious": estimated_payload > 0.08
    }

def check_container_overlays(filepath: Path) -> Dict[str, Any]:
    """
    Checks for trailing data appended beyond standard container markers.
    - JPEG: Past FF D9 (EOI)
    - PNG: Past IEND chunk
    """
    with open(filepath, "rb") as f:
        data = f.read()
    
    total_len = len(data)
    overlay_found = False
    overlay_size = 0
    overlay_preview = ""
    marker_name = ""
    
    # JPEG check
    if data.startswith(b"\xff\xd8\xff"):
        eoi_idx = data.rfind(b"\xff\xd9")
        if eoi_idx != -1 and (eoi_idx + 2) < total_len:
            overlay_size = total_len - (eoi_idx + 2)
            if overlay_size > 4: # Ignore minor padding
                overlay_found = True
                marker_name = "JPEG End-of-Image (FF D9)"
                trailing_data = data[eoi_idx + 2:]
                try:
                    overlay_preview = trailing_data[:200].decode("utf-8", errors="replace")
                except Exception:
                    overlay_preview = f"Hex: {trailing_data[:64].hex()}"

    # PNG check
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        iend_idx = data.rfind(b"IEND")
        if iend_idx != -1:
            # IEND chunk has: 4 bytes len (0), 4 bytes type (IEND), 4 bytes CRC
            chunk_end = iend_idx + 4 + 4
            if chunk_end < total_len:
                overlay_size = total_len - chunk_end
                if overlay_size > 4:
                    overlay_found = True
                    marker_name = "PNG IEND Chunk"
                    trailing_data = data[chunk_end:]
                    try:
                        overlay_preview = trailing_data[:200].decode("utf-8", errors="replace")
                    except Exception:
                        overlay_preview = f"Hex: {trailing_data[:64].hex()}"

    return {
        "overlay_found": overlay_found,
        "marker_name": marker_name,
        "overlay_size_bytes": overlay_size,
        "overlay_preview": overlay_preview if overlay_found else "None"
    }

def extract_blind_lsb_candidates(img: Image.Image) -> Dict[str, Any]:
    """
    Blind LSB extraction:
    Extracts LSB stream from RGB channels and scans for ASCII/UTF-8 candidate strings
    or StegoForge/known magic markers like 'SFRG', 'flag{', or readable messages.
    """
    rgb = img.convert("RGB")
    pixels = np.array(rgb)
    h, w, c = pixels.shape
    
    # Extract flat LSBs (up to first 10,000 bytes)
    max_bits = min(h * w * c, 80000)
    flat_channels = pixels.reshape(-1)[:max_bits]
    lsbs = (flat_channels & 1).astype(np.uint8)
    
    # Pack bits into bytes
    num_bytes = len(lsbs) // 8
    truncated_lsbs = lsbs[:num_bytes * 8]
    bytes_arr = np.packbits(truncated_lsbs)
    
    raw_extracted = bytes(bytes_arr)
    
    # Check for known signatures or printable sequences
    candidates = []
    
    # Check for SFRG magic (StegoForge signature)
    if b"SFRG" in raw_extracted:
        idx = raw_extracted.find(b"SFRG")
        candidates.append({
            "type": "StegoForge (SFRG) Payload Signature",
            "offset": idx,
            "preview": raw_extracted[idx:idx+64].decode("latin1", errors="replace")
        })

    # Search for readable ASCII sequences (length >= 8)
    current_str = []
    for b in raw_extracted[:4096]:
        if 32 <= b <= 126 or b in (10, 13):
            current_str.append(chr(b))
        else:
            if len(current_str) >= 8:
                s = "".join(current_str)
                if any(w in s.lower() for w in ["hidden", "secret", "flag", "confidential", "pass", "key", "test"]):
                    candidates.append({
                        "type": "Suspicious Text String in LSB",
                        "offset": 0,
                        "preview": s[:120]
                    })
                elif len(current_str) >= 16:
                    candidates.append({
                        "type": "Sequential ASCII String in LSB",
                        "offset": 0,
                        "preview": s[:120]
                    })
            current_str = []
            
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "sample_lsb_hex": raw_extracted[:32].hex()
    }

def generate_error_level_analysis(img: Image.Image, temp_output_path: Path, quality: int = 90) -> str:
    """
    Generates Error Level Analysis (ELA) visual representation.
    Saves image at quality 90, calculates difference, amplifies by 20x.
    Returns path or base64 data.
    """
    rgb = img.convert("RGB")
    
    # Save to memory buffer at specific quality
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    
    resaved = Image.open(buf)
    
    # Calculate difference
    diff = ImageChops.difference(rgb, resaved)
    
    # Amplify difference
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / max(max_diff, 1) if max_diff > 0 else 1.0
    scale = min(scale, 20.0) # Cap amplification
    
    enhancer = ImageEnhance.Brightness(diff)
    diff_enhanced = enhancer.enhance(scale)
    
    diff_enhanced.save(temp_output_path, format="PNG")
    
    # Also encode to base64 for direct UI embedding
    out_buf = io.BytesIO()
    diff_enhanced.save(out_buf, format="PNG")
    b64_str = base64.b64encode(out_buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def generate_lsb_plane_visualization(img: Image.Image, temp_output_path: Path) -> str:
    """
    Extracts LSB plane (bit 0) for visual analysis.
    Steganography generates visible noise/static patterns in LSB planes.
    """
    rgb = img.convert("RGB")
    arr = np.array(rgb)
    
    # Bit 0 extracted and scaled to 0 or 255
    lsb_plane = (arr & 1) * 255
    lsb_img = Image.fromarray(lsb_plane.astype(np.uint8))
    
    lsb_img.save(temp_output_path, format="PNG")
    
    out_buf = io.BytesIO()
    lsb_img.save(out_buf, format="PNG")
    b64_str = base64.b64encode(out_buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def analyze_image(filepath: Path, temp_dir: Path) -> Dict[str, Any]:
    """
    Comprehensive Level 2 Steganography Analysis for Images:
    - Chi-Square PoV detector
    - RS Steganalysis
    - Container overlay inspection
    - Blind LSB extraction
    - Visual ELA & LSB bit plane generation
    """
    img = Image.open(filepath)
    width, height = img.size
    mode = img.mode
    format_name = img.format or "UNKNOWN"
    
    rgb = img.convert("RGB")
    arr = np.array(rgb)
    
    # 1. Chi-Square for R, G, B channels
    chi2_results = {}
    channel_names = ["Red", "Green", "Blue"]
    suspicious_channels = []
    
    for i, ch_name in enumerate(channel_names):
        res = calculate_channel_chi_square(arr[:, :, i])
        chi2_results[ch_name] = res
        if res["suspicious"]:
            suspicious_channels.append(ch_name)
            
    # 2. RS Steganalysis on Grayscale
    gray = np.array(img.convert("L"))
    rs_results = calculate_rs_steganalysis(gray)
    
    # 3. Container Overlays
    overlay_results = check_container_overlays(filepath)
    
    # 4. Blind LSB extraction candidates
    blind_results = extract_blind_lsb_candidates(img)
    
    # 5. Visual Artifacts (ELA + LSB Plane)
    ela_filename = f"ela_{filepath.stem}.png"
    lsb_filename = f"lsb_{filepath.stem}.png"
    ela_path = temp_dir / ela_filename
    lsb_path = temp_dir / lsb_filename
    
    ela_b64 = generate_error_level_analysis(img, ela_path)
    lsb_b64 = generate_lsb_plane_visualization(img, lsb_path)
    
    # Extract EXIF metadata if present
    exif_data = {}
    try:
        raw_exif = img.getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = str(tag_id)
                exif_data[tag_name] = str(value)[:80]
    except Exception:
        pass

    return {
        "dimensions": f"{width} x {height}",
        "color_mode": mode,
        "format": format_name,
        "exif_metadata_count": len(exif_data),
        "exif_samples": exif_data,
        "chi_square": {
            "channels": chi2_results,
            "suspicious_channels": suspicious_channels,
            "is_suspicious": len(suspicious_channels) > 0
        },
        "rs_analysis": rs_results,
        "container_overlay": overlay_results,
        "blind_lsb": blind_results,
        "visual_artifacts": {
            "ela_data_url": ela_b64,
            "lsb_plane_data_url": lsb_b64
        }
    }
