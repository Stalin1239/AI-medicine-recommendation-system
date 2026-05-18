# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Set working directory
WORKDIR /app

# Install system dependencies (needed for compiling packages like bcrypt or cffi if wheels aren't used)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Create reports and exports directories so they exist in the container
RUN mkdir -p /app/reports /app/exports

# Expose the API port
EXPOSE 8000

# Run uvicorn server on container startup
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
