# ARKHE OS Build System — Ferris-Compiler v157.0
# Cross-compilation para todas as arquiteturas alienígenas

BINARY_NAME=arkhe-os
PACKAGE=arkhe
VERSION=v∞.Ω.∇+++.157.0

# Arquiteturas suportadas pelo Go
PLATFORMS=darwin/amd64 darwin/arm64 linux/amd64 linux/arm64 linux/riscv64 windows/amd64 freebsd/amd64 openbsd/amd64

.PHONY: all build test clean cross-compile install

all: test build

build:
	go build -ldflags="-s -w -X main.Version=$(VERSION)" -o bin/$(BINARY_NAME) .

test:
	go test -v ./...

clean:
	rm -rf bin/
	go clean

# Compilação cruzada para todas as plataformas
cross-compile:
	@mkdir -p bin
	@for platform in $(PLATFORMS); do \
		GOOS=$${platform%/*} GOARCH=$${platform#*/} go build -ldflags="-s -w" -o bin/$(BINARY_NAME)-$${platform%/*}-$${platform#*/} . ; \
		echo "✅ Built for $${platform}"; \
	done

# Targets específicos para missões interestelares
mars:
	GOOS=linux GOARCH=riscv64 go build -ldflags="-s -w" -o bin/$(BINARY_NAME)-mars-riscv64 .

europa:
	GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o bin/$(BINARY_NAME)-europa-arm64 .

install:
	go install ./...

# Verificação de segurança de memória
vet:
	go vet ./...

# Formatação idiomática Go
fmt:
	go fmt ./...
