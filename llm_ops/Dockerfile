FROM ubuntu:22.04

# Instalar dependências
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clonar llama.cpp e compilar o llama-server
RUN git clone https://github.com/ggerganov/llama.cpp.git .
RUN cmake -B build && cmake --build build --config Release -j$(nproc)

# Expor a porta 8080 do servidor
EXPOSE 8080

# Comando para iniciar o servidor, mapeando o modelo
# Espera-se que o modelo esteja mapeado em /models/arkhe-os.gguf
CMD ["/app/build/bin/llama-server", "-m", "/models/arkhe-os.gguf", "-c", "2048", "-t", "4", "--host", "0.0.0.0", "--port", "8080"]
