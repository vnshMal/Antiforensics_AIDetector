import re
from pathlib import Path
from typing import Dict, Any, List

ZERO_WIDTH_CHARS = {
    '\u200b': "Zero-Width Space (ZWSP)",
    '\u200c': "Zero-Width Non-Joiner (ZWNJ)",
    '\u200d': "Zero-Width Joiner (ZWJ)",
    '\ufeff': "Zero-Width No-Break Space (BOM)",
    '\u2060': "Word Joiner",
    '\u200e': "Left-to-Right Mark (LRM)",
    '\u200f': "Right-to-Left Mark (RLM)",
    '\u202a': "Left-to-Right Embedding",
    '\u202c': "Pop Directional Formatting"
}

def decode_zero_width_binary(text: str) -> str:
    """
    Attempts to decode binary concealed via zero-width characters.
    Common convention:
    \u200b = 0, \u200c = 1 (or vice versa)
    """
    zw_seq = [c for c in text if c in ('\u200b', '\u200c', '\u200d', '\ufeff')]
    if len(zw_seq) < 8:
        return ""

    # Strategy 1: ZWSP=0, ZWNJ=1
    bits1 = ""
    for c in zw_seq:
        if c == '\u200b':
            bits1 += "0"
        elif c == '\u200c':
            bits1 += "1"
            
    # Try decoding chunks of 8 bits
    def bits_to_ascii(b_str):
        chars = []
        for i in range(0, len(b_str) - 7, 8):
            byte = b_str[i:i+8]
            val = int(byte, 2)
            if 32 <= val <= 126 or val in (10, 13):
                chars.append(chr(val))
            else:
                return ""
        return "".join(chars)

    decoded1 = bits_to_ascii(bits1)
    if decoded1 and len(decoded1) >= 2:
        return decoded1

    # Strategy 2: ZWSP=1, ZWNJ=0
    bits2 = ""
    for c in zw_seq:
        if c == '\u200b':
            bits2 += "1"
        elif c == '\u200c':
            bits2 += "0"
    decoded2 = bits_to_ascii(bits2)
    if decoded2 and len(decoded2) >= 2:
        return decoded2

    return ""

def analyze_text(filepath: Path) -> Dict[str, Any]:
    """
    Level 2 Text Steganography Screening:
    - Counts and catalogues zero-width characters
    - Computes zero-width density ratio
    - Reconstructs and decodes hidden payload if present
    """
    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1", errors="replace")

    total_chars = len(text)
    zw_counts = {name: 0 for name in ZERO_WIDTH_CHARS.values()}
    total_zw = 0
    zw_positions = []

    for idx, ch in enumerate(text):
        if ch in ZERO_WIDTH_CHARS:
            name = ZERO_WIDTH_CHARS[ch]
            zw_counts[name] += 1
            total_zw += 1
            if len(zw_positions) < 10:
                zw_positions.append({"char": f"U+{ord(ch):04X}", "name": name, "index": idx})

    zw_ratio = (total_zw / max(1, total_chars)) * 100
    is_suspicious = total_zw >= 8 or zw_ratio > 1.0

    decoded_payload = ""
    if total_zw >= 8:
        decoded_payload = decode_zero_width_binary(text)

    # Preview of visible text
    visible_preview = "".join(c for c in text[:300] if c not in ZERO_WIDTH_CHARS)

    return {
        "total_characters": total_chars,
        "zero_width_characters_found": total_zw,
        "zero_width_ratio_percent": round(zw_ratio, 2),
        "zero_width_breakdown": {k: v for k, v in zw_counts.items() if v > 0},
        "sample_positions": zw_positions,
        "is_suspicious": is_suspicious,
        "decoded_hidden_payload": decoded_payload,
        "has_decoded_payload": bool(decoded_payload),
        "visible_text_preview": visible_preview
    }

