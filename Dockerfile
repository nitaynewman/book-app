# Set default port
ARG PORT=8080

# Use a valid Cypress image
FROM cypress/included:12.17.1

# Install required dependencies
RUN apt-get update && apt-get install -y python3-pip

# Set up Python environment
COPY requirements.txt .
ENV PATH /home/root/.local/bin:${PATH}
RUN pip install -r requirements.txt

# Copy the project files
COPY . .

# Expose the port
EXPOSE $PORT

# Start the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
