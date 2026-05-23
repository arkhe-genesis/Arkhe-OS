# syntax=docker/dockerfile:1
# Optimized Dockerfile for MegaKernel

# Stage 1: Build environment
FROM ubuntu:24.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    make \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

# Compile MegaKernel
RUN make TARGET=megakernel

# Stage 2: Minimal runtime environment
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/megakernel

# Copy binary from builder
COPY --from=builder /build/megakernel /opt/megakernel/megakernel

# Optional: Add any necessary config files if they exist
# COPY --from=builder /build/*.conf /opt/megakernel/

# Configure entrypoint
ENTRYPOINT ["/opt/megakernel/megakernel"]
