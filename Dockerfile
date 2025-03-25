ARG PORT=8080
FROM python:3.9-slim

# Install dependencies for headless chrome (including chromium)
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv

# Ensure the virtual environment is used
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies in the virtual environment
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE $PORT

# Start the FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
