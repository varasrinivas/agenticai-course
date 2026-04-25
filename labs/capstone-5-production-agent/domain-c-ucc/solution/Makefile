.PHONY: run test eval docker-build docker-run clean help

# Default target
help:
	@echo "UCC Production Agent — Available Commands"
	@echo "=========================================="
	@echo "  make run            Run the agent in interactive mode"
	@echo "  make query Q='...'  Run a single query"
	@echo "  make eval           Run the full evaluation suite (100 tests)"
	@echo "  make eval-quick     Run evaluation with max 10 tests"
	@echo "  make dashboard      Show metrics dashboard"
	@echo "  make docker-build   Build the Docker image"
	@echo "  make docker-run     Run the agent in Docker"
	@echo "  make docker-eval    Run evaluation in Docker"
	@echo "  make clean          Remove Docker artifacts"
	@echo "  make install        Install Python dependencies"

# Install dependencies
install:
	pip install -r requirements.txt

# Run interactive mode
run:
	python main.py

# Single query
query:
	python main.py --query "$(Q)"

# Run evaluation suite
eval:
	python main.py --eval

# Quick eval (10 tests)
eval-quick:
	python main.py --eval --max-tests 10

# Show dashboard
dashboard:
	python main.py --dashboard

# Docker commands
docker-build:
	docker build -t ucc-production-agent .

docker-run:
	docker run -it --rm \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		-p 8080:8080 \
		ucc-production-agent

docker-eval:
	docker run -it --rm \
		-e ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY) \
		ucc-production-agent --eval

# Run with docker-compose
compose-up:
	docker-compose up -d

compose-down:
	docker-compose down

# Clean up
clean:
	docker-compose down -v 2>/dev/null || true
	docker rmi ucc-production-agent 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
