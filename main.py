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


@app.get("/audio_from_book")
async def generate_audio(book_name: str, background_tasks: BackgroundTasks, voice: str = "male"):
    print("[audio] Start")
    decoded_name = urllib.parse.unquote(book_name)
    print(f"[audio] Decoded name: {decoded_name}")

    file_path = download_book(decoded_name)
    print(f"[audio] Downloaded file path: {file_path}")

    if not file_path or not os.path.exists(file_path):
        print("[audio] PDF file not found.")
        return {"error": "Download failed or file not found"}

    print("[audio] Initializing converter")
    converter = PDFToMP3Converter()

    print("[audio] Starting conversion")
    await converter.convert_with_voice(file_path, voice)
    print("[audio] Conversion complete")

    mp3_path = os.path.join(converter.output_dir, f"{book_name}.mp3")
    print(f"[audio] MP3 path: {mp3_path}")

    if not os.path.exists(mp3_path):
        print("[audio] MP3 file not generated.")
        return {"error": f"MP3 file not generated at {mp3_path}"}

    print("[audio] Returning MP3 response")
    return FileResponse(
        mp3_path,
        media_type="audio/mpeg",
        filename=os.path.basename(mp3_path),
        background=BackgroundTask(cleanup_folders)
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
