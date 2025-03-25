ARG PORT=8080
FROM python:3.9-slim

# Install Chromium dependencies (needed for Selenium headless mode)
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install pip dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE $PORT

# Start the FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
