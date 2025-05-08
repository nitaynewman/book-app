import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "pdf")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def setup_driver():
    options = Options()
    options.add_argument("--headless=new")  # Headless mode for Chrome 135+
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

    # Point directly to chromedriver installed via Dockerfile
    service = Service("/usr/local/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)


def wait_for_file(download_dir, timeout=30):
    seconds = 0
    while seconds < timeout:
        files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
        if files:
            print(f"Found {files[0]} in the download directory. {download_dir}")
            return os.path.join(download_dir, files[0])
        time.sleep(1)
        seconds += 1
    print(f"No PDF file found after {timeout} seconds.")
    return None


def download_book(book_name: str):
    print("Driver fetch")
    driver = setup_driver()
    print("Driver started")

    file_path = None

    try:
        print("Navigating to login...")
        driver.get("https://fliphtml5.com/login.php")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "loginEmail")))
        driver.find_element(By.ID, "loginEmail").send_keys("nitaynewman@gmail.com")
        driver.find_element(By.ID, "loginPassword").send_keys("YX.qTJBf!T6QWJ7")
        time.sleep(2)
        driver.find_element(By.XPATH, '//*[@id="loginButton"]').click()
        print("Logged in")
        time.sleep(5)

        search_url = f"https://fliphtml5.com/exploring/?q={book_name}"
        print(f"Navigating to: {search_url}")
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "i.icon-download-btn"))
        )
        print("Found download buttons")

        download_buttons = driver.find_elements(By.CSS_SELECTOR, "i.icon-download-btn")
        if not download_buttons:
            print("No download buttons found")
            return None

        print("Clicking download button")
        download_buttons[0].click()

        print("Waiting for popup download link...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div/div[3]/div[1]/div[2]/a'))
        ).click()

        print("Download triggered")

    except Exception as e:
        print(f"Error during download: {e}")

    finally:
        file_path = wait_for_file(DOWNLOAD_DIR)
        driver.quit()
        print("Driver closed")

    if file_path:
        print(f"Downloaded file: {file_path}")
    else:
        print("Download failed or file not found.")

    return file_path