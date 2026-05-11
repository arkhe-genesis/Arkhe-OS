FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema para matplotlib/numpy/scipy
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos de lógica do agente
COPY skills.py fret_reader.py mesh_agent.py main.py ./
COPY soul.md agent.md ./

# Criar diretório de saída
RUN mkdir output

EXPOSE 8080

# Iniciar o servidor FastAPI através do script main.py
CMD ["python", "main.py", "--server"]
