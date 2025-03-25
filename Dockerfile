# Use an official Python image
FROM python:3.10

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_VERSION=134.0.6998.117

# Install dependencies and Chromium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    curl

# Install the correct ChromeDriver for Chromium 134
RUN wget -q "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" -O /chromedriver.zip && \
    unzip /chromedriver.zip -d /usr/local/bin && \
    rm /chromedriver.zip

# Verify Chromium and ChromeDriver versions
RUN chromium --version && chromedriver --version

# Set environment variables for the browser and driver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/local/bin/chromedriver

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
