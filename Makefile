.PHONY: up down newdata

up:
	docker compose up --build

down:
	docker compose down

# Wipe database and start with fresh demo data
newdata:
	docker compose down -v
	SEED_ON_STARTUP=true docker compose up --build
