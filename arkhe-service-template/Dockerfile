FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import requests; requests.get('http://localhost:8080/health')"
CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8080"]
