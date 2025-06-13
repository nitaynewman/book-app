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
import json
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job tracker with expiration
job_results: Dict[str, Dict[str, Any]] = {}
JOB_EXPIRY_HOURS = 2  # Jobs expire after 2 hours

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

def cleanup_expired_jobs():
    """Clean up expired jobs"""
    current_time = time.time()
    expired_jobs = []
    
    for job_id, job in job_results.items():
        job_age = current_time - job.get('created_at', current_time)
        if job_age > (JOB_EXPIRY_HOURS * 3600):  # Convert hours to seconds
            expired_jobs.append(job_id)
    
    for job_id in expired_jobs:
        cleanup_job_files(job_id)

def cleanup_job_files(job_id: str):
    """Clean up files for a specific job"""
    try:
        job = job_results.get(job_id)
        if job and job.get("chunks_dir") and os.path.exists(job["chunks_dir"]):
            shutil.rmtree(job["chunks_dir"])
            logger.info(f"Cleaned up chunks directory for job {job_id}")
        
        if job_id in job_results:
            del job_results[job_id]
            logger.info(f"Removed job {job_id} from memory")
    except Exception as e:
        logger.error(f"Error cleaning up job {job_id}: {e}")

def cleanup_folders():
    """Clean up PDF and MP3 directories"""
    folder_counter = 0
    for folder in [PDF_DIR, MP3_DIR]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)
                logger.info(f"Cleaned folder: {folder}")
                folder_counter += 1
            except Exception as e:
                logger.error(f"Error cleaning folder {folder}: {e}")
    return folder_counter

@app.delete("/delete_folders")
def cleanup_folders_endpoint():
    """Clean up folders and expired jobs"""
    cleanup_expired_jobs()
    folder_counter = cleanup_folders()
    if folder_counter > 0:
        return {"message": f"Cleaned {folder_counter} folders and expired jobs"}     
    return {"message": "No folders to clean"}

@app.get("/book_pdf")
def get_book(book_name: str, background_tasks: BackgroundTasks):
    try:
        decoded_name = urllib.parse.unquote(book_name)
        file_path = download_book(decoded_name)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Download failed or file not found")

        background_tasks.add_task(cleanup_folders)
        
        return FileResponse(
            file_path, 
            filename=os.path.basename(file_path), 
            media_type='application/pdf'
        )
    except Exception as e:
        logger.error(f"Error in get_book: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def iterfile(file_path: str, chunk_size: int = 8192):
    """Generator to read file in chunks"""
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

@app.get("/download_chunk/{job_id}/{chunk_index}")
async def download_audio_chunk(job_id: str, chunk_index: int):
    """Download a specific audio chunk with better error handling"""
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready. Status: {job['status']}")
    
    chunks_dir = job.get("chunks_dir")
    if not chunks_dir or not os.path.exists(chunks_dir):
        cleanup_job_files(job_id)
        raise HTTPException(status_code=404, detail="Audio chunks no longer available")
    
    chunk_file = os.path.join(chunks_dir, f"chunk_{chunk_index:03d}.mp3")
    if not os.path.exists(chunk_file):
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_index} not found")
    
    try:
        file_size = os.path.getsize(chunk_file)
        filename = f"chunk_{chunk_index:03d}.mp3"
        
        logger.info(f"Serving chunk {chunk_index}: {filename} ({file_size / (1024*1024):.1f}MB)")
        
        return StreamingResponse(
            iterfile(chunk_file),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.error(f"Error serving chunk {chunk_index} for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error serving audio chunk")

@app.get("/audio_status/{job_id}")
async def get_audio_status(job_id: str):
    """Get job status with enhanced information"""
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    if job["status"] == "completed":
        chunks_dir = job.get("chunks_dir")
        if not chunks_dir or not os.path.exists(chunks_dir):
            cleanup_job_files(job_id)
            raise HTTPException(status_code=404, detail="Audio chunks no longer available")
        
        # Count available chunks
        try:
            chunk_files = [f for f in os.listdir(chunks_dir) 
                          if f.startswith("chunk_") and f.endswith(".mp3")]
            chunk_files.sort()
            
            if not chunk_files:
                cleanup_job_files(job_id)
                raise HTTPException(status_code=404, detail="No audio chunks found")
            
            total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
            
            return {
                "status": "completed",
                "total_chunks": len(chunk_files),
                "chunk_urls": [f"/download_chunk/{job_id}/{i}" for i in range(len(chunk_files))],
                "total_size": total_size,
                "filename": job.get("original_filename", "audiobook.mp3"),
                "estimated_duration": job.get("estimated_duration", "Unknown"),
                "created_at": job.get("created_at")
            }
        except Exception as e:
            logger.error(f"Error checking chunks for job {job_id}: {e}")
            cleanup_job_files(job_id)
            raise HTTPException(status_code=500, detail="Error accessing audio chunks")

    return {
        "status": job["status"],
        "message": job.get("message", ""),
        "progress": job.get("progress", 0),
        "created_at": job.get("created_at")
    }

def process_audio_job(job_id: str, book_name: str, voice: str):
    """Background function to process audio conversion with chunking and better progress tracking"""
    try:
        logger.info(f"Starting audio processing for job {job_id}")
        
        # Update job status
        job_results[job_id]["status"] = "downloading"
        job_results[job_id]["message"] = "Downloading book PDF..."
        job_results[job_id]["progress"] = 10
        
        decoded_name = urllib.parse.unquote(book_name)
        file_path = download_book(decoded_name)

        if not file_path or not os.path.exists(file_path):
            job_results[job_id] = {
                "status": "failed", 
                "reason": "Book download failed or file not found",
                "created_at": time.time()
            }
            logger.error(f"Download failed for job {job_id}")
            return

        # Update progress
        job_results[job_id]["status"] = "processing"
        job_results[job_id]["message"] = "Extracting text from PDF..."
        job_results[job_id]["progress"] = 30

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            converter = PDFToMP3Converter()
            
            # Update progress during conversion
            job_results[job_id]["message"] = "Converting text to speech..."
            job_results[job_id]["progress"] = 50
            
            # Use the chunked conversion method
            chunks_dir = loop.run_until_complete(
                converter.convert_with_voice_chunked(file_path, voice, job_id, 
                                                   progress_callback=lambda p: update_job_progress(job_id, p))
            )
            
            if not chunks_dir or not os.path.exists(chunks_dir):
                job_results[job_id] = {
                    "status": "failed", 
                    "reason": "Audio conversion failed - no chunks created",
                    "created_at": time.time()
                }
                logger.error(f"Chunks not created for job {job_id}")
                return

            # Calculate estimated duration
            try:
                chunk_files = [f for f in os.listdir(chunks_dir) 
                              if f.startswith("chunk_") and f.endswith(".mp3")]
                estimated_duration = f"~{len(chunk_files) * 5} minutes"  # Rough estimate
            except:
                estimated_duration = "Unknown"

            safe_name = os.path.splitext(os.path.basename(file_path))[0]
            job_results[job_id] = {
                "status": "completed", 
                "chunks_dir": chunks_dir,
                "original_filename": f"{safe_name}.mp3",
                "estimated_duration": estimated_duration,
                "message": "Conversion completed successfully!",
                "progress": 100,
                "created_at": time.time()
            }
            logger.info(f"Job {job_id} completed successfully with chunks")
            
        finally:
            loop.close()
            # Clean up the original PDF file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up PDF file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up PDF file {file_path}: {e}")
            
    except Exception as e:
        job_results[job_id] = {
            "status": "failed", 
            "reason": str(e),
            "created_at": time.time()
        }
        logger.error(f"Error in job {job_id}: {e}")

def update_job_progress(job_id: str, progress: int):
    """Update job progress"""
    if job_id in job_results:
        job_results[job_id]["progress"] = min(progress, 95)  # Cap at 95% until complete

@app.post("/audio_from_book")
def generate_audio_async(book_name: str, voice: str = "male"):
    """Start audio generation process asynchronously with improved validation"""
    try:
        # Clean up expired jobs first
        cleanup_expired_jobs()
        
        converter = PDFToMP3Converter()
        if voice not in converter.voices:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid voice. Available voices: {list(converter.voices.keys())}"
            )
        
        job_id = str(uuid4())
        job_results[job_id] = {
            "status": "queued", 
            "chunks_dir": None,
            "book_name": book_name,
            "voice": voice,
            "message": "Job queued for processing...",
            "progress": 0,
            "created_at": time.time()
        }

        thread = threading.Thread(
            target=process_audio_job,
            args=(job_id, book_name, voice),
            daemon=True
        )
        thread.start()

        logger.info(f"Started job {job_id} for book: {book_name}")
        return {
            "message": "Audio generation started", 
            "job_id": job_id,
            "status_check_url": f"/audio_status/{job_id}",
            "estimated_wait": "This may take 5-15 minutes depending on book size"
        }
        
    except Exception as e:
        logger.error(f"Error starting audio generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
def list_jobs():
    """List all jobs for debugging"""
    cleanup_expired_jobs()  # Clean up first
    return {
        "jobs": {
            job_id: {
                "status": job["status"],
                "book_name": job.get("book_name", "unknown"),
                "voice": job.get("voice", "unknown"),
                "has_chunks": job.get("chunks_dir") is not None,
                "progress": job.get("progress", 0),
                "created_at": job.get("created_at"),
                "age_hours": (time.time() - job.get("created_at", time.time())) / 3600
            }
            for job_id, job in job_results.items()
        },
        "total_jobs": len(job_results)
    }

@app.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel/remove a job"""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    cleanup_job_files(job_id)
    return {"message": f"Job {job_id} cancelled/removed"}

@app.get("/health")
def health_check():
    """Enhanced health check endpoint"""
    cleanup_expired_jobs()  # Clean up during health check
    
    return {
        "status": "healthy",
        "active_jobs": len([j for j in job_results.values() 
                           if j["status"] in ["queued", "downloading", "processing", "converting"]]),
        "completed_jobs": len([j for j in job_results.values() if j["status"] == "completed"]),
        "failed_jobs": len([j for j in job_results.values() if j["status"] == "failed"]),
        "total_jobs": len(job_results),
        "server_uptime": "N/A",  # Could add actual uptime tracking
        "memory_usage": "N/A"    # Could add memory monitoring
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
