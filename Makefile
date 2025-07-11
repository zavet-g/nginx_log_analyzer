PORT:=8000

run:
	uvicorn apps.main:app --host 0.0.0.0 --port "$(PORT)" --reload

migrations_init:
	alembic revision --autogenerate -m "init"

migrations:
	alembic revision --autogenerate -m "$(MSG)"

migrate:
	alembic upgrade head

migrate_with_data:
	alembic -x data=true upgrade head

stamp:
	alembic stamp head

dump_migrations:
	alembic upgrade head --sql > migration.sql

test:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc

test-unit:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "not integration"

test-integration:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "integration"

test-services:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "services"

test-handlers:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "handlers"

test-cli:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "cli"

test-schemas:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "schemas"

test-fast:
	pytest -vv --maxfail=1 --cov=apps --cov-config .coveragerc -m "not slow and not integration"

lint:
	pre-commit run --all-files

up:
	docker compose up -d

monitor:
	python apps/cli_commands.py monitor /var/log/nginx/access.log

check-logs:
	python apps/cli_commands.py check /var/log/nginx/access.log

dashboard:
	@echo "Откройте http://localhost:8000/static/index.html в браузере"

dev:
	uvicorn apps.main:app --host 0.0.0.0 --port 8000 --reload	

