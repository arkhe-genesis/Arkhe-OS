.PHONY: help build test deploy

help:
	@echo "Comandos disponíveis: build, test, deploy"

build:
	docker-compose build

test:
	cd backend && npm test
	cd frontend && npm test

deploy:
	docker-compose up -d
