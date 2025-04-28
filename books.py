from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
import os
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

BASE_URL = "https://www.pdfdrive.com"
PDF_FOLDER = "pdf"
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")
CHROME_DRIVER = os.getenv("CHROME_DRIVER", "/usr/local/bin/chromedriver")

# Ensure PDF folder exists
os.makedirs(PDF_FOLDER, exist_ok=True)

router = APIRouter(prefix="/books", tags=["books"])

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # NEW headless mode required for Chrome 109+
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # No need to set binary_location unless you install Chrome in a weird place

    service = Service(CHROME_DRIVER)
    return webdriver.Chrome(service=service, options=options)

def get_book_url_page(book_name):
    search_url = f"{BASE_URL}/search?q={book_name}"
    print(f"Searching URL: {search_url}")

    driver = create_driver()
    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "ul")))

        # Debug: print the first few book titles in the search results
        book_items = driver.find_elements(By.CSS_SELECTOR, "ul li")
        print(f"Found {len(book_items)} book items.")
        
        for book in book_items:
            try:
                title_element = book.find_element(By.CSS_SELECTOR, "h2")
                book_title = title_element.text.strip()
                print(f"Found book: {book_title}")

                if book_name.lower() in book_title.lower():
                    link_element = book.find_element(By.CSS_SELECTOR, "a")
                    book_url = link_element.get_attribute("href")
                    if book_url:
                        new_url = re.sub(r'-e(\d+\.html)$', r'-d\1', book_url)
                        print(f"Book URL page found: {new_url}")
                        return new_url
            except Exception as e:
                print(f"Error processing book item: {e}")
                continue
    except Exception as e:
        print(f"Error fetching book URL: {e}")
    finally:
        driver.quit()

    return None

def extract_pdf_from_viewer(viewer_url):
    try:
        response = requests.get(viewer_url)
        if response.status_code != 200:
            print("Failed to access the PDF viewer page.")
            return None

        match = re.search(r'href="(https?://[^"]+\.pdf)"', response.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error extracting PDF link: {e}")
    return None

def download_request(url, book_name="book"):
    print("Downloading from:", url)
    safe_name = re.sub(r'\W+', '_', book_name)
    file_path = os.path.join(PDF_FOLDER, f"{safe_name}.pdf")

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            print(f"Failed to download book. Check URL: {url}")
            return None

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading book: {e}")
        return None

def download_book(book_name: str):
    url = get_book_url_page(book_name)
    if not url:
        print("No book URL found")
        return None

    driver = create_driver()
    try:
        driver.get(url)
        try:
            download_button = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/div/a'))
            )
            download_url = download_button.get_attribute("href")
        except:
            print("Primary download button not found. Checking alternatives...")
            alternative_link = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/a'))
            )
            download_url = alternative_link.get_attribute("href")
            if not download_url.endswith(".pdf"):
                download_url = extract_pdf_from_viewer(download_url)
                if not download_url:
                    return None

        if not download_url:
            return None

        return download_request(download_url, book_name)
    except Exception as e:
        print(f"Error during download process: {e}")
        return None
    finally:
        driver.quit()

def book_title_pdf(book_name):
    safe_name = re.sub(r'\W+', '_', book_name)
    file_path = os.path.join(PDF_FOLDER, f"{safe_name}.pdf")
    return file_path if os.path.exists(file_path) else None

@router.get("/get_book_url")
def get_book_url(book_name: str):
    return get_book_url_page(book_name)

@router.get("/book_title_pdf")
def get_pdf_path(book_name: str):
    path = book_title_pdf(book_name)
    return path if path else {"error": "File not found"}

@router.get("/download_book")
def download_book_by_name(book_name: str = Query(..., description="Name of the book to download")):
    file_path = book_title_pdf(book_name)
    if not file_path:
        file_path = download_book(book_name)

    if file_path and os.path.exists(file_path):
        return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type="application/pdf")
    return {"error": "Book could not be downloaded."}

