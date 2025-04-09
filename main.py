from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import os

app = FastAPI()

def download_selenium():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Optional: use CHROME_BIN env variable if needed
    chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")

    driver = webdriver.Chrome(
        service=Service(os.getenv("CHROME_DRIVER", "/usr/local/bin/chromedriver")),
        options=chrome_options
    )

    driver.get('https://google.com')
    title = driver.title
    language = driver.find_element(By.XPATH, "//div[@id='SIvCob']").text
    driver.quit()
    return {'page title': title, 'language': language}

@app.get('/')
def home():
    return download_selenium()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
