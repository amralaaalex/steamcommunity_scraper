# Define base image as python slim-buster.
FROM python:3.10-slim-buster AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
## Start builder stage.

# This is the first stage of the build.
# It will install all requirements.
FROM base AS builder

# Install all packages for chromedriver
RUN apt-get update && \
    apt-get install -y xvfb gnupg wget curl unzip --no-install-recommends

# Download and install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm ./google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN wget -q https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/

    # Copy any python requirements file into the install directory and install all python requirements.
COPY requirements.txt /requirements.txt
RUN pip install --upgrade --no-cache-dir -r /requirements.txt
RUN rm /requirements.txt # Remove requirements file from container.

# Copy the source code into /app and move into that directory.
COPY . /app

## End builder stage.

#####

## Start base stage.

# This is the image that will be run.
FROM builder

# Set the working directory to /app
WORKDIR /app


# Define the command to run the application
CMD ["python", "dota2_selenium.py"]