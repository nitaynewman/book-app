import os
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from helper.authentication import APIKeyChecker
from functions.book_pdf import download_book

router = APIRouter(
    prefix='/book_pdf',
    tags=['book_pdf']
)

# API key checker for book download operations
book_auth = APIKeyChecker("book")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "pdf")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class BookRequest(BaseModel):
    book_name: str

@router.get("/download/{book_name}")
async def download_book_get(
    book_name: str,
    api_key: str = Depends(book_auth)
):
    """Download a book PDF by name (GET method)"""
    try:
        print(f"Starting download for: {book_name}")
        file_path = download_book(book_name)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Book '{book_name}' not found or download failed"
            )
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path),
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.basename(file_path)}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in download endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading book: {str(e)}"
        )

@router.post("/download")
async def download_book_endpoint(
    request: BookRequest,
    api_key: str = Depends(book_auth)
):
    """Download a book PDF by name (POST method)"""
    try:
        print(f"Starting download for: {request.book_name}")
        file_path = download_book(request.book_name)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Book '{request.book_name}' not found or download failed"
            )
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path),
            headers={
                "Content-Disposition": f'attachment; filename="{os.path.basename(file_path)}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in download endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading book: {str(e)}"
        )