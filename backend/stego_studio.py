import io
import struct
from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageDraw
import numpy as np

def create_clean_baseline_image(output_path: Path) -> Path:
    """Creates a natural gradient image with geometric shapes that tests clean."""
    width, height = 300, 300
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Smooth gradient background
    for y in range(height):
        r = int(50 + 150 * (y / height))
        g = int(80 + 120 * (1.0 - (y / height)))
        b = int(120 + 80 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw soft shapes
    draw.ellipse([50, 50, 250, 250], fill=(200, 160, 60), outline=(240, 200, 100))
    draw.rectangle([80, 80, 220, 220], fill=(60, 140, 220), outline=(100, 180, 255))
    
    img.save(output_path, format="PNG")
    return output_path

def create_lsb_stego_image(secret_text: str, output_path: Path) -> Path:
    """Embeds a secret string into the LSB plane of an image."""
    width, height = 300, 300
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        r = int(60 + 140 * (y / height))
        g = int(70 + 130 * (1.0 - (y / height)))
        b = int(100 + 100 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    draw.ellipse([60, 60, 240, 240], fill=(180, 120, 80))
    
    # Format payload with StegoForge magic signature: SFRG<len:4bytes><text>
    payload_bytes = b"SFRG" + len(secret_text).to_bytes(4, "big") + secret_text.encode("utf-8") + b"\x00"
    
    # Convert payload into bits
    bits = []
    for b in payload_bytes:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
            
    arr = np.array(img)
    flat = arr.reshape(-1)

    # Embed payload followed by pseudo-random bitstream across 45% of the carrier
    target_embed_bits = int(len(flat) * 0.45)
    import random
    rng = random.Random(42)
    while len(bits) < target_embed_bits:
        bits.append(rng.randint(0, 1))
    
    embed_len = min(len(bits), len(flat))
    for i in range(embed_len):
        flat[i] = (flat[i] & 0xFE) | bits[i]
        
    stego_arr = flat.reshape(arr.shape)
    stego_img = Image.fromarray(stego_arr.astype(np.uint8))
    stego_img.save(output_path, format="PNG")
    return output_path

def create_trailing_overlay_image(secret_text: str, output_path: Path) -> Path:
    """Creates a valid JPEG image and appends a hidden overlay past the FF D9 marker."""
    width, height = 250, 250
    img = Image.new("RGB", (width, height), color=(40, 90, 160))
    draw = ImageDraw.Draw(img)
    draw.text((30, 110), "Digital Evidence Sample", fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    jpeg_bytes = buf.getvalue()
    
    # Hidden payload appended to EOF
    hidden_payload = (
        f"\n--- CONCEALED FORENSIC PAYLOAD ---\n"
        f"CLASSIFIED_EVIDENCE_ID: CR-2026-9812\n"
        f"SECRET_DATA: {secret_text}\n"
        f"TIMESTAMP: 2026-11-12T17:30:00Z\n"
        f"-----------------------------------\n"
    ).encode("utf-8")
    
    total_data = jpeg_bytes + hidden_payload
    with open(output_path, "wb") as f:
        f.write(total_data)
        
    return output_path

def create_zero_width_text(cover_text: str, secret_text: str, output_path: Path) -> Path:
    """
    Converts secret_text to binary using \u200b (0) and \u200c (1)
    and hides it invisibly inside cover_text.
    """
    zw_binary = ""
    for ch in secret_text:
        val = ord(ch)
        for i in range(7, -1, -1):
            bit = (val >> i) & 1
            zw_binary += '\u200b' if bit == 0 else '\u200c'
            
    # Insert invisible string between first word and second word
    words = cover_text.split(" ", 1)
    if len(words) > 1:
        stego_text = words[0] + " " + zw_binary + words[1]
    else:
        stego_text = cover_text + zw_binary

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(stego_text)
        
    return output_path

def create_disguised_file(output_path: Path) -> Path:
    """Creates a file with .jpg extension that is actually a ZIP/OpenXML archive."""
    import zipfile
    with zipfile.ZipFile(output_path, "w") as z:
        z.writestr("confidential.txt", "This is a hidden zip archive disguised with an image extension!")
    return output_path

def create_stego_pdf(secret_text: str, output_path: Path) -> Path:
    """Creates a basic valid PDF containing a /StegoData dictionary entry."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /StegoData (" + secret_text.encode("latin1") + b") >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 50 >>\nstream\nBT /F1 12 Tf 100 700 Td (Forensic Evidence Document) Tj ET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000095 00000 n \n0000000154 00000 n \n0000000244 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n346\n%%EOF\n"
    )
    with open(output_path, "wb") as f:
        f.write(pdf_content)
    return output_path
