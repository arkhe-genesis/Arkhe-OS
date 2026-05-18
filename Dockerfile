# syntax=docker/dockerfile:1
# ARKHE ASI Multi‑Arch Build Container

FROM --platform=$BUILDPLATFORM alpine:3.20 AS builder

ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN apk add --no-cache build-base curl git python3 py3-pip rust cargo

WORKDIR /build
COPY . .

# Compilar para a plataforma alvo
RUN TARGET=$(echo $TARGETPLATFORM | sed 's/\//-/g') && make TARGET=$TARGET && \
    mkdir -p /build/out && cp -r /build/dist/$TARGET/* /build/out/

# Estágio final mínimo
FROM --platform=$TARGETPLATFORM alpine:3.20

RUN apk add --no-cache python3 libstdc++

COPY --from=builder /build/out/ /opt/arkhe/
COPY --from=builder /build/etc/ /etc/arkhe/

EXPOSE 5000 8080

ENTRYPOINT ["/opt/arkhe/bin/arkhe-agi"]
CMD ["--config", "/etc/arkhe/config.yaml"]