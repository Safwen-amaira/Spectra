FROM python:3.11-slim

# Install system dependencies for OpenCV and X11 (for pyautogui)
# Note: Debian Trixie uses different package names
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx-mesa0 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Run the application
CMD ["python", "-m", "src.main"]

