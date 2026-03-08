"""
PDF to Video Converter - Main FastAPI Application
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uuid
import os
from datetime import datetime

from app.processors.pdf_processor import PDFProcessor
from app.processors.video_generator import VideoGenerator

app = FastAPI(
    title="PDF to Video Converter",
    description="Convert PDFs to animated educational videos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path("/var/arionix/data/pdf-to-video")
UPLOAD_DIR = BASE_DIR / "uploads"
TEMP_DIR = BASE_DIR / "temp"
VIDEO_DIR = BASE_DIR / "videos"

# Create directories
for dir_path in [UPLOAD_DIR, TEMP_DIR, VIDEO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# In-memory job storage (replace with DB in production)
jobs = {}


class JobStatus:
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@app.get("/")
async def root():
    return {
        "name": "PDF to Video Converter API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload a PDF and start processing"""

    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Check file size (max 50MB)
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB allowed")

    # Create job
    job_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{job_id}.pdf"

    # Save PDF
    with open(pdf_path, 'wb') as f:
        f.write(file_content)

    # Create job record
    jobs[job_id] = {
        "id": job_id,
        "filename": file.filename,
        "status": JobStatus.UPLOADED,
        "progress": 0,
        "created_at": datetime.utcnow().isoformat(),
        "pdf_path": str(pdf_path),
        "video_path": None,
        "error": None
    }

    # Start processing in background
    background_tasks.add_task(process_video, job_id)

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": JobStatus.UPLOADED,
        "message": "PDF uploaded successfully. Processing started."
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]


@app.get("/api/video/{job_id}")
async def get_video(job_id: str):
    """Download or stream the generated video"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Video not ready yet")

    video_path = Path(job["video_path"])

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{job['filename'].replace('.pdf', '')}_animated.mp4"
    )


async def process_video(job_id: str):
    """Background task to process PDF and generate video"""
    try:
        job = jobs[job_id]
        job["status"] = JobStatus.PROCESSING
        job["progress"] = 10

        pdf_path = Path(job["pdf_path"])
        temp_dir = TEMP_DIR / job_id
        temp_dir.mkdir(exist_ok=True)

        # Step 1: Process PDF
        print(f"[{job_id}] Processing PDF...")
        pdf_processor = PDFProcessor()
        pdf_data = pdf_processor.process(str(pdf_path), str(temp_dir))
        job["progress"] = 40

        # Step 2: Generate video
        print(f"[{job_id}] Generating video...")
        video_generator = VideoGenerator()
        video_path = VIDEO_DIR / f"{job_id}.mp4"

        video_generator.generate(
            pdf_data=pdf_data,
            output_path=str(video_path),
            temp_dir=str(temp_dir),
            progress_callback=lambda p: update_progress(job_id, 40 + int(p * 0.6))
        )

        # Complete
        job["status"] = JobStatus.COMPLETED
        job["progress"] = 100
        job["video_path"] = str(video_path)
        job["completed_at"] = datetime.utcnow().isoformat()

        print(f"[{job_id}] Video generation completed!")

    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        job["status"] = JobStatus.FAILED
        job["error"] = str(e)
        job["failed_at"] = datetime.utcnow().isoformat()


def update_progress(job_id: str, progress: int):
    """Update job progress"""
    if job_id in jobs:
        jobs[job_id]["progress"] = min(progress, 100)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
