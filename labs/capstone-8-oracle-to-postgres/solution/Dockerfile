# Slim base -- python-oracledb runs in thin mode, so no Oracle Instant
# Client install is needed. That single fact is what keeps this image
# under 200 MB instead of over a gigabyte.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /work/solution

# Dependencies first so a code edit does not invalidate the pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Artifacts are bind-mounted in compose, but create the directory so a
# bare `docker run` still works.
RUN mkdir -p /work/artifacts

# Non-root. The agent writes only to artifacts/, which is mounted.
RUN useradd --create-home --uid 10001 migrator \
 && chown -R migrator:migrator /work
USER migrator

CMD ["python", "coordinator.py", "--migrate-all"]
