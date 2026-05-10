.PHONY: all build test lint fmt docker clean deploy-tee

# Variables
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "v0.0.1")
BUILD_TIME ?= $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
GIT_COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
LDFLAGS := -X main.version=$(VERSION) \
           -X main.buildTime=$(BUILD_TIME) \
           -X main.gitCommit=$(GIT_COMMIT)

# Targets
all: build test fmt

build:
	@echo "Building ARKHE Node v$(VERSION)..."
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags "$(LDFLAGS)" -o bin/arkhe-node ./cmd/arkhe-node
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -ldflags "$(LDFLAGS)" -o bin/arkhe-node-arm64 ./cmd/arkhe-node

test:
	@echo "Running tests..."
	go test -race -coverprofile=coverage.out -covermode=atomic ./...
	go tool cover -func=coverage.out | grep total

lint:
	@echo "Running linters..."
	golangci-lint run ./...

fmt:
	@echo "Formatting code..."
	go fmt ./...


docker:
	@echo "Building Docker image..."
	docker build -t arkhe-os/node:$(VERSION) -f Dockerfile .

deploy-tee: build
	@echo "Building TEE-compatible binary (SGX/SEV)..."
	# Em produção: usar SGX SDK ou sev-tool para enclaves
	./scripts/build-tee.sh bin/arkhe-node

clean:
	@echo "Cleaning build artifacts..."
	rm -rf bin/ coverage.out dist/

# Help
help:
	@echo "ARKHE OS Go Build System"
	@echo ""
	@echo "Targets:"
	@echo "  build       - Build binaries for linux/amd64 and linux/arm64"
	@echo "  test        - Run tests with race detector and coverage"
	@echo "  lint        - Run golangci-lint"
	@echo "  fmt         - Format code with gofmt and goimports"
	@echo "  docker      - Build Docker image"
	@echo "  deploy-tee  - Build TEE-compatible binary (SGX/SEV)"
	@echo "  clean       - Remove build artifacts"
	@echo "  help        - Show this help"
