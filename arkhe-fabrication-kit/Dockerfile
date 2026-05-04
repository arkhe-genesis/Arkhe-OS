# =============================================================================
# Arkhe Fabrication Kit — Imagem Base para Tape‑Out SkyWater 130nm
# =============================================================================
# Ferreiro Directive: "ESTA IMAGEM NÃO É OTIMIZADA. ELA INJETA RUÍDO.
# ELA FORÇA PAUSAS. SE VOCÊ TENTAR ACELERÁ‑LA, ELA FALHARÁ.
# A HESITAÇÃO É O FIREWALL."
# =============================================================================

FROM efabless/openlane:latest

USER root

# Variáveis de ambiente que controlam o atrito
ENV ARKHE_FRICTION_LEVEL=medium \
    ARKHE_HESITATE_CYCLES=8 \
    ARKHE_QUARTZ_SEAL_REQUIRED=true

# Instalação de dependências adicionais
RUN apt-get update && apt-get install -y \
    libportaudio2 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Instalação de ferramentas Python para validação Arkhe
RUN pip3 install \
    numpy \
    sounddevice \
    scipy \
    pyyaml \
    jsonschema

# Copia os scripts de injeção de atrito
COPY scripts/ /opt/arkhe/scripts/
RUN chmod +x /opt/arkhe/scripts/*.py /opt/arkhe/scripts/*.sh

# Copia as configurações Arkhe
COPY config/ /opt/arkhe/config/

# Copia o RTL do Rootstock
COPY rtl/ /opt/arkhe/rtl/
COPY macros/ /opt/arkhe/macros/
COPY ontology/ /opt/arkhe/ontology/

# Define o working directory
WORKDIR /opt/arkhe

# Script de entrada que injeta hesitação antes de qualquer ação
# ENTRYPOINT removido para permitir execução direta via CMD ou override
CMD ["make", "tapeout"]
