FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ollama firebase-admin pydantic psutil msgpack
CMD ["python", "main.py"]
