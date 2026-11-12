import hashlib
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple

MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png", "PNG Image"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg", "JPEG Image"),
    (b"GIF87a", "image/gif", ".gif", "GIF Image (87a)"),
    (b"GIF89a", "image/gif", ".gif", "GIF Image (89a)"),
    (b"BM", "image/bmp", ".bmp", "BMP Bitmap"),
    (b"%PDF-", "application/pdf", ".pdf", "PDF Document"),
    (b"PK\x03\x04", "application/zip", ".zip", "ZIP Archive / OpenXML Package"),
    (b"\x7fELF", "application/x-elf", ".elf", "Linux ELF Executable"),
    (b"MZ", "application/x-dosexec", ".exe", "DOS/Windows Executable (PE)"),
    (b"7z\xbc\xaf'\x1c", "application/x-7z-compressed", ".7z", "7-Zip Archive"),
    (b"\x1f\x8b", "application/gzip", ".gz", "GZIP Compressed File"),
]

def calculate_hashes(data: bytes) -> Dict[str, str]:
    """Calculates cryptographic hashes for evidence preservation and chain of custody."""
    sha256 = hashlib.sha256(data).hexdigest()
    md5 = hashlib.md5(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    return {
        "sha256": sha256,
        "md5": md5,
        "sha1": sha1
    }

def detect_magic_signature(data: bytes) -> Tuple[str, str, str]:
    """
    Detects true MIME type and format based on magic header bytes.
    Returns (mime_type, expected_ext, description).
    """
    # RIFF container check (WAV or WEBP)
    if len(data) >= 12 and data[:4] == b"RIFF":
        riff_type = data[8:12]
        if riff_type == b"WAVE":
            return "audio/wav", ".wav", "WAV Audio File"
        elif riff_type == b"WEBP":
            return "image/webp", ".webp", "WebP Image"

    for magic, mime, ext, desc in MAGIC_SIGNATURES:
        if data.startswith(magic):
            return mime, ext, desc

    # Plain text check
    try:
        sample = data[:4096]
        sample.decode('utf-8')
        # Check control chars ratio
        control_chars = sum(1 for b in sample if (b < 32 and b not in (9, 10, 13)))
        if control_chars == 0:
            return "text/plain", ".txt", "Plain Text / UTF-8 File"
    except UnicodeDecodeError:
        pass

    return "application/octet-stream", ".bin", "Binary / Unknown Format"

def perform_triage(filepath: Path, original_filename: str) -> Dict[str, Any]:
    """
    Level 1: File Triage & Fingerprinting
    - Preserves file identity
    - Calculates SHA-256, MD5, SHA-1 hashes
    - Inspects file size and timestamp
    - Detects file signature and flags extension mismatches
    """
    with open(filepath, "rb") as f:
        data = f.read()

    file_size = len(data)
    hashes = calculate_hashes(data)
    detected_mime, expected_ext, format_desc = detect_magic_signature(data)

    claimed_ext = Path(original_filename).suffix.lower()
    
    # Check for extension disguise / mismatch
    is_extension_mismatch = False
    mismatch_severity = "normal"
    mismatch_details = ""

    # Group equivalent extensions
    jpeg_exts = {".jpg", ".jpeg", ".jpe", ".jfif"}
    zip_exts = {".zip", ".docx", ".xlsx", ".pptx", ".jar", ".apk"}

    if expected_ext == ".jpg" and claimed_ext in jpeg_exts:
        pass
    elif expected_ext == ".zip" and claimed_ext in zip_exts:
        pass
    elif detected_mime != "application/octet-stream" and claimed_ext != expected_ext:
        # Flag discrepancy!
        is_extension_mismatch = True
        mismatch_severity = "high"
        mismatch_details = (
            f"File extension claimed '{claimed_ext}', but magic byte inspection reveals "
            f"true file signature is '{format_desc}' ({detected_mime})."
        )

    # Shannon Entropy calculation on entire file
    import math
    if file_size > 0:
        byte_counts = [0] * 256
        for b in data:
            byte_counts[b] += 1
        entropy = 0.0
        for count in byte_counts:
            if count > 0:
                p = count / file_size
                entropy -= p * math.log2(p)
    else:
        entropy = 0.0

    stat_info = os.stat(filepath)

    return {
        "filename": original_filename,
        "filesize": file_size,
        "filesize_formatted": f"{file_size / 1024:.2f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.2f} MB",
        "hashes": hashes,
        "claimed_extension": claimed_ext,
        "detected_mime": detected_mime,
        "detected_format": format_desc,
        "expected_extension": expected_ext,
        "extension_mismatch": is_extension_mismatch,
        "mismatch_details": mismatch_details,
        "global_entropy": round(entropy, 4),
        "created_time": time.ctime(stat_info.st_ctime),
        "modified_time": time.ctime(stat_info.st_mtime),
    }

