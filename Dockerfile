FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUARRY_INTERACTIVE=0

# Create non-root user
RUN adduser --disabled-password --gecos "" app && \
    mkdir -p /app && chown -R app:app /app
WORKDIR /app

# Install build deps for scientific stack if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install
COPY . /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir .

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["quarry"]
