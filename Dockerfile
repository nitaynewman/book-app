FROM python:3.8-slim
# work dir
WORKDIR /app
# copy local files in to the container
COPY . /app
# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# install chrome driver
RUN apt-get update && apt-get install -y  wget unzip \
    && wget -q -o /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/2.44/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /user/local/bin/ \
    && rm /tmp/chromedriver.zip

# install chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# set enviroment variable to disable sandboxing in chrome
ENV CHROME_BIN=/user/bin/google-chrome
ENV CHROME_DRIVER=/user/local/bin/chromedriver

# Start the FastAPI app
CMD uvicorn main:app --host 0.0.0.0 --port 8080
