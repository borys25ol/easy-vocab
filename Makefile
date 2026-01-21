MSG ?= migration

ve:
	python3 -m venv .ve; \
	. .ve/bin/activate; \
	pip install -r requirements.txt

clean:
	test -d .ve && rm -rf .ve

runserver:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

db-upgrade:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(MSG)"

db-downgrade:
	alembic downgrade -1

run_hooks:
	pre-commit run --all-files

lint:
	ruff check .

lint_fix:
	ruff check --fix .

format:
	ruff format .

types:
	mypy .

test:
	pytest

# Docker commands
docker-build:
	docker compose build

docker-up:
	docker compose up

docker-up-d:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-prod-build:
	docker compose -f docker-compose.prod.yml build

docker-prod-up:
	docker compose -f docker-compose.prod.yml --env-file .env.production up -d

docker-prod-down:
	docker compose -f docker-compose.prod.yml down

docker-prod-logs:
	docker compose -f docker-compose.prod.yml logs -f
