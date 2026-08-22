# Slim base. This agent reads files and parses SQL and XML with the standard
# library -- no database driver, no Oracle client, no JDK. That is why the
# image is small, and it is also why the lab runs on a laptop.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /work/solution

# Dependencies first, so a code edit does not invalidate the pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Both source trees are mounted READ-ONLY in compose. Creating the mount
# points here means a bare `docker run` still starts.
RUN mkdir -p /work/artifacts /work/bh-um-lite /work/bhauthtrack /work/reference-umlite

# Non-root. The agent writes to artifacts/ and bh-um-lite/ and nowhere else --
# which is also what the confine_writes hook enforces, one layer up.
RUN useradd --create-home --uid 10001 modernizer \
 && chown -R modernizer:modernizer /work
USER modernizer

# Phases 1-6, then stop at the human gate. Finalization is a SEPARATE
# invocation on purpose; see deploy/README.md.
CMD ["python", "coordinator.py", "--phase", "all"]
