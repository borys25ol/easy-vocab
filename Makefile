ve:
	python3 -m venv .ve; \
	. .ve/bin/activate; \
	pip install -r requirements.txt

clean:
	test -d .ve && rm -rf .ve

runserver:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 --reload

run_hooks:
	pre-commit run --all-files

style:
	flake8 main tests && isort main tests --diff && black main tests --check

types:
	mypy --config-file setup.cfg .

format:
	black main --check

lint:
	flake8 main tests
	isort main tests --diff
	black main tests --check
