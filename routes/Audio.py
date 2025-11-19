from fastapi import APIRouter
from functions.pdf2mp3 import PDFToMP3Converter
from fastapi.responses import FileResponse
import os
import re
import sys

# Import download_book function from book_pdf
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from routes.book_pdf import download_book

router = APIRouter(
    prefix='/audio',
    tags=['audio']
)

@router.get('/mp3_download')
async def download_audio(book_name: str, voice: str = 'male'):
    """
    Download a book PDF and convert it to MP3 audiobook.
    
    Args:
        book_name: Name of the book to download and convert
        voice: Voice type for audio generation (default: 'male')
        
    Returns:
        FileResponse with the generated MP3 file or error status
    """
    print(f'\n{"="*60}')
    print(f'Starting MP3 conversion for: {book_name}')
    print(f'Voice selected: {voice}')
    print(f'{"="*60}\n')
    
    # Step 1: Download the book PDF
    print("[MP3 Step 1] Downloading PDF...")
    pdf_path = download_book(book_name)
    
    if not pdf_path or not os.path.exists(pdf_path):
        return {
            "status": "failed",
            "error": f"Failed to download PDF for book: {book_name}",
            "step": "pdf_download"
        }
    
    print(f"[MP3 Step 2] PDF downloaded successfully: {pdf_path}")
    
    # Step 2: Convert PDF to MP3
    try:
        safe_name = re.sub(r'\W+', '_', book_name)
        converter = PDFToMP3Converter()
        
        mp3_filename = os.path.join(converter.output_dir, f"{safe_name}.mp3")
        
        print(f"[MP3 Step 3] Converting PDF to MP3 with {voice} voice...")
        
        # Use async conversion for ALL voices (including male)
        await converter.convert_with_voice(pdf_path, voice)
        
        print(f"[MP3 Step 4] Checking if MP3 file was created...")
        
        if os.path.exists(mp3_filename):
            print(f"\n✅ SUCCESS: MP3 file created at: {mp3_filename}")
            return FileResponse(
                mp3_filename, 
                media_type="audio/mpeg", 
                filename=f"{book_name}.mp3"
            )
        else:
            return {
                "status": "failed",
                "error": "MP3 file was not generated",
                "step": "mp3_conversion",
                "expected_path": mp3_filename
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "step": "mp3_conversion"
        }