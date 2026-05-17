FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir numpy

COPY temporal_network.py ai_router.py run.py test_quantum.py ./

EXPOSE 8000

CMD ["python3", "run.py", "--server", "--port", "8000"]
