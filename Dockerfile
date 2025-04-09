FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libdrm2 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libgl1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and install specific version of Google Chrome manually
RUN wget https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_122.0.6261.112-1_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_122.0.6261.112-1_amd64.deb \
    && rm google-chrome-stable_122.0.6261.112-1_amd64.deb

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app
WORKDIR /app

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
