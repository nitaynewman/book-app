FROM python:3.8-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y wget unzip gnupg ca-certificates

# Install ChromeDriver (v114)
RUN wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/135.0.0.0/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Install Chrome (v114)
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

RUN pip install --no-cache-dir -r requirements.txt

ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
