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
