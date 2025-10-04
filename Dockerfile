# Use slim Python base
FROM python:3.11-slim

# Install system deps (Chrome + fonts + curl + unzip + wget)
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    python3-pip \
    python3-dev \
    build-essential \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome (stable)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver (match Chrome version)
RUN CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //g' | cut -d '.' -f 1) \
    && LATEST_DRIVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://chromedriver.storage.googleapis.com/${LATEST_DRIVER}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin \
    && rm chromedriver_linux64.zip

# Set display for headless Chrome
ENV DISPLAY=:99

# Create app dir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Back4App uses PORT env var
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
