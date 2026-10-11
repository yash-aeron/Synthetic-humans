.PHONY: help install test run-backend run-frontend run-demo-app demo docker-up docker-down

help:
	@echo "Synthetic Humans - Behavioral Simulation & Software Testing Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        Install backend and frontend dependencies"
	@echo "  make test           Run automated test suite"
	@echo "  make run-backend    Start FastAPI backend server"
	@echo "  make run-frontend   Start React frontend dev server"
	@echo "  make run-demo-app   Start Toy Target Application (port 5050)"
	@echo "  make demo           Run the end-to-end 100-user demonstration experiment"
	@echo "  make docker-up      Start full stack via Docker Compose"
	@echo "  make docker-down    Stop Docker Compose services"

install:
	python -m pip install -r backend/requirements.txt
	playwright install chromium
	cd frontend && npm install

test:
	pytest tests/ backend/app/tests/ -v

run-backend:
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

run-demo-app:
	python -m uvicorn tests.fixtures.demo_app.server:app --host 0.0.0.0 --port 5050

demo:
	python -m tests.run_demo_experiment

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
