# M22B: UCC Agent — Production Dockerfile
# ========================================
# Complete the TODOs to build a secure, production-ready container.
#
# Build:  docker build -t ucc-agent .
# Run:    docker run -p 8000:8000 --env-file .env ucc-agent
# Test:   curl http://localhost:8000/health

# TODO 1: Use python:3.11-slim as the base image
# Why slim? Full python image is ~900MB. Slim is ~150MB.
# FROM python:3.11-slim AS base


# TODO 2: Set the working directory inside the container
# WORKDIR /app


# TODO 3: Install dependencies FIRST (Docker layer caching)
# Copy requirements.txt separately so Docker caches this layer.
# If your code changes but requirements don't, pip install is skipped.
# COPY requirements_api.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt


# TODO 4: Copy the application code
# COPY models.py .
# COPY mock_agent.py .
# COPY server.py .


# TODO 5: Create a non-root user (security best practice)
# Running as root inside a container is dangerous — if an attacker
# escapes the app, they have root access to the container filesystem.
# RUN useradd --create-home --shell /bin/bash appuser
# USER appuser


# TODO 6: Expose the port and add a health check
# EXPOSE tells Docker which port the container listens on.
# HEALTHCHECK lets Docker (and orchestrators) know if the app is alive.
# EXPOSE 8000
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1


# TODO 7: Start the application
# Use uvicorn directly (not "python server.py") for production.
# --host 0.0.0.0 makes it accessible from outside the container.
# CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
