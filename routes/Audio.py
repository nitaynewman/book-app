from fastapi import APIRouter
from functions.pdf2mp3 import PDFToMP3Converter
from fastapi.responses import FileResponse
import os
import re

router = APIRouter(
    prefix='/audio',
    tags=['audio']
)

@router.get('/mp3_download')
async def download_audio(file_name: str, voice: str = 'male'):
    print(f'file_name1: {file_name}')
    safe_name = re.sub(r'\W+', '_', file_name)
    
    pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdf"))
    pdf_path = os.path.join(pdf_dir, f"{safe_name}.pdf")

    print(f"pdf_dir2: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        return {"error": f"PDF file not found: {pdf_path}"}

    converter = PDFToMP3Converter()
    
    mp3_filename = os.path.join(converter.output_dir, f"{safe_name}.mp3")

    if voice == 'male':
        converter.convert(pdf_path)  # Synchronous
    else:
        await converter.convert_with_voice(pdf_path, voice)  # Asynchronous

    if os.path.exists(mp3_filename):
        return FileResponse(mp3_filename, media_type="audio/mpeg", filename=f"{file_name}.mp3")

    return {"error": "MP3 file was not generated"}
