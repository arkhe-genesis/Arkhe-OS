FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir Pillow opencv-python fastapi uvicorn httpx

COPY arkhe_visual/ /app/arkhe_visual/

# Mock entrypoint since we are containerizing the modules
CMD ["python", "-c", "print('Arkhe Visual modules loaded successfully.')"]
