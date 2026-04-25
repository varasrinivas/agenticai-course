# M21: UCC Agent API — Dockerfile
# Build a secure, production-ready container for the FastAPI server.

# ---------------------------------------------------------------------------
# TODO 1: Use Python 3.11-slim as base image
# Hint: FROM python:3.11-slim
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 2: Set working directory to /app
# Hint: WORKDIR /app
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 3: Copy requirements and install dependencies
#
# Best practice: Copy requirements.txt FIRST, then install.
# This way, Docker caches the dependency layer and only re-runs
# pip install when requirements change (not when your code changes).
#
# Hint:
#   COPY requirements_api.txt .
#   RUN pip install --no-cache-dir -r requirements_api.txt
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 4: Copy application code
#
# Now copy the rest of your application files.
# Hint: COPY . .
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 5: Create non-root user for security
#
# Running as root inside a container is a security risk.
# If an attacker exploits your app, they get root access to the container.
#
# Hint:
#   RUN useradd --create-home appuser
#   USER appuser
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 6: Expose port 8000
# This documents which port the container listens on.
# Hint: EXPOSE 8000
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TODO 7: Set the startup command
#
# Use uvicorn to run the server. Do NOT use --reload in production.
# Hint: CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
# ---------------------------------------------------------------------------
