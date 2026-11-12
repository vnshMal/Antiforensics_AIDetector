import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLES_DIR = BASE_DIR / "samples"
TEMP_DIR = BASE_DIR / "temp"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Risk Thresholds
RISK_CLEAN = 15
RISK_LOW = 40
RISK_MEDIUM = 70

# Maximum upload size: 50MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

SUPPORTED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"}
SUPPORTED_DOC_EXTS = {".pdf", ".docx", ".xlsx", ".pptx"}
SUPPORTED_TEXT_EXTS = {".txt", ".log", ".csv", ".json", ".md"}
SUPPORTED_AUDIO_EXTS = {".wav", ".mp3"}
SUPPORTED_BINARY_EXTS = {".exe", ".dll", ".elf", ".bin"}

