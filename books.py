from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uvicorn
import os
from selenium.webdriver.chrome.options import Options

router = APIRouter(
    prefix='/books',
    tags=['books']
)

BASE_URL = "https://www.pdfdrive.com"


@router.get("/download_book/{book_name}")
def download_book_by_name(book_name: str):
    file_path = download_book(book_name)
    
    if file_path and os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=f"{book_name}.pdf")
    
    return JSONResponse(content={"error": "File not found"}, status_code=404)

@router.get("/book_title_pdf/{book_name}")
def book_title_pdf(book_name: str):
    safe_name = re.sub(r"\W+", "_", book_name)
    file_path = f"pdf/{safe_name}.pdf"

    if os.path.exists(file_path):
        return {"file_path": file_path}
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)


def download_book(book_name: str):
    """ Searches for a book and downloads it if available """
    url = get_book_url_page(book_name)
    print('this is the url: ', url)
    if not url:
        print("No book URL found")
        return None

    print("Looking for download button...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Additional headless flag

    # Using the service for the ChromeDriver installed in Docker
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)

        try:
            download_button = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/div/a'))
            )
            download_url = download_button.get_attribute("href")
            print("download_url", download_url)
        except:
            print("Download button not found, checking for alternative PDF link...")

            alternative_link = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/a'))
            )
            download_url = alternative_link.get_attribute("href")
            print("download_url", download_url)

            if not download_url.endswith(".pdf"):
                print(f"Extracting real PDF URL from: {download_url}")
                extracted_url = extract_pdf_from_viewer(download_url)
                if extracted_url:
                    download_url = extracted_url
                else:
                    print("Failed to extract a direct PDF link.")
                    return None

        if not download_url:
            print("Download URL not found.")
            return None

        print("Download URL found:", download_url)
        return download_request(download_url, book_name)

    except Exception as e:
        print(f"Error finding download button: {e}")
        return None
    finally:
        driver.quit()


def extract_pdf_from_viewer(viewer_url):
    """ Extracts the actual PDF download link from a web-based PDF viewer """
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


def get_book_url_page(book_name):
    """ Searches for a book and returns the book page URL """
    url = f"{BASE_URL}/search?q={book_name}"
    print("Searching URL:", url)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)
    print("webdriver success:")

    try:
        driver.get(url)
        print("go to url: ", url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "ul"))
        )
        print("went to url: ")
        book_items = driver.find_elements(By.CSS_SELECTOR, "ul li")
        print("book_items: ", book_items)

        for book in book_items:
            try:
                title_element = book.find_element(By.CSS_SELECTOR, "h2")
                print("title_element: ", title_element)

                book_title = title_element.text.strip()
                print("book_title: ", book_title)

                if book_name.lower() in book_title.lower():
                    link_element = book.find_element(By.CSS_SELECTOR, "a")
                    print("link_element: ", link_element)

                    book_url = link_element.get_attribute("href")
                    print("book_url: ", book_url)

                    if book_url:
                        new_url = re.sub(r"-e(\d+\.html)$", r"-d\1", book_url)
                        print("new_url: ", new_url)
                        return new_url
            except Exception as e:
                print(f"Error processing book: {e}")
                continue  

    except Exception as e:
        print(f"Error fetching book URL: {e}")
        return None
    finally:
        driver.quit()
    
    return None


def download_request(url, book_name="book"):
    """ Downloads a book and saves it to the 'pdf' folder. """
    print("Downloading from:", url)

    os.makedirs("pdf", exist_ok=True)

    safe_name = re.sub(r"\W+", "_", book_name)
    print("safe_name:", safe_name)

    file_path = os.path.join("pdf", f"{safe_name}.pdf")
    print("file_path:", file_path)

    try:
        response = requests.get(url, stream=True)
        print("response:", response)
        if response.status_code != 200:
            error_message = f"Failed to download book. Please check this URL: {url}"
            print(error_message)
            return error_message

        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading book: {e}")
        return None


