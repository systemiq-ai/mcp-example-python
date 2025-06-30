# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Define environment variable, with a default value for production
ENV ENVIRONMENT=production

# Use JSON format for CMD to prevent OS signal issues
CMD ["/bin/sh", "-c", "if [ \"$ENVIRONMENT\" = \"development\" ]; then \
      echo 'Starting in development mode with auto-reload...' && \
      uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level warning; \
    else \
      echo 'Starting in production mode...' && \
      uvicorn main:app --host 0.0.0.0 --port 8000; \
    fi"]