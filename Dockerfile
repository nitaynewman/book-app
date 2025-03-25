# Set default port
ARG PORT=8080

<<<<<<< HEAD
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
=======
# Use a valid Cypress image
FROM cypress/included:12.17.1

# Set up Docker authentication
ARG DOCKER_USERNAME
ARG DOCKER_PASSWORD
RUN echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# Install required dependencies
RUN apt-get update && apt-get install -y python3-pip

# Set up Python environment
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
>>>>>>> dc2814d (changing selenium posission)
RUN pip install -r requirements.txt

# Copy the project files
COPY . .

# Expose the port
EXPOSE $PORT

# Start the FastAPI application
<<<<<<< HEAD
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
=======
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
>>>>>>> dc2814d (changing selenium posission)
