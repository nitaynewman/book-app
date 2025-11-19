FROM selenium/standalone-chrome:131.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

# Install Python + pip
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies globally
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy app code
COPY . .

# Expose fixed port
EXPOSE 8080

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
