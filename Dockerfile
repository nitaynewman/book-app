# Use the official Python image as base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Copy application files
COPY . .

# Expose the FastAPI port
EXPOSE 8080

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
