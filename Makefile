.PHONY: up, down, build

up:
	docker-compose -f docker-compose.yml up -d

build:
	docker-compose -f docker-compose.yml up --build -d

down:
	docker-compose -f docker-compose.yml down -v
