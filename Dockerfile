FROM ghcr.io/astral-sh/uv:alpine AS uv_build
WORKDIR /app
COPY pyproject.toml ./
RUN uv export --no-hashes --no-emit-project --format requirements-txt > requirements.txt

FROM python:3.13-slim-bookworm

# Set environment variables for better logging and behavior in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies if needed (e.g. for psycopg2, though -binary is used)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

COPY --from=uv_build /app/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env ./
COPY prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

# Use uvicorn directly. FastMCP by default runs on 8000 when using HTTP transport.
# If prestart.sh is needed, we can call it in CMD or via an ENTRYPOINT.
# We use exec to ensure signals are passed correctly to the python process.
CMD ["/bin/bash", "-c", "/app/prestart.sh && exec python -m app.slack_reaction_notifier"]

EXPOSE 8000
