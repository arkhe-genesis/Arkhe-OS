# 🜏 Arkhe(n) Squadron Base Image
# Optimized for High-Performance Cognitive Agents

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     git     build-essential     libssl-dev     libffi-dev     curl     ca-certificates     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY arkhe_brain/requirements.txt ./requirements-brain.txt
COPY src/arkhe_core/requirements-arkhe-core.txt ./requirements-core.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-brain.txt -r requirements-core.txt
RUN pip install --no-cache-dir fastapi uvicorn grpcio grpcio-tools structlog torch torchvision torchaudio

# Copy source code
COPY arkhe_brain/ ./arkhe_brain/
COPY src/arkhe_core/ ./arkhe_core/
COPY src/squadron/ ./squadron/

# Set environment variables
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 50052 9090

# Default command (overridden by StatefulSet)
CMD ["python", "-m", "squadron.main"]
