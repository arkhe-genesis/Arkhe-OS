# deploy/docker/Dockerfile
# Multi-stage build for ARKHE.D

# Stage 1: Builder
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git gcc musl-dev

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w" \
    -o /arkhe \
    ./cmd/arkhe

# Stage 2: Minimal runtime
FROM alpine:3.19

LABEL org.opencontainers.image.title="ARKHE.D — Unity & Steam Parser"
LABEL org.opencontainers.image.description="Parser for game development artifacts with coherence analysis"
LABEL org.opencontainers.image.version="1.0.0"

# Install CA certificates for HTTPS
RUN apk add --no-cache ca-certificates

# Copy binary from builder
COPY --from=builder /arkhe /usr/local/bin/arkhe

# Create non-root user
RUN addgroup -S arkhe && adduser -S arkhe -G arkhe
USER arkhe

# Working directory for mounted volumes
WORKDIR /workspace

# Default command
ENTRYPOINT ["/usr/local/bin/arkhe"]
CMD ["game", "--help"]
