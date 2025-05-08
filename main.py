import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
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

@app.delete("/delete_folders")
def cleanup_folders():
    folder_counter = 0
    for folder in [PDF_DIR, MP3_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Deleted folder: {folder}")
            folder_counter += 1
    if folder_counter > 0:
        return {"message": f"Deleted {folder_counter} folders"}     
    return {"message": "No folders to delete"}

@app.get("/book_pdf")
def get_book(book_name: str, background_tasks: BackgroundTasks):
    decoded_name = urllib.parse.unquote(book_name)
    file_path = download_book(decoded_name)

    if not file_path or not os.path.exists(file_path):
        return {"error": "Download failed or file not found"}

    background_tasks.add_task(cleanup_folders)
    return FileResponse(file_path, filename=os.path.basename(file_path), media_type='application/pdf')

@app.get("/audio_status/{job_id}")
def get_audio_status(job_id: str):
    job = job_results.get(job_id)
    if not job:
        return {"status": "not_found"}

    if job["status"] == "completed":
        return FileResponse(
            job["file_path"],
            media_type="audio/mpeg",
            filename=os.path.basename(job["file_path"]),
            background=BackgroundTask(cleanup_folders)
        )

    return job



@app.get("/audio_from_book")
def generate_audio_async(book_name: str, voice: str = "male"):
    job_id = str(uuid4())
    job_results[job_id] = {"status": "processing", "file_path": None}

    def process():
        try:
            decoded_name = urllib.parse.unquote(book_name)
            file_path = download_book(decoded_name)
            # file_path = 'pdf/12 Rules For Life.pdf'

            if not file_path or not os.path.exists(file_path):
                job_results[job_id] = {"status": "failed", "reason": "Download failed"}
                return

            converter = PDFToMP3Converter()
            asyncio.run(converter.convert_with_voice(file_path, voice))
            mp3_path = os.path.join(converter.output_dir, f"{book_name}.mp3")
            if not os.path.exists(mp3_path):
                job_results[job_id] = {"status": "failed", "reason": "MP3 not created"}
                return

            job_results[job_id] = {"status": "completed", "file_path": mp3_path}
        except Exception as e:
            job_results[job_id] = {"status": "failed", "reason": str(e)}

    threading.Thread(target=process).start()

    return {"message": "Processing started", "job_id": job_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
