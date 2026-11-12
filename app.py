import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import BASE_DIR, UPLOAD_DIR, SAMPLES_DIR, TEMP_DIR
from backend.triage import perform_triage
from backend.image_stego import analyze_image
from backend.text_stego import analyze_text
from backend.doc_stego import analyze_pdf, analyze_office
from backend.binary_audio_stego import analyze_pe_executable, analyze_wav_audio
from backend.correlation import correlate_findings
from backend.report_generator import generate_forensic_report
import backend.stego_studio as studio

app = FastAPI(
    title="Anti-Forensics & Steganography AI Detection Suite",
    description="Digital Forensics Tool for Concealed & Manipulated Digital Evidence",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for recent analyses
analysis_store: Dict[str, Dict[str, Any]] = {}

# Mount static frontend
frontend_dir = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

def ensure_demo_samples():
    """Generates default demo samples if not already present."""
    clean_img = SAMPLES_DIR / "sample_clean_evidence.png"
    if not clean_img.exists():
        studio.create_clean_baseline_image(clean_img)
        
    lsb_img = SAMPLES_DIR / "sample_stego_lsb.png"
    if not lsb_img.exists():
        studio.create_lsb_stego_image("TOP_SECRET_COVERT_EXFILTRATION_FLAG{FORENSIC_TRIAGE_SUCCESS}", lsb_img)
        
    overlay_img = SAMPLES_DIR / "sample_overlay_stego.jpg"
    if not overlay_img.exists():
        studio.create_trailing_overlay_image("CONFIDENTIAL_PROJECT_BLUEPRINT_ENCRYPTED_ARCHIVE", overlay_img)
        
    zw_txt = SAMPLES_DIR / "sample_zero_width_stego.txt"
    if not zw_txt.exists():
        cover = "The quick brown fox jumps over the lazy dog in broad daylight."
        secret = "ATTACK_AT_DAWN_1001"
        studio.create_zero_width_text(cover, secret, zw_txt)
        
    disguised = SAMPLES_DIR / "sample_disguised_archive.jpg"
    if not disguised.exists():
        studio.create_disguised_file(disguised)

    pdf_sample = SAMPLES_DIR / "sample_pdf_stego.pdf"
    if not pdf_sample.exists():
        studio.create_stego_pdf("RESTRICTED_ACCESS_PAYLOAD_KEY_9921", pdf_sample)

@app.on_event("startup")
async def startup_event():
    ensure_demo_samples()

@app.get("/")
async def serve_index():
    return FileResponse(frontend_dir / "index.html")

def execute_pipeline(filepath: Path, filename: str) -> Dict[str, Any]:
    """Runs the 4-level triage, steganography screening, and correlation pipeline."""
    analysis_id = str(uuid.uuid4())
    
    # Level 1: Triage
    triage_info = perform_triage(filepath, filename)
    detected_mime = triage_info["detected_mime"]
    detected_ext = triage_info["expected_extension"]
    claimed_ext = triage_info["claimed_extension"]
    
    specific_analysis = {}
    file_category = "unknown"
    
    # Level 2: Specific Steganography Screening
    # Route by detected format or claimed extension
    if detected_mime.startswith("image/") or claimed_ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
        file_category = "image"
        try:
            specific_analysis = analyze_image(filepath, TEMP_DIR)
        except Exception as e:
            specific_analysis = {"error": f"Image analysis failed: {str(e)}"}
            
    elif detected_mime == "text/plain" or claimed_ext in [".txt", ".log", ".csv", ".json"]:
        file_category = "text"
        try:
            specific_analysis = analyze_text(filepath)
        except Exception as e:
            specific_analysis = {"error": f"Text analysis failed: {str(e)}"}
            
    elif detected_mime == "application/pdf" or claimed_ext == ".pdf":
        file_category = "pdf"
        try:
            specific_analysis = analyze_pdf(filepath)
        except Exception as e:
            specific_analysis = {"error": f"PDF analysis failed: {str(e)}"}
            
    elif claimed_ext in [".docx", ".xlsx", ".pptx"] or (detected_mime == "application/zip" and claimed_ext in [".docx", ".xlsx"]):
        file_category = "office"
        try:
            specific_analysis = analyze_office(filepath)
        except Exception as e:
            specific_analysis = {"error": f"Office analysis failed: {str(e)}"}
            
    elif detected_mime == "application/x-dosexec" or claimed_ext in [".exe", ".dll"]:
        file_category = "binary"
        try:
            specific_analysis = analyze_pe_executable(filepath)
        except Exception as e:
            specific_analysis = {"error": f"Binary analysis failed: {str(e)}"}
            
    elif detected_mime == "audio/wav" or claimed_ext == ".wav":
        file_category = "audio"
        try:
            specific_analysis = analyze_wav_audio(filepath)
        except Exception as e:
            specific_analysis = {"error": f"Audio analysis failed: {str(e)}"}
            
    else:
        file_category = "generic"
        specific_analysis = {"note": "Standard triage and entropy assessment completed."}

    # Level 3: Forensic Correlation
    correlation_info = correlate_findings(triage_info, specific_analysis, file_category)
    
    # Level 4: Report Generation
    report = generate_forensic_report(analysis_id, triage_info, specific_analysis, correlation_info)
    
    result = {
        "analysis_id": analysis_id,
        "file_category": file_category,
        "triage": triage_info,
        "analysis": specific_analysis,
        "correlation": correlation_info,
        "report": report
    }
    
    analysis_store[analysis_id] = result
    return result

@app.post("/api/analyze")
async def analyze_uploaded_file(file: UploadFile = File(...)):
    """Uploads and analyzes an evidence file."""
    temp_filename = f"{uuid.uuid4().hex}_{file.filename}"
    save_path = UPLOAD_DIR / temp_filename
    
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = execute_pipeline(save_path, file.filename)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/samples")
async def get_sample_files():
    """Lists available pre-generated test samples."""
    ensure_demo_samples()
    samples = []
    
    descriptions = {
        "sample_clean_evidence.png": "Baseline clean natural image (No steganography, normal entropy)",
        "sample_stego_lsb.png": "Image with secret data embedded in LSB plane (Chi-Square & RS detectable)",
        "sample_overlay_stego.jpg": "JPEG image with secret payload appended past FF D9 End-of-Image",
        "sample_zero_width_stego.txt": "Cover text with hidden Unicode zero-width binary secret message",
        "sample_disguised_archive.jpg": "ZIP archive disguised with .jpg extension (Magic byte mismatch)",
        "sample_pdf_stego.pdf": "PDF document with embedded /StegoData dictionary entry"
    }
    
    for f in SAMPLES_DIR.iterdir():
        if f.is_file():
            samples.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "description": descriptions.get(f.name, "Forensic sample evidence")
            })
            
    return JSONResponse(content={"samples": samples})

@app.post("/api/analyze-sample")
async def analyze_sample_file(sample_name: str = Form(...)):
    """Runs instant analysis on a pre-built demo sample."""
    sample_path = SAMPLES_DIR / sample_name
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample file not found")
        
    result = execute_pipeline(sample_path, sample_name)
    return JSONResponse(content=result)

@app.post("/api/generate-demo")
async def generate_custom_demo(
    demo_type: str = Form(...),
    secret_text: str = Form("CONFIDENTIAL_FLAG_2026"),
    cover_text: Optional[str] = Form("Standard corporate memorandum document.")
):
    """Generates custom on-demand stego files for live classroom demonstration."""
    gen_id = uuid.uuid4().hex[:6]
    
    if demo_type == "lsb":
        out_name = f"custom_lsb_{gen_id}.png"
        out_path = SAMPLES_DIR / out_name
        studio.create_lsb_stego_image(secret_text, out_path)
    elif demo_type == "overlay":
        out_name = f"custom_overlay_{gen_id}.jpg"
        out_path = SAMPLES_DIR / out_name
        studio.create_trailing_overlay_image(secret_text, out_path)
    elif demo_type == "zero_width":
        out_name = f"custom_zw_{gen_id}.txt"
        out_path = SAMPLES_DIR / out_name
        studio.create_zero_width_text(cover_text or "Hello world", secret_text, out_path)
    elif demo_type == "pdf":
        out_name = f"custom_pdf_{gen_id}.pdf"
        out_path = SAMPLES_DIR / out_name
        studio.create_stego_pdf(secret_text, out_path)
    elif demo_type == "clean":
        out_name = f"custom_clean_{gen_id}.png"
        out_path = SAMPLES_DIR / out_name
        studio.create_clean_baseline_image(out_path)
    else:
        raise HTTPException(status_code=400, detail="Invalid demo type")
        
    result = execute_pipeline(out_path, out_name)
    return JSONResponse(content={"filename": out_name, "analysis": result})

@app.get("/api/report/{analysis_id}")
async def get_report(analysis_id: str):
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Report not found")
    return JSONResponse(content=analysis_store[analysis_id]["report"])

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Anti-Forensics & Steganography AI Detection Suite...")
    print("Server running at: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

