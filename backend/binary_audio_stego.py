import struct
from pathlib import Path
from typing import Dict, Any, List

def analyze_pe_executable(filepath: Path) -> Dict[str, Any]:
    """
    Level 2 PE Executable Anomaly & Overlay Detection:
    Parses DOS and PE headers, calculates end of last section,
    and detects appended overlay payloads.
    """
    with open(filepath, "rb") as f:
        data = f.read()

    total_size = len(data)
    if total_size < 64 or data[:2] != b"MZ":
        return {"format": "Invalid PE", "is_suspicious": False}

    try:
        pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
        if pe_offset + 4 > total_size or data[pe_offset:pe_offset+4] != b"PE\x00\x00":
            return {"format": "DOS Executable (No PE)", "is_suspicious": False}

        # Number of sections at pe_offset + 6 (WORD)
        num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
        # Size of optional header at pe_offset + 20 (WORD)
        opt_hdr_size = struct.unpack_from("<H", data, pe_offset + 20)[0]

        section_tbl_offset = pe_offset + 24 + opt_hdr_size
        max_raw_end = 0

        # Each section header is 40 bytes
        for i in range(num_sections):
            sec_offset = section_tbl_offset + (i * 40)
            if sec_offset + 40 > total_size:
                break
            size_raw_data = struct.unpack_from("<I", data, sec_offset + 16)[0]
            ptr_raw_data = struct.unpack_from("<I", data, sec_offset + 20)[0]
            sec_end = ptr_raw_data + size_raw_data
            if sec_end > max_raw_end:
                max_raw_end = sec_end

        overlay_size = 0
        has_overlay = False
        overlay_preview = ""

        if max_raw_end > 0 and max_raw_end < total_size:
            overlay_size = total_size - max_raw_end
            if overlay_size > 16: # Ignore tiny compiler alignment padding
                has_overlay = True
                overlay_data = data[max_raw_end:]
                try:
                    overlay_preview = overlay_data[:120].decode("utf-8", errors="replace")
                except Exception:
                    overlay_preview = f"Hex: {overlay_data[:48].hex()}"

        return {
            "format": "Windows PE Executable",
            "number_of_sections": num_sections,
            "logical_size_bytes": max_raw_end,
            "total_file_size_bytes": total_size,
            "has_trailing_overlay": has_overlay,
            "overlay_size_bytes": overlay_size,
            "overlay_preview": overlay_preview,
            "is_suspicious": has_overlay
        }
    except Exception as e:
        return {"format": "PE Executable (Parse error)", "is_suspicious": False, "error": str(e)}

def analyze_wav_audio(filepath: Path) -> Dict[str, Any]:
    """
    Level 2 WAV Audio Steganography Detection:
    - Verifies RIFF/WAVE header integrity
    - Checks for trailing payload past RIFF chunk boundary
    - Examines PCM audio sample LSB entropy
    """
    with open(filepath, "rb") as f:
        data = f.read()

    total_size = len(data)
    if total_size < 44 or not data.startswith(b"RIFF") or data[8:12] != b"WAVE":
        return {"format": "Invalid WAV", "is_suspicious": False}

    riff_size = struct.unpack_from("<I", data, 4)[0]
    expected_file_size = riff_size + 8

    has_trailing_data = False
    trailing_size = 0
    trailing_preview = ""

    if total_size > expected_file_size + 8:
        has_trailing_data = True
        trailing_size = total_size - expected_file_size
        trailing_bytes = data[expected_file_size:]
        try:
            trailing_preview = trailing_bytes[:100].decode("utf-8", errors="replace")
        except Exception:
            trailing_preview = f"Hex: {trailing_bytes[:48].hex()}"

    # Find 'data' chunk
    data_idx = data.find(b"data")
    pcm_lsb_entropy = 0.0
    if data_idx != -1 and data_idx + 8 < total_size:
        data_chunk_size = struct.unpack_from("<I", data, data_idx + 4)[0]
        samples = data[data_idx + 8 : data_idx + 8 + min(data_chunk_size, 32768)]
        if len(samples) > 0:
            lsb_bits = [b & 1 for b in samples]
            ones = sum(lsb_bits)
            zeros = len(lsb_bits) - ones
            # Natural audio has slight bias; random/encrypted stego tends towards 0.5 ratio
            p1 = ones / len(lsb_bits)
            p0 = zeros / len(lsb_bits)
            import math
            if p1 > 0 and p0 > 0:
                pcm_lsb_entropy = -(p0 * math.log2(p0) + p1 * math.log2(p1))

    is_suspicious = has_trailing_data or (pcm_lsb_entropy > 0.999 and len(samples) > 4000)

    return {
        "format": "WAV Audio (PCM)",
        "declared_riff_size": riff_size,
        "actual_file_size": total_size,
        "has_trailing_data": has_trailing_data,
        "trailing_size_bytes": trailing_size,
        "trailing_preview": trailing_preview,
        "lsb_entropy": round(pcm_lsb_entropy, 4),
        "is_suspicious": is_suspicious
    }
