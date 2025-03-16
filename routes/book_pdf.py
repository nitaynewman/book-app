from fastapi import APIRouter
from functions.book_pdf import get_book_url_page, download_book
from fastapi.responses import FileResponse

import re
import os



router = APIRouter(
    prefix='/book_pdf',
    tags=['book_pdf']
)

@router.get('/get_book_url')
def get_book_url(book_name: str):
    return get_book_url_page(book_name)


@router.get('/download_book')
def download_book_by_name(book_name):
    download_book(book_name)
    file_path = book_title_pdf(book_name)
    print(file_path)

    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=f"{book_name}.pdf")

    return {"error": "File not found"}



@router.get('/book_title_pdf')
def book_title_pdf(book_name):
    safe_name = re.sub(r'\W+', '_', book_name) 
    file_path = os.path.join(f"{safe_name}.pdf")
    if os.path.exists(f'pdf/{file_path}'):
        return f'pdf/{file_path}'
    else:
        return None