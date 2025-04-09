from selenium import webdriver
from fastapi import FastAPI
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

app = FastAPI()

def download_selenium():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Create WebDriver using WebDriverManager and options
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.get('https://google.com')
    title = driver.title
    try:
        language = driver.find_element(By.XPATH, "//div[@id='SIvCob']").text
    except:
        language = "Not found"
    driver.quit()
    return {'page_title': title, 'language': language}


@app.get('/')
def home():
    return download_selenium()
