FROM ubuntu:22.04

# Evita interações durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências e o FreeCAD
RUN apt-get update && apt-get install -y \
    software-properties-common \
    python3 \
    python3-pip \
    xvfb \
    && add-apt-repository ppa:freecad-maintainers/freecad-stable \
    && apt-get update \
    && apt-get install -y freecad \
    && rm -rf /var/lib/apt/lists/*

# Configura o ambiente Python para encontrar o FreeCAD
ENV PYTHONPATH="/usr/lib/freecad/lib:${PYTHONPATH}"

# Cria diretório de trabalho
WORKDIR /app

# Copia o script headless
COPY headless_pipeline.py /app/

# Script de entrada (usa Xvfb para simular display se necessário, 
# embora o FreeCADCmd geralmente não precise, algumas importações podem falhar sem ele)
RUN echo '#!/bin/bash\nxvfb-run -a "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "/app/headless_pipeline.py", "--help"]
