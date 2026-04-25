# M21: UCC Agent API — Dockerfile (Solution)
# Secure, production-ready container for the FastAPI server.

# 1. Use Python 3.11-slim as base image
#    slim variant is ~150MB vs ~900MB for full — no compiler, no dev headers
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install dependencies FIRST
#    Docker caches each layer. By copying requirements separately,
#    pip install only re-runs when requirements_api.txt changes —
#    not every time you edit server.py.
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# 4. Copy application code
COPY models.py mock_agent.py server.py ./

# 5. Create non-root user for security
#    If an attacker escapes the app, they land as "appuser" (UID 1000),
#    not root. This limits what they can access inside the container.
RUN useradd --create-home appuser
USER appuser

# 6. Expose port 8000
#    This is documentation — it tells operators which port to map.
#    It does NOT actually publish the port (that's docker run -p).
EXPOSE 8000

# 7. Startup command
#    No --reload in production (it watches files and restarts, which
#    wastes CPU and is a security risk in containers).
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
