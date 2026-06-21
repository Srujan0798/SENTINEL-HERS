.PHONY: up down logs test seed worker-% build

# Start all services in detached mode
up:
	docker compose up --build -d

# Stop and remove all containers
down:
	docker compose down

# Tail logs from all services
logs:
	docker compose logs -f

# Build all images without starting
build:
	docker compose build

# Run the test suite (placeholder — expanded by later waves)
test:
	docker compose exec api python -m pytest

# Seed demo data
seed:
	python3 scripts/seed_demo.py

# Run tests locally (fast suite, skips slow anomaly test)
test-fast:
	python3 -m pytest tests/ --ignore=tests/performance --ignore=tests/integration/test_anomaly.py -q

# Run full test suite including ML anomaly (~5 min)
test-full:
	python3 -m pytest tests/ --ignore=tests/performance -q
