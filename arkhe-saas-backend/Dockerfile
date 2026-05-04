FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY arkhe-saas-backend/pyproject.toml arkhe-saas-backend/schemas.py arkhe-saas-backend/models.py arkhe-saas-backend/main.py ./
COPY arkhe-saas-backend/routers ./routers
COPY arkhe-saas-backend/services ./services
COPY consensus_engine.py ./

RUN uv pip install --system fastapi uvicorn pydantic numpy

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
