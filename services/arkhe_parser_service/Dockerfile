# Estágio 1: compilação de tree‑sitter + ANTLR (se necessário)
FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc libtree-sitter-dev antlr4
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Estágio 2: runtime mínimo
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "arkhe_parser_service:app", "--host", "0.0.0.0", "--port", "8080"]