FROM python:3.11-slim
WORKDIR /app
RUN pip install redis requests
COPY collectors/geo_collector.py .
CMD ["python", "geo_collector.py"]
