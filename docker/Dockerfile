# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pygame and other packages
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    python3-dev \
    python3-numpy \
    python3-setuptools \
    libsdl1.2-dev \
    libsmpeg-dev \
    libsdl-image1.2-dev \
    libsdl-mixer1.2-dev \
    libsdl-ttf2.0-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for pygame
ENV SDL_VIDEODRIVER=dummy
ENV DISPLAY=:99

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (from parent directory)
COPY ../src ./src
COPY ../config ./config
COPY ../main.py .
COPY ../.env.example .

# Create a non-root user for security
RUN useradd -m -u 1000 droneuser && chown -R droneuser:droneuser /app
USER droneuser

# Expose port (not strictly necessary for this app, but good practice)
EXPOSE 8000

# Set default command
CMD ["python", "main.py"]
