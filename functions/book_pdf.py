import os
import requests
import re
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.pdfdrive.com"

def get_driver():
    """ Configures and returns a Selenium WebDriver instance """
    chromedriver_autoinstaller.install()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Necessary for Render.com
    options.add_argument("--disable-dev-shm-usage")  # Prevent resource issues
    options.add_argument("--disable-gpu")

    return webdriver.Chrome(service=Service(), options=options)

def download_book(book_name: str):
    """ Searches for a book and downloads it if available """
    url = get_book_url_page(book_name)
    if not url:
        print("No book URL found")
        return None

    print("Looking for download button...")
    driver = get_driver()

    try:
        driver.get(url)

        # First attempt: Find the usual download button
        try:
            download_button = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/div/a'))
            )
            download_url = download_button.get_attribute("href")

        except:
            print("Download button not found, checking for alternative PDF link...")

            # Second attempt: Find a direct web-viewer PDF link
            alternative_link = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="alternatives"]/div[1]/a'))
            )
            download_url = alternative_link.get_attribute("href")

            # Extract actual PDF URL if necessary
            if not download_url.endswith(".pdf"):
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

        # Try to find a direct PDF link in the HTML response
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
    
    driver = get_driver()

    try:
        driver.get(url)

        # Wait for the list to be available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "ul"))
        )

        # Get all <li> elements inside <ul>
        book_items = driver.find_elements(By.CSS_SELECTOR, "ul li")
        
        for book in book_items:
            try:
                title_element = book.find_element(By.CSS_SELECTOR, "h2")
                book_title = title_element.text.strip()
                
                if book_name.lower() in book_title.lower():
                    link_element = book.find_element(By.CSS_SELECTOR, "a")
                    book_url = link_element.get_attribute("href")
                    if book_url:
                        new_url = re.sub(r'-e(\d+\.html)$', r'-d\1', book_url)
                        print("Book URL page found:", new_url)
                        return new_url
            except Exception:
                continue  # Skip elements that don't match the pattern

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

    safe_name = re.sub(r'\W+', '_', book_name)  # Replace non-word characters with "_"
    file_path = os.path.join("pdf", f"{safe_name}.pdf")

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            error_message = f'Failed to download book. Please check this URL: {url}'
            print(error_message)
            return error_message

        # Save the file
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading book: {e}")
        return None
