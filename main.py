from selenium import webdriver
from fastapi import FastAPI
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import uvicorn

app = FastAPI()

def download_selenium():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)
    driver.get('https://google.com')
    title = driver.title
    language = driver.find_element(By.XPATH, "//div[@id='SIvCob']").text
    data = {'page title': title, 'language': language}
    return data


@app.get('/')
def home():
    return download_selenium()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)