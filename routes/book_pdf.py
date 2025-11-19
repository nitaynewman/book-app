import os
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Router setup
router = APIRouter(
    prefix='/book_pdf',
    tags=['book_pdf']
)

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "pdf")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Request model
class BookRequest(BaseModel):
    book_name: str


def setup_driver():
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222")

    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "plugins.always_open_pdf_externally": True,
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)

    # Try multiple approaches to locate ChromeDriver
    try:
        # Method 1: Use webdriver-manager (recommended)
        service = Service(ChromeDriverManager().install())
        print(f"Using ChromeDriver from webdriver-manager")
    except Exception as e:
        print(f"webdriver-manager failed: {e}")
        try:
            # Method 2: Check if chromedriver is in /usr/local/bin
            if os.path.exists("/usr/local/bin/chromedriver"):
                service = Service("/usr/local/bin/chromedriver")
                print("Using ChromeDriver from /usr/local/bin/chromedriver")
            # Method 3: Check if chromedriver is in /usr/bin
            elif os.path.exists("/usr/bin/chromedriver"):
                service = Service("/usr/bin/chromedriver")
                print("Using ChromeDriver from /usr/bin/chromedriver")
            # Method 4: Let Selenium find it automatically
            else:
                service = Service()
                print("Using default ChromeDriver location")
        except Exception as e2:
            print(f"All ChromeDriver location methods failed: {e2}")
            raise

    return webdriver.Chrome(service=service, options=options)


def wait_for_file(download_dir, timeout=60):
    """Wait for PDF file to appear, checking for both complete and in-progress downloads"""
    seconds = 0
    print(f"Waiting for file in directory: {download_dir}")
    
    while seconds < timeout:
        try:
            all_files = os.listdir(download_dir)
            print(f"Files in directory at {seconds}s: {all_files}")
            
            # Check for completed PDF files
            pdf_files = [f for f in all_files if f.endswith(".pdf")]
            if pdf_files:
                file_path = os.path.join(download_dir, pdf_files[0])
                # Verify file is not empty and is accessible
                if os.path.getsize(file_path) > 0:
                    print(f"Found complete PDF: {pdf_files[0]} ({os.path.getsize(file_path)} bytes)")
                    return file_path
                else:
                    print(f"PDF file {pdf_files[0]} is still being written...")
            
            # Check for in-progress downloads (.crdownload for Chrome)
            temp_files = [f for f in all_files if f.endswith('.crdownload') or f.endswith('.tmp')]
            if temp_files:
                print(f"Download in progress: {temp_files}")
            
        except Exception as e:
            print(f"Error checking directory: {e}")
        
        time.sleep(1)
        seconds += 1
    
    print(f"No PDF file found after {timeout} seconds.")
    print(f"Final directory contents: {os.listdir(download_dir)}")
    return None


def download_book(book_name: str):
    """
    Download a book PDF by name.
    
    Args:
        book_name: Name of the book to search and download
        
    Returns:
        str: Path to the downloaded PDF file, or None if download failed
    """
    print(f"\n{'='*60}")
    print(f"Starting download for: {book_name}")
    print(f"Download directory: {DOWNLOAD_DIR}")
    print(f"{'='*60}\n")
    
    # Clear old files from download directory
    try:
        for file in os.listdir(DOWNLOAD_DIR):
            if file.endswith('.pdf'):
                old_file = os.path.join(DOWNLOAD_DIR, file)
                os.remove(old_file)
                print(f"Removed old file: {file}")
    except Exception as e:
        print(f"Error cleaning directory: {e}")
    
    print("Initializing Chrome driver...")
    driver = setup_driver()
    print("Driver started successfully")

    file_path = None

    try:
        print("\n[Step 1] Navigating to login page...")
        driver.get("https://fliphtml5.com/login.php")

        print("[Step 2] Waiting for login form...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "login-email")))
        
        print("[Step 3] Entering credentials...")
        driver.find_element(By.NAME, "login-email").send_keys("nitaynewman@gmail.com")
        driver.find_element(By.NAME, "login-password").send_keys("YX.qTJBf!T6QWJ7")
        time.sleep(3)
        
        print("[Step 4] Clicking login button...")
        driver.find_element(By.XPATH, '/html/body/div[1]/div/main/div[3]/div/div[6]/div[2]').click()
        print("Login clicked, waiting for page load...")
        time.sleep(5)

        search_url = f"https://fliphtml5.com/exploring/?q={book_name}"
        print(f"\n[Step 5] Navigating to search: {search_url}")
        driver.get(search_url)

        print("[Step 6] Waiting for download buttons...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "i.icon-download-btn"))
        )
        
        download_buttons = driver.find_elements(By.CSS_SELECTOR, "i.icon-download-btn")
        print(f"[Step 7] Found {len(download_buttons)} download button(s)")
        
        if not download_buttons:
            print("ERROR: No download buttons found")
            return None

        print("[Step 8] Clicking first download button...")
        download_buttons[0].click()
        time.sleep(3)

        print("[Step 9] Waiting for popup download link...")
        download_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div/div[3]/div[1]/div[2]/a'))
        )
        
        print("[Step 10] Clicking download link...")
        download_link.click()
        print("Download triggered successfully!")
        
        # Give extra time for download to start
        time.sleep(5)

    except Exception as e:
        print(f"\n❌ ERROR during download process: {e}")
        print(f"Current URL: {driver.current_url}")
        
        # Take screenshot for debugging
        try:
            screenshot_path = os.path.join(DOWNLOAD_DIR, "error_screenshot.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
        except:
            pass

    finally:
        print("\n[Step 11] Waiting for file to complete download...")
        file_path = wait_for_file(DOWNLOAD_DIR, timeout=60)
        
        print("[Step 12] Closing driver...")
        driver.quit()
        print("Driver closed")

    if file_path:
        print(f"\n✅ SUCCESS: Downloaded file at: {file_path}")
    else:
        print("\n❌ FAILED: Download failed or file not found.")

    return file_path


# API Routes
@router.post("/download")
async def download_book_endpoint(request: BookRequest):
    """
    Download a book PDF by name
    
    Args:
        request: BookRequest with book_name field
        
    Returns:
        FileResponse with the downloaded PDF
    """
    try:
        file_path = download_book(request.book_name)
        
        if not file_path or not os.path.exists(file_path):
            # Return status on failure
            return {
                "status": "failed",
                "error": f"Book '{request.book_name}' not found or download failed",
                "download_directory": DOWNLOAD_DIR,
                "directory_exists": os.path.exists(DOWNLOAD_DIR)
            }
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path)
        )
    
    except Exception as e:
        # Return status on exception
        return {
            "status": "error",
            "error": str(e),
            "download_directory": DOWNLOAD_DIR,
            "directory_exists": os.path.exists(DOWNLOAD_DIR)
        }


@router.get("/download/{book_name}")
async def download_book_get(book_name: str):
    """
    Download a book PDF by name (GET method)
    
    Args:
        book_name: Name of the book to download
        
    Returns:
        FileResponse with the downloaded PDF
    """
    try:
        file_path = download_book(book_name)
        
        if not file_path or not os.path.exists(file_path):
            # Return status on failure
            return {
                "status": "failed",
                "error": f"Book '{book_name}' not found or download failed",
                "download_directory": DOWNLOAD_DIR,
                "directory_exists": os.path.exists(DOWNLOAD_DIR)
            }
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=os.path.basename(file_path)
        )
    
    except Exception as e:
        # Return status on exception
        return {
            "status": "error",
            "error": str(e),
            "download_directory": DOWNLOAD_DIR,
            "directory_exists": os.path.exists(DOWNLOAD_DIR)
        }