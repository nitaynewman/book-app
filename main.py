import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from utils.selenium_client import download_book
from utils.audio import PDFToMP3Converter
import os
import urllib.parse
import shutil
import uvicorn
from starlette.background import BackgroundTask
from pathlib import Path
from uuid import uuid4
import threading
import logging
import aiofiles
import time
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job tracker with timestamps for cleanup
job_results = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdf")
MP3_DIR = os.path.join(BASE_DIR, "mp3")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(MP3_DIR, exist_ok=True)

# Cleanup old jobs periodically (older than 1 hour)
def cleanup_old_jobs():
    """Clean up old jobs and their files"""
    current_time = time.time()
    jobs_to_remove = []
    
    for job_id, job in job_results.items():
        # Remove jobs older than 1 hour
        if current_time - job.get('created_at', 0) > 3600:
            jobs_to_remove.append(job_id)
            
            # Remove associated file if it exists
            if job.get('file_path') and os.path.exists(job['file_path']):
                try:
                    os.remove(job['file_path'])
                    logger.info(f"Removed old file: {job['file_path']}")
                except Exception as e:
                    logger.error(f"Error removing old file: {e}")
    
    for job_id in jobs_to_remove:
        del job_results[job_id]
        logger.info(f"Cleaned up old job: {job_id}")

def cleanup_folders():
    """Clean up PDF and MP3 directories"""
    folder_counter = 0
    for folder in [PDF_DIR, MP3_DIR]:
        if os.path.exists(folder):
            try:
                # Only remove files, not the directory itself
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                logger.info(f"Cleaned files in folder: {folder}")
                folder_counter += 1
            except Exception as e:
                logger.error(f"Error cleaning folder {folder}: {e}")
    return folder_counter

@app.delete("/delete_folders")
def cleanup_folders_endpoint():
    folder_counter = cleanup_folders()
    cleanup_old_jobs()  # Also cleanup old jobs
    if folder_counter > 0:
        return {"message": f"Cleaned {folder_counter} folders and old jobs"}     
    return {"message": "No folders to clean"}

@app.get("/book_pdf")
def get_book(book_name: str, background_tasks: BackgroundTasks):
    """Quick PDF download endpoint with timeout protection"""
    try:
        decoded_name = urllib.parse.unquote(book_name)
        
        # Start download in background thread to avoid blocking
        job_id = str(uuid4())
        job_results[job_id] = {
            "status": "downloading", 
            "created_at": time.time(),
            "book_name": decoded_name,
            "type": "pdf_only"
        }
        
        def download_task():
            try:
                file_path = download_book(decoded_name)
                if file_path and os.path.exists(file_path):
                    job_results[job_id]["status"] = "completed"
                    job_results[job_id]["file_path"] = file_path
                else:
                    job_results[job_id]["status"] = "failed"
                    job_results[job_id]["reason"] = "Download failed"
            except Exception as e:
                job_results[job_id]["status"] = "failed"
                job_results[job_id]["reason"] = str(e)
                logger.error(f"Download error for {decoded_name}: {e}")
        
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()
        
        # Return job ID for status checking
        return {
            "message": "Download started",
            "job_id": job_id,
            "status_check_url": f"/download_status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Error in get_book: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_status/{job_id}")
async def get_download_status(job_id: str):
    """Check PDF download status and return file when ready"""
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed" and job.get("type") == "pdf_only":
        if not os.path.exists(job["file_path"]):
            job_results[job_id] = {"status": "failed", "reason": "File no longer exists"}
            raise HTTPException(status_code=404, detail="Generated file no longer exists")
        
        return FileResponse(
            job["file_path"], 
            filename=os.path.basename(job["file_path"]), 
            media_type='application/pdf',
            background=BackgroundTask(cleanup_folders)
        )

    return job

async def file_streamer(file_path: str, chunk_size: int = 8192):
    """Stream file in chunks to handle large files"""
    try:
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(chunk_size):
                yield chunk
    except Exception as e:
        logger.error(f"Error streaming file {file_path}: {e}")
        raise

@app.get("/audio_status/{job_id}")
async def get_audio_status(job_id: str):
    """Check audio conversion status and return file when ready"""
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        if not os.path.exists(job["file_path"]):
            # File was deleted, update job status
            job_results[job_id] = {"status": "failed", "reason": "File no longer exists"}
            raise HTTPException(status_code=404, detail="Generated file no longer exists")
        
        # Get file size to determine if we should stream
        file_size = os.path.getsize(job["file_path"])
        filename = os.path.basename(job["file_path"])
        
        # For files larger than 10MB, use streaming response
        if file_size > 10 * 1024 * 1024:  # 10MB threshold for streaming
            logger.info(f"Streaming large file: {filename} ({file_size / (1024*1024):.1f}MB)")
            
            return StreamingResponse(
                file_streamer(job["file_path"]),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes"
                },
                background=BackgroundTask(cleanup_folders)
            )
        else:
            # For smaller files, use regular FileResponse
            return FileResponse(
                job["file_path"],
                media_type="audio/mpeg",
                filename=filename,
                background=BackgroundTask(cleanup_folders)
            )

    return job

def process_audio_job(job_id: str, book_name: str, voice: str):
    """Background function to process audio conversion with better error handling"""
    try:
        logger.info(f"Starting audio processing for job {job_id}")
        
        # Update job status
        job_results[job_id]["status"] = "downloading"
        
        decoded_name = urllib.parse.unquote(book_name)
        
        # Add timeout for download to prevent hanging
        start_time = time.time()
        file_path = download_book(decoded_name)
        
        # Check if download took too long (more than 5 minutes)
        if time.time() - start_time > 300:
            job_results[job_id] = {"status": "failed", "reason": "Download timeout"}
            logger.error(f"Download timeout for job {job_id}")
            return

        if not file_path or not os.path.exists(file_path):
            job_results[job_id] = {"status": "failed", "reason": "Download failed or file not found"}
            logger.error(f"Download failed for job {job_id}")
            return

        # Update job status
        job_results[job_id]["status"] = "converting"
        job_results[job_id]["progress"] = "Starting text extraction and audio generation"
        logger.info(f"Starting conversion for job {job_id}")

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            converter = PDFToMP3Converter()
            
            # Add progress callback to update job status
            def progress_callback(message):
                if job_id in job_results:
                    job_results[job_id]["progress"] = message
            
            # Pass progress callback to converter if it supports it
            loop.run_until_complete(converter.convert_with_voice(file_path, voice))
            
            # Use the decoded name for the MP3 file
            safe_name = os.path.splitext(os.path.basename(file_path))[0]
            mp3_path = os.path.join(converter.output_dir, f"{safe_name}.mp3")
            
            if not os.path.exists(mp3_path):
                job_results[job_id] = {"status": "failed", "reason": "MP3 conversion failed"}
                logger.error(f"MP3 not created for job {job_id}")
                return

            # Verify file size
            file_size = os.path.getsize(mp3_path)
            if file_size == 0:
                job_results[job_id] = {"status": "failed", "reason": "Generated MP3 file is empty"}
                logger.error(f"Empty MP3 file for job {job_id}")
                return

            job_results[job_id] = {
                "status": "completed", 
                "file_path": mp3_path,
                "file_size": file_size,
                "created_at": job_results[job_id]["created_at"],
                "book_name": book_name,
                "voice": voice
            }
            logger.info(f"Job {job_id} completed successfully - Size: {file_size / (1024*1024):.2f}MB")
            
        finally:
            loop.close()
            
    except Exception as e:
        job_results[job_id] = {"status": "failed", "reason": str(e)}
        logger.error(f"Error in job {job_id}: {e}")

@app.post("/audio_from_book")
def generate_audio_async(book_name: str, voice: str = "male"):
    """Start audio generation process asynchronously - optimized for Render"""
    try:
        # Validate voice parameter
        converter = PDFToMP3Converter()
        if voice not in converter.voices:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid voice. Available voices: {list(converter.voices.keys())}"
            )
        
        # Clean up old jobs before starting new one
        cleanup_old_jobs()
        
        job_id = str(uuid4())
        job_results[job_id] = {
            "status": "queued", 
            "file_path": None,
            "book_name": book_name,
            "voice": voice,
            "created_at": time.time(),
            "progress": "Job queued"
        }

        # Start background thread with daemon flag for Render compatibility
        thread = threading.Thread(
            target=process_audio_job,
            args=(job_id, book_name, voice),
            daemon=True  # Thread will die when main program exits
        )
        thread.start()

        logger.info(f"Started job {job_id} for book: {book_name} with voice: {voice}")
        return {
            "message": "Audio generation started", 
            "job_id": job_id,
            "status_check_url": f"/audio_status/{job_id}",
            "estimated_time": "This may take 5-15 minutes depending on book size"
        }
        
    except Exception as e:
        logger.error(f"Error starting audio generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
def list_jobs():
    """List all jobs for debugging"""
    cleanup_old_jobs()  # Clean up old jobs when listing
    return {
        "jobs": {
            job_id: {
                "status": job["status"],
                "book_name": job.get("book_name", "unknown"),
                "voice": job.get("voice", "unknown"),
                "progress": job.get("progress", ""),
                "file_size": job.get("file_size", 0),
                "created_at": job.get("created_at", 0)
            }
            for job_id, job in job_results.items()
        }
    }

@app.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel/remove a job"""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_results.pop(job_id)
    if job["status"] == "completed" and job.get("file_path") and os.path.exists(job["file_path"]):
        try:
            os.remove(job["file_path"])
            logger.info(f"Removed file for cancelled job: {job['file_path']}")
        except Exception as e:
            logger.error(f"Error removing file {job['file_path']}: {e}")
    
    return {"message": f"Job {job_id} cancelled/removed"}

@app.get("/health")
def health_check():
    """Enhanced health check endpoint for Render"""
    cleanup_old_jobs()  # Clean up during health checks
    
    active_jobs = len([j for j in job_results.values() if j["status"] in ["queued", "downloading", "converting"]])
    completed_jobs = len([j for j in job_results.values() if j["status"] == "completed"])
    failed_jobs = len([j for j in job_results.values() if j["status"] == "failed"])
    
    # Check disk space
    pdf_files = len([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]) if os.path.exists(PDF_DIR) else 0
    mp3_files = len([f for f in os.listdir(MP3_DIR) if f.endswith('.mp3')]) if os.path.exists(MP3_DIR) else 0
    
    return {
        "status": "healthy",
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "total_jobs": len(job_results),
        "pdf_files": pdf_files,
        "mp3_files": mp3_files,
        "uptime": "running"
    }

# Cleanup endpoint for manual maintenance
@app.post("/cleanup")
def manual_cleanup():
    """Manual cleanup endpoint for maintenance"""
    cleanup_old_jobs()
    folder_count = cleanup_folders()
    return {
        "message": "Manual cleanup completed",
        "folders_cleaned": folder_count,
        "remaining_jobs": len(job_results)
    }

if __name__ == "__main__":
    # For Render, use port from environment
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
