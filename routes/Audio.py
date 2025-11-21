from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from helper.authentication import APIKeyChecker
import os
import re
import sys
import asyncio
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from routes.book_pdf import download_book
from functions.pdf2mp3 import PDFToMP3Converter

router = APIRouter(
    prefix='/audio',
    tags=['audio']
)

# API key checker for audio operations
audio_auth = APIKeyChecker("audio")

# Store job status in memory (use Redis in production)
jobs = {}

class AudioJobRequest(BaseModel):
    book_name: str
    voice: str = "male"

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, downloading, extracting, converting, merging, completed, failed
    progress: int = 0
    reason: str = None
    filename: str = None

# Background task to process audio conversion
async def process_audio_job(job_id: str, book_name: str, voice: str):
    """Background task to download PDF and convert to MP3."""
    
    def update_progress(status: str, progress: int):
        """Update job progress in jobs dict."""
        jobs[job_id]["status"] = status
        jobs[job_id]["progress"] = progress
        print(f"[Job {job_id}] Status: {status} | Progress: {progress}%")
    
    try:
        # Update status: downloading
        update_progress("downloading", 5)
        
        print(f'[Job {job_id}] Downloading PDF for: {book_name}')
        pdf_path = download_book(book_name)
        
        if not pdf_path or not os.path.exists(pdf_path):
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["reason"] = f"Failed to download PDF for book: {book_name}"
            return
        
        update_progress("downloading", 10)
        print(f"[Job {job_id}] PDF downloaded successfully")
        
        # Initialize converter with progress callback
        safe_name = re.sub(r'\W+', '_', book_name)
        converter = PDFToMP3Converter(progress_callback=update_progress)
        mp3_filename = os.path.join(converter.output_dir, f"{safe_name}.mp3")
        
        # Convert based on voice type (with progress updates handled by converter)
        await converter.convert_with_voice(pdf_path, voice)
        
        if not os.path.exists(mp3_filename):
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["reason"] = "MP3 file was not generated"
            return
        
        # Update status: completed
        update_progress("completed", 100)
        jobs[job_id]["filename"] = f"{safe_name}.mp3"
        jobs[job_id]["file_path"] = mp3_filename
        
        print(f"[Job {job_id}] ✅ Conversion completed successfully")
        print(f"[Job {job_id}] File: {mp3_filename}")
        
    except Exception as e:
        print(f"[Job {job_id}] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["reason"] = str(e)

@router.post("/audio_from_book")
async def start_audio_conversion(
    background_tasks: BackgroundTasks,
    book_name: str,
    voice: str = "male",
    api_key: str = Depends(audio_auth)
):
    """Start audio conversion job and return job_id."""
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "book_name": book_name,
        "voice": voice,
        "created_at": datetime.now()
    }
    
    print(f"[Job {job_id}] Created new conversion job")
    print(f"  Book: {book_name}")
    print(f"  Voice: {voice}")
    
    # Add background task
    background_tasks.add_task(process_audio_job, job_id, book_name, voice)
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/audio_status/{job_id}")
async def get_audio_status(job_id: str, api_key: str = Depends(audio_auth)):
    """Get status of audio conversion job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Clean up old jobs (older than 2 hours)
    if job["status"] in ["completed", "failed"]:
        age = datetime.now() - job["created_at"]
        if age > timedelta(hours=2):
            # Clean up files
            if "file_path" in job and os.path.exists(job["file_path"]):
                try:
                    os.remove(job["file_path"])
                    print(f"[Job {job_id}] Cleaned up old file")
                except Exception as e:
                    print(f"[Job {job_id}] Cleanup error: {e}")
            del jobs[job_id]
            raise HTTPException(status_code=404, detail="Job expired")
    
    return {
        "status": job["status"],
        "progress": job.get("progress", 0),
        "reason": job.get("reason"),
        "filename": job.get("filename")
    }

@router.get("/download_audio/{job_id}")
async def download_complete_file(
    job_id: str,
    api_key: str = Depends(audio_auth)
):
    """Download complete audio file."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed yet. Current status: {job['status']}")
    
    if "file_path" not in job or not os.path.exists(job["file_path"]):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = job.get("filename", "audio.mp3")
    
    print(f"[Job {job_id}] Serving download: {filename}")
    
    return FileResponse(
        job["file_path"],
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Accept-Ranges": "bytes"
        }
    )

@router.delete("/delete_folders")
async def cleanup_files(api_key: str = Depends(audio_auth)):
    """Clean up temporary files and old jobs."""
    try:
        converter = PDFToMP3Converter()
        cleaned = 0
        
        # Clean up old jobs
        current_time = datetime.now()
        jobs_to_delete = []
        
        for job_id, job in jobs.items():
            age = current_time - job["created_at"]
            # Clean up jobs older than 2 hours
            if age > timedelta(hours=2):
                # Clean up files
                if "file_path" in job and os.path.exists(job["file_path"]):
                    try:
                        os.remove(job["file_path"])
                        cleaned += 1
                        print(f"[Cleanup] Removed file for job {job_id}")
                    except Exception as e:
                        print(f"[Cleanup] Error removing file: {e}")
                jobs_to_delete.append(job_id)
        
        for job_id in jobs_to_delete:
            del jobs[job_id]
        
        print(f"[Cleanup] Removed {len(jobs_to_delete)} old jobs, cleaned {cleaned} files")
        
        return {"status": "success", "cleaned_jobs": len(jobs_to_delete), "cleaned_files": cleaned}
    except Exception as e:
        print(f"[Cleanup] Error: {e}")
        return {"status": "error", "error": str(e)}
    