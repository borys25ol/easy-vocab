ve:
	python3 -m venv .ve; \
	. .ve/bin/activate; \
	pip install -r requirements.txt

clean:
	test -d .ve && rm -rf .ve

runserver:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

run_hooks:
	pre-commit run --all-files

style:
	flake8 app tests && isort app tests --diff && black app tests --check

types:
	mypy --config-file setup.cfg .

format:
	black app tests

lint:
	flake8 app tests
	isort app tests --diff
	black app tests --check

test:
	pytest

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-up-d:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-prod-build:
	docker-compose -f docker-compose.prod.yml build

docker-prod-up:
	docker-compose -f docker-compose.prod.yml up -d

docker-prod-down:
	docker-compose -f docker-compose.prod.yml down

docker-prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f
