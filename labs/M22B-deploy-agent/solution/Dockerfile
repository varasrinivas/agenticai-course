# M22B: UCC Agent — Production Dockerfile (Solution)
# =====================================================
# Build:  docker build -t ucc-agent .
# Run:    docker run -p 8000:8000 --env-file .env ucc-agent
# Test:   curl http://localhost:8000/health

# --- Stage: Base image ---
FROM python:3.11-slim AS base

# --- Working directory ---
WORKDIR /app

# --- Install dependencies (cached layer) ---
# Copy requirements first so this layer is cached when code changes
COPY requirements_api.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy application code ---
COPY models.py .
COPY mock_agent.py .
COPY server.py .

# --- Security: non-root user ---
# Running as root inside a container is a security risk.
# Create a dedicated user with minimal privileges.
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# --- Expose port and health check ---
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# --- Start command ---
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
