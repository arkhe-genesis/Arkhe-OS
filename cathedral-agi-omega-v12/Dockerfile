FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir web3 numpy

COPY . /app

CMD ["python", "node_entrypoint.py"]
