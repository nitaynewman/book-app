# Use Selenium image with Chrome + Chromedriver preinstalled
FROM selenium/standalone-chrome:131.0

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PORT=443

# Install Python + pip
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies globally (ignore PEP 668 restriction)
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy project code
COPY . .

# Expose port
EXPOSE $PORT

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
