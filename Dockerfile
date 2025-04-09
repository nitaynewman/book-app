FROM python:3.8-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y wget unzip gnupg ca-certificates

# Install ChromeDriver (v122 to match Chrome v122)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/122.0.6261.112/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip


# Install Google Chrome (specific version)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable=122.0.6261.112-1 \
    && apt-mark hold google-chrome-stable


RUN pip install --no-cache-dir -r requirements.txt

ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
