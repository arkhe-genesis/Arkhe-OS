# Dockerfile — Arkhe OS API v∞.2.1
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libfftw3-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY arkhe_os/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Imagem final
FROM python:3.11-slim

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Copiar apenas o necessário do builder
COPY --from=builder /root/.local /root/.local
COPY arkhe_os/ ./arkhe_os/

EXPOSE 8000

# Health check integrado
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python3", "-m", "arkhe_os.api.main", "--host", "0.0.0.0", "--port", "8000"]
