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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory job tracker
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
    folder_counter = cleanup_folders()
    if folder_counter > 0:
        return {"message": f"Cleaned {folder_counter} folders"}     
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
    """Download a specific audio chunk"""
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready. Status: {job['status']}")
    
    chunk_file = os.path.join(job["chunks_dir"], f"chunk_{chunk_index:03d}.mp3")
    if not os.path.exists(chunk_file):
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_index} not found")
    
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
            "Cache-Control": "no-cache"
        }
    )

@app.get("/audio_status/{job_id}")
async def get_audio_status(job_id: str):
    job = job_results.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        chunks_dir = job.get("chunks_dir")
        if not chunks_dir or not os.path.exists(chunks_dir):
            job_results[job_id] = {"status": "failed", "reason": "Chunks directory no longer exists"}
            raise HTTPException(status_code=404, detail="Generated chunks no longer exist")
        
        # Count available chunks
        chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".mp3")]
        chunk_files.sort()
        
        total_size = sum(os.path.getsize(os.path.join(chunks_dir, f)) for f in chunk_files)
        
        return {
            "status": "completed",
            "total_chunks": len(chunk_files),
            "chunk_urls": [f"/download_chunk/{job_id}/{i}" for i in range(len(chunk_files))],
            "total_size": total_size,
            "filename": job.get("original_filename", "audiobook.mp3")
        }

    return job

def process_audio_job(job_id: str, book_name: str, voice: str):
    """Background function to process audio conversion with chunking"""
    try:
        logger.info(f"Starting audio processing for job {job_id}")
        
        job_results[job_id]["status"] = "downloading"
        
        decoded_name = urllib.parse.unquote(book_name)
        file_path = download_book(decoded_name)

        if not file_path or not os.path.exists(file_path):
            job_results[job_id] = {"status": "failed", "reason": "Download failed or file not found"}
            logger.error(f"Download failed for job {job_id}")
            return

        job_results[job_id]["status"] = "converting"
        logger.info(f"Starting conversion for job {job_id}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            converter = PDFToMP3Converter()
            # Use the new chunked conversion method
            chunks_dir = loop.run_until_complete(
                converter.convert_with_voice_chunked(file_path, voice, job_id)
            )
            
            if not chunks_dir or not os.path.exists(chunks_dir):
                job_results[job_id] = {"status": "failed", "reason": "Chunked conversion failed"}
                logger.error(f"Chunks not created for job {job_id}")
                return

            safe_name = os.path.splitext(os.path.basename(file_path))[0]
            job_results[job_id] = {
                "status": "completed", 
                "chunks_dir": chunks_dir,
                "original_filename": f"{safe_name}.mp3"
            }
            logger.info(f"Job {job_id} completed successfully with chunks")
            
        finally:
            loop.close()
            
    except Exception as e:
        job_results[job_id] = {"status": "failed", "reason": str(e)}
        logger.error(f"Error in job {job_id}: {e}")

@app.post("/audio_from_book")
def generate_audio_async(book_name: str, voice: str = "male"):
    """Start audio generation process asynchronously"""
    try:
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
            "voice": voice
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
            "status_check_url": f"/audio_status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting audio generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
def list_jobs():
    """List all jobs for debugging"""
    return {
        "jobs": {
            job_id: {
                "status": job["status"],
                "book_name": job.get("book_name", "unknown"),
                "voice": job.get("voice", "unknown"),
                "has_chunks": job.get("chunks_dir") is not None
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
    if job["status"] == "completed" and job.get("chunks_dir") and os.path.exists(job["chunks_dir"]):
        try:
            shutil.rmtree(job["chunks_dir"])
        except Exception as e:
            logger.error(f"Error removing chunks directory {job['chunks_dir']}: {e}")
    
    return {"message": f"Job {job_id} cancelled/removed"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_jobs": len([j for j in job_results.values() if j["status"] in ["queued", "downloading", "converting"]]),
        "completed_jobs": len([j for j in job_results.values() if j["status"] == "completed"]),
        "failed_jobs": len([j for j in job_results.values() if j["status"] == "failed"])
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
