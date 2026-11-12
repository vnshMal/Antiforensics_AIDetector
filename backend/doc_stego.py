import zipfile
import re
from pathlib import Path
from typing import Dict, Any, List
import pypdf

def analyze_pdf(filepath: Path) -> Dict[str, Any]:
    """
    Level 2 PDF Steganography Inspection:
    - Scans for known project markers like /StegoData
    - Checks for trailing data after %%EOF
    - Checks document metadata and object structure
    """
    with open(filepath, "rb") as f:
        data = f.read()

    total_size = len(data)
    has_stegodata_marker = b"/StegoData" in data
    stegodata_offset = data.find(b"/StegoData") if has_stegodata_marker else -1
    
    # Check for trailing overlay past the last %%EOF
    eof_idx = data.rfind(b"%%EOF")
    trailing_size = 0
    trailing_preview = ""
    has_trailing_data = False
    
    if eof_idx != -1 and (eof_idx + 5) < total_size:
        trailing = data[eof_idx + 5:].strip(b"\r\n \t\x00")
        if len(trailing) > 4:
            has_trailing_data = True
            trailing_size = len(trailing)
            try:
                trailing_preview = trailing[:120].decode("utf-8", errors="replace")
            except Exception:
                trailing_preview = f"Hex: {trailing[:48].hex()}"

    # Try pypdf parsing
    num_pages = 0
    metadata = {}
    is_encrypted = False
    try:
        reader = pypdf.PdfReader(filepath)
        num_pages = len(reader.pages)
        is_encrypted = reader.is_encrypted
        if reader.metadata:
            for k, v in reader.metadata.items():
                metadata[str(k)] = str(v)[:80]
    except Exception as e:
        metadata["parser_warning"] = str(e)

    is_suspicious = has_stegodata_marker or has_trailing_data

    return {
        "format": "PDF Document",
        "num_pages": num_pages,
        "is_encrypted": is_encrypted,
        "stegodata_marker_found": has_stegodata_marker,
        "stegodata_offset": stegodata_offset,
        "trailing_data_after_eof": has_trailing_data,
        "trailing_bytes": trailing_size,
        "trailing_preview": trailing_preview,
        "metadata": metadata,
        "is_suspicious": is_suspicious
    }

def analyze_office(filepath: Path) -> Dict[str, Any]:
    """
    Level 2 Office OpenXML (DOCX/XLSX) Inspection:
    - Scans for project marker 'word/custom/stegodata.xml'
    - Inspects zip package parts for unexpected or hidden files
    - Checks for zero-width characters in document body XML
    """
    has_stegodata_part = False
    suspicious_parts = []
    total_parts = 0
    zero_width_in_doc = 0
    part_names = []

    try:
        with zipfile.ZipFile(filepath, "r") as z:
            part_names = z.namelist()
            total_parts = len(part_names)
            
            for name in part_names:
                if "stegodata.xml" in name.lower():
                    has_stegodata_part = True
                    suspicious_parts.append(name)
                elif "custom/" in name.lower() or "hidden" in name.lower():
                    suspicious_parts.append(name)

            # Check word/document.xml for zero-width characters
            if "word/document.xml" in part_names:
                doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
                zw_chars = ['\u200b', '\u200c', '\u200d', '\ufeff']
                for c in zw_chars:
                    zero_width_in_doc += doc_xml.count(c)

    except zipfile.BadZipFile:
        return {
            "format": "Corrupted or Malformed Office Document",
            "is_suspicious": True,
            "error": "File claims Office format but is not a valid Zip package."
        }
    except Exception as e:
        return {
            "format": "Office Document",
            "is_suspicious": False,
            "error": str(e)
        }

    is_suspicious = has_stegodata_part or (zero_width_in_doc > 5) or (len(suspicious_parts) > 0)

    return {
        "format": "Office OpenXML Document (DOCX/XLSX)",
        "total_package_parts": total_parts,
        "stegodata_xml_found": has_stegodata_part,
        "suspicious_custom_parts": suspicious_parts,
        "zero_width_characters_in_xml": zero_width_in_doc,
        "sample_parts": part_names[:15],
        "is_suspicious": is_suspicious
    }

