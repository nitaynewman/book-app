from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote_plus
import re
import time
import os
import requests

router = APIRouter(prefix="/books", tags=["books"])

BASE_URL = "https://www.pdfdrive.com"
PDF_FOLDER = "./pdf"

# Make sure the pdf directory exists
os.makedirs(PDF_FOLDER, exist_ok=True)

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def find_book_url(driver, book_name: str) -> str:
    search_url = f"{BASE_URL}/search?q={quote_plus(book_name)}"
    driver.get(search_url)

    ul = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'files-new'))
    )

    target_title = book_name.lower().strip()
    li_elements = ul.find_elements(By.TAG_NAME, 'li')

    for li in li_elements:
        try:
            h2 = li.find_element(By.TAG_NAME, "h2")
            title = h2.text.lower().strip()
            if title == target_title:
                href = li.find_element(By.TAG_NAME, "a").get_attribute("href")
                return href
        except:
            continue

    return None

def convert_to_download_page_url(book_url):
    return re.sub(r'-e(\d+)\.html$', r'-d\1.html', book_url)

def extract_pdf_from_viewer(url):
    # This function is a placeholder if PDFDrive uses a viewer (not direct link)
    # You could potentially scrape it here
    print(f"[!] Viewer PDF extraction not implemented for: {url}")
    return None

def download_pdf(driver, book_name: str, download_page_url: str) -> str:
    driver.get(download_page_url)
    time.sleep(30)  # Wait for page to fully load

    download_url = None

    try:
        download_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/div/a'))
        )
        download_url = download_button.get_attribute("href")
    except:
        try:
            alt_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/a'))
            )
            download_url = alt_link.get_attribute("href")

            if not download_url.endswith(".pdf"):
                download_url = extract_pdf_from_viewer(download_url)
        except:
            pass

    if not download_url:
        return None

    # Download the PDF file
    filename = f"{book_name.replace(' ', '_').lower()}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)

    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return filepath
    else:
        return None

@router.get("/download")
def download_book(book: str = Query(..., description="Book title to search and download")):
    driver = create_driver()

    try:
        print(f"[1] Searching for: {book}")
        book_url = find_book_url(driver, book)
        if not book_url:
            raise HTTPException(status_code=404, detail="Book not found")

        download_page = convert_to_download_page_url(book_url)
        print(f"[2] Converted download URL: {download_page}")

        file_path = download_pdf(driver, book, download_page)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to download the book")

        print(f"[3] Successfully downloaded: {file_path}")
        return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type='application/pdf')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.quit()
