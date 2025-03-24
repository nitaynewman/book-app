# Set default port
ARG PORT=8080

# Start with a Python image (which has apt-get)
FROM python:3.9

# Install Cypress manually (since it's not a default Python package)
RUN apt-get update && apt-get install -y wget curl \
    && curl -o /tmp/cypress.zip -L https://download.cypress.io/desktop/12.17.1 \
    && apt-get install -y unzip \
    && unzip /tmp/cypress.zip -d /usr/local/lib \
    && rm -rf /tmp/cypress.zip

# Install required Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the project files
COPY . .

# Expose the port
EXPOSE $PORT

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
