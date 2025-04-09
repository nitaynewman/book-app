from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import re
import time
import requests

router = APIRouter(prefix="/books", tags=["books"])
BASE_URL = "https://www.pdfdrive.com"

PDF_FOLDER = "pdf"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

@router.get("/download_book/{book_name}")
def download_book_by_name(book_name: str):
    file_path = download_book(book_name)
    if file_path and os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=f"{book_name}.pdf")
    return JSONResponse(content={"error": "File not found"}, status_code=404)

@router.get("/book_title_pdf/{book_name}")
def book_title_pdf(book_name: str):
    safe_name = re.sub(r"\W+", "_", book_name)
    file_path = os.path.join(PDF_FOLDER, f"{safe_name}.pdf")
    if os.path.exists(file_path):
        return {"file_path": file_path}
    return JSONResponse(content={"error": "File not found"}, status_code=404)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

def get_book_url_page(book_name):
    url = f"{BASE_URL}/search?q={book_name.replace(' ', '+')}"
    print("Searching URL:", url)

    driver = setup_driver()
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.ai-search")))

        results = driver.find_elements(By.CSS_SELECTOR, "a.ai-search")
        print(f"Found {len(results)} result(s)")

        for link in results:
            title_element = link.find_element(By.CSS_SELECTOR, "h2")
            title = title_element.text.strip()
            print("Found title:", title)

            if book_name.lower() in title.lower():
                book_url = link.get_attribute("href")
                print("Book URL:", book_url)
                return book_url
    except Exception as e:
        print("Error fetching book URL:", e)
    finally:
        driver.quit()

    return None

def extract_pdf_link(book_page_url):
    print("Opening book page:", book_page_url)
    driver = setup_driver()

    try:
        driver.get(book_page_url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "download-button-link")))

        btn = driver.find_element(By.ID, "download-button-link")
        intermediate_url = btn.get_attribute("href")

        driver.get(intermediate_url)

        final_link = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.btn-user"))
        )
        pdf_url = final_link.get_attribute("href")
        print("Final PDF link:", pdf_url)

        if pdf_url.endswith(".pdf"):
            return pdf_url
    except Exception as e:
        print("Could not extract PDF URL:", e)
    finally:
        driver.quit()

    return None

def download_request(url, book_name):
    print("Downloading from:", url)
    os.makedirs(PDF_FOLDER, exist_ok=True)

    safe_name = re.sub(r"\W+", "_", book_name)
    file_path = os.path.join(PDF_FOLDER, f"{safe_name}.pdf")

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            print("Failed to download, status:", response.status_code)
            return None

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Download completed:", file_path)
        return file_path
    except Exception as e:
        print("Download error:", e)
        return None

def download_book(book_name: str):
    book_url = get_book_url_page(book_name)
    if not book_url:
        print("Book URL not found")
        return None

    pdf_link = extract_pdf_link(book_url)
    if not pdf_link:
        print("PDF link not found")
        return None

    return download_request(pdf_link, book_name)
