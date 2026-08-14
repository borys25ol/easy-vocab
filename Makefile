MSG ?= migration

ve:
	uv venv; \
	uv sync --all-groups

clean:
	test -d .ve && rm -rf .ve

runserver:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

run-mcp:
	python -m mcp_service.server

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

format_check:
	ruff format --check .

types:
	ty check .

test:
	pytest

# Plain node, no runner and no packages. The escaping these cover is the only
# thing standing between a stored word and innerHTML.
test_js:
	node tests/js/card-renderer.test.mjs

# Mirrors the CI Checks workflow. Keep the two in step, or a green local run
# stops meaning anything about the pull request.
check: lint format_check types test test_js

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




