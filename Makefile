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

