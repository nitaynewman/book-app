FROM python:3.8-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y wget unzip gnupg ca-certificates

# Install ChromeDriver v135 from Chrome for Testing
RUN wget -q -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/135.0.7049.0/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver*


# Install Google Chrome v135
RUN wget -q -O /tmp/chrome-linux.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/135.0.7049.0/linux64/chrome-linux64.zip \
    && unzip /tmp/chrome-linux.zip -d /opt/ \
    && ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome \
    && rm /tmp/chrome-linux.zip


RUN pip install --no-cache-dir -r requirements.txt

ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
