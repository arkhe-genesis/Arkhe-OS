# Makefile for ARKHE.D (Substrate 298)

.PHONY: all build test clean install examples

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOTEST=$(GOCMD) test

# Output binary name
BINARY_NAME=arkhe

# Build targets
all: build

build:
	@echo "🎮 Building ARKHE.D..."
	$(GOBUILD) -o bin/$(BINARY_NAME) -ldflags="-s -w" ./cmd/arkhe

test:
	@echo "🧪 Running tests..."
	$(GOTEST) -v ./tests/...

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf bin/ coverage.out coverage.html
